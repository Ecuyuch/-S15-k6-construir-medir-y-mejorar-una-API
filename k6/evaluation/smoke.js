import http from 'k6/http';
import {check,sleep} from 'k6';
import {BASE_URL,mixedTraffic,dateOffset,params,json,stats} from './lib.js';
export const options={vus:1,duration:'30s',summaryTrendStats:stats,thresholds:{checks:['rate==1'],http_req_failed:['rate==0'],http_req_duration:['p(95)<2000']}};
export default function(){
 const health=http.get(BASE_URL+'/health',params('health'));
 check(health,{'health valido':r=>r.status===200 && json(r).status==='ok'});
 mixedTraffic({phase:'humo'});
 const body={resourceId:1,customerName:'smoke-negative',date:dateOffset(2000),slot:10,guests:21};
 const over=http.post(BASE_URL+'/reservations',JSON.stringify(body),{...params('overbooking'),responseCallback:http.expectedStatuses(409)});
 check(over,{'sobrecupo 409':r=>r.status===409});
 const bad=http.post(BASE_URL+'/reservations','{}',{...params('invalid'),responseCallback:http.expectedStatuses(400)});
 check(bad,{'invalido 400':r=>r.status===400});sleep(1);
}
