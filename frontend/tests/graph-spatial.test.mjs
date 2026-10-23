import test from 'node:test';
import assert from 'node:assert/strict';
import { cameraFrame, fallbackReason, neighborhoodIds, spatialLayout, WORLD_SCALE } from '../src/features/graphs/spatial.ts';
import { layoutGraph, MAX_EDGES } from '../src/features/graphs/helpers.ts';
import { DEMO_GRAPH } from '../src/features/graphs/demo.ts';

const {nodes, edges} = DEMO_GRAPH.content;

test('WebGL layout preserves deterministic existing positions and input snapshots', () => {
  const before = JSON.stringify(DEMO_GRAPH);
  const actual = spatialLayout(nodes, edges);
  assert.deepEqual(actual, layoutGraph(nodes, edges).map(point => ({id:point.id, x:point.x*WORLD_SCALE, y:point.y*WORLD_SCALE, z:point.z*WORLD_SCALE})));
  assert.deepEqual(actual, spatialLayout([...nodes].reverse(), [...edges].reverse()));
  assert.equal(JSON.stringify(DEMO_GRAPH), before);
});

test('renderer mutations cannot corrupt a cached layout or another caller', () => {
  const first = spatialLayout(nodes, edges);
  const before = structuredClone(first);
  first[0].x = 99999;
  first[0].id = 'renderer-mutated';
  first.push({id:'renderer-added',x:0,y:0,z:0});
  assert.deepEqual(spatialLayout(nodes, edges), before);
});

test('cache signatures distinguish endpoint topology and validation still runs on hits', () => {
  const base = spatialLayout(nodes, edges);
  const changed = [{...edges[0],to_node:nodes.find(node => node.id !== edges[0].from_node.id && node.id !== edges[0].to_node.id)}, ...edges.slice(1)];
  assert.notDeepEqual(spatialLayout(nodes, changed), base);
  assert.throws(() => spatialLayout(nodes, [{...edges[0],from_node:{...edges[0].from_node,revision:100}}, ...edges.slice(1)]), RangeError);
});

test('bounded cache eviction does not change deterministic geometry', () => {
  const before = spatialLayout(nodes, edges);
  for (let i=0;i<10;i++) spatialLayout([{...nodes[0],id:`cache-${i}`}], []);
  assert.deepEqual(spatialLayout(nodes, edges), before);
  assert.deepEqual(spatialLayout([], []), []);
});

test('renderer helper does not relax the 400-edge public contract for stress fixtures', () => {
  assert.equal(MAX_EDGES,400);
  assert.throws(() => spatialLayout(nodes, Array.from({length:500},(_,i)=>({...edges[i%edges.length],id:`stress-${i}`}))), RangeError);
});

const node = id => ({...nodes[0],id});
const link = (from,to) => ({...edges[0],id:`${from}-${to}`,from_node:node(from),to_node:node(to)});
const chain = [link('a','b'),link('c','b'),link('c','d'),link('d','a'),link('b','a')];

test('visual neighborhood respects depth, cycles and directions without changing links', () => {
  const before=JSON.stringify(chain);
  assert.deepEqual(neighborhoodIds('a',chain,0),['a']);
  assert.deepEqual(neighborhoodIds('a',chain,1),['a','b','d']);
  assert.deepEqual(neighborhoodIds('a',chain,2),['a','b','c','d']);
  assert.deepEqual(neighborhoodIds('a',[...chain].reverse(),10000),['a','b','c','d']);
  assert.deepEqual(neighborhoodIds('isolated',chain,2),['isolated']);
  assert.deepEqual(neighborhoodIds('a',chain,NaN),['a']);
  assert.equal(JSON.stringify(chain),before);
});

test('camera fit has a finite meaningful empty view and ignores invalid points', () => {
  const empty=cameraFrame([]);
  assert.deepEqual(empty.target,{x:0,y:0,z:0});
  assert.ok(Number.isFinite(empty.distance)&&empty.distance>0);
  assert.deepEqual(cameraFrame([{x:NaN,y:0,z:0},{x:0,y:Infinity,z:0}]),empty);
  const one=cameraFrame([{x:100,y:-30,z:4}]);
  assert.deepEqual(one.target,{x:100,y:-30,z:4});
  assert.ok(one.distance>=180);
});

test('camera fit centers translated points and leaves sufficient margin at portrait and wide aspects', () => {
  const points=[{x:-200,y:-30,z:-50},{x:300,y:130,z:70}];
  for (const aspect of [.1,.45,1,1.8,3]) {
    const frame=cameraFrame(points,aspect);
    assert.deepEqual(frame.target,{x:50,y:50,z:10});
    const radius=Math.max(...points.map(point=>Math.hypot(point.x-50,point.y-50,point.z-10)));
    const halfFov=Math.min(Math.PI/9,Math.atan(Math.tan(Math.PI/9)*aspect));
    assert.ok(frame.distance*Math.sin(halfFov)>radius+32);
  }
  assert.ok(cameraFrame(points,.45).distance>cameraFrame(points,1.8).distance);
  for(const invalid of [0,-1,NaN,Infinity]) assert.deepEqual(cameraFrame(points,invalid),cameraFrame(points,1));
});

test('fallback honors explicit accessibility, GPU and data preferences in priority order', () => {
  const capable={reducedMotion:false,webgl:true,deviceMemory:8,hardwareConcurrency:8};
  assert.equal(fallbackReason(capable),null);
  assert.match(fallbackReason({...capable,reducedMotion:true,webgl:false}),/movimento reduzido/);
  assert.match(fallbackReason({...capable,webgl:false}),/não disponibilizou o 3D/);
  assert.match(fallbackReason({...capable,saveData:true}),/economizar dados/);
  assert.match(fallbackReason({...capable,deviceMemory:2}),/navegação leve/);
  assert.match(fallbackReason({...capable,hardwareConcurrency:1}),/navegação leve/);
});

test('unknown or invalid hardware hints are not mistaken for a weak device', () => {
  assert.equal(fallbackReason({reducedMotion:false,webgl:true}),null);
  for(const unknown of [0,-1,NaN,Infinity]) assert.equal(fallbackReason({reducedMotion:false,webgl:true,deviceMemory:unknown,hardwareConcurrency:unknown}),null);
});
