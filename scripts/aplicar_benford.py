"""Descriptive digit diagnostics, not a fraud detector. Python + numpy + scipy."""
from pathlib import Path
import gzip, hashlib, json, math, subprocess
from collections import defaultdict
from datetime import datetime, timezone
import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dados/2026/benford'
REFERENCES = [
    'https://authors.library.caltech.edu/records/5jbtk-8wn05',
    'https://doi.org/10.1093/pan/mpr024',
]
WARNING = ('Diagnóstico exploratório de dígitos. Desvio de Benford não demonstra fraude; '
           'aderência não certifica integridade. P-valores nominais pressupõem amostras '
           'independentes e uma distribuição de referência aplicável, condições não '
           'demonstradas nas seções eleitorais. Holm não corrige esses problemas.')

def probabilities(position):
    if position == 1:
        return np.log10(1 + 1 / np.arange(1, 10))
    return np.array([sum(math.log10(1 + 1 / (10*k+d)) for k in range(1, 10))
                     for d in range(10)])

def diagnose(values, position):
    a = np.asarray(values, dtype=np.int64)
    eligible = a[a >= (1 if position == 1 else 10)]
    digits = np.array([int(str(int(v))[position-1]) for v in eligible], dtype=int)
    labels = list(range(1, 10)) if position == 1 else list(range(10))
    counts = np.array([np.count_nonzero(digits == d) for d in labels])
    n = len(eligible)
    p = probabilities(position)
    observed = counts / n if n else np.zeros(len(labels))
    expected = p * n
    statistic = float(np.sum((counts-expected)**2/expected)) if n else None
    allowed = bool(n and np.min(expected) >= 5)
    result = dict(position=position, n=int(n), total=len(a), zeros=int(np.count_nonzero(a == 0)),
                  below_minimum=int(np.count_nonzero(a < (1 if position == 1 else 10))),
                  digits=labels, counts=counts.tolist(), expected_counts=expected.tolist(),
                  expected_min=float(np.min(expected)),
                  mad_pp=float(100*np.mean(abs(observed-p))) if n else None,
                  chi_square=statistic, df=len(labels)-1,
                  p_nominal=float(chi2.sf(statistic, len(labels)-1)) if allowed else None,
                  p_holm=None, chi_square_eligible=allowed,
                  applicability='Não demonstrada; votos limitados pelo tamanho da seção e dependência territorial.')
    if n:
        q = np.quantile(eligible, [0, .01, .5, .99, 1])
        result.update(quantiles=q.tolist(), central_orders_of_magnitude=float(math.log10(q[3]/q[1])))
    return result

