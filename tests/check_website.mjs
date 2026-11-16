import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const work=path.join(root,'work'),shots=path.join(work,'visuals_site_screenshots');
fs.mkdirSync(shots,{recursive:true});
const live=process.argv[2];
const result={execution:"Local VS Code integrated terminal; headless browser on the user's PC",passed:false,viewports:[]};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let server,browser,ws,sequence=0,sessionId,loadResolve;
const pending=new Map(),errors=[];
function send(method,params={},session){
  const id=++sequence;
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP timeout '+method));},20000);
    pending.set(id,{resolve,reject,timer});
    ws.send(JSON.stringify({id,method,params,...(session?{sessionId:session}:{})}));
  });
}
const command=(method,params={})=>send(method,params,sessionId);
async function evaluate(expression){
  const r=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function load(method,params){
  const ready=new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{loadResolve=null;reject(new Error('Page load timeout'));},20000);
    loadResolve=()=>{clearTimeout(timer);loadResolve=null;resolve();};
  });
  await command(method,params);await ready;
}
try{
  if(process.env.HOUSEHOLD_FINANCE_VSCODE!=='1')throw new Error('Run from the local project VS Code terminal');
  let base=live;
  if(!base){
    const docs=path.join(root,'docs');
    server=http.createServer((req,res)=>{
      const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
      const file=path.resolve(docs,'.'+(pathname.endsWith('/')?pathname+'index.html':pathname));
      if(!file.startsWith(docs+path.sep)){res.writeHead(403);res.end();return;}
      fs.readFile(file,(error,bytes)=>{
        if(error){res.writeHead(404);res.end();return;}
        const mime=file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/html';
        res.writeHead(200,{'Content-Type':mime+'; charset=utf-8'});res.end(bytes);
      });
    });
    await new Promise(r=>server.listen(0,'127.0.0.1',r));
    base='http://127.0.0.1:'+server.address().port+'/';
  }
  result.url=base;
  const exe=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(fs.existsSync);
  if(!exe)throw new Error('No installed Chromium browser');
  const profile=path.join(work,'housing-browser-'+Date.now());
  browser=spawn(exe,['--headless=new','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe'],windowsHide:true});
  browser.stderr.on('data',()=>{});
  const active=path.join(profile,'DevToolsActivePort');
  for(let i=0;i<120&&!fs.existsSync(active);i++)await pause(100);
  if(!fs.existsSync(active))throw new Error('Browser did not start');
  const [port,endpoint]=fs.readFileSync(active,'utf8').trim().split(/\r?\n/);
  ws=new WebSocket('ws://127.0.0.1:'+port+endpoint);
  ws.onmessage=event=>{
    const m=JSON.parse(event.data);
    if(m.id&&pending.has(m.id)){
      const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);
      m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result??{});
    }else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);
    else if(m.method==='Page.loadEventFired'&&m.sessionId===sessionId&&loadResolve)loadResolve();
  };
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const target=await send('Target.createTarget',{url:'about:blank'});
  ({sessionId}=await send('Target.attachToTarget',{targetId:target.targetId,flatten:true}));
  await command('Page.enable');await command('Runtime.enable');
  await command('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'},{name:'prefers-color-scheme',value:'dark'}]});
  const expected=JSON.parse(fs.readFileSync(path.join(root,'data/processed/housing_audit_summary.json'),'utf8'));
  const regionalExpected=JSON.parse(fs.readFileSync(path.join(root,'docs/assets/visuals-data.json'),'utf8'));
  for(const [width,height] of [[1440,1000],[768,1024],[390,844],[320,780]]){
    await command('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<600});
    await load('Page.navigate',{url:base});
    await evaluate(`new Promise((resolve,reject)=>{let count=0;const timer=setInterval(()=>{if(document.documentElement.dataset.visuals==='ready'&&document.documentElement.dataset.homebuying==='ready'){clearInterval(timer);resolve(true);}else if(document.documentElement.dataset.visuals==='error'||++count>150){clearInterval(timer);reject(new Error('Visuals did not become ready'));}},100);})`);
    if(await evaluate('document.documentElement.dataset.theme')!=='light')throw new Error('Fresh visit must start light despite dark system preference');
    const check=await evaluate(`(()=>{
      const expected=${JSON.stringify(expected)};
      const badMetrics=[...document.querySelectorAll('[data-metric]')].flatMap(e=>{
        const key=e.dataset.metric,value=Number(e.textContent.replaceAll('−','-').replace(/[^0-9.-]/g,''));
        return !Number.isFinite(expected[key])||Math.abs(value-expected[key])>.001?[{key,value,expected:expected[key]}]:[];
      });
      const brokenAnchors=[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash);
      const clipped=[...document.querySelectorAll('.calculation>div,.button,figcaption,.header-tools')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.textContent);
      return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,badMetrics,brokenAnchors,clipped,question:document.querySelector('h1').textContent,figures:document.querySelectorAll('figure').length,metricCount:document.querySelectorAll('[data-metric]').length,font:getComputedStyle(document.body).fontFamily};
    })()`);
    if(check.scrollWidth>width||check.badMetrics.length||check.brokenAnchors.length||check.clipped.length||check.question!==expected.question||check.figures<7||check.metricCount<8||!check.font.includes('system-ui'))throw new Error('Page check failed '+JSON.stringify(check));
    await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    if(await evaluate('document.activeElement.className')!=='skip-link')throw new Error('Skip link is not first');
    await evaluate('document.activeElement.blur();window.scrollTo(0,0)');

    // Homebuying case checks use the saved desktop outputs as the independent UI oracle.
    const hbExpected=JSON.parse(fs.readFileSync(path.join(root,'docs/assets/homebuying-data.json'),'utf8'));
    const hbCheck=await evaluate(`(()=>{
      const data=${JSON.stringify({"cases": []})};
      const failures=[],el=id=>document.getElementById(id);
      const change=(id,value)=>{el(id).value=value;el(id).dispatchEvent(new Event('change',{bubbles:true}));};
      const check=(v,label)=>{if(!v)failures.push(label);};
      check(el('hb-city').value==='Vancouver'&&el('hb-profile').value==='couple','default city/profile');
      check(el('hb-bars').textContent.includes('CAD 190,014')&&el('hb-bars').textContent.includes('CAD 40,014'),'baseline income values');
      check(el('hb-verdict').textContent==='Cash is enough. Income is the hurdle.','clear baseline verdict');
      check(document.querySelectorAll('.hb-city-marker').length===3,'three official city markers');
      change('hb-scenario','price20');
      check(el('hb-verdict').textContent==='Both modeled checks are within limits.','cheaper home clears example');
      check(el('hb-audit-conclusion').textContent.includes('income shortfall'),'audit remains baseline');
      change('hb-scenario','baseline');change('hb-profile','single');
      check(el('hb-income-scope').textContent.includes('If minimum cash were available'),'cash-short conditional income');
      change('hb-city','Victoria');
      check(el('hb-verdict').textContent==='Cash is enough. Income is the hurdle.','Victoria cash/income split');
      change('hb-profile','couple');
      check(el('hb-verdict').textContent==='Both modeled checks are within limits.','Victoria two earners');
      document.querySelector('.hb-city-marker[data-city="Halifax"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));
      check(el('hb-city').value==='Halifax'&&el('hb-history-caption').textContent.startsWith('Halifax'),'marker links comparison and history');
      change('hb-program','HBP existing RRSP');
      check(el('hb-program-result').textContent.includes('No increase in total assets')&&el('hb-program-result').textContent.includes('repayment'),'HBP tradeoff');
      change('hb-program','FHSA one-year illustration');
      check(el('hb-program-result').textContent.includes('counted once'),'FHSA accounting');
      const before=el('hb-wait-readout').textContent;change('hb-rent','0.06');
      check(el('hb-wait-readout').textContent!==before,'rent sensitivity changes result');
      check(el('hb-audit-controls').querySelectorAll('article').length===8,'eight bank audit objectives');
      check(el('hb-audit-conclusion').textContent.includes('Hold:'),'no approval without evidence');
      change('hb-city','Vancouver');change('hb-profile','couple');change('hb-scenario','baseline');
      change('hb-program','30-year amortization');change('hb-rent','0.03');
      check(el('hb-program-result').textContent.includes('CAD 196,837'),'30-year interest tradeoff');
      // Expand archived context so its keyboard controls and plots remain testable.
      el('renter-context').open=true;
      return {failures,city_map:true,cash_income:true,sensitivities:true,programs:true,waiting:true,bank_audit:true};
    })()`);
    if(hbCheck.failures.length)throw new Error('Homebuying checks failed '+JSON.stringify(hbCheck));
    const displayedIncome=await evaluate('document.getElementById("hb-bars").textContent');
    const oracle=hbExpected.cases.find(r=>r.city==='Vancouver'&&r.profile==='couple'&&r.year===2023&&r.scenario==='baseline');
    if(!displayedIncome.includes(Math.round(oracle.required_gross_income).toLocaleString('en-CA')))throw new Error('Saved-data/UI mismatch');
    result.homebuying??=[];result.homebuying.push({width,...hbCheck});
    const interactions=await evaluate(`(()=>{
      const failures=[];
      const el=id=>document.getElementById(id);
      const change=(id,value)=>{el(id).value=value;el(id).dispatchEvent(new Event('change',{bubbles:true}));};
      const check=(condition,label)=>{if(!condition)failures.push(label);};
      check(document.querySelectorAll('#canada-map .province').length===13,'13 map regions');
      check(document.querySelectorAll('.province-bar').length===10,'10 provincial bars');
      check(el('region-detail').textContent.includes('Ontario')&&el('region-detail').textContent.includes('25.0%'),'initial Ontario estimate');
      document.querySelector('#canada-map [data-region="59"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));
      check(el('region-detail').textContent.includes('British Columbia')&&el('region-detail').textContent.includes('29.0%'),'map click BC');
      check(el('map-region').value==='59'&&document.querySelector('.province-bar.selected').dataset.region==='59','map and bar linked');
      change('map-year','2018');
      const expected=${JSON.stringify(regionalExpected.regional.records['2018']['59'])};
      check(el('region-detail').textContent.includes(expected.value.toFixed(1)+'%'),'year changes published estimate');
      change('map-year','2024');
      change('map-region','60');
      check(el('region-detail').textContent.includes('No estimate')&&el('region-detail').textContent.includes('not a zero'),'territory is missing');
      check(el('canada-map').getAttribute('viewBox')===${JSON.stringify(regionalExpected.map.view_all.join(' '))},'all Canada view for territory');
      change('map-region','11');el('map-zoom').click();
      const smallView=el('canada-map').getAttribute('viewBox');
      change('map-region','59');
      check(el('canada-map').getAttribute('viewBox')!==smallView&&el('region-detail').textContent.includes('British Columbia'),'zoom follows next selection');
      check(el('canada-map').getAttribute('viewBox')!==${JSON.stringify(regionalExpected.map.view_all.join(' '))},'zoom to small province');
      el('map-provinces').click();
      check(el('canada-map').getAttribute('viewBox')===${JSON.stringify(regionalExpected.map.view_provinces.join(' '))},'reset provinces');
      document.querySelector('.province-bar[data-region="35"]').focus();
      document.querySelector('.province-bar[data-region="35"]').click();
      check(document.activeElement.classList.contains('province-bar')&&document.activeElement.dataset.region==='35','comparison bar keeps keyboard focus');
      check(document.querySelectorAll('[data-download]').length===2,'figure download links');
      check(el('map-region').value==='35','bar click selects province');
      change('trend-year','2020');
      check(el('trend-readout').textContent.includes('CAD 59,468')&&el('trend-readout').textContent.includes('CAD 55,088'),'2020 annual values');
      document.querySelector('.trend-income-point[data-year="2022"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));
      check(el('trend-year').value==='2022'&&el('trend-readout').textContent.includes('−CAD 5,607'),'trend point click and gap');
      change('trend-year','2025');
      change('cash-allowance','4');
      check(el('cash-readout').textContent.includes('CAD 59,000'),'4 percent allowance');
      change('cash-price','1500000');
      check(el('cash-readout').textContent.includes('CAD 300,000')&&el('cash-readout').textContent.includes('CAD 360,000'),'insurance boundary');
      change('cash-price','1499999');
      check(el('cash-readout').textContent.includes('CAD 185,000'),'below-boundary saved case');
      check(document.querySelectorAll('#cash-chart .cash-line').length===2,'line breaks at rule threshold');
      change('cash-price','600000');change('cash-allowance','2.5');
      check(el('cash-readout').textContent.includes('CAD 50,000'),'restore default scenario');
      check(el('trend-readout').textContent.includes('CAD 70,099'),'map does not filter national trend');
      return {failures,map_regions:13,covered_provinces:10,year_switch:true,territories_missing:true,linked_selection:true,zoom:true,trend_selection:true,cash_selection:true,boundary:true};
    })()`);
    if(interactions.failures.length)throw new Error('Interactive checks failed '+JSON.stringify(interactions));
    await evaluate('document.querySelector(\'#canada-map [data-region="24"]\').focus()');
    await command('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    await command('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
    if(!(await evaluate('document.getElementById("region-detail").textContent')).includes('Quebec'))throw new Error('Keyboard map selection failed');
    await evaluate('document.querySelector(\'#canada-map [data-region="35"]\').dispatchEvent(new MouseEvent("click",{bubbles:true}));document.activeElement.blur();window.scrollTo(0,0)');
    result.interactions??=[];result.interactions.push({width,...interactions,keyboard_map:true});
    if(width===1440||width===390){
      for(const [id,name] of [['buying','buyers'],['bank-audit','bank-audit'],['history','history'],['waiting','waiting'],['explore','map'],['story','trend'],['cash-heading','cash']]){
        await evaluate('document.getElementById('+JSON.stringify(id)+').scrollIntoView({block:"start"});');
        const shot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
        fs.writeFileSync(path.join(shots,(live?'live-':'')+width+'-'+name+'.png'),Buffer.from(shot.data,'base64'));
      }
      await evaluate('window.scrollTo(0,0)');
    }

    if(await evaluate('document.documentElement.dataset.theme')!=='light')await evaluate('document.getElementById("theme-toggle").click()');
    const light=await evaluate('getComputedStyle(document.body).backgroundColor');
    const lightMap=await evaluate("getComputedStyle(document.getElementById(\"canada-map\").querySelector(\".selected\")).fill");
    if(width===1440||width===390){
      const s=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.join(shots,(live?'live-':'')+width+'-light.png'),Buffer.from(s.data,'base64'));
    }
    await evaluate('document.getElementById("theme-toggle").click()');
    const dark=await evaluate('({theme:document.documentElement.dataset.theme,pressed:document.getElementById("theme-toggle").getAttribute("aria-pressed"),label:document.getElementById("theme-toggle").getAttribute("aria-label"),background:getComputedStyle(document.body).backgroundColor})');
    if(dark.theme!=='dark'||dark.pressed!=='true'||dark.label!=='Switch to light mode'||dark.background===light)throw new Error('Dark theme failed '+JSON.stringify(dark));
    await load('Page.reload',{ignoreCache:true});
    await evaluate(`new Promise((resolve,reject)=>{let count=0;const timer=setInterval(()=>{if(document.documentElement.dataset.visuals==='ready'&&document.documentElement.dataset.homebuying==='ready'){clearInterval(timer);resolve(true);}else if(document.documentElement.dataset.visuals==='error'||++count>150){clearInterval(timer);reject(new Error('Visuals did not become ready'));}},100);})`);
    if(await evaluate('document.documentElement.dataset.theme')!=='dark')throw new Error('Theme preference did not persist');
    if(await evaluate("getComputedStyle(document.getElementById(\"canada-map\").querySelector(\".selected\")).fill")===lightMap)throw new Error('Map colours did not follow dark mode');
    if(width===1440||width===390){
      await evaluate('document.getElementById("renter-context").open=true;document.getElementById("explore").scrollIntoView({block:"start"})');
      const mapShot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.join(shots,(live?'live-':'')+width+'-map-dark.png'),Buffer.from(mapShot.data,'base64'));
      await evaluate('window.scrollTo(0,0)');
    }

    if(width===1440||width===390){
      const s=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.join(shots,(live?'live-':'')+width+'-dark.png'),Buffer.from(s.data,'base64'));
    }
    await evaluate('document.getElementById("theme-toggle").click()');
    if(await evaluate('document.documentElement.dataset.theme')!=='light')throw new Error('Switch back to light failed');
    await evaluate('document.querySelector("nav a[href=\\"#report\\"]").click()');
    if(await evaluate('location.hash')!=='#report')throw new Error('Report navigation failed');
    result.viewports.push({...check,keyboard_skip_link:true,dark_toggle:true,theme_persists_on_reload:true});
  }
  if(errors.length)throw new Error('Browser errors '+errors.join('; '));
  result.passed=true;result.browser_errors=errors;
}catch(error){result.error=error.stack;process.exitCode=1;}
finally{
  if(ws?.readyState===WebSocket.OPEN){try{await send('Browser.close');}catch{}ws.close();}
  if(browser&&browser.exitCode===null){await pause(500);if(browser.exitCode===null)browser.kill();}
  if(server){server.closeAllConnections();await new Promise(r=>server.close(r));}
  fs.writeFileSync(path.join(work,live?'visuals_site_live_check.json':'visuals_site_check.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}
