"""Deterministic stdlib SVG charts from validated stored verdicts; no model imports."""
from pathlib import Path
import sys,json,html,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from local_pro_release.cli import report_inputs,summary,publish
ROOT=Path(__file__).resolve().parents[1]
def chart(rows,title,caption,footer):
    width=1100;height=210+len(rows)*82
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',f'<title>{html.escape(title)}</title>',f'<rect width="{width}" height="{height}" fill="#f8fafc"/>','<g font-family="Arial, sans-serif" fill="#172033">']
    def text(x,y,s,size=16):parts.append(f'<text x="{x}" y="{y}" font-size="{size}">{html.escape(s)}</text>')
    text(30,38,title,24);text(30,65,caption,14)
    for tick in range(0,101,20):
        x=365+tick*4.8;parts.append(f'<path d="M{x} 90 V{height-90}" stroke="#d9e2ec"/>');text(x-10,height-66,str(tick)+'%',13)
    for i,(label,value,detail,primary) in enumerate(rows):
        y=110+i*82;text(30,y+19,label,17);text(30,y+41,detail,12)
        color='#166b69' if primary else '#667b9b'
        parts.append(f'<rect x="365" y="{y}" width="{value*4.8:.5f}" height="34" fill="{color}" rx="4" data-value="{value:.10f}"/>')
        text(865,y+23,f'{value:.2f}%'+(' · '+detail if detail.replace('/','').isdigit() else ''),16)
    for i,line in enumerate(footer):text(30,height-37+i*19,line,13)
    return '\n'.join(parts+['</g></svg>'])+'\n'
def build(output):
    _,refs,scores=report_inputs(ROOT,ROOT/'results/v0.1/scores.json');data=summary(scores,refs)
    labels={'strict_prompt':'Strict prompt · PRIMARY','strict_instruction':'Strict instruction · auxiliary','loose_prompt':'Loose prompt · auxiliary','loose_instruction':'Loose instruction · auxiliary'}
    rows=[(labels[k],v['full_accuracy']*100,f"{v['correct']}/{v['denominator']}",k=='strict_prompt') for k,v in data['metrics'].items()]
    own=chart(rows,'Local Pro v0.1 · IFEval','541 prompts / 834 instruction checks · Original scorer · Public benchmark self-evaluation',['78 cached + 463 new · 9 length-limited outputs included · Zero retries','Fixed P0; no general-superiority or independent-certification claim.'])
    publish(output/'ifeval.svg',own)
    ext=json.loads((ROOT/'results/external_references.json').read_text())
    rows=[('Local Pro P0',431/541*100,'Own measurement · 2026-09-24/25 · 431/541',True)]
    for x in ext['rows']:
        if not x['verified']:continue
        assert x['exact_metric']=='IFEval English strict prompt accuracy' and 0<=x['value']<=100
        rows.append((x['snapshot'],x['value'],'DeepSeek report · Evaluation date not stated',False))
    publish(output/'external-context.svg',chart(rows,'Historical IFEval reference context','Different evaluation setups; not a head-to-head comparison.',['Source: DeepSeek-V3 README · Fixed source revision in external_references.json','External: 8K output, repeated sampling; Local Pro: 2048 output, one response/item.']))
    return data
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.output)
