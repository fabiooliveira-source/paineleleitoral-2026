/* Territorial slices reuse the fitted coefficients; no model is refitted. */
(()=>{
'use strict';
const regions={Norte:['AC','AM','AP','PA','RO','RR','TO'],Nordeste:['AL','BA','CE','MA','PB','PE','PI','RN','SE'],'Centro-Oeste':['DF','GO','MS','MT'],Sudeste:['ES','MG','RJ','SP'],Sul:['PR','RS','SC']};
const controls=$('territory').closest('.controls');
const make=(id,label)=>{const l=document.createElement('label');l.append(label+' ');const s=document.createElement('select');s.id=id;l.append(s);controls.append(l);return s;};
const region=make('ecoRegion','Região'),city=make('ecoCity','Município'),zone=make('ecoZone','Zona'),section=make('ecoSection','Seção');
controls.prepend(region.parentElement);region.add(new Option('Todas',''));Object.keys(regions).forEach(r=>region.add(new Option(r,r)));
const status=document.createElement('p');status.setAttribute('role','status');controls.after(status);
let municipal=[],local=null,active=null,revision=0;
const cache=new Map(),originalAggregate=aggregate,originalHist=renderHist,originalRender=renderTable;
const reset=(s,label,disabled=true)=>{s.replaceChildren(new Option(label,''));s.disabled=disabled;};
reset(city,'Todos os municípios');reset(zone,'Todas as zonas');reset(section,'Todas as seções');
const states=()=>DATA.by_uf.filter(s=>(!region.value||regions[region.value].includes(s.uf))&&($('territory').value==='BR'||$('territory').value==='BRonly'&&s.uf!=='ZZ'||s.uf===$('territory').value));
selectedStates=states;
async function read(path,packed=false){const r=await fetch('dados/2026/'+path);if(!r.ok)throw Error(path+': HTTP '+r.status);if(packed){const p=await r.json(),b=Uint8Array.from(atob(p.dados),c=>c.charCodeAt(0));return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).json();}return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();}
async function load(uf){if(!cache.has(uf))cache.set(uf,Promise.all([read('secoes-'+uf+'.json.gz'),read('candidatos-secao-'+uf+'.json',true),read('transferencias-modelos-'+uf+'.json',true)]).then(([s,c,m])=>({rows:s.linhas.map(row=>Object.fromEntries(s.colunas.map((k,i)=>[k,row[i]]))),extras:new Map(c.linhas.map(r=>[r.slice(0,3).join(':'),r.slice(3)])),numbers:c.numeros,model:m,keys:new Map(m.sections.map(r=>[r[0],r[1]]))})).catch(e=>{cache.delete(uf);throw e;}));return cache.get(uf);}
function rows(){return local?local.rows.filter(r=>String(r.codigo_municipio_tse)===city.value&&(!zone.value||String(r.zona)===zone.value)&&(!section.value||String(r.secao)===section.value)):[];}
function options(s,values,label){reset(s,label,false);[...new Set(values)].sort((a,b)=>Number(a)-Number(b)).forEach(v=>s.add(new Option(v,v)));}
function calculate(){
 const origins=DATA.origins.map(()=>0),flow=origins.map(()=>DATA.destinations.map(()=>0)),observed=DATA.destinations.map(()=>0),histograms=Object.fromEntries(DATA.codes.map(c=>[c,Array.from({length:2},()=>({urnas:Array(20).fill(0),votos_origem:Array(20).fill(0)}))]));let count=0,excluded=0;
 for(const r of rows()){
  const key=[r.codigo_municipio_tse,r.zona,r.secao].join(':'),block=local.keys.get(key),extra=local.extras.get(key),coeff=local.model.coefficients[String(block)]?.[local.model.selected_index];
  if(!coeff||!extra||r.situacao_dados_1t!=='conferido'||r.situacao_dados_2t!=='conferido'){excluded++;continue;}
  const counts=new Map(local.numbers.map((n,i)=>[String(n),extra[i]]));counts.set('13',r.lula_1t);counts.set('22',r.flavio_1t);
  const a=DATA.codes.map(c=>counts.get(c));a.push(r.brancos_1t,r.nulos_1t,r.abstencoes_1t);
  const b=[r.lula_2t,r.flavio_2t,r.brancos_2t,r.nulos_2t,r.abstencoes_2t];
  if([...a,...b,r.aptos_1t,r.aptos_2t].some(v=>!Number.isFinite(v)||v<0)){excluded++;continue;}
  if(a.slice(0,DATA.codes.length).reduce((s,x)=>s+x,0)!==r.nominais_1t||r.lula_2t+r.flavio_2t!==r.nominais_2t){excluded++;continue;}
  const total1=a.reduce((s,x)=>s+x,0),total2=b.reduce((s,x)=>s+x,0),universe=Math.max(r.aptos_1t,r.aptos_2t,total1,total2);a.push(universe-total1);b.push(universe-total2);if(!universe){excluded++;continue;}count++;
  a.forEach((v,i)=>{origins[i]+=v;coeff[i].forEach((p,j)=>{flow[i][j]+=v*p;});if(i<DATA.codes.length&&v>0)for(let j=0;j<2;j++){const h=histograms[DATA.codes[i]][j],bin=Math.min(19,Math.floor(coeff[i][j]*20));h.urnas[bin]++;h.votos_origem[bin]+=v;}});b.forEach((v,j)=>observed[j]+=v);
 }
 const label=municipal.find(m=>m.uf===$('territory').value&&String(m.codigo_municipio_tse)===city.value)?.municipio||city.value;
 return {ss:[{uf:$('territory').value+' · '+label+(zone.value?' · zona '+zone.value:'')+(section.value?' · seção '+section.value:''),sections:count,histograms}],origin:origins,flow,observed,excluded};
}
aggregate=function(){if(city.value){if(!active)throw Error('Recorte local ainda não carregado');return active;}return originalAggregate();};
renderHist=function(){const saved=DATA.by_uf;try{DATA.by_uf=city.value?(active?.ss||[]):states();originalHist();}finally{DATA.by_uf=saved;}};
renderTable=function(){originalRender();renderHist();if(city.value)$('tableNote').textContent+=' Coeficientes locais já ajustados, sem conciliação posterior. '+active.excluded+' seções excluídas por falta de correspondência ou conferência. As métricas de teste e a dispersão nacional permanecem referências fixas.';};
function display(){if(city.value)active=calculate();else active=null;$('flowMode').options[1].disabled=!!city.value;if(city.value)$('flowMode').value='flow';renderTable();status.textContent=city.value?active.ss[0].uf+' · '+fmt(active.ss[0].sections)+' seções modeladas.':(region.value||$('territory').selectedOptions[0].textContent)+' · resultados do recorte selecionado.';}
function fillCities(){const uf=$('territory').value;reset(city,'Todos os municípios',!DATA.by_uf.some(s=>s.uf===uf)||!municipal.length);reset(zone,'Todas as zonas');reset(section,'Todas as seções');municipal.filter(m=>m.uf===uf).sort((a,b)=>a.municipio.localeCompare(b.municipio,'pt-BR')).forEach(m=>city.add(new Option(m.municipio,String(m.codigo_municipio_tse))));}
function territoryChange(){revision++;['exportCSV','exportAccumulation','exportNetAccumulation','flowMode'].forEach(id=>$(id).disabled=false);local=null;active=null;fillCities();display();}
region.onchange=()=>{const allowed=region.value?regions[region.value]:null;for(const o of $('territory').options)o.hidden=!!allowed&&!['BR','BRonly',...allowed].includes(o.value);if(allowed&&!['BR','BRonly',...allowed].includes($('territory').value))$('territory').value='BRonly';territoryChange();};
$('territory').onchange=territoryChange;
city.onchange=async()=>{const mine=++revision;active=null;reset(zone,'Todas as zonas');reset(section,'Todas as seções');if(!city.value){display();return;}status.textContent='Carregando seções e coeficientes locais…';$('tableNote').textContent=status.textContent;['rates','finals','fullMatrix','accumulation','reconstruction','netAccumulation','nonvalidChanges','deltaContributions','histograms'].forEach(id=>$(id).replaceChildren());const ids=['exportCSV','exportAccumulation','exportNetAccumulation'];ids.forEach(id=>$(id).disabled=true);$('flowMode').disabled=true;city.disabled=true;try{const loaded=await load($('territory').value);if(mine!==revision)return;local=loaded;options(zone,rows().map(r=>String(r.zona)),'Todas as zonas');display();}catch(e){if(mine===revision){city.value='';display();status.textContent='Recorte local indisponível: '+e.message;}}finally{if(mine===revision){ids.forEach(id=>$(id).disabled=false);$('flowMode').disabled=false;city.disabled=false;}}};
zone.onchange=()=>{reset(section,'Todas as seções');if(zone.value)options(section,rows().map(r=>String(r.secao)),'Todas as seções');display();};section.onchange=display;
$('flowMode').onchange=display;
$('exportJSON').onclick=()=>download('inferencia-recorte.json',JSON.stringify({recorte:{regiao:region.value,territorio:$('territory').value,municipio:city.value,zona:zone.value,secao:section.value},modo:$('flowMode').value,modelo:DATA.selected,resultados:aggregate(),nota:'Fluxos estimados; não são trajetórias individuais nem intervalos de confiança.'},null,2),'application/json');
read('municipios.json.gz').then(data=>{municipal=data;fillCities();status.textContent='Selecione região ou UF; escolha uma UF para habilitar município, zona e seção.';}).catch(e=>{status.textContent='Lista de municípios indisponível: '+e.message;});
display();
})();
