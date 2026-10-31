/* Imputação hierárquica de distribuições estimadas. Não altera resultados observados.
   Input: [{uf,municipio,zona,secao,comparavel,origem:[...],fluxo:[[...]],destinoObservado:[...]}].
   Rows comparaveis must have a modeled flow; excluded rows require observed margins.
   Output: [{...row,fluxoImputado,metodoImputacao,nDoadores}] with balanced matrices.
*/
(function(root){
'use strict';
function key(x){return String(x??'').trim().toUpperCase()}
function sum(a){return a.reduce((s,v)=>s+v,0)}
function normalized(v,n){const x=Array.from({length:n},(_,i)=>Math.max(0,Number(v?.[i])||0)),t=sum(x);return t?x.map(z=>z/t):Array(n).fill(1/n)}
function donors(rows,level){const map=new Map();for(const r of rows){if(!r.comparavel||!r.fluxo)continue;const k=level(r);if(!k)continue;let v=map.get(k);if(!v){v={flows:[],n:0};map.set(k,v)}r.fluxo.forEach((a,i)=>{v.flows[i]??=[];a.forEach((z,j)=>v.flows[i][j]=(v.flows[i][j]||0)+Math.max(0,Number(z)||0))});v.n++}return map}
const levels=[r=>[key(r.uf),key(r.municipio),key(r.zona)].join('|'),r=>[key(r.uf),key(r.municipio)].join('|'),r=>key(r.uf),r=>'BR'];
const labels=['zona/município','município','UF','Brasil'];
function balance(matrix,origin,dest,iterations=300){const m=origin.length,n=dest.length,rows=origin.map((v,i)=>normalized(matrix[i],n).map(x=>x*Math.max(0,v))),total=sum(origin),dtotal=sum(dest);if(!total)return rows.map(row=>row.map(()=>0));if(Math.abs(total-dtotal)>1e-5*Math.max(1,total))throw Error('Margens incompatíveis: origens e destinos não fecham');for(let t=0;t<iterations;t++){for(let j=0;j<n;j++){let s=0;for(let i=0;i<m;i++)s+=rows[i][j];let f=s>0?dest[j]/s:0;for(let i=0;i<m;i++)rows[i][j]*=f}for(let i=0;i<m;i++){let s=sum(rows[i]),f=s>0?origin[i]/s:0;for(let j=0;j<n;j++)rows[i][j]*=f}}return rows}
function estimate(rows){if(!Array.isArray(rows)||!rows.length)return[];const maps=levels.map(f=>donors(rows,f));return rows.map(r=>{if(r.comparavel)return {...r,metodoImputacao:'observado/modelado no recorte',nDoadores:0};if(!Array.isArray(r.origem)||!Array.isArray(r.destinoObservado))return {...r,metodoImputacao:'sem margens; não imputado',nDoadores:0};let chosen=null,level=-1;for(let i=0;i<levels.length;i++){const group=maps[i].get(levels[i](r));if(group?.n){chosen=group;level=i;break}}if(!chosen)return {...r,metodoImputacao:'sem doadores',nDoadores:0};let flow;try{flow=balance(chosen.flows,r.origem,r.destinoObservado)}catch(e){return {...r,metodoImputacao:'margens incompatíveis; não imputado',nDoadores:chosen.n}}return {...r,fluxoImputado:flow,metodoImputacao:labels[level],nDoadores:chosen.n}})}
root.ImputacaoTerritorial={estimate,balance};
})(typeof window!=='undefined'?window:globalThis);
