'use strict';
(async()=>{
 const el=document.getElementById('probabilidade-ei-apuracao');
 if(!el)return;
 const fmt=n=>Math.round(n).toLocaleString('pt-BR');
 const pct=n=>(100*n).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:2})+'%';
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 try{
  const response=await fetch('dados/2026/inferencia-resultados.json');
  if(!response.ok)throw Error('HTTP '+response.status);
  const pack=await response.json();
  const bytes=Uint8Array.from(atob(pack.dados),c=>c.charCodeAt(0));
  const db=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  const b=db.territories.BR;
  if(!b||!b.rates)throw Error('Modelo nacional indisponível');
  const indices=b.origins.map((name,i)=>({name,i})).filter(x=>x.i>=2&&x.i<b.origins.length-3);
  let html='<p><strong>Modelo estatístico alternativo ao rateio determinístico:</strong> regressão ecológica multivariada restrita, ajustada às seções pareadas, com reamostragem por municípios. As taxas abaixo são <strong>probabilidades estimadas condicionais às hipóteses do modelo</strong>, não probabilidades comprovadas da escolha de um eleitor. O intervalo bootstrap de 95% quantifica variação amostral condicional; não comprova 95% de acurácia.</p>';
  html+='<p>Seções elegíveis: '+fmt(db.audit.included)+'; excluídas: '+fmt(db.audit.excluded)+'; municípios no ajuste: '+fmt(b.municipal_clusters)+'; replicações bootstrap bem-sucedidas: '+fmt(b.bootstrap_success)+'. Sensibilidade à regularização: '+b.ridge_sensitivity_max_pp.toLocaleString('pt-BR',{maximumFractionDigits:2})+' p.p.</p>';
  for(const target of ['Lula','Flávio']){
   const col=b.destinations.indexOf(target);
   html+='<h3>Probabilidades estimadas de transferência para '+esc(target)+'</h3><div style="overflow-x:auto"><table><thead><tr><th>Origem</th><th>Votos 1º turno</th><th>Probabilidade estimada</th><th>Votos estimados</th><th>Intervalo bootstrap 95%</th></tr></thead><tbody>';
   for(const {name,i} of indices){
    const p=b.rates[i]?.[col],base=b.origin_totals[i],lo=b.bootstrap95_lower?.[i]?.[col],hi=b.bootstrap95_upper?.[i]?.[col];
    if(!Number.isFinite(p)||!Number.isFinite(base))continue;
    html+='<tr><td>'+esc(name)+'</td><td>'+fmt(base)+'</td><td>'+pct(p)+'</td><td>'+fmt(base*p)+'</td><td>'+(Number.isFinite(lo)&&Number.isFinite(hi)?pct(lo)+' a '+pct(hi):'Não disponível')+'</td></tr>';
   }
   html+='</tbody></table></div>';
  }
  html+='<p><strong>Confiança de que as transferências individuais ocorreram nessas proporções: não identificada.</strong> Os intervalos de 95% acima são condicionais ao modelo; a meta de acurácia de 95% não foi certificada. Votos estimados são produtos de totais de origem por taxas modeladas, podendo diferir da reconciliação exata do rateio determinístico acima. <a href="inferencia.html">Consultar diagnóstico e limites de identificação</a>.</p>';
  el.innerHTML=html;
 }catch(e){el.textContent='Estimativas estatísticas indisponíveis: '+e.message}
})();
