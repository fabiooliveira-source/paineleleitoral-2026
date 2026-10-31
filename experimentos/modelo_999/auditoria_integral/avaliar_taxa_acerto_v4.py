"""Avalia metas aninhadas99..95, sem retuning nem inflar n com checkpoints."""
import math,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent

def lower_exact(successes,trials,confidence=.95):
    if not isinstance(trials,int) or not isinstance(successes,int) or trials<0 or not 0<=successes<=trials or not 0<confidence<1:
        raise ValueError('contagens ou confianca invalidas')
    if trials==0:return None
    if successes==0:return 0.
    alpha=1-confidence
    if successes==trials:return alpha**(1/trials)
    def tail(p):
        terms=[math.lgamma(trials+1)-math.lgamma(k+1)-math.lgamma(trials-k+1)+k*math.log(p)+(trials-k)*math.log1p(-p) for k in range(successes,trials+1)]
        maximum=max(terms);return math.exp(maximum)*math.fsum(math.exp(x-maximum) for x in terms)
    lo,hi=0.,1.
    for _ in range(100):
        mid=(lo+hi)/2
        if tail(mid)>alpha:hi=mid
        else:lo=mid
    return (lo+hi)/2

def min_all_success_trials(target,confidence=.95):
    if not 0<target<1 or not 0<confidence<1:raise ValueError('meta invalida')
    return math.ceil(math.log(1-confidence)/math.log(target))

def evaluate():
    policy=json.loads((ROOT/'politica_taxa_acerto_v4.json').read_text());events=[]
    for year in [2018,2022,2020]:
        result=json.loads((ROOT/f'resultado_v4_{year}.json').read_text());data=json.loads((ROOT/f'entradas_pareadas_v4_{year}.json').read_text())
        point=next(x for x in result['checkpoints'] if x['threshold_pct']==5)
        predicted=point['estimate_a_pct'];target=100*data['target_a'];correct=predicted is not None and predicted!=50 and target!=50 and (predicted>50)==(target>50)
        comparable=year in [2018,2022];external=result['role'].startswith('external_');development=year in policy['exclude_development_elections']
        events.append({'contest_id':f'{year}-presidente' if comparable else '2020-prefeito-71072','year':year,'correct_winner_at_5_pct':correct,'scope':result['role'],'development':development,'comparable_to_target_population':comparable,'eligible_independent_external':external and comparable and not development})
    assert len(set(x['contest_id'] for x in events))==len(events)
    eligible=[x for x in events if x['eligible_independent_external']];n=len(eligible);k=sum(x['correct_winner_at_5_pct'] for x in eligible);bound=lower_exact(k,n,policy['statistical_confidence_pct']/100)
    stages=[]
    for target in policy['targets_descending_pct']:
        passed=bound is not None and bound>=target/100
        stages.append({'target_pct':target,'supported_by_eligible_evidence':passed,'minimum_fixed_sample_if_zero_failures':min_all_success_trials(target/100,policy['statistical_confidence_pct']/100),'status':'SUPPORTED_CONDITIONALLY_ON_SAMPLING_ASSUMPTIONS' if passed else 'NOT_DEMONSTRATED'})
    chosen=next((x['target_pct'] for x in stages if x['supported_by_eligible_evidence']),None)
    report={'policy_version':policy['version'],'model_unchanged':True,'targets_evaluated_pct':policy['targets_descending_pct'],'floor_pct':policy['floor_pct'],'selected_supported_target_pct':chosen,'eligible_external_presidential_elections':n,'eligible_successes':k,'eligible_lower_bound_pct':None if bound is None else 100*bound,'descriptive_cases_correct':sum(x['correct_winner_at_5_pct'] for x in events),'descriptive_cases_total':len(events),'descriptive_accuracy_is_not_certification':True,'cases':events,'stages':stages,'decision':'TARGET_NOT_DEMONSTRATED_AT_OR_ABOVE_95' if chosen is None else 'NUMERICAL_TARGET_SUPPORTED_SUBJECT_TO_SAMPLING_AND_DATA_AUTHENTICITY','integral_certification_granted':False,'limitations':['Confidence level95 is distinct from accuracy targets99..95.','2018 and2022 were used for development; municipal2020 is not an external national-presidential validation.','Binomial inference assumes comparable independent representative trials and a fixed sampling/testing plan.','Zero-failure sample counts are optimistic planning values, not a guarantee or permission to reuse the same election.','Lowering the target does not resolve source availability, operational integration or independent-review requirements.'],'method_source':'https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm'}
    (ROOT/'resultado_metas_acerto_v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':evaluate()
