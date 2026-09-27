"""Thin optional adapter to installed canonical core; never issues authority.

Not a standalone generation engine. A supported, separately issued stage is
required. Existing closed research scopes must not be reopened for release.
"""
from pathlib import Path
import sys,importlib.util
from .cli import require,sha,publish,message_hash
def run_registered(core,cfg,refs,output,registration_sha256):
    require(not output.exists(),'OUTPUT_EXISTS')
    sys.path.insert(0,str(core/'src'))
    from aiden_local.bridge import research_phase as phase
    from aiden_local.bridge.decision_store import read_receipt
    # registry performs the existing live mandate/identity/deadline gates.
    registration=phase.registry(core);stage=phase.stage_store(core)
    require(sha(stage/'registration/receipt.json')==registration_sha256,'REGISTRATION_BINDING')
    bundles=registration['proposal']['bundles'];seen=set()
    for b in bundles:
        s=b['research'];uid=s['task_id'];require(uid in refs and uid not in seen,'REGISTRATION_ITEMS');seen.add(uid)
        require(s['condition']=='P0' and s['contract']=='ifeval-native-v1','P0_ONLY')
        require(s['max_new_tokens']==cfg['generation']['max_new_tokens'] and b['model']==cfg['model']['repository'] and b['revision']==cfg['model']['revision'],'MODEL_CONFIG')
        case=b['cases'][0];require((core/case['prompt']).read_bytes()==refs[uid]['prompt'].encode() and case['message_sha256']==message_hash(refs[uid]),'EXACT_INPUT')
        from aiden_local.bridge.research_runtime import generation_config
        require(generation_config(core,b).model_dump()==cfg['generation'],'GENERATION')
    require(bool(bundles),'EMPTY_REGISTRATION')
    publish(output,dict(state='REGISTERED_DISPATCH_INTENT',registration_sha256=registration_sha256,items=sorted(seen)))
    # Existing network sandbox, helper, locks, ownership, cancellation and closeout.
    result=phase.run(core)
    publish(output.with_suffix('.execution.json'),result)
    path=core/'runs/phase-b-output-public-20260922-004844/experiment.py'
    spec=importlib.util.spec_from_file_location('release_existing_collector',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    publish(output.with_suffix('.ledger.json'),dict(rows=m.collect()))
    return result
