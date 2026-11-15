import http from 'k6/http';
import {check} from 'k6';
import exec from 'k6/execution';

export const BASE_URL=__ENV.BASE_URL || 'http://localhost:3001';
if (!/^http:\/\/(api:3000|localhost:3001|127\.0\.0\.1:3001)$/.test(BASE_URL)) throw new Error('Solo destinos locales autorizados');
export const stats=['avg','min','med','max','p(90)','p(95)','p(99)'];
export function dateOffset(days){return new Date(Date.UTC(2026,10,14)+days*86400000).toISOString().slice(0,10);}
export function json(r){try{return r.json();}catch(_){return null;}}
export function params(endpoint,tags={}) {return {timeout:'6s',tags:{endpoint,name:endpoint,...tags},headers:{'Content-Type':'application/json'}};}
export function mixedTraffic(tags={}) {
 const n=exec.scenario.iterationInTest, op=n%10;
 let r;
 if(op<4){
  r=http.get(BASE_URL+'/availability?resourceId='+((n%50)+1)+'&date='+dateOffset((Math.floor(n/50)%181)-90),params('availability',tags));
  const b=json(r);
  check(r,{'availability HTTP 200':x=>x.status===200,'12 franjas y capacidad coherente':()=>!!b && b.slots.length===12 && b.slots.every(s=>s.capacity===20 && s.booked>=0 && s.booked<=20 && s.available===20-s.booked)},tags);
 }else if(op<7){
  const page=(Math.floor(n/10)%20)+1;
  r=http.get(BASE_URL+'/reservations?page='+page+'&pageSize=50&status=confirmed',params('list',tags));
  const b=json(r);
  check(r,{'list HTTP 200':x=>x.status===200,'pagina de 50 reservas confirmadas':()=>!!b && b.page===page && b.pageSize===50 && b.data.length===50 && b.data.every(x=>x.status==='confirmed' && typeof x.resource_name==='string')},tags);
 }else{
  // Una combinación única por iteración: evita conflictos accidentales por datos.
  const p={resourceId:n%50+1,customerName:'k6-eval-'+n,date:dateOffset(400+Math.floor(n/600)),slot:9+Math.floor(n/50)%12,guests:1+n%2};
  r=http.post(BASE_URL+'/reservations',JSON.stringify(p),params('create',tags));
  const b=json(r);
  check(r,{'create HTTP 201':x=>x.status===201,'reserva conserva campos':()=>!!b && b.id!==undefined && b.resource_id===p.resourceId && b.guests===p.guests && b.status==='confirmed'},tags);
 }
 return r;
}
export function safety(){
 return {http_req_failed:[{threshold:'rate<0.10',abortOnFail:true,delayAbortEval:'30s'}],
 http_req_duration:[{threshold:'p(99)<5000',abortOnFail:true,delayAbortEval:'30s'}]};
}
