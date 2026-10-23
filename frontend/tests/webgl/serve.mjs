import http from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import ts from 'typescript';

const directory=path.dirname(fileURLToPath(import.meta.url));
const repository=path.resolve(directory,'../../..');
const feature=path.join(repository,'frontend/src/features/graphs');
const portArgument=process.argv.indexOf('--port');
const port=portArgument<0?8002:Number(process.argv[portArgument+1]);
if(!Number.isSafeInteger(port)||port<1024||port>65535)throw new Error('Use --port com uma porta local entre 1024 e 65535.');

async function compile(name){
  const filename=path.join(feature,name);
  let source=await readFile(filename,'utf8');
  if(name==='graph-canvas-3d.tsx'){
    // Extract the current factory, not a copied implementation. The React wrapper
    // is intentionally outside this isolated renderer/performance fixture.
    const tree=ts.createSourceFile(filename,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
    const wrapper=tree.statements.find(statement=>ts.isFunctionDeclaration(statement)&&statement.name?.text==='GraphCanvas3D'&&statement.modifiers?.some(modifier=>modifier.kind===ts.SyntaxKind.DefaultKeyword));
    if(!wrapper)throw new Error('GraphCanvas3D wrapper not found; review the harness extraction.');
    source=source.slice(0,wrapper.getFullStart());
    source=source.replace(/^import .* from ["']react["'];?\r?\n/gm,'').replace(/^import .* from ["'][^"']+\.css["'];?\r?\n/gm,'');
    if(!source.includes('export function createGraphRenderer'))throw new Error('Current renderer factory is missing.');
  }
  return ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022,jsx:ts.JsxEmit.ReactJSX,removeComments:false}}).outputText
    .replace(/from ["']\.\/helpers(?:\.ts)?["']/g,'from "/modules/helpers.js"')
    .replace(/from ["']\.\/spatial(?:\.ts)?["']/g,'from "/modules/spatial.js"')
    .replace(/from ["']\.\/interaction(?:\.ts)?["']/g,'from "/modules/interaction.js"');
}

const staticFiles=new Map([
  ['/',[path.join(directory,'index.html'),'text/html; charset=utf-8']],
  ['/harness.mjs',[path.join(directory,'harness.mjs'),'text/javascript; charset=utf-8']],
  ['/frame-sample.mjs',[path.join(directory,'frame-sample.mjs'),'text/javascript; charset=utf-8']],
  ['/tokens.css',[path.join(repository,'frontend/src/app/tokens.css'),'text/css; charset=utf-8']],
  ['/vendor/three.module.js',[path.join(repository,'node_modules/three/build/three.module.js'),'text/javascript; charset=utf-8']],
  ['/vendor/three.core.js',[path.join(repository,'node_modules/three/build/three.core.js'),'text/javascript; charset=utf-8']],
  ['/vendor/OrbitControls.js',[path.join(repository,'node_modules/three/examples/jsm/controls/OrbitControls.js'),'text/javascript; charset=utf-8']],
]);
const modules=new Map([['/modules/graph-canvas-3d.js','graph-canvas-3d.tsx'],['/modules/helpers.js','helpers.ts'],['/modules/spatial.js','spatial.ts'],['/modules/interaction.js','interaction.ts']]);
const server=http.createServer(async(request,response)=>{
  const pathname=new URL(request.url,'http://127.0.0.1').pathname;
  if(request.method!=='GET'&&request.method!=='HEAD'){response.writeHead(405);response.end();return;}
  try{
    let body,type;
    if(modules.has(pathname)){body=await compile(modules.get(pathname));type='text/javascript; charset=utf-8';}
    else if(staticFiles.has(pathname)){const item=staticFiles.get(pathname);body=await readFile(item[0]);type=item[1];}
    else{response.writeHead(404);response.end();return;}
    response.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'});
    response.end(request.method==='HEAD'?undefined:body);
  }catch(error){response.writeHead(500,{'Content-Type':'text/plain; charset=utf-8'});response.end(error.message);}
});
server.listen(port,'127.0.0.1',()=>console.log(`Renderer-only stress fixture: http://127.0.0.1:${port}/ (200 synthetic nodes / 500 edges; no API or database)`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));
