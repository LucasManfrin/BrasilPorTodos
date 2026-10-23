import test from 'node:test';
import assert from 'node:assert/strict';
import {layoutGraph, projectPoint, filterGraph, neighbors, uuidFromSlug, graphPath, safePublicPath, assertGraphLimits, graphWithinLimits, MAX_NODES, MAX_EDGES} from '../src/features/graphs/helpers.ts';
import {DEMO_GRAPH} from '../src/features/graphs/demo.ts';

const {nodes,edges} = DEMO_GRAPH.content;
const camera = {yaw:0,pitch:0,zoom:1,panX:0,panY:0};
test('deterministic layout is independent of input order and does not mutate the snapshot',()=>{
  const before=JSON.stringify(DEMO_GRAPH);
  assert.deepEqual(layoutGraph(nodes,edges),layoutGraph([...nodes].reverse(),[...edges].reverse()));
  assert.equal(JSON.stringify(DEMO_GRAPH),before);
});
test('layout has one finite bounded point for every node, including isolated nodes',()=>{
  const points=layoutGraph(nodes,edges);assert.equal(points.length,nodes.length);
  assert.deepEqual(new Set(points.map(p=>p.id)),new Set(nodes.map(n=>n.id)));
  for(const p of points)for(const axis of ['x','y','z'])assert.ok(Number.isFinite(p[axis])&&Math.abs(p[axis])<=1.6);
  assert.equal(new Set(points.map(p=>`${p.x},${p.y},${p.z}`)).size,nodes.length);
});
test('empty and singleton layouts remain meaningful',()=>{assert.deepEqual(layoutGraph([],[]),[]);assert.deepEqual(layoutGraph(nodes.slice(0,1),[]),[{id:nodes[0].id,x:0,y:0,z:0}]);});
test('initial desktop projection spreads the connected demo and separates selectable nodes',()=>{
  const points=layoutGraph(nodes,edges).map(point=>({...projectPoint(point,{...camera,yaw:-.32,pitch:.28},850,550),id:point.id}));
  const nearest=points.map((point,index)=>Math.min(...points.filter((_,other)=>other!==index).map(other=>Math.hypot(point.x-other.x,point.y-other.y))));
  assert.ok(nearest.reduce((sum,value)=>sum+value,0)/nearest.length>30,'Average nearest neighbor must exceed 30px.');
  assert.ok(Math.min(...nearest)>30,'Front and back nodes must not overlap in the initial scene.');
  const connected=points.filter(point=>point.id!=='demo-lacuna');
  assert.ok(Math.max(...connected.map(point=>point.x))-Math.min(...connected.map(point=>point.x))>370,'Isolated concepts cannot shrink the main cluster.');
  assert.ok(Math.max(...connected.map(point=>point.y))-Math.min(...connected.map(point=>point.y))>200);
});
test('projection centers the origin, rotates, zooms and pans in viewport pixels',()=>{
  const point={id:'p',x:1,y:0,z:0};const a=projectPoint(point,camera,1000,640);
  assert.equal(projectPoint({...point,x:0},camera,1000,640).x,500);
  assert.ok(Math.abs(projectPoint(point,{...camera,yaw:Math.PI/2},1000,640).x-500)<1e-8);
  const zoomed=projectPoint(point,{...camera,zoom:2,panX:10,panY:5},1000,640);
  assert.ok(Math.abs((zoomed.x-510)-(a.x-500)*2)<1e-8);assert.equal(zoomed.y,325);
});
test('projection guards missing dimensions and nonfinite camera geometry',()=>{
  const projected=projectPoint({id:'bad',x:NaN,y:Infinity,z:-Infinity},{yaw:NaN,pitch:Infinity,zoom:NaN,panX:NaN,panY:Infinity},NaN,0);
  for(const value of Object.values(projected))assert.ok(Number.isFinite(value));
});
test('all filter preserves existing exact node and edge references',()=>{const value=filterGraph(nodes,edges,'','ALL');assert.deepEqual(value,{nodes,edges});assert.equal(value.edges[0],edges[0]);});
test('text filter ignores accents and case and keeps exact endpoints',()=>{
  const value=filterGraph(nodes,edges,'COORDENACAO','ALL');assert.ok(value.nodes.some(n=>n.id==='demo-coordenacao'));
  assert.ok(value.edges.length>0);const ids=new Set(value.nodes.map(n=>n.id));
  for(const edge of value.edges){assert.ok(edges.includes(edge));assert.ok(ids.has(edge.from_node.id)&&ids.has(edge.to_node.id));}
});
test('an edge statement match keeps both endpoints instead of inventing links',()=>{
  const changed=edges.map((edge,i)=>i===0?{...edge,statement:'uma expressão exclusiva'}:edge);
  const value=filterGraph(nodes,changed,'EXPRESSAO EXCLUSIVA','ALL');
  assert.deepEqual(value.nodes.map(n=>n.id),[changed[0].from_node.id,changed[0].to_node.id]);assert.deepEqual(value.edges,[changed[0]]);
});
test('type filtering retains attached context and never leaves a dangling edge',()=>{
  const value=filterGraph(nodes,edges,'','AFFECTED_GROUP');assert.ok(value.nodes.some(n=>n.kind==='AFFECTED_GROUP'));
  const ids=new Set(value.nodes.map(n=>n.id));for(const edge of value.edges)assert.ok(ids.has(edge.from_node.id)&&ids.has(edge.to_node.id));
});
test('unknown query returns an honest empty network',()=>assert.deepEqual(filterGraph(nodes,edges,'naoexistente987','ALL'),{nodes:[],edges:[]}));
test('isolated node filter does not create any relation',()=>{const value=filterGraph(nodes,edges,'O que ainda falta saber','ALL');assert.equal(value.nodes.length,1);assert.equal(value.edges.length,0);});
test('neighbors preserves incoming/outgoing direction and deduplicates neighboring identities',()=>{
  const id='demo-acesso',value=neighbors(id,edges);assert.ok(value.incoming.length&&value.outgoing.length);
  for(const edge of value.incoming)assert.equal(edge.to_node.id,id);for(const edge of value.outgoing)assert.equal(edge.from_node.id,id);
  assert.equal(new Set(value.nodeIds).size,value.nodeIds.length);assert.ok(!value.nodeIds.includes(id));
  assert.deepEqual(neighbors('missing',edges),{incoming:[],outgoing:[],nodeIds:[]});
});
const uuid='12345678-1234-4234-8234-123456789abc';
test('pure slug converts only its exact identity namespace to persisted UUID',()=>{assert.equal(uuidFromSlug('node-'+uuid.replaceAll('-',''),'node'),uuid);assert.equal(uuidFromSlug('edge-'+uuid.replaceAll('-',''),'node'),null);});
for(const id of ['demo-acesso','node-abc','node-'+uuid, '../nodes/private', 'node-12345678123442348234123456789abc?draft=true'])test(`invalid slug does not become API route: ${id}`,()=>assert.equal(uuidFromSlug(id),null));
test('public paths pin revision and never target a draft or use a slug as UUID',()=>{assert.equal(safePublicPath('edge','edge-'+uuid.replaceAll('-',''),2),`/api/v1/graphs/edges/${uuid}/versions/2`);assert.equal(graphPath(uuid,3),`/grafos/${uuid}/versoes/3`);assert.equal(graphPath(uuid),`/grafos/${uuid}`);});
for(const revision of [0,-1,1.2,NaN,Infinity,2147483648])test(`invalid revision rejected: ${revision}`,()=>{assert.equal(graphPath(uuid,revision),null);assert.equal(safePublicPath('node','node-'+uuid.replaceAll('-',''),revision),null);});
for(const id of ['demonstracao-local','../draft','https://example.com','1234'])test(`unsafe graph identity rejected: ${id}`,()=>assert.equal(graphPath(id),null));
test('UI bounds reject oversize, duplicate identities and dangling relations instead of silently truncating',()=>{
  assert.equal(MAX_NODES,200);assert.equal(MAX_EDGES,400);
  const many=Array.from({length:201},(_,i)=>({...nodes[0],id:`n-${i}`}));
  assert.throws(()=>layoutGraph(many,[]),RangeError);assert.throws(()=>filterGraph(nodes,Array.from({length:401},()=>edges[0]),'','ALL'),RangeError);
  assert.throws(()=>assertGraphLimits([nodes[0],nodes[0]],[]),RangeError);assert.throws(()=>assertGraphLimits(nodes,[edges[0],edges[0]]),RangeError);
  assert.throws(()=>assertGraphLimits(nodes.slice(1),edges),RangeError);
});
test('maximum permitted scene remains finite and bounded',()=>{
  const all=Array.from({length:200},(_,i)=>({...nodes[0],id:`bounded-${i}`}));
  const links=Array.from({length:400},(_,i)=>({...edges[0],id:`edge-${i}`,from_node:all[i%200],to_node:all[(i+1)%200]}));
  const points=layoutGraph(all,links);assert.equal(points.length,200);for(const p of points){assert.ok(Number.isFinite(p.x+p.y+p.z));assert.ok(Math.abs(p.x)<=1.5&&Math.abs(p.y)<=1.05&&Math.abs(p.z)<=.65);}
  assert.deepEqual(points,layoutGraph([...all].reverse(),[...links].reverse()));
});
test('render guard rejects different endpoint revisions and definitions instead of replacing them',()=>{
  assert.equal(graphWithinLimits(DEMO_GRAPH),true);
  for(const replacement of [{...edges[0].from_node,revision:2},{...edges[0].from_node,definition:'Changed definition'}]){
    const content={...DEMO_GRAPH.content,edges:[{...edges[0],from_node:replacement},...edges.slice(1)]};
    assert.equal(graphWithinLimits({...DEMO_GRAPH,content}),false);
  }
  assert.equal(graphWithinLimits({content:{nodes:[],edges:[edges[0]]}}),false);
  assert.equal(graphWithinLimits({content:null}),false);
});
test('demonstration has no fake human review, publication, official indicator or usable public route',()=>{
  assert.equal(DEMO_GRAPH.is_example,true);assert.equal(DEMO_GRAPH.published_at,null);assert.deepEqual(DEMO_GRAPH.publications,[]);
  assert.equal(nodes.length,18);assert.equal(edges.length,24);assert.equal(graphPath(DEMO_GRAPH.id),null);
  assert.deepEqual(new Set(nodes.map(node=>node.kind)),new Set(['MEASURE','MECHANISM','INDICATOR','AFFECTED_GROUP']));
  for(const node of nodes)if(node.indicator_code!==null){assert.match(node.indicator_code,/^demo-/);assert.match(node.definition,/sem medição ou catálogo oficial/);}
  for(const edge of edges){assert.equal(edge.consensus,'SPECULATIVE');assert.equal(edge.authorship,'AI_ASSISTED');assert.equal(edge.effect,'QUALITATIVE');assert.equal(edge.counterpoint_status,'NOT_RESEARCHED');assert.equal(edge.links[0].relation,'CONTEXT');assert.ok(edge.sources.every(source=>new URL(source.url).hostname==='example.invalid'));assert.equal(safePublicPath('edge',edge.id,edge.revision),null);}
});
