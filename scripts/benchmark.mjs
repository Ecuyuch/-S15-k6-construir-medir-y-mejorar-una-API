import {spawn,execFileSync} from 'node:child_process';
import {mkdirSync,writeFileSync,appendFileSync,readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,join} from 'node:path';
import os from 'node:os';
const root=resolve(import.meta.dirname,'..'),out=join(root,'results','evaluacion-2026-11-14');
mkdirSync(out,{recursive:true});
const docker=process.env.DOCKER_EXE || 'C:/Program Files/Docker/Docker/resources/bin/docker.exe';
const image='grafana/k6:1.0.0';
const env={...process.env,PATH:'C:/Program Files/Docker/Docker/resources/bin;'+process.env.PATH};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function run(exe,args,extra={}){return execFileSync(exe,args,{cwd:root,env,encoding:'utf8',maxBuffer:30*1024*1024,...extra});}
function d(args){return run(docker,args);}
function sql(query){return d(['compose','exec','-T','db','psql','-U','reserva','-d','reservaflow','-v','ON_ERROR_STOP=1','-At','-c',query]);}
function file(name,data){writeFileSync(join(out,name),typeof data==='string'?data:JSON.stringify(data,null,2));}
function log(text){console.log(new Date().toISOString()+' '+text);appendFileSync(join(out,'execution.log'),new Date().toISOString()+' '+text+'\n');}
async function ready(){
 for(let i=0;i<60;i++){try{sql('SELECT 1');const r=await fetch('http://127.0.0.1:3001/health');if(r.ok)return;}catch{}await sleep(1000);}
 throw new Error('API/DB no preparada');
}
async function reset(version){
 d(['compose','exec','-T','db','psql','-U','reserva','-d','reservaflow','-v','ON_ERROR_STOP=1','-f','/db/reset.sql']);
 if(version==='v2')d(['compose','exec','-T','db','psql','-U','reserva','-d','reservaflow','-v','ON_ERROR_STOP=1','-f','/db/v2_fix.sql']);
 const copy=sql("COPY (SELECT id,resource_id,customer_name,reservation_date,slot,guests,status,created_at FROM reservations ORDER BY id) TO STDOUT WITH CSV");
 const fingerprint=createHash('sha256').update(copy).digest('hex');
 return {sha256:fingerprint,distribution:sql("SELECT status,count(*) FROM reservations GROUP BY status ORDER BY status"),indexes:sql("SELECT indexname FROM pg_indexes WHERE tablename='reservations' ORDER BY indexname")};
}
function integrity(){
 return {overbooked:Number(sql("SELECT count(*) FROM (SELECT resource_id,reservation_date,slot FROM reservations WHERE status='confirmed' GROUP BY 1,2,3 HAVING sum(guests)>20) q").trim()),
 resources:Number(sql('SELECT count(*) FROM resources').trim()),reservations:Number(sql('SELECT count(*) FROM reservations').trim())};
}
async function k6(name,script,vars={}){
 log('INICIO '+name);const start=Date.now(),container='reservaflow-k6-eval';
 const args=['run','--rm','--name',container,'--cpus','1','--memory','256m','--network','reservaflowbackend_default',
 '-v',root.replaceAll('\\','/')+'/k6:/scripts:ro','-v',out.replaceAll('\\','/')+':/results',
 '-e','BASE_URL=http://api:3000','-e','K6_NO_USAGE_REPORT=true'];
 for(const [k,v] of Object.entries(vars))args.push('-e',k+'='+v);
 args.push(image,'run','--no-color','--quiet','--summary-export=/results/'+name+'.summary.json',
 '--out','json=/results/'+name+'.timeseries.json.gz','/scripts/evaluation/'+script);
 const child=spawn(docker,args,{cwd:root,env,windowsHide:true});
 let text='';child.stdout.on('data',x=>text+=x.toString());child.stderr.on('data',x=>text+=x.toString());
 const resources=[],stopReasons=[];let violations=0,finished=false,monitoring=false;
 child.on('exit',()=>finished=true);
 async function sample(){
  if(finished || monitoring)return;monitoring=true;
  try {
   const lines=d(['stats','--no-stream','--format','{{json .}}','reservaflow-api','reservaflow-db',container]).trim().split('\n').filter(Boolean).map(x=>JSON.parse(x));
   const free=os.freemem(),bad=free<700*1024*1024 || lines.some(x=>Number(x.MemPerc.replace('%',''))>90);
   resources.push({time:new Date().toISOString(),elapsedSeconds:(Date.now()-start)/1000,hostFreeBytes:free,hostTotalBytes:os.totalmem(),containers:lines});
   violations=bad?violations+1:0;
   if(violations>=3 && !stopReasons.length){stopReasons.push('RAM fuera del límite seguro durante tres muestras');log('PARADA SEGURIDAD '+name);d(['stop','--time','10',container]);}
  }catch(e){resources.push({time:new Date().toISOString(),error:e.message});}
  finally{monitoring=false;}
 }
 const timer=setInterval(sample,5000);
 const code=await new Promise((res,rej)=>{child.on('error',rej);child.on('close',res);});clearInterval(timer);
 file(name+'.console.txt',text);file(name+'.resources.json',resources);
 const result={name,script,started:new Date(start).toISOString(),ended:new Date().toISOString(),seconds:(Date.now()-start)/1000,exitCode:code,stopReasons,integrity:integrity()};
 file(name+'.meta.json',result);log('FIN '+name+' exit='+code+' duracion='+result.seconds.toFixed(1)+'s');return result;
}
async function explain(version){
 const query="SELECT r.id,r.resource_id,rs.name,r.customer_name,r.reservation_date FROM reservations r JOIN resources rs ON rs.id=r.resource_id WHERE r.status='confirmed' ORDER BY r.reservation_date DESC,r.id DESC LIMIT 50 OFFSET 450";
 file(version+'-explain.txt',sql('EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) '+query));
}
const codeFiles=['app/src/server.ts','app/src/listing.ts','app/src/db.ts','app/Dockerfile','app/package.json','docker-compose.yml','docker-compose.override.yml','db/init.sql','db/v2_fix.sql',...readdirSync(join(root,'k6/evaluation')).map(x=>'k6/evaluation/'+x),'scripts/benchmark.mjs','scripts/functional.mjs'];
const hashes=Object.fromEntries(codeFiles.map(x=>[x,createHash('sha256').update(readFileSync(join(root,x))).digest('hex')]));
file('code-manifest.json',{gitCommit:run('git',['rev-parse','HEAD']).trim(),branch:run('git',['branch','--show-current']).trim(),hashes});
file('environment.json',{recorded:new Date().toISOString(),host:JSON.parse(run('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',['-NoProfile','-Command',"$c=Get-CimInstance Win32_ComputerSystem; $p=Get-CimInstance Win32_Processor; $o=Get-CimInstance Win32_OperatingSystem; [pscustomobject]@{Manufacturer=$c.Manufacturer;Model=$c.Model;PhysicalMemory=$c.TotalPhysicalMemory;CPU=$p.Name;Cores=$p.NumberOfCores;LogicalProcessors=$p.NumberOfLogicalProcessors;OS=$o.Caption;OSVersion=$o.Version} | ConvertTo-Json -Compress"])),
 docker:JSON.parse(d(['info','--format','{{json .}}'])),k6:d(['run','--rm',image,'version']).trim(),
 images:JSON.parse(d(['image','inspect',image,'reservaflowbackend-api','postgres:16-alpine'])),
 compose:d(['compose','config']),otherContainers:d(['ps','--format','{{.Names}} {{.Image}} {{.Status}}']),cache:'Calentamiento 15s después de cada restauración; no se vacía caché del SO/WSL; contenedores compartiendo host; dos repeticiones ABBA.'});