def holm(records):
    valid = sorted((r for r in records if r['p_nominal'] is not None), key=lambda r:r['p_nominal'])
    maximum = 0.
    for i,r in enumerate(valid):
        maximum = max(maximum, min(1., (len(valid)-i)*r['p_nominal']))
        r['p_holm'] = maximum
    return len(valid)

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    names = {(m['uf'],str(m['codigo_municipio_tse'])):m['municipio'] for m in
             json.loads(gzip.decompress((ROOT/'dados/2026/municipios.json.gz').read_bytes()))}
    groups = defaultdict(list)
    manifest, coverage = [], {}
    for path in sorted((ROOT/'dados/2026').glob('secoes-??.json.gz')):
        uf = path.name.split('-')[1].split('.')[0]
        raw = path.read_bytes()
        manifest.append(dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest()))
        data = json.loads(gzip.decompress(raw)); seen=set(); usable=defaultdict(int)
        for line in data['linhas']:
            r = dict(zip(data['colunas'],line))
            key = tuple(str(r[k]) for k in ['codigo_municipio_tse','zona','secao'])
            if key in seen: raise ValueError('Chave duplicada: '+uf+str(key))
            seen.add(key)
            for turn in ['1t','2t']:
                if r['situacao_dados_'+turn] != 'conferido': continue
                usable[turn]+=1
                for candidate in ['lula','flavio']:
                    value = r[candidate+'_'+turn]
                    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or int(value)!=value:
                        raise ValueError('Contagem inválida: '+uf+str(key))
                    groups[('UF',uf,candidate,turn)].append(int(value))
                    groups[('Municipio',uf+':'+key[0],candidate,turn)].append(int(value))
                    if uf != 'ZZ': groups[('Brasil','BR',candidate,turn)].append(int(value))
                    else: groups[('Exterior','ZZ',candidate,turn)].append(int(value))
        coverage[uf] = dict(sections=len(seen), conferred=dict(usable))
    records=[]
    for (level,geo,candidate,turn), values in sorted(groups.items()):
        label = names.get(tuple(geo.split(':')),geo) if level=='Municipio' else geo
        for position in [1,2]:
            records.append(dict(level=level,geo=geo,label=label,candidate=candidate,turn=turn,
                                **diagnose(values,position)))
    families={}
    # The geographic levels overlap; all formal eligible comparisons form ONE family.
    families['all_eligible_comparisons']=holm(records)
    # Exact conservation of per-section vote counts between municipalities and UFs.
    for uf in coverage:
        for candidate in ['lula','flavio']:
            for turn in ['1t','2t']:
                for position in [1,2]:
                    parent=next(r for r in records if r['level']=='UF' and r['geo']==uf and r['candidate']==candidate and r['turn']==turn and r['position']==position)
                    children=[r for r in records if r['level']=='Municipio' and r['geo'].startswith(uf+':') and r['candidate']==candidate and r['turn']==turn and r['position']==position]
                    assert np.array_equal(parent['counts'],np.sum([r['counts'] for r in children],axis=0))
    payload=dict(schema=1,generated_at=datetime.now(timezone.utc).isoformat(),
                 source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 source_status='Derivados do repositório; autenticidade TSE não revalidada nesta execução.',
                 warning=WARNING, references=REFERENCES, coverage=coverage, inputs=manifest,
                 protocol=dict(unit='Votos de um candidato por seção eleitoral; sem ponderação por votos.',
                     candidates=['Lula','Flávio'],turns=['1t','2t'],positions=[1,2],
                     scope='Brasil sem exterior, UF, município/localidade; exterior separado.',
                     inclusion='Situação conferido no respectivo turno; não exige par conferido entre turnos.',
                     first_digit='log10(1+1/d), d=1..9',
                     second_digit='soma k=1..9 de log10(1+1/(10*k+d)), d=0..9',
                     chi_square='soma (observado-esperado)^2/esperado; gl=8 ou 9; somente esperado mínimo >=5.',
                     mad='100*media(abs(frequencia_observada-probabilidade_Benford)), em pp; sem limiar de fraude.',
                     multiplicity='Holm sobre todos os testes elegíveis, incluindo sobreposição de níveis.',
                     underflow='P nominal igual a zero significa subfluxo numérico; não probabilidade zero.',
                     fit='Sem ajuste de parâmetros; nenhuma classificação de município ou urna como fraudulento.'),
                 families=families, results=records)
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    (OUT/'resultados.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    summary={k:v for k,v in payload.items() if k!='results'}
    summary['results']=[r for r in records if r['level'] in ['Brasil','UF','Exterior'] or
                        (r['label']=='SERRINHA' and r['geo'].startswith('BA:'))]
    (OUT/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    national=[r for r in records if r['level']=='Brasil']
    serrinha=[r for r in records if r['level']=='Municipio' and r['label']=='SERRINHA' and r['geo'].startswith('BA:')]
    def table(rs):
        lines=['| Candidato | Turno | Dígito | N elegível | MAD (pp) | Qui-quadrado | p nominal | p Holm |',
               '|---|---:|---:|---:|---:|---:|---:|---:|']
        def pv(p):return 'não calculado' if p is None else '<1e-300 (subfluxo)' if p==0 else f'{p:.3g}'
        for r in rs:
            lines.append(f"| {r['candidate'].title()} | {r['turn']} | {r['position']} | {r['n']} | {r['mad_pp']:.3f} | {r['chi_square']:.2f} | {pv(r['p_nominal'])} | {pv(r['p_holm'])} |")
        return '\n'.join(lines)
    report=['# Benford — diagnóstico exploratório dos votos por seção',WARNING,
            '## Resultado e interpretação',
            'As tabelas medem distância de uma distribuição matemática de referência. '
            'Nenhum p-valor representa probabilidade de fraude ou de honestidade. '
            'O primeiro dígito é particularmente afetado pelos limites de tamanho das seções; '
            'o segundo também depende do processo eleitoral. Não foi construída uma linha de base '
            'de eleições comparáveis nem calibrado um detector de irregularidades.',
            '## Brasil — sem exterior',table(national),
            '![Frequências do segundo dígito no Brasil](segundo-digito-brasil.png)',
            '## Serrinha — BA',table(serrinha),
            '## Cobertura e método',
            f"{sum(c['sections'] for c in coverage.values()):,} seções distintas na base, incluindo exterior. "
            f"{len(records):,} diagnósticos; {families['all_eligible_comparisons']:,} comparações com frequências esperadas suficientes. "
            'Cada teste territorial usa os votos de suas próprias seções, sem substituir municípios por dados estaduais. '
            'Zeros são preservados na cobertura, mas excluídos dos dígitos significativos. '
            'Valores de 1 a 9 não possuem segundo dígito e são excluídos somente nesse teste. '
            'Pequena amostra: frequências apresentadas, p-valor suprimido se alguma contagem esperada for menor que 5. '
            'Os níveis territoriais se sobrepõem; Holm usa uma família global. Dependência espacial e inadequação '
            'da hipótese de referência continuam não resolvidas.',
            '## Proveniência e reprodução',
            f"Fonte congelada: `{payload['source_commit']}`. "+payload['source_status'],
            'Os 28 arquivos de seção são validados quanto a chaves duplicadas e contagens não negativas. '
            'Somas das frequências municipais reproduzem as UFs. SHA-256 de cada entrada, exclusões, '
            'frequências, probabilidades esperadas e resultados municipais estão em `resultados.json.gz`.',
            'Executar na raiz: `python scripts/aplicar_benford.py` (numpy, scipy e matplotlib).',
            '## Referências',*REFERENCES]
    (OUT/'RESULTADOS.md').write_text('\n\n'.join(report)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,7),sharex=True,sharey=True)
    for ax,r in zip(axes.flat,[r for r in national if r['position']==2]):
        x=np.arange(10);ax.bar(x-.18,np.array(r['counts'])/r['n']*100,.36,label='Observado',color='#227c9d');ax.bar(x+.18,probabilities(2)*100,.36,label='Referência Benford',color='#efb547')
        ax.set_title(r['candidate'].title()+' · '+r['turn']);ax.set_xticks(x);ax.set_ylim(0,18);ax.set_ylabel('Seções elegíveis (%)');ax.set_xlabel('Segundo dígito');ax.grid(axis='y',alpha=.2)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Votos por seção — Brasil sem exterior\nDesvios de Benford não demonstram fraude',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.92));fig.savefig(OUT/'segundo-digito-brasil.png',dpi=150);plt.close(fig)
    print(json.dumps(dict(coverage=coverage,records=len(records),family=families,national=national,serrinha=serrinha),ensure_ascii=False))

if __name__=='__main__': run()
