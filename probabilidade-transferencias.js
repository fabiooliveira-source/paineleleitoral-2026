/* Sensitivity engine for USER-SUPPLIED conditional scenario weights.
 * Does not estimate actual probabilities or identify voter transfers.
 */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TransferScenarioSensitivity=api})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
function calculate(input){
 try{
  if(!input||!Array.isArray(input.origins)||!Array.isArray(input.destinations))throw Error('Origens e destinos ausentes');
  const {origins,destinations}=input;
  if(origins.length<1||origins.length>40||destinations.length<2||destinations.length>12)throw Error('Dimensões fora do limite');
  if(new Set(destinations).size!==destinations.length||destinations.some(s=>typeof s!=='string'||!s.trim()))throw Error('Destinos inválidos');
  let total=0;const sums=destinations.map(()=>0),rows=[];
  for(const r of origins){
   if(typeof r.name!=='string'||!r.name.trim()||!Number.isSafeInteger(r.votes)||r.votes<0||!Array.isArray(r.weights)||r.weights.length!==destinations.length)throw Error('Origem inválida');
   if(!r.weights.every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=0&&x<=1))throw Error('Pesos fora de [0,1]');
   const weightSum=r.weights.reduce((a,b)=>a+b,0);
   if(Math.abs(weightSum-1)>1e-8)throw Error('Pesos de '+r.name+' não somam 100%');
   total+=r.votes;if(!Number.isSafeInteger(total))throw Error('Total excede precisão');
   const contributions=r.weights.map((w,j)=>{const v=w*r.votes;sums[j]+=v;return v});
   rows.push({name:r.name,votes:r.votes,weights:r.weights,contributions});
  }
  if(new Set(rows.map(x=>x.name)).size!==rows.length)throw Error('Origens repetidas');
  if(total===0)throw Error('Total zero');
  const totalExpected=sums.reduce((a,b)=>a+b,0);
  if(Math.abs(totalExpected-total)>Math.max(1e-6,total*1e-10))throw Error('Falha de conservação');
  const reference=input.observedDestinations;
  let comparison=null;
  if(reference!==undefined){
   if(!Array.isArray(reference)||reference.length!==destinations.length||!reference.every(x=>Number.isSafeInteger(x)&&x>=0)||reference.reduce((a,b)=>a+b,0)!==total)throw Error('Totais observados não reconciliados');
   comparison=destinations.map((name,i)=>({destination:name,expected:sums[i],observed:reference[i],residual:sums[i]-reference[i]}));
  }
  return {status:'OK',model:'CONDITIONAL_USER_SUPPLIED_WEIGHTS',total,rows,
   totals:destinations.map((name,i)=>({destination:name,expected:sums[i]})),comparison,
   is_empirical_probability:false,is_calibrated:false,individual_transfer_observed:false,
   warning:'Pesos condicionais definidos pelo usuário: hipóteses, não probabilidades estimadas. Sem identificação causal.'};
 }catch(e){return {status:'ABSTAIN',reason:e.message,is_empirical_probability:false}}
}
return Object.freeze({calculate});
});