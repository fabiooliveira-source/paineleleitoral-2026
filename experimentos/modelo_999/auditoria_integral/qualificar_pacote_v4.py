"""Qualifica apenas o escopo explicitamente demonstrado; nunca autocertifica 99,9%."""
import pathlib,json,hashlib,subprocess,sys,os,datetime
ROOT=pathlib.Path(__file__).resolve().parent

def run():
 package=json.loads((ROOT/'manifesto_pacote_v4.json').read_text());checked=[]
 for row in package['files']:
  f=ROOT/row['name'];actual=hashlib.sha256(f.read_bytes()).hexdigest();assert actual==row['sha256'],'Pinned file changed: '+row['name'];checked.append(row['name'])
 proc=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT),'-p','test_preditor_causal_v*.py'],capture_output=True,text=True);print(proc.stdout+proc.stderr,flush=True);assert proc.returncode==0,'Unit suite failed'
 from avaliar_v4_pareado import run as evaluate
 from verificar_v4_fracoes import run as verify
 results={};checks={}
 for year in [2018,2022,2020]:results[str(year)]=evaluate(year);checks[str(year)]=verify(year)
 numeric=all(r['all_numerical_criteria_passed'] for r in results.values())
 out={'state':'QUALIFICADO_NO_ESCOPO_REPLAY_PAREADO' if numeric else 'QUALIFICACAO_NUMERICA_REPROVADA','certificacao_integral_concedida':False,'model':'audit-v4-paired-ratio','reviewed_scope':'Predictor byte identity, deterministic bounds, synchronized matched-ledger replays, numerical external municipal2020 test, programmed stress checks.','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reproduction_environment':'GitHubActions' if os.environ.get('GITHUB_ACTIONS')=='true' else 'local','github_run_id':os.environ.get('GITHUB_RUN_ID'),'github_commit':os.environ.get('GITHUB_SHA'),'files_verified':len(checked),'unit_tests_exit_code':proc.returncode,'stress_checks_passed':sum(r['stress_checks_passed'] for r in results.values()),'fraction_checks':checks,'results':{y:{k:v for k,v in r.items() if k!='checkpoints'} for y,r in results.items()},'unresolved_integral_requirements':{'authenticated_contemporary_public_snapshots':False,'authenticated_first_round_reference_asof_prediction':False,'authenticated_electorate_asof_prediction':False,'production_matched_section_feed_integrated':False,'probabilities_calibrated_across_independent_elections':False,'independent_expert_review_replicated':False},'limits':['Municipal external test is not national presidential operational certification.','Deterministic bounds are conditional on no future count revision and valid remaining-electorate upper bound.','Same-author tests and CI reproduction are not independent expert review.','2018 and2022 are development;2020 becomes examined after this test.']}
 (ROOT/'qualificacao_v4_escopo.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'state':out['state'],'certificacao_integral_concedida':False,'stress_checks_passed':out['stress_checks_passed']},ensure_ascii=False),flush=True)
 return out
if __name__=='__main__':run()