const order=[['v1','load-1'],['v2','load-1'],['v2','load-2'],['v1','load-2'],['v1','stress'],['v2','stress']];
for(const [version,type] of order){
 env.APP_VERSION=version;
 d(['compose','up','-d','--no-deps','--force-recreate','api']);
 await ready();
 const initial=await reset(version);file(version+'-'+type+'.initial.json',initial);
 if(type==='load-1'){
  file(version+'-functional.json',run(process.execPath,['scripts/functional.mjs']));
  if(integrity().overbooked!==0)throw new Error('Falla de integridad');
  await reset(version);
  await k6(version+'-smoke','smoke.js');
  await reset(version);
  await explain(version);
 }
 await k6(version+'-'+type+'-warmup','warmup.js');
 // El calentamiento también escribe: restaurar exactamente las filas de prueba
 // eliminando solo sus reservas y restablecer secuencia. Mantiene caché caliente.
 sql("DELETE FROM reservations WHERE customer_name LIKE 'k6-eval-%'; SELECT setval('reservations_id_seq',(SELECT max(id) FROM reservations)); ANALYZE reservations");
 file(version+'-'+type+'.measured-start.json',{initial,integrity:integrity()});
 const result=await k6(version+'-'+type,type==='stress'?'stress_recovery.js':'load.js');
 if(type==='stress' && result.exitCode!==0){
  // Recuperación posterior a una interrupción sin reiniciar API ni DB.
  sql("DELETE FROM reservations WHERE customer_name LIKE 'k6-eval-%'; SELECT setval('reservations_id_seq',(SELECT max(id) FROM reservations));");
  await k6(version+'-recovery-safe','warmup.js',{DURATION:'30s',PHASE:'recuperacion_posterior'});
 }
 if(result.integrity.overbooked!==0)throw new Error('Sobrecupo detectado');
}
env.APP_VERSION='v2';d(['compose','up','-d','--no-deps','--force-recreate','api']);await ready();await reset('v2');
file('v2-functional-final.json',run(process.execPath,['scripts/functional.mjs']));await reset('v2');
file('final-state.json',{version:'v2',integrity:integrity(),containers:d(['compose','ps'])});
log('EVALUACION COMPLETA');
