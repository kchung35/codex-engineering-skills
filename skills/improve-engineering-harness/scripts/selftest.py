from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
PY=sys.executable

def run(args, ok=True):
    r=subprocess.run([PY,str(HERE/args[0]),*args[1:]],capture_output=True,text=True)
    if ok and r.returncode!=0: raise AssertionError(r.stdout+r.stderr)
    if not ok and r.returncode==0: raise AssertionError('expected failure: '+' '.join(args))
    return r

def dump(p,o): p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')

def main():
    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        # deterministic gap should prefer a mechanical check
        cl=t/'class.json'; dump(cl,{'primary':'DETERMINISTIC_REASONING_GAP'})
        r=run(['select_remediation.py','--classification',str(cl)])
        assert 'MECHANICAL_CHECK' in r.stdout
        # new Skill without boundary evidence must fail
        pr=t/'proposal.json'; dump(pr,{'selected_remediation':'NEW_SKILL','new_skill_boundary':{'distinct_user_intent':True}})
        run(['skill_boundary_check.py',str(pr)],ok=False)
        # complete new Skill boundary passes
        dump(pr,{'selected_remediation':'NEW_SKILL','new_skill_boundary':{k:True for k in ['distinct_user_intent','different_procedure','different_tools_or_safety','independently_useful','not_stage_of_existing','not_deterministic_only','not_reference_only','routing_nonoverlap']}})
        run(['skill_boundary_check.py',str(pr)])

        # regression gate blocks unresolved historical failure
        plan=t/'plan.json'; res=t/'res.json'
        dump(plan,{'failing_cases':['F1'],'control_cases':['C1']})
        dump(res,{'required_case_results':[{'case_id':'F1','status':'FAIL','kind':'FAILURE'},{'case_id':'C1','status':'PASS','kind':'CONTROL'}]})
        run(['regression_gate.py','--plan',str(plan),'--results',str(res)],ok=False)
        dump(res,{'required_case_results':[{'case_id':'F1','status':'PASS','kind':'FAILURE'},{'case_id':'C1','status':'PASS','kind':'CONTROL'}]})
        run(['regression_gate.py','--plan',str(plan),'--results',str(res)])
        # protected metric regression blocks evaluation
        ep=t/'ep.json'; bef=t/'before.json'; aft=t/'after.json'
        dump(ep,{'metrics':[{'name':'routing_accuracy','direction':'MAXIMIZE','minimum_after':0.95,'maximum_regression':0.0}]})
        dump(bef,{'metrics':{'routing_accuracy':0.98}}); dump(aft,{'metrics':{'routing_accuracy':0.96}})
        run(['compare_evaluation.py','--plan',str(ep),'--before',str(bef),'--after',str(aft)],ok=False)
        dump(aft,{'metrics':{'routing_accuracy':0.99}})
        run(['compare_evaluation.py','--plan',str(ep),'--before',str(bef),'--after',str(aft)])
        # ordinary one-off friction cannot advance to remediation without recurrence/reproducer/exception
        cases=t/'cases'
        r=run(['init_improvement.py','--title','one off friction','--root',str(cases)])
        cased=Path(r.stdout.strip())
        case=json.loads((cased/'case.json').read_text()); case['failure_statement']='Agent missed one optional note'; case['impact']='Minor rework'; dump(cased/'case.json',case)
        (cased/'signals.jsonl').write_text(json.dumps({'id':'S1','observation':'one miss'})+'\n',encoding='utf-8')
        dump(cased/'classification.json',{'primary':'MISSING_INVARIANT','contributing':[],'rationale':'','confidence':'MEDIUM'})
        dump(cased/'causal-model.json',{'status':'SUFFICIENT_FOR_REMEDIATION','primary_mechanism':'missing invariant','chain':['task','miss'],'alternatives':[],'evidence':['S1']})
        dump(cased/'proposal.json',{'proposal_id':'P1','classification':'MISSING_INVARIANT','mechanism':'missing invariant','selected_remediation':'MECHANICAL_CHECK','target_components':['checker'],'change_summary':'add checker','why_this_layer':'deterministic','alternatives_rejected':[],'blast_radius':'LOCAL','reversibility':'HIGH','new_skill_boundary':None,'regression_obligation':'fixture','security_impact':'NONE'})
        run(['harness_gate.py',str(cased),'--to','REMEDIATION'],ok=False)
        case['deterministic_reproducer']=True; dump(cased/'case.json',case)
        run(['harness_gate.py',str(cased),'--to','REMEDIATION'])

        # descriptions should parse without crashing
        skills=t/'skills'; skills.mkdir()
        for name,desc in [('a','diagnose unexplained workflow failures'),('b','publish reviewed changes to production')]:
            d=skills/name; d.mkdir(); (d/'SKILL.md').write_text(f'---\nname: {name}\ndescription: "{desc}"\n---\n',encoding='utf-8')
        run(['detect_skill_overlap.py',str(skills),'--threshold','0.9'])
    print('SELFTEST PASS')
if __name__=='__main__': main()
