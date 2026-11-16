const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'output','evidencias');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1120,height:300},deviceScaleFactor:1});
 const evidence=[];
 try{
  for(const [name,route] of [['salud','/health'],['reservas','/reservations?page=1&pageSize=1']]){
   const url='http://127.0.0.1:3001'+route,response=await page.goto(url);
   const body=await response.json();
   evidence.push({name,url,status:response.status(),body,time:new Date().toISOString()});
   await page.evaluate(({url,body,status})=>{
    document.body.textContent='';
    const head=document.createElement('h1');head.textContent='ReservaFlow | HTTP '+status;document.body.append(head);
    const addr=document.createElement('p');addr.textContent=url;document.body.append(addr);
    const pre=document.createElement('pre');pre.textContent=JSON.stringify(body,null,2);document.body.append(pre);
   },{url,body,status:response.status()});
   await page.addStyleTag({content:'body{padding:28px;font-family:Arial,sans-serif;color:#172334;background:white}h1{font-size:25px;margin:0 0 12px}p{font-size:18px;margin:0 0 24px}pre{font-family:Consolas,monospace;font-size:22px;line-height:1.4;white-space:pre-wrap;background:#f4f6f8;padding:20px}'});
   await page.screenshot({path:path.join(out,'captura_api_'+name+'.png'),fullPage:true});
  }
  fs.writeFileSync(path.join(out,'respuestas_api.json'),JSON.stringify({browser:await browser.version(),evidence},null,2));
 }finally{await browser.close();}
 console.log('Capturas de respuestas HTTP reales guardadas');
})().catch(e=>{console.error(e);process.exitCode=1;});
