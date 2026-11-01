/* Decision-theoretic minimax election-night call.
 * This is NOT a voter-strategy game and NOT a calibrated probability.
 * Loss: wrong call = 1; abstention = abstentionCost in (0,1).
 * States are possible final outcomes in an interval [low,high] for A's share.
 * A/B calls are permitted only if ALL feasible states have that winner,
 * and are labeled robust scenario calls, not mathematical determinations.
 * Physical guaranteed calls are derived from observed votes and remaining
 * eligible electorate, not from scenario assumptions.
 */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ElectionGameTheory=api})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
const VERSION='ROBUST_MINIMAX_V1_2026-11-01';
const abstain=(reason,extra={})=>Object.assign({model_version:VERSION,status:'ABSTAIN',action:'WAIT',reason,confidence:null,probability:null,mathematical_winner:null,scenario_robust_winner:null},extra);
function compute(x){
 try{
  if(!x||typeof x!=='object')return abstain('Entrada ausente');
  const {observedA,observedB,remainingElectors,scenarioLow,scenarioHigh}=x;
  for(const [k,v] of Object.entries({observedA,observedB,remainingElectors})){
   if(!Number.isSafeInteger(v)||v<0)throw Error('Contagem inválida: '+k);
  }
  if(!Number.isSafeInteger(observedA+observedB+remainingElectors))throw Error('Soma excede precisão segura');
  const n=observedA+observedB+remainingElectors;
  if(n===0)return abstain('Nenhum eleitor informado');
  const lowPhysical=observedA/n, highPhysical=(observedA+remainingElectors)/n;
  const mathWinner=observedA>observedB+remainingElectors?'A':observedB>observedA+remainingElectors?'B':null;
  if(!Number.isFinite(scenarioLow)||!Number.isFinite(scenarioHigh)||scenarioLow<0||scenarioHigh>1||scenarioLow>scenarioHigh)
   throw Error('Intervalo de cenários inválido');
  if(scenarioLow<lowPhysical-1e-12||scenarioHigh>highPhysical+1e-12)
   throw Error('Cenários extrapolam limites físicos');
  const cost=x.abstentionCost==null?0.2:x.abstentionCost;
  if(!Number.isFinite(cost)||cost<=0||cost>=1)throw Error('Custo de abstenção deve estar entre 0 e 1');
  const possibleA=scenarioHigh>0.5;
  const possibleB=scenarioLow<0.5;
  const possibleTie=scenarioLow<=0.5&&scenarioHigh>=0.5;
  const lossA=possibleB||possibleTie?1:0;
  const lossB=possibleA||possibleTie?1:0;
  const lossWait=cost;
  const min=Math.min(lossA,lossB,lossWait);
  const action=min===lossWait?'WAIT':min===lossA?'CALL_A':'CALL_B';
  const robustWinner=action==='CALL_A'?'A':action==='CALL_B'?'B':null;
  if(mathWinner&&robustWinner!==mathWinner)throw Error('Intervalo não respeita vencedor matemático');
  return {model_version:VERSION,status:'OK',action,
   reason:action==='WAIT'?'Os cenários restantes admitem resultados distintos ou empate':'Todos os cenários admitidos apontam o mesmo vencedor',
   mathematical_winner:mathWinner,scenario_robust_winner:robustWinner,
   confidence:null,probability:null,
   physical_bounds_a:[lowPhysical,highPhysical],
   scenario_bounds_a:[scenarioLow,scenarioHigh],
   possible_outcomes:{A:possibleA,B:possibleB,tie:possibleTie},
   worst_case_loss:{callA:lossA,callB:lossB,wait:lossWait},
   abstention_cost:cost,assumptions_verified:false};
 }catch(e){return abstain(e.message||'Erro na entrada')}
}
return Object.freeze({VERSION,compute});
});
