import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
const base=process.env.BASE_URL || 'http://127.0.0.1:3001';
assert.match(base, /^http:\/\/(127\.0\.0\.1|localhost):3001$/, 'Solo API local autorizada');
const results=[];
async function request(path, body) {
  const r=await fetch(base+path, {method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(15000)});
  return {status:r.status, body:await r.json()};
}
async function test(name,fn) {try {await fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,error:e.message});}}
const fixture={resourceId:1, customerName:'regression-test', date:'2031-01-01',slot:9,guests:3};
await test('salud y versión',async()=>{const r=await request('/health');assert.equal(r.status,200);assert.ok(['v1','v2'].includes(r.body.version));});
await test('paginación no vacía y orden estable',async()=>{
 const a=await request('/reservations?page=1&pageSize=50&status=confirmed');
 const b=await request('/reservations?page=2&pageSize=50&status=confirmed');
 assert.equal(a.status,200);assert.equal(a.body.data.length,50);assert.equal(b.body.data.length,50);
 assert.equal(a.body.hasNext,true);
 for(const row of a.body.data){assert.equal(row.status,'confirmed');assert.ok(row.resource_name);}
 const ids=new Set(a.body.data.map(x=>x.id));assert.ok(b.body.data.every(x=>!ids.has(x.id)));
 for(let i=1;i<a.body.data.length;i++){const x=a.body.data[i-1],y=a.body.data[i];assert.ok(x.reservation_date>y.reservation_date || (x.reservation_date===y.reservation_date && BigInt(x.id)>BigInt(y.id)));}
});
await test('400 ante entradas inválidas',async()=>{
 for (const body of [{},{...fixture,guests:0},{...fixture,slot:21},{...fixture,customerName:' '}])assert.equal((await request('/reservations',body)).status,400);
 for (const path of ['/reservations?page=0','/reservations?pageSize=101','/reservations?status=bad','/availability?resourceId=x&date=2026-11-14'])assert.equal((await request(path)).status,400);
});
await test('404 recurso inexistente',async()=>{assert.equal((await request('/availability?resourceId=9999&date=2026-11-14')).status,404);assert.equal((await request('/reservations',{...fixture,resourceId:9999})).status,404);});
await test('concurrencia conserva capacidad y rechazo 409',async()=>{
 const rows=await Promise.all(Array.from({length:20},(_,i)=>request('/reservations',{...fixture,customerName:'regression-'+i})));
 assert.equal(rows.filter(x=>x.status===201).length,6);assert.equal(rows.filter(x=>x.status===409).length,14);
 const a=await request('/availability?resourceId=1&date=2031-01-01');
 assert.equal(a.body.slots.length,12);const s=a.body.slots.find(x=>x.slot===9);assert.equal(s.booked,18);assert.equal(s.available,2);
 assert.equal((await request('/reservations',{...fixture,guests:21})).status,409);
});
const report={time:new Date().toISOString(),base,version:(await request('/health')).body.version,passed:results.filter(x=>x.pass).length,total:results.length,results};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));if(results.some(x=>!x.pass))process.exitCode=1;
