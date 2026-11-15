import {mixedTraffic,stats} from './lib.js';
export const options={
 summaryTrendStats:stats,
 scenarios:{normal:{executor:'constant-arrival-rate',rate:40,timeUnit:'1s',duration:'120s',preAllocatedVUs:60,maxVUs:60,gracefulStop:'10s'}},
 thresholds:{
  http_req_duration:['p(95)<200','p(99)<500',{threshold:'p(99)<5000',abortOnFail:true,delayAbortEval:'30s'}],
  http_req_failed:['rate<0.01',{threshold:'rate<0.10',abortOnFail:true,delayAbortEval:'30s'}],
  checks:['rate==1'],dropped_iterations:['count==0'],
  'http_req_duration{endpoint:availability}':['p(95)<150'],
  'http_req_duration{endpoint:list}':['p(95)<250'],
  'http_req_duration{endpoint:create}':['p(95)<250'],
 }
};
export default function(){mixedTraffic({phase:'carga'});}
