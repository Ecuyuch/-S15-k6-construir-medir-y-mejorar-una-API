import exec from 'k6/execution';
import {sleep} from 'k6';
import {mixedTraffic,stats,safety} from './lib.js';
export const options={
 summaryTrendStats:stats,
 scenarios:{stress:{executor:'ramping-vus',startVUs:2,gracefulRampDown:'6s',gracefulStop:'10s',stages:[
 {duration:'20s',target:2},{duration:'25s',target:10},{duration:'25s',target:20},
 {duration:'20s',target:40},{duration:'20s',target:40},{duration:'10s',target:2},
 {duration:'50s',target:2},{duration:'10s',target:0}]}},
 thresholds:{...safety(),checks:['rate==1'],
 'http_req_duration{phase:recuperacion}':['p(95)<300'],
 'http_req_failed{phase:recuperacion}':['rate<0.01'],
 'http_reqs{phase:recuperacion}':['count>20'],
 'http_req_duration{phase:base}':['p(95)<300'],
 'http_req_duration{phase:meseta}':['p(95)<5000']}
};
export default function(){
 const t=(Date.now()-exec.scenario.startTime)/1000;
 const phase=t<20?'base':t<90?'subida':t<110?'meseta':t<120?'descenso':t<170?'recuperacion':'cierre';
 mixedTraffic({phase});sleep(0.25);
}
