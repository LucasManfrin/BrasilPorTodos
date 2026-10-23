import {createGraphRenderer} from '/modules/graph-canvas-3d.js';
import {fallbackReason} from '/modules/spatial.js';
import {createFrameSample} from '/frame-sample.mjs';

const host=document.querySelector('#host');
const status=document.querySelector('#status');
const output=document.querySelector('#report');
const types=['MEASURE','INDICATOR','MECHANISM','AFFECTED_GROUP'];
const nodes=Array.from({length:200},(_,index)=>({id:`stress-node-${String(index).padStart(3,'0')}`,revision:1,kind:types[index%4],label:`Conceito de teste ${String(index+1).padStart(3,'0')}`,definition:'Objeto sintético usado somente para medir renderização.',dimension:'Dimensão visual de teste',unit:null,indicator_code:null,policy_version_id:null,policy_version_number:null}));
const edges=Array.from({length:500},(_,index)=>{
  const from=index%nodes.length;let to=(index*37+19+Math.floor(index/nodes.length)*53)%nodes.length;if(to===from)to=(to+1)%nodes.length;
  return {id:`stress-edge-${index}`,revision:1,contract_version:'1.0.0',from_node:nodes[from],to_node:nodes[to],statement:`Relação sintética ${index+1}; sem evidência ou alegação sobre o mundo real.`,direction:['INCREASES','DECREASES','UNCERTAIN'][index%3],consensus:['ESTABLISHED','DEBATED','SPECULATIVE'][index%3],horizon:'SHORT',effect:'QUALITATIVE',authorship:'AI_ASSISTED',sources:[],evidence:[],links:[],premises:[],limitations:[],unknowns:[],scope:'Teste de renderização',period:'Sem período real',counterpoint_status:'NOT_RESEARCHED'};
});
// Independent precomputed geometry. No change or bypass in production validation.
const positions=nodes.map((node,index)=>{const y=1-2*(index+.5)/nodes.length;const radius=Math.sqrt(1-y*y);const angle=index*Math.PI*(3-Math.sqrt(5));return{id:node.id,x:Math.cos(angle)*radius*320,y:y*220,z:Math.sin(angle)*radius*180};});
const report={fixture:'Synthetic renderer-only stress; NOT a publishable graph',nodes:200,edges:500,publicContractMaxEdges:400,renderer:'Current createGraphRenderer export',created:0,disposed:0,canvasCount:0,renderSubmissions:0,events:[],performance:null,error:null};
let engine=null,rotating=true,measurement=0,capture=null;
const update=()=>{report.canvasCount=host.querySelectorAll('canvas').length;report.viewport={width:innerWidth,height:innerHeight,hostWidth:host.clientWidth,hostHeight:host.clientHeight,canvasWidth:host.querySelector('canvas')?.width??null,canvasHeight:host.querySelector('canvas')?.height??null,devicePixelRatio};output.textContent=JSON.stringify(report,null,2);};
function log(action,detail){report.events.push({action,detail});report.events=report.events.slice(-20);status.textContent=`${action}${detail?`: ${detail}`:''}`;update();}
function selection(value){engine?.select(value);log('Seleção',value?`${value.kind} ${value.id}`:'Visão geral');}
function create(){if(engine)dispose();report.error=null;try{engine=createGraphRenderer(host,nodes,edges,positions,{rendered,select:selection,dive:id=>{engine?.dive(id,1);log('Mergulho',id);},pause:()=>{rotating=false;document.querySelector('#rotation').textContent='Girar';},hover:text=>{status.textContent=text||'Rede sintética pronta.';},failure:reason=>{report.error=reason;log('Falha',reason);}});report.created++;rotating=true;document.querySelector('#rotation').textContent='Pausar giro';log('Rede criada','200 nós / 500 arestas');}catch(error){report.error=String(error);log('3D indisponível',String(error));}update();}
function finishCapture(result){
  if(!capture)return;
  capture.cleanup();capture=null;
  report.performance=result;
  log(result.state==='complete'?'Medição concluída':'Medição invalidada',result.state==='complete'?`${result.averageFps} chamadas de desenho/s · resultado local`:result.reason);
}
function invalidate(reason){if(capture)finishCapture(capture.sample.cancel(reason));}
function dispose(){measurement++;invalidate('Renderizador descartado.');engine?.dispose();engine=null;report.disposed++;log('Recursos descartados',`${host.querySelectorAll('canvas').length} canvas no DOM`);}
function rendered(time){
  report.renderSubmissions++;
  if(!capture)return;
  const result=capture.sample.frame(time);
  if(result.state!=='measuring')finishCapture(result);
  else if(result.collectedIntervals>0&&result.collectedIntervals%30===0){status.textContent=`Medindo desenhos reais: ${result.collectedIntervals}/240`;update();}
}
function hostVisible(){const rect=host.getBoundingClientRect();return rect.width>0&&rect.height>0&&Math.min(rect.bottom,innerHeight)-Math.max(rect.top,0)>=rect.height*.9;}
function measure(){
  invalidate('Nova medição solicitada.');
  if(!engine){log('Medição não iniciada','Crie a rede primeiro.');return;}
  const id=++measurement;engine.reset();engine.rotate(true);rotating=true;document.querySelector('#rotation').textContent='Pausar giro';
  host.scrollIntoView({block:'center',behavior:'instant'});
  // Establish the viewport after the deliberate scroll, before installing guards.
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    if(id!==measurement||!engine)return;
    if(document.hidden||!hostVisible()){report.performance={state:'invalidated',reason:'O palco precisa estar pelo menos 90% visível em uma aba ativa.'};log('Medição não iniciada',report.performance.reason);return;}
    const sample=createFrameSample();
    const cancelInteraction=()=>invalidate('Houve interação durante a medição; repita sem tocar nos controles.');
    const cancelViewport=()=>invalidate('Rolagem ou tamanho da janela mudou durante a medição.');
    const cancelVisibility=()=>{if(document.hidden)invalidate('A aba ficou oculta durante a medição.');};
    const observer=new IntersectionObserver(()=>{if(!hostVisible())invalidate('O palco deixou de ficar pelo menos 90% visível.');},{threshold:[0,.9,1]});
    document.addEventListener('pointerdown',cancelInteraction,true);document.addEventListener('keydown',cancelInteraction,true);document.addEventListener('wheel',cancelInteraction,{capture:true,passive:true});
    window.addEventListener('resize',cancelViewport);window.addEventListener('scroll',cancelViewport,{passive:true});document.addEventListener('visibilitychange',cancelVisibility);
    const timeout=setTimeout(()=>invalidate('Tempo limite de 30 segundos; captura incompleta, sem FPS publicado.'),30000);
    capture={sample,cleanup:()=>{clearTimeout(timeout);observer.disconnect();document.removeEventListener('pointerdown',cancelInteraction,true);document.removeEventListener('keydown',cancelInteraction,true);document.removeEventListener('wheel',cancelInteraction,true);window.removeEventListener('resize',cancelViewport);window.removeEventListener('scroll',cancelViewport);document.removeEventListener('visibilitychange',cancelVisibility);}};
    observer.observe(host);report.performance=null;
    log('Medindo','30 desenhos de aquecimento + 240 intervalos de desenho real. Não interaja durante a captura.');
  }));
}
document.querySelector('#node').onclick=()=>selection({kind:'node',id:nodes[0].id});
document.querySelector('#edge').onclick=()=>selection({kind:'edge',id:edges[1].id});
document.querySelector('#uncertain').onclick=()=>selection({kind:'edge',id:edges[2].id});
document.querySelector('#dive').onclick=()=>{engine?.dive(nodes[0].id,1);log('Mergulho','1 nível');};
document.querySelector('#expand').onclick=()=>{engine?.dive(nodes[0].id,2);log('Mergulho','2 níveis');};
document.querySelector('#reset').onclick=()=>{engine?.reset();log('Visão geral restaurada');};
document.querySelector('#rotation').onclick=event=>{rotating=!rotating;engine?.rotate(rotating);event.currentTarget.textContent=rotating?'Pausar giro':'Girar';log('Giro',rotating?'ativo':'pausado');};
document.querySelector('#measure').onclick=measure;
document.querySelector('#snapshot').onclick=()=>{update();status.textContent='Diagnóstico atualizado sem mover a rede.';};
document.querySelector('#dispose').onclick=dispose;
document.querySelector('#recreate').onclick=create;
document.querySelector('#theme').onclick=()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';log('Tema',document.documentElement.dataset.theme);};
window.addEventListener('beforeunload',()=>{measurement++;invalidate('Página encerrada.');engine?.dispose();});

const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const probe=document.createElement('canvas');const gl=probe.getContext('webgl2');const webgl=!!gl;gl?.getExtension('WEBGL_lose_context')?.loseContext();
const actual={reducedMotion,webgl,deviceMemory:navigator.deviceMemory,hardwareConcurrency:navigator.hardwareConcurrency,saveData:navigator.connection?.saveData};
const cases=[['Preferências reais do navegador',actual],['Caso sintético: movimento reduzido',{webgl:true,reducedMotion:true}],['Caso sintético: GPU indisponível',{webgl:false,reducedMotion:false}],['Caso sintético: dispositivo de 2 GB',{webgl:true,reducedMotion:false,deviceMemory:2}],['Caso sintético: economia de dados',{webgl:true,reducedMotion:false,saveData:true}]];
document.querySelector('#fallbacks').textContent=JSON.stringify(cases.map(([name,capabilities])=>({name,capabilities,reason:fallbackReason(capabilities)})),null,2);
create();
