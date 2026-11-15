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
