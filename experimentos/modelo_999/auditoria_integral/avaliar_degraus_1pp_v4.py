"""Busca de metas em passos de1pp; sem retuning ou troca de população."""
import pathlib,json
from avaliar_taxa_acerto_v4 import lower_exact
ROOT=pathlib.Path(__file__).resolve().parent

def scan(successes,trials,confidence=.95):
 lower=lower_exact(successes,trials,confidence)
 stages=[{'target_pct':target,'supported_under_binomial_assumptions':lower is not None and lower>=target/100} for target in range(99,0,-1)]
 return {'lower_bound_pct':None if lower is None else 100*lower,'highest_supported_target_pct':next((x['target_pct'] for x in stages if x['supported_under_binomial_assumptions']),None),'stages':stages}

def run():
 source=json.loads((ROOT/'resultado_metas_acerto_v4.json').read_text());presidential=scan(source['eligible_successes'],source['eligible_external_presidential_elections'])
 report={'policy':'v4-degraus-1pp-v2','step_percentage_points':1,'targets_start_pct':99,'targets_stop_pct':1,'previous_floor95_superseded_by_user_request':True,'model_unchanged':True,'target_population_unchanged':'segundo_turno_presidencial_nacional','statistical_confidence_pct':95,'independent_external_presidential_trials':source['eligible_external_presidential_elections'],'presidential':presidential,'certification_granted':False,'decision':'SEM_META_POSITIVA_DEMONSTRADA' if presidential['highest_supported_target_pct'] is None else 'META_NUMERICA_CONDICIONAL_A_HIPOTESES','warning':'Reduzir a meta nao cria evidencia independente. Nao transformar checkpoints em novas eleicoes, nem trocar presidencial por municipal para forcar aprovacao.'}
 (ROOT/'resultado_degraus_1pp_v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='presidential'},ensure_ascii=False));print(json.dumps({'stages_evaluated':len(presidential['stages']),'highest_supported':presidential['highest_supported_target_pct']}));return report
if __name__=='__main__':run()
