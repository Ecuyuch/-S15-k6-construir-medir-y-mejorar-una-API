import {existsSync,readdirSync} from 'node:fs';
export function assertFreshDirectory(path){
 if(existsSync(path) && readdirSync(path).length)throw new Error('Carpeta de campaña no vacía: use CAMPAIGN nuevo para conservar evidencia');
}
export function assertWarmupComplete(result){
 if(result.exitCode!==0 || result.stopReasons.length)throw new Error('Calentamiento fallido o interrumpido: no iniciar carga');
}
export function monitorStopReason(unsafeSamples,missingSamples){
 if(unsafeSamples>=3)return 'RAM fuera del límite seguro durante tres muestras';
 if(missingSamples>=3)return 'Pérdida de telemetría durante tres muestras';
 return null;
}
export function persistWithRetry(operation,delayMs=50){
 for(let attempt=0;;attempt++){
  try{return operation();}catch(error){
   if(attempt>=4 || !['UNKNOWN','EPERM','EBUSY','EACCES'].includes(error.code))throw error;
   if(delayMs)Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,delayMs);
  }
 }
}
