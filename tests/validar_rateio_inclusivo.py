"""Valida matrizes publicadas e conciliação municipal dos finalistas."""
import gzip,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]/'dados/2026'

def main():
    report=json.loads((ROOT/'rateio-inclusivo.json').read_text())
    official=json.load(gzip.open(ROOT/'municipios.json.gz'))
    by={(r['uf'],str(int(r['codigo_municipio_tse']))):r for r in official}
    checks=0;count=0;municipalities=0;stateflows=[]
    for uf,state in report['territories'].items():
        if uf=='BR':continue
        municipal=json.load(gzip.open(ROOT/f'rateio-inclusivo-{uf}.json.gz'))
        flows=[]
        for code,r in municipal.items():
            m=np.array(r['flow']);assert np.isfinite(m).all() and (m>=0).all()
            # Acúmulo de erros de ponto flutuante por seção; limite individual 1e-7.
            tolerance=r['sections']*1e-7+1e-6
            assert np.max(abs(m.sum(1)-r['origin_totals']))<tolerance
            assert np.max(abs(m.sum(0)-r['destination_totals']))<tolerance
            source=by[(uf,code)]
            for key,value in [('lula_1t',r['origin_totals'][0]),('flavio_1t',r['origin_totals'][1]),('lula_2t',r['destination_totals'][0]),('flavio_2t',r['destination_totals'][1])]:
                assert value==source[key],(uf,code,key,value,source[key]);checks+=1
            count+=r['sections'];municipalities+=1;flows.append(m)
        np.testing.assert_allclose(np.sum(flows,axis=0),state['flow'],atol=1e-6)
        stateflows.append(state['flow'])
    np.testing.assert_allclose(np.sum(stateflows,axis=0),report['territories']['BR']['flow'],atol=1e-6)
    assert count==report['audit']['included']
    br=report['territories']['BR']
    for key,value in [('lula_1t',br['origin_totals'][0]),('flavio_1t',br['origin_totals'][1]),('lula_2t',br['destination_totals'][0]),('flavio_2t',br['destination_totals'][1])]:
        assert value==sum(r[key] for r in official),(key,value)

    result={'national_finalist_checks':4,'official_municipal_fallback_blocks':report['audit']['official_municipal_fallback_blocks'],'municipal_candidate_checks':checks,'mismatches':0,'municipalities':municipalities,'included_sections':count,'changed_electorate_included':report['audit']['changed_electorate_included'],'pending_sections':report['audit']['pending_count'],'independence_fallback_sections':report['audit']['independence_fallback_sections']}
    print(json.dumps(result));return result
if __name__=='__main__':main()
