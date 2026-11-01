'use strict';
(()=>{
const el=document.getElementById('numeros-vizinhanca-finalistas'),d=window.__spatialBuildup2026;
if(!el||!d)return;
const fmt=n=>Math.round(n).toLocaleString('pt-BR');
const pct=n=>(100*n).toFixed(2).replace('.',',')+'%';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let html='<p>Modelo espacial IDW², 8 vizinhos; estimativas condicionais ao modelo, não transferências individuais observadas. Teste reservado: '+fmt(d.test.sections)+' seções; erro médio ponderado dos totais: '+d.test.weighted_mae_pp.toFixed(2).replace('.',',')+' p.p. <strong>Confiança de migração: não demonstrada.</strong></p>';
for(const [dest,idx] of [['Lula',0],['Flávio',1]]){
html+='<h3>Entradas estimadas para '+dest+' por origem no 1º turno</h3><div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse"><thead><tr><th style="text-align:left">Origem</th><th>Votos estimados</th><th>% da origem</th><th>Faixa entre modelos</th><th>Erro médio do indicador</th></tr></thead><tbody>';
let total=0;
for(let i=2;i<d.origins.length;i++){
const base=d.base[i]||0,flow=d.flows[i][idx]||0;if(!base)continue;total+=flow;
const variations=d.models.map(m=>100*(m[i][idx]||0)/base);
const low=Math.min(...variations)/100,high=Math.max(...variations)/100;
html+='<tr><td>'+esc(d.origins[i])+'</td><td style="text-align:right">'+fmt(flow)+'</td><td style="text-align:right">'+pct(flow/base)+'</td><td style="text-align:right">'+pct(low)+'–'+pct(high)+'</td><td style="text-align:right">Não estimado</td></tr>';
}
html+='</tbody></table></div><p><strong>Total de entradas estimadas de outras origens: '+fmt(total)+' votos.</strong> Faixa = sensibilidade entre cinco modelos, não intervalo de confiança de 95%. O MAE global de '+d.test.weighted_mae_pp.toFixed(2).replace('.',',')+' p.p. não é o erro individual de cada origem e não pode ser atribuído a estas linhas.</p>';
}
el.innerHTML=html;
})();
