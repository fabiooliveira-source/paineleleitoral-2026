(function() {
'use strict';
const el=id=>document.getElementById(id);
const pct=n=>n==null?'—':(100*n).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
const pp=n=>n==null?'—':n.toLocaleString('pt-BR',{minimumFractionDigits:3,maximumFractionDigits:3})+' pp';
const nfmt=n=>Number(n).toLocaleString('pt-BR');
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let result=null;
function render(){
 if(!result)return;
 const uf=el('scope').value;
 const data=result.scopes.find(x=>x.uf===uf);
 if(!data)return;
 const total=data.final_votes_13+data.final_votes_22;
 el('scopeSummary').textContent=(uf==='BR'?'Brasil':uf==='ZZ'?'Exterior (ZZ)':uf)+
   ' • '+nfmt(data.snapshots)+' snapshots • '+nfmt(data.final_sections)+' seções no final'+
   ' • votos finais: Lula '+nfmt(data.final_votes_13)+', Flávio '+nfmt(data.final_votes_22)+
   ' • Lula '+pct(data.final_share_13)+' • MAE da proporção observada: '+pp(data.raw_mae_pp)+
   ' • lideranças observadas erradas nos checkpoints 5–95%: '+data.raw_wrong_leader_checkpoints+'/'+data.primary_checkpoints;
 const items=data.checkpoints.filter(c=>c.raw_observed_share_13!=null);
 const W=920,H=270,L=55,R=20,T=22,B=43;
 const xmin=0,xmax=100,ymin=0,ymax=100;
 const x=p=>L+(p-xmin)/(xmax-xmin)*(W-L-R);
 const y=p=>H-B-(p-ymin)/(ymax-ymin)*(H-T-B);
 const path=items.map((c,i)=>(i?'L':'M')+x(c.threshold_pct).toFixed(2)+' '+y(c.raw_observed_share_13*100).toFixed(2)).join(' ');
 const finalY=y(data.final_share_13*100);
 const ticks=[0,25,50,75,100].map(v=>'<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="#395269"/><text x="'+(L-9)+'" y="'+(y(v)+5)+'" text-anchor="end" fill="#bfd6e4" font-size="14">'+v+'%</text>').join('');
 el('graph').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Curva observada de Lula em porcentagem por marco de seções, comparada ao resultado final">'+ticks+
 '<line x1="'+L+'" x2="'+(W-R)+'" y1="'+finalY+'" y2="'+finalY+'" stroke="#e6b95b" stroke-width="2" stroke-dasharray="8 5"/>'+
 '<path d="'+path+'" fill="none" stroke="#79d9d0" stroke-width="3"/>'+
 '<text x="'+(W-R-5)+'" y="'+Math.max(16,finalY-7)+'" text-anchor="end" fill="#e6b95b" font-size="14">Resultado final</text>'+
 '<text x="'+(W/2)+'" y="'+(H-8)+'" text-anchor="middle" fill="#c4d9e6" font-size="14">Marco de seções contabilizadas (%)</text></svg>';
 el('rows').innerHTML=data.checkpoints.map(c=>'<tr><td>'+c.threshold_pct+'%</td><td>'+
 (c.actual_sections_pct==null?'—':c.actual_sections_pct.toLocaleString('pt-BR',{maximumFractionDigits:2})+'%')+
 '</td><td>'+escape(c.timestamp||'sem snapshot')+'</td><td>'+pct(c.raw_observed_share_13)+'</td><td>'+
 pp(c.raw_observed_error_pp)+'</td><td>Bloqueada: sem seções pareadas</td></tr>').join('');
}
fetch('dados/2026/backtest/replay_2026_resultado.json',{cache:'no-store'})
.then(r=>{if(!r.ok)throw Error('Arquivo histórico não publicado ('+r.status+')');return r.json()})
.then(data=>{
 if(data.status!=='HISTORICAL_2026_REPLAY_COMPLETED_V7_NOT_IDENTIFIABLE'||data.national_and_ufs!==29||
 data.v7_primary_checkpoints_evaluated!==0||!Array.isArray(data.scopes)||data.scopes.length!==29)
 throw Error('Acervo incompatível com a política de segurança');
 result=data;
 el('scopes').textContent='29 (BR + 27 UFs + ZZ)';
 el('checkpoints').textContent=nfmt(data.checkpoints_requested);
 el('v7').textContent='0 — bloqueadas';
 const national=data.scopes.find(x=>x.uf==='BR');
 el('mae').textContent=pp(national.raw_mae_pp);
 const select=el('scope');
 data.scopes.filter(x=>x.uf!=='BR').sort((a,b)=>a.uf.localeCompare(b.uf)).forEach(x=>{
   const opt=document.createElement('option');opt.value=x.uf;opt.textContent=x.uf==='ZZ'?'Exterior (ZZ)':x.uf;select.appendChild(opt)
 });
 select.addEventListener('change',render);render();
})
.catch(e=>{el('scopeSummary').textContent='Erro ao carregar histórico: '+e.message+'; nenhuma projeção foi exibida.'});
})();