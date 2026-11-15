import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {assertFreshDirectory,assertWarmupComplete,monitorStopReason} from './trial-policy.mjs';
test('conservar resultados existentes al repetir una campaña',()=>{
 const dir=mkdtempSync(join(tmpdir(),'reservaflow-evidence-'));
 writeFileSync(join(dir,'raw.json'),'original');
 assert.throws(()=>assertFreshDirectory(dir),/no vacía/);
 assert.equal(readFileSync(join(dir,'raw.json'),'utf8'),'original');
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
