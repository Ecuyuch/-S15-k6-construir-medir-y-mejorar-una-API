import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {assertFreshDirectory,assertWarmupComplete,monitorStopReason,persistWithRetry} from './trial-policy.mjs';
test('conservar resultados existentes al repetir una campaña',()=>{
 const dir=mkdtempSync(join(tmpdir(),'reservaflow-evidence-'));
 writeFileSync(join(dir,'raw.json'),'original');
 assert.throws(()=>assertFreshDirectory(dir),/no vacía/);
 assert.equal(readFileSync(join(dir,'raw.json'),'utf8'),'original');
});
test('reintentar un bloqueo transitorio de archivo y propagar un error permanente',()=>{
 let calls=0;
 assert.equal(persistWithRetry(()=>{if(++calls<3)throw Object.assign(new Error('sharing'),{code:'UNKNOWN'});return 'saved';},0),'saved');
 assert.equal(calls,3);
 assert.throws(()=>persistWithRetry(()=>{throw Object.assign(new Error('disk full'),{code:'ENOSPC'});},0),/disk full/);
});
test('un calentamiento interrumpido nunca permite iniciar carga',()=>{
 assert.throws(()=>assertWarmupComplete({exitCode:105,stopReasons:['RAM']}),/calentamiento/i);
 assert.throws(()=>assertWarmupComplete({exitCode:99,stopReasons:[]}),/calentamiento/i);
 assert.doesNotThrow(()=>assertWarmupComplete({exitCode:0,stopReasons:[]}));
});
test('parar al perder tres muestras o tres lecturas inseguras de memoria',()=>{
 assert.equal(monitorStopReason(2,0),null);
 assert.match(monitorStopReason(3,0),/RAM/);
 assert.match(monitorStopReason(0,3),/telemetría/);
});
