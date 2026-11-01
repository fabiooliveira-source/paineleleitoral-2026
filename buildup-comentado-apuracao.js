'use strict';
(async()=>{
 const host=document.getElementById('buildup-comentado');
 if(!host)return;
 const nf=new Intl.NumberFormat('pt-BR');
 const fmt=n=>nf.format(n||0);
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 try{
  const res=await fetch('dados/2026/comportamento_rateios_pacote.json');
  if(!res.ok)throw Error('HTTP '+res.status);
  const pack=await res.json();
  const bytes=Uint8Array.from(atob(pack.dados),c=>c.charCodeAt(0));
  const rates=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  const g={first:{},second:{},matrix:{},detail:[],otherDetail:[]};
  const add=(to,from)=>{for(const [k,v] of Object.entries(from||{}))to[k]=(to[k]||0)+v};
  const mergeRows=(target,source,key)=>{for(const r of source||[]){const id=key(r);let x=target.find(t=>key(t)===id);if(!x){x={name:r.name,number:r.number,base:0,dest:{}};target.push(x)}x.base+=r.base||0;add(x.dest,r.dest)}};
  for(const uf of Object.keys(rates.ufs||{})){const x=rates.ufs[uf]?.all;if(!x)continue;add(g.first,x.first);add(g.second,x.second);for(const [o,d] of Object.entries(x.matrix||{})){g.matrix[o]??={};add(g.matrix[o],d)}mergeRows(g.detail,x.detail,r=>r.number);mergeRows(g.otherDetail,x.otherDetail,r=>r.number)}
  const origins=[...g.detail.slice(0,4),...g.otherDetail].filter(x=>x.base>0);
  const names=['Lula','Flávio'];
  let html='<p>Reconstrução <strong>histórica nacional</strong> com rateio por urna, não atualização ao vivo. Os valores de origem e destino são totais agregados; os fluxos são <strong>alocações estimadas pelo algoritmo</strong>, não transferências individuais comprovadas.</p>';
  for(const candidate of names){
   const first=g.first[candidate]||0,second=g.second[candidate]||0;
   const rows=[];
   for(const x of origins){const n=x.dest[candidate]||0;if(n)rows.push('<li>'+esc(x.name)+': <strong>'+fmt(n)+'</strong> votos estimados ('+(100*n/x.base).toFixed(2).replace('.',',')+'% da origem)</li>')}
   for(const name of ['Brancos/nulos','Abstenção','Ajuste cadastral',...names.filter(n=>n!==candidate)]){const n=g.matrix[name]?.[candidate]||0;if(n)rows.push('<li>'+esc(name)+': <strong>'+fmt(n)+'</strong> votos estimados</li>')}
   const retained=g.matrix[candidate]?.[candidate]||0;
   const departures=Object.entries(g.matrix[candidate]||{}).filter(([d])=>d!==candidate).reduce((s,[,n])=>s+n,0);
   const arrivals=Object.entries(g.matrix).filter(([o])=>o!==candidate).reduce((s,[,d])=>s+(d[candidate]||0),0);
   const delta=first+arrivals-departures-second;
   html+='<h3>'+esc(candidate)+': '+fmt(first)+' votos no 1º turno → '+fmt(second)+' no 2º turno</h3><p>Composição estimada: '+fmt(first)+' votos de origem + '+fmt(arrivals)+' entradas − '+fmt(departures)+' saídas = '+fmt(second)+' votos. Permanência estimada: '+fmt(retained)+'. Diferença contábil: '+fmt(delta)+' votos.</p><p><strong>Confiança estatística das transferências: não calculável com os dados e a validação atuais (meta: ≥95%).</strong> Não é possível atribuir um percentual numérico defensável somente a partir dos totais por urna.</p><details><summary>Ver contribuições estimadas para '+esc(candidate)+'</summary><ul>'+rows.join('')+'</ul><p><strong>Confiança por origem: não demonstrada (meta: ≥95%).</strong></p></details>';
  }
  html+='<p><strong>Certeza estatística de cada transferência: não demonstrada.</strong> O modelo determinístico não sustenta uma afirmação de 95% de confiança. Brancos e nulos permanecem agregados; ajuste cadastral não equivale a mudança de voto.</p>';
  host.innerHTML=html;
 }catch(e){host.textContent='Não foi possível calcular a composição histórica: '+e.message}
})();
