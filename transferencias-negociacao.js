/* Feasible transport matrices, not observed voter switches.
   The optimization selects a reproducible neutral maximum-entropy
   independence coupling. Row/column totals are always exact integers.
   Neither Nash nor Shapley utilities determine individual vote transfers.
*/
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TransferNegotiation=factory()})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
function compute(input){
 try{
  if(!input||!Array.isArray(input.origins)||!Array.isArray(input.destinations))throw Error('Origens e destinos obrigatórios');
  const origins=input.origins,destinations=input.destinations;
  if(!origins.length||!destinations.length||origins.length>30||destinations.length>30)throw Error('Dimensões inválidas');
  const valid=x=>x&&typeof x.name==='string'&&x.name.trim()&&Number.isSafeInteger(x.votes)&&x.votes>=0;
  if(!origins.every(valid)||!destinations.every(valid))throw Error('Nomes ou votos inválidos');
  if(new Set(origins.map(x=>x.name)).size!==origins.length||new Set(destinations.map(x=>x.name)).size!==destinations.length)throw Error('Nomes repetidos');
  const sum=x=>x.reduce((a,b)=>a+b.votes,0);
  const total=sum(origins);if(total!==sum(destinations)||!Number.isSafeInteger(total)||total===0)throw Error('Totais não reconciliados');
  // Hamilton rounding of independence expected counts with iterative residual
  // allocation under both exact margins. Floor all cells, then fill largest
  // fractional remainders subject to row/column residuals.
  const mat=origins.map(()=>destinations.map(()=>0)),parts=[];
  let rowLeft=origins.map(x=>x.votes),colLeft=destinations.map(x=>x.votes);
  for(let i=0;i<origins.length;i++)for(let j=0;j<destinations.length;j++){
   const expected=origins[i].votes*destinations[j].votes/total;
   const floor=Math.floor(expected);
   mat[i][j]=floor;rowLeft[i]-=floor;colLeft[j]-=floor;
   parts.push({i,j,frac:expected-floor});
  }
  parts.sort((a,b)=>b.frac-a.frac||a.i-b.i||a.j-b.j);
  for(const p of parts)if(rowLeft[p.i]>0&&colLeft[p.j]>0){mat[p.i][p.j]++;rowLeft[p.i]--;colLeft[p.j]--}
  // Residual bipartite greedy completion (always possible with no cell caps).
  for(let i=0;i<origins.length;i++)for(let j=0;j<destinations.length;j++){
   const v=Math.min(rowLeft[i],colLeft[j]);mat[i][j]+=v;rowLeft[i]-=v;colLeft[j]-=v;
  }
  if(rowLeft.some(Boolean)||colLeft.some(Boolean))throw Error('Falha de reconciliação');
  const cells=[];
  for(let i=0;i<origins.length;i++)for(let j=0;j<destinations.length;j++){
   const lo=Math.max(0,origins[i].votes+destinations[j].votes-total);
   const hi=Math.min(origins[i].votes,destinations[j].votes);
   const v=mat[i][j];
   if(v<lo||v>hi)throw Error('Fora dos limites de Fréchet');
   cells.push({origin:origins[i].name,destination:destinations[j].name,allocated:v,
     share_of_origin:origins[i].votes?v/origins[i].votes:null,frechet_min:lo,frechet_max:hi});
  }
  return {status:'OK',method:'INDEPENDENCE_NEUTRAL_BASELINE_HAMILTON',total,origins,destinations,cells,
    observed_individual_migration:false,causal_inference:false,calibrated_probability:null,
    assumptions:'Acoplamento de independência, não inferência de negociação; células inteiras e margens reconciliadas'};
 }catch(e){return {status:'ABSTAIN',reason:e.message,observed_individual_migration:false}}
}
return Object.freeze({compute});
});