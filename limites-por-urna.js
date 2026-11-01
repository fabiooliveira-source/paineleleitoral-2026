/* Partial-identification bounds computed independently for each matched section.
   No individual transfers or estimated conditional probabilities are claimed.
*/
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SectionTransferBounds=api})(typeof globalThis==='object'?globalThis:this,function(){
'use strict';
const origins=['Lula','Flávio','Demais candidatos','Brancos','Nulos','Abstenção','Ajuste cadastral'];
const destinations=['Lula','Flávio','Brancos','Nulos','Abstenção','Ajuste cadastral'];
function evaluate(rows){
 try{
  if(!Array.isArray(rows)||rows.length===0)throw Error('Sem seções');
  const totals=origins.map(o=>destinations.map(d=>({origin:o,destination:d,min:0,max:0})));
  let counted=0,excluded=0,adjusted=0,universe=0;
  for(const r of rows){
   const get=k=>{const n=Number(r[k]);if(!Number.isSafeInteger(n)||n<0)throw Error('Contagem inválida: '+k);return n};
   try{
    const a=[get('lula_1t'),get('flavio_1t'),0,get('brancos_1t'),get('nulos_1t'),get('abstencoes_1t')];
    const b=[get('lula_2t'),get('flavio_2t'),get('brancos_2t'),get('nulos_2t'),get('abstencoes_2t')];
    const v1=get('validos_1t'),v2=get('validos_2t'),ap1=get('aptos_1t'),ap2=get('aptos_2t');
    a[2]=v1-a[0]-a[1];if(a[2]<0||v2!==b[0]+b[1])throw Error('Votos válidos inconsistentes');
    const sum=x=>x.reduce((p,q)=>p+q,0);
    const s1=sum(a),s2=sum(b),M=Math.max(s1,s2,ap1,ap2);
    a.push(M-s1);b.push(M-s2);
    if(a.some(x=>x<0)||b.some(x=>x<0)||M===0)throw Error('Universo inválido');
    for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++){
      const c=totals[i][j];c.min+=Math.max(0,a[i]+b[j]-M);c.max+=Math.min(a[i],b[j]);
    }
    universe+=M;counted++;if(ap1!==ap2||a[6]||b[5])adjusted++;
   }catch(e){excluded++}
  }
  if(!counted)throw Error('Nenhuma seção validada');
  return {status:'OK',sections:counted,excluded,adjusted,universe,
    bounds:totals.flat(),method:'SECTIONWISE_FRECHET_PARTIAL_IDENTIFICATION',
    empirical_probability:null,individual_migration_observed:false,
    warning:'Limites são por seção e somados, não probabilidades; extremos por célula não são simultaneamente atingíveis. Ajuste cadastral não representa pessoa observada.'};
 }catch(e){return {status:'ABSTAIN',reason:e.message}}
}
return Object.freeze({evaluate,origins,destinations});
});