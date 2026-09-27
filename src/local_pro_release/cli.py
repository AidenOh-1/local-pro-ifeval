"""run/score/report only. No model import in offline commands; no authority creation."""
from pathlib import Path
import argparse,hashlib,json,os,random,sys,tempfile

PACKAGE=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text_hash(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def require(ok,code):
    if not ok:raise ValueError(code)
def publish(path,value):
    """Same-filesystem atomic no-clobber publication; failed writes leave no final file."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.exists(),'OUTPUT_EXISTS')
    raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    fd,temp=tempfile.mkstemp(prefix='.release-tmp-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.link(temp,path)
    finally:os.unlink(temp)
def settings(root):
    cfg=read(root/'config.json')
    for name,h in cfg['hashes'].items():
        p=(root/name).resolve();require(p.is_relative_to(root.resolve()),'PATH_ESCAPE');require(p.is_file(),'MISSING_EVALUATION_ASSET:'+name);require(sha(p)==h,'ARTIFACT_HASH_MISMATCH')
    return cfg
def dataset(root,cfg):
    p=root/cfg['dataset']['path'];require(sha(p)==cfg['dataset']['sha256'],'DATA_HASH')
    rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    require(len(rows)==cfg['dataset']['count'],'DATA_COUNT')
    require(len({x['key'] for x in rows})==len(rows),'DUPLICATE_UID')
    require(len({x['prompt'] for x in rows})==len(rows),'DUPLICATE_PROMPT')
    return {f"ifeval.{x['key']:06}":x for x in rows}
def messages(row):
    # Deliberately excludes instruction_id_list, kwargs, key and all evaluator data.
    return [dict(role='user',content=row['prompt'])]
def message_hash(row):return text_hash(json.dumps(messages(row),ensure_ascii=False,sort_keys=True))
def response_rows(path,refs,cfg):
    source=read(path)['items'];seen=set();ready=[];blocked=[]
    for x in source:
        uid=x['uid'];require(uid in refs and uid not in seen,'DUPLICATE_OR_UNKNOWN_RESPONSE');seen.add(uid)
        require(isinstance(x.get('response'),str),'RESPONSE_MISSING_NOT_EMPTY')
        require(text_hash(x['response'])==x['response_sha256'],'RESPONSE_HASH')
        require(x['messages_sha256']==message_hash(refs[uid]),'MESSAGE_BINDING')
        require(x['configuration']==cfg['generation'],'GENERATION_BINDING')
        require(x['finish_reason'] in ('stop','length'),'FINISH_REASON')
        if x.get('cleanup_confirmed') is not True or x.get('ownership_state')!='SEALED':blocked.append(uid)
        else:ready.append(x)
    return ready,blocked
def block_network(event,args):
    if event in ('socket.connect','socket.getaddrinfo','socket.gethostbyname','socket.gethostbyaddr'):raise RuntimeError('OFFLINE_EVALUATOR_NETWORK_DENIED')
def original_scorer(root):
    # Exact vendored author source; no AST rewriting or scoring normalization.
    from importlib.metadata import version
    for line in (root/'requirements.lock.txt').read_text().splitlines():
        if not line.strip():continue
        name,pinned=line.split()[0].split('==')
        require(version(name)==pinned,'EVALUATOR_DEPENDENCY_VERSION:'+name)
    sys.path.insert(0,str(root/'vendor'));os.environ['NLTK_DATA']=str(root/'nltk_data')
    import nltk
    nltk.data.path[:]=[str(root/'nltk_data')]
    from instruction_following_eval import evaluation_lib
    return evaluation_lib
def score_one(lib,ref,response):
    from langdetect import DetectorFactory
    inp=lib.InputExample(key=ref['key'],instruction_id_list=ref['instruction_id_list'],prompt=ref['prompt'],kwargs=ref['kwargs'])
    DetectorFactory.seed=42;saved=random.getstate()
    try:
        random.seed(42);strict=lib.test_instruction_following_strict(inp,{inp.prompt:response})
        random.seed(42);loose=lib.test_instruction_following_loose(inp,{inp.prompt:response})
    finally:random.setstate(saved)
    return dict(strict_prompt=strict.follow_all_instructions,loose_prompt=loose.follow_all_instructions,strict_instructions=strict.follow_instruction_list,loose_instructions=loose.follow_instruction_list,instruction_total=len(inp.instruction_id_list))
def do_score(root,responses,output):
    cfg=settings(root);refs=dataset(root,cfg);rows,blocked=response_rows(responses,refs,cfg)
    lib=original_scorer(root);items=[]
    for x in rows:
        result=score_one(lib,refs[x['uid']],x['response'])
        items.append(dict(uid=x['uid'],run_id=x['run_id'],response_sha256=x['response_sha256'],finish_reason=x['finish_reason'],empty_response=not bool(x['response'].strip()),metrics=x.get('metrics'),**result))
    value=dict(schema=1,kind='IFEVAL_ORIGINAL_SCORE',config_sha256=sha(root/'config.json'),responses_sha256=sha(responses),dataset_sha256=cfg['dataset']['sha256'],planned=len(refs),items=items,blocked=blocked,missing=sorted(set(refs)-{x['uid'] for x in rows}-set(blocked)),model_calls=0)
    publish(output,value);return dict(scored=len(items),blocked=len(blocked),missing=len(value['missing']))
def summary(score,refs):
    require(isinstance(score,dict) and all(isinstance(score.get(k),list) for k in ('items','blocked','missing')),'SCORE_SCHEMA')
    require(type(score.get('planned')) is int,'PLANNED_COUNT')
    for k in ('blocked','missing'):
        require(all(isinstance(v,str) for v in score[k]) and len(set(score[k]))==len(score[k]),'DUPLICATE_COVERAGE')
    items=score['items'];uids=[x['uid'] for x in items]
    require(len(set(uids))==len(uids) and set(uids)<=set(refs),'SCORE_UIDS')
    require(score['planned']==len(refs),'PLANNED_COUNT')
    require(set(uids).isdisjoint(score['blocked']) and set(uids).isdisjoint(score['missing']) and set(score['blocked']).isdisjoint(score['missing']),'COVERAGE_OVERLAP')
    require(set(uids)|set(score['blocked'])|set(score['missing'])==set(refs),'COVERAGE_GAP')
    out=dict(status='COMPLETE' if len(items)==len(refs) else 'PARTIAL',planned=len(refs),responses_scored=len(items),blocked=len(score['blocked']),missing=len(score['missing']),length=sum(x['finish_reason']=='length' for x in items),metrics={})
    for mode in ('strict','loose'):
        for x in items:
            v=x[mode+'_instructions'];require(isinstance(v,list) and type(x['instruction_total']) is int and len(v)==len(refs[x['uid']]['instruction_id_list'])==x['instruction_total'] and all(type(b) is bool for b in v),'INSTRUCTION_DENOMINATOR')
            require(type(x[mode+'_prompt']) is bool and x[mode+'_prompt']==all(v),'PROMPT_CONJUNCTION')
        for level in ('prompt','instruction'):
            num=sum(x[mode+'_prompt'] for x in items) if level=='prompt' else sum(sum(x[mode+'_instructions']) for x in items)
            den=len(items) if level=='prompt' else sum(x['instruction_total'] for x in items)
            out['metrics'][mode+'_'+level]=dict(correct=num,denominator=den,partial_accuracy=num/den if den else None,full_accuracy=num/den if den and out['status']=='COMPLETE' else None)
    out['observed_resources']={}
    for name in ('generated_tokens','prompt_tokens','wall_seconds'):
        values=[(x.get('metrics') or {}).get(name) for x in items]
        known=[v for v in values if type(v) in (int,float)]
        out['observed_resources'][name]=dict(coverage=len(known),responses=len(items),sum=sum(known) if len(known)==len(items) and items else None)
    return out
def report_inputs(root,scores,coverage=None):
    cfg=read(root/'config.json');sc=read(scores)
    require(sc.get('schema')==1,'SCORE_SCHEMA')
    if coverage is None:
        base=root/'results/v0.1';binding=read(base/'binding.json')
        require(sha(scores)==binding['scores.json'],'SCORE_BINDING')
        require(sha(base/'coverage.json')==binding['coverage.json'],'COVERAGE_BINDING')
        c=read(base/'coverage.json')
        require(sc['kind']=='IFEVAL_ORIGINAL_SCORE' and sc['config_sha256']==sha(root/'config.json') and sc['dataset_sha256']==cfg['dataset']['sha256'],'SCORE_BINDING')
    else:
        require(sc.get('kind')=='SYNTHETIC_VERDICT_EXAMPLE','EXAMPLE_ONLY')
        c=read(coverage)
    require(c.get('schema')==1 and c.get('kind')=='VERDICT_COVERAGE_NOT_PROMPT_DATA','COVERAGE_SCHEMA')
    refs=c['refs'];require(isinstance(refs,dict) and bool(refs),'COVERAGE_SCHEMA')
    for uid,v in refs.items():
        require(isinstance(uid,str) and isinstance(v,dict) and set(v)=={'instruction_id_list'} and isinstance(v['instruction_id_list'],list) and len(v['instruction_id_list'])>0,'COVERAGE_SCHEMA')
    return cfg,refs,sc
def do_report(root,scores,output,coverage=None):
    cfg,refs,sc=report_inputs(root,scores,coverage)
    out=summary(sc,refs);out.update(config_sha256=sha(root/'config.json'),scores_sha256=sha(scores),public_release=False,independent_hidden=False)
    if coverage is not None:out['synthetic_example_not_benchmark']=True
    dest=Path(output);require(not dest.exists(),'OUTPUT_EXISTS');dest.mkdir(parents=True)
    publish(dest/'summary.json',out)
    title='Synthetic usage example — NOT benchmark measurement' if coverage is not None else 'Local Pro P0 / IFEval'
    lines=['# '+title+' — '+out['status'],'',f"Coverage: {len(sc['items'])}/{len(refs)} items. Missing {out['missing']}; unresolved {out['blocked']}.",'','| Metric | Correct | Scored denominator | Accuracy |','|---|---:|---:|---:|']
    for k,v in out['metrics'].items():lines.append(f"| {k} | {v['correct']} | {v['denominator']} | {v['partial_accuracy']} |")
    lines+=['', 'Observed cached-run resources: '+json.dumps(out['observed_resources'],sort_keys=True), '', 'wall_seconds is generation time, not end-to-end throughput.', '', 'Stored-response rescoring, not new model inference. Public, development-exposed data; not hidden or third-party certification.']
    publish(dest/'scorecard.md','\n'.join(lines)+'\n');return out
def do_run(root,output,dry_run,core_root=None,registration_sha256=None):
    if not dry_run:require(core_root is not None and registration_sha256 is not None,'VALID_EXISTING_REGISTRATION_REQUIRED')
    cfg=settings(root);refs=dataset(root,cfg)
    plan=dict(kind='DRY_RUN_NOT_MODEL_EXECUTION',config_sha256=sha(root/'config.json'),generation=cfg['generation'],items=[dict(uid=u,messages=messages(r),messages_sha256=message_hash(r)) for u,r in refs.items()],model_calls=0,authority_created=False,tokenizer_template_validation='PINNED_IDENTITIES_ONLY_NO_TOKENIZER_OR_MODEL_LOAD')
    if dry_run:publish(output,plan);return dict(state=plan['kind'],planned=len(refs),model_calls=0)
    require(core_root is not None and registration_sha256 is not None,'VALID_EXISTING_REGISTRATION_REQUIRED')
    # Optional local dependency, never vendored authority files or synthesized tokens.
    from .runtime import run_registered
    return run_registered(Path(core_root),cfg,refs,Path(output),registration_sha256)
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=PACKAGE);sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--dry-run',action='store_true');r.add_argument('--core-root',type=Path);r.add_argument('--registration-sha256');r.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('score');s.add_argument('--responses',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('report');s.add_argument('--scores',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
    r=sub.choices['report'];r.add_argument('--coverage',type=Path,help='Synthetic example coverage only; not an alternative benchmark reference')
    a=p.parse_args()
    if a.command=='score':sys.addaudithook(block_network)
    try:
        if a.command=='run':result=do_run(a.root,a.output,a.dry_run,a.core_root,a.registration_sha256)
        elif a.command=='score':result=do_score(a.root,a.responses,a.output)
        else:result=do_report(a.root,a.scores,a.output,a.coverage)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as e:
        print(json.dumps(dict(state='BLOCKED_OR_ERROR',error_type=type(e).__name__,reason=str(e))),file=sys.stderr);raise SystemExit(2)
