from __future__ import annotations
import argparse
from common import load_json, nonempty, die

def main():
    p=argparse.ArgumentParser(); p.add_argument('--case',required=True); p.add_argument('--proposal',required=True); p.add_argument('--evaluation-plan',required=True); a=p.parse_args()
    c,pr,ev=map(load_json,[a.case,a.proposal,a.evaluation_plan]); errs=[]
    for k in ['failure_statement','impact']:
        if not nonempty(c.get(k)): errs.append(f'case.{k} missing')
    for k in ['classification','mechanism','selected_remediation','target_components','change_summary','why_this_layer','regression_obligation']:
        if not nonempty(pr.get(k)): errs.append(f'proposal.{k} missing')
    if pr.get('selected_remediation')=='NEW_SKILL' and not pr.get('new_skill_boundary'): errs.append('new Skill boundary evidence missing')
    allowed={'REGRESSION_FIXTURE','MECHANICAL_CHECK','TOOL_OR_ENVIRONMENT_CAPABILITY','OBSERVABILITY_OR_INSPECTION_TOOL','SOURCE_OF_TRUTH_OR_GENERATED_DOC','REPOSITORY_MAP_OR_INDEX','AGENTS_INVARIANT','UPDATE_EXISTING_SKILL','MERGE_OR_NARROW_SKILLS','ROUTING_DESCRIPTION_OR_MAP','STRUCTURED_SCHEMA_OR_OUTPUT','FAIL_CLOSED_MECHANICAL_GATE','NEW_SKILL','OTHER'}
    if pr.get('selected_remediation') not in allowed: errs.append('proposal.selected_remediation invalid')
    if not nonempty(ev.get('failure_mechanism')): errs.append('evaluation-plan.failure_mechanism missing')
    if not ev.get('failing_cases'): errs.append('evaluation-plan requires failing_cases')
    if pr.get('blast_radius') in ['BROAD','ORGANIZATION'] and not ev.get('control_cases'): errs.append('broad change requires control_cases')
    if not ev.get('metrics'): errs.append('evaluation-plan requires metrics')
    if errs: die(['BLOCKED: '+e for e in errs])
    print('PASS proposal and evaluation plan')
if __name__=='__main__': main()
