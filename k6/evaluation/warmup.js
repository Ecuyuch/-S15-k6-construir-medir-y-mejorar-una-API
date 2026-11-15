import {sleep} from 'k6';
import {mixedTraffic,stats} from './lib.js';
export const options={vus:1,duration:__ENV.DURATION || '15s',summaryTrendStats:stats,
 thresholds:{checks:['rate==1'],http_req_failed:['rate<0.01'],http_req_duration:['p(95)<300']}};
export default function(){mixedTraffic({phase:__ENV.PHASE || 'calentamiento'});sleep(0.5);}
