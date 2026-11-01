/* Laboratório neutro de negociação e coalizões.
 * Nenhuma inferência de voto individual, recomendação política ou probabilidade.
 * Nash bargaining: solução axiomática para duas partes, ganhos positivos acima
 * de alternativas externas; não equivale a transferência real de votos.
 * Shapley: valor marginal de coalizões hipotéticas, não causalidade.
 */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ElectoralBargaining=api})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
const VERSION='COALITION_BARGAINING_EXPLORATORY_V1';
function invalid(reason){return {status:'ABSTAIN',reason,model_version:VERSION,observed_voter_transfer:null,individual_vote_inference:false,probability:null}}
function finite(n,label){if(typeof n!=='number'||!Number.isFinite(n))throw Error(label+' inválido');return n}
function nash(input){
 try{
  if(!input||!Array.isArray(input.frontier)||input.frontier.length===0||input.frontier.length>10000)throw Error('Fronteira de barganha ausente ou excessiva');
  const d=input.disagreement;if(!Array.isArray(d)||d.length!==2)throw Error('Alternativas externas inválidas');
  d.forEach((x,i)=>finite(x,'Alternativa '+i));
  let best=-Infinity,solutions=[];
  for(const p of input.frontier){
   if(!Array.isArray(p)||p.length!==2)throw Error('Ponto da fronteira inválido');
   p.forEach((x,i)=>finite(x,'Utilidade '+i));
   const gainA=p[0]-d[0],gainB=p[1]-d[1];
   if(gainA<0||gainB<0)continue;
   const score=gainA*gainB;
   if(!Number.isFinite(score))throw Error('Produto fora da precisão numérica');
   if(score>best+1e-10){best=score;solutions=[p]}
   else if(Math.abs(score-best)<=1e-10)solutions.push(p);
  }
  if(best===-Infinity)return invalid('Nenhum acordo individualmente racional na fronteira');
  return {status:'OK',model_version:VERSION,disagreement:d,nash_product:best,solutions,ambiguous:solutions.length!==1,observed_voter_transfer:null,individual_vote_inference:false,probability:null,warning:'Utilidades e fronteira são hipóteses, não votos reais nem preferências reveladas'};
 }catch(e){return invalid(e.message)}
}
function shapley(input){
 try{
  if(!input||!Array.isArray(input.groups)||!Array.isArray(input.coalitionValues))throw Error('Jogo cooperativo inválido');
  const names=input.groups,n=names.length;
  if(n<1||n>8||new Set(names).size!==n||names.some(x=>typeof x!=='string'||!x.trim()))throw Error('Entre 1 e 8 grupos distintos');
  const vals=input.coalitionValues;if(vals.length!==(1<<n))throw Error('São necessários 2^n valores de coalizão');
  vals.forEach((x,i)=>finite(x,'Coalizão '+i));
  if(Math.abs(vals[0])>1e-10)throw Error('Valor da coalizão vazia deve ser zero');
  const factorial=k=>{let z=1;for(let i=2;i<=k;i++)z*=i;return z};
  const weight=k=>factorial(k)*factorial(n-k-1)/factorial(n);
  const contribution=names.map((name,i)=>{
   let sum=0;
   for(let mask=0;mask<(1<<n);mask++){
    if(mask&(1<<i))continue;
    let size=0;for(let bit=0;bit<n;bit++)if(mask&(1<<bit))size++;
    sum+=weight(size)*(vals[mask|(1<<i)]-vals[mask]);
   }
   return {group:name,marginal_value:sum};
  });
  const total=contribution.reduce((a,b)=>a+b.marginal_value,0);
  if(Math.abs(total-vals[(1<<n)-1])>1e-7*Math.max(1,Math.abs(total)))throw Error('Falha na propriedade de eficiência');
  return {status:'OK',model_version:VERSION,contributions:contribution,grand_coalition_value:vals[(1<<n)-1],observed_voter_transfer:null,individual_vote_inference:false,probability:null,warning:'Valores marginais dependem da função de coalizão assumida; não são migrações individuais'};
 }catch(e){return invalid(e.message)}
}
return Object.freeze({VERSION,nash,shapley});
});
