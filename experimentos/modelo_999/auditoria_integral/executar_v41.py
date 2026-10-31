"""Executa V4 congelada e produz contrato JSON experimental para o painel.
Não coleta dados, não implanta na main e não gera probabilidades calibradas.
"""
import argparse,hashlib,json,pathlib,os,tempfile,sys
from preditor_v4_guardado import predict_guarded
ROOT=pathlib.Path(__file__).resolve().parent

def model_identity():
    manifest=json.loads((ROOT/'congelamento_v4.json').read_text())
    expected=next(x['sha256'] for x in manifest['files'] if x['path'].endswith('/preditor_causal_v4.py'))
    actual=hashlib.sha256((ROOT/'preditor_causal_v4.py').read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError('Preditor difere do congelamento; execução bloqueada')
    guard=json.loads((ROOT/'congelamento_guard_v41.json').read_text())
    for row in guard['files']:
        if hashlib.sha256((ROOT/row['name']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Camada V4.1 difere do congelamento; execucao bloqueada')
    return actual

def select_frame(document,checkpoint=None):
    if 'checkpoints' in document:
        if checkpoint is None:
            raise ValueError('Replay exige --checkpoint explícito')
        matches=[x for x in document['checkpoints'] if x.get('threshold_pct')==checkpoint]
        if len(matches)!=1:
            raise ValueError('Marco inexistente ou duplicado')
        selected=matches[0]
        return selected['current'],document['reference'],selected['ledger']
    if checkpoint is not None:
        raise ValueError('--checkpoint somente para documento de replay')
    return document['current'],document['reference'],document['ledger']

def build(document,checkpoint=None,input_digest=None,previous=None):
    identity=model_identity()
    current,reference,ledger=select_frame(document,checkpoint)
    if previous is None and 'checkpoints' in document:
        earlier=[x for x in document['checkpoints'] if x['threshold_pct']<checkpoint]
        if earlier:previous=max(earlier,key=lambda x:x['threshold_pct'])['current']
    p=predict_guarded(current,reference,ledger,previous=previous)
    a,b=current['votes_a'],current['votes_b'];s=a+b
    return {
        'schema_version':'v4.1-panel-1','model':'audit-v4.1-guarded-paired-ratio',
        'model_sha256':identity,'source_document_sha256':input_digest,
        'mode':'experimental_replay' if 'checkpoints' in document else 'experimental_supplied_ledger',
        'operational_approved':False,'certification_integral':False,
        'timestamp':current['timestamp'],'checkpoint_pct':checkpoint,
        'contest':{'year':document.get('year'),
                   'candidate_a_id':document.get('config',{}).get('a'),
                   'candidate_b_id':document.get('config',{}).get('b'),
                   'municipality_tse':document.get('config',{}).get('municipality')},
        'status':p['status'],'reason':p['reason'],'guard_version':p['guard_version'],
        'clear_prior_forecast':p['clear_prior_forecast'],
        'observed':{'votes_a':a,'votes_b':b,'share_a_pct':100*a/s if s else None,
                    'electorate_total':current['electorate_total'],
                    'electorate_counted':current['electorate_counted'],
                    'remaining_electorate':p['remaining_electorate']},
        'projection':{'share_a_pct':100*p['estimate_a'] if p['estimate_a'] is not None else None,
                      'share_b_pct':100*(1-p['estimate_a']) if p['estimate_a'] is not None else None,
                      'probability_a':None,'probability_b':None},
        'conditional_bounds':{'lower_a_pct':100*p['lower_a'] if p['lower_a'] is not None else None,
                              'upper_a_pct':100*p['upper_a'] if p['upper_a'] is not None else None,
                              'kind':'deterministic_not_confidence_interval',
                              'conditional_winner':p['conditional_winner'],
                              'assumptions':['Observed counts will not be revised in a way that invalidates the inequality.',
                                             'Remaining electorate is a true upper bound on additional valid votes.']},
        'provenance':{'availability_is_assumed':document.get('availability_is_assumed'),
                       'source_authenticity_verified_by_adapter':False},
    }

def atomic_write(path,payload):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,prefix='.v4-',delete=False) as f:
        temp=pathlib.Path(f.name);f.write(content);f.flush();os.fsync(f.fileno())
    try:os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=pathlib.Path)
    parser.add_argument('--output',required=True,type=pathlib.Path)
    parser.add_argument('--state',type=pathlib.Path,help='Estado persistente necessario para entrada operacional de instante unico')
    parser.add_argument('--checkpoint',type=int,choices=range(5,100,5))
    args=parser.parse_args(argv)
    if args.input.resolve()==args.output.resolve():
        parser.error('Entrada e saída devem ser arquivos distintos')
    if args.state and args.state.resolve() in [args.input.resolve(),args.output.resolve()]:
        parser.error('Estado, entrada e saida devem ter caminhos distintos')
    try:
        raw=args.input.read_bytes();document=json.loads(raw)
        if 'checkpoints' not in document and args.state is None:raise ValueError('Instante unico exige --state para detectar revisoes')
        previous=json.loads(args.state.read_text())['current'] if args.state and args.state.exists() else None
        result=build(document,args.checkpoint,hashlib.sha256(raw).hexdigest(),previous=previous)
        if args.state and result['status'] in ['ESTIMATED','CLOSED']:
            current,_,_=select_frame(document,args.checkpoint)
            atomic_write(args.state,{'current':current,'guard_version':'4.1'})
    except (ValueError,KeyError,TypeError,AttributeError,OverflowError,StopIteration,OSError) as error:
        result={'schema_version':'v4.1-panel-1','model':'audit-v4.1-guarded-paired-ratio','status':'ERROR',
                'reason':str(error),'operational_approved':False,'certification_integral':False,
                'projection':{'share_a_pct':None,'share_b_pct':None,'probability_a':None,'probability_b':None}}
        atomic_write(args.output,result);print(json.dumps({'status':'ERROR','reason':str(error)},ensure_ascii=False),file=sys.stderr);return 2
    atomic_write(args.output,result)
    print(json.dumps({'status':result['status'],'output':str(args.output),'model_sha256':result['model_sha256']},ensure_ascii=False))
    return 0
if __name__=='__main__':sys.exit(main())
