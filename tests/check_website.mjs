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
    if(check.scrollWidth>width||check.badMetrics.length||check.brokenAnchors.length||check.clipped.length||check.question!==expected.question||check.figures<6||check.metricCount<8||!check.font.includes('system-ui'))throw new Error('Page check failed '+JSON.stringify(check));
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
      check(document.querySelectorAll('#canada-map .province').length===13,'restored provincial map');
      check(!el('explore').closest('details')&&el('explore').getBoundingClientRect().height>200,'map visible without opening details');
      check(!!(el('explore').compareDocumentPosition(el('buying'))&Node.DOCUMENT_POSITION_FOLLOWING),'map before buyer cases');
      check(!el('hb-city-map'),'one main Canada map');
      change('hb-scenario','price20');
      check(el('hb-verdict').textContent==='Both modeled checks are within limits.','cheaper home clears example');
      check(el('hb-audit-conclusion').textContent.includes('income shortfall'),'audit remains baseline');
      change('hb-scenario','baseline');change('hb-profile','single');
      check(el('hb-income-scope').textContent.includes('If minimum cash were available'),'cash-short conditional income');
      change('hb-city','Victoria');
      check(el('hb-verdict').textContent==='Cash is enough. Income is the hurdle.','Victoria cash/income split');
      change('hb-profile','couple');
      check(el('hb-verdict').textContent==='Both modeled checks are within limits.','Victoria two earners');
      change('hb-city','Halifax');
      check(el('hb-city').value==='Halifax'&&el('hb-history-caption').textContent.startsWith('Halifax'),'city control links comparison and history');
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
      check(!el('hb-program-result').textContent.includes('Cash shortfall'),'show the affected program measure');
      check(el('hb-program-result').textContent.includes('CAD 4,742')&&el('hb-program-result').textContent.includes('CAD 4,367'),'payment change is visible');
      check(el('hb-sensitivity').querySelector('tr[data-scenario="baseline"] td').textContent==='CAD 14,640 above','cash above minimum replaces zero');
      check(el('hb-sensitivity').querySelector('tr[data-scenario="price20"]').textContent.includes('CAD 2,630 above'),'income above requirement replaces zero');
      check(el('hb-limit-price').textContent==='About CAD 690,000'&&el('hb-limit-cash').textContent==='About CAD 168,000 more cash','price and cash alternatives');
      change('hb-city','Halifax');change('hb-program','BC transfer relief');
      check(el('hb-program-result').textContent.includes('Not applicable')&&!el('hb-program-result').textContent.includes('CAD 0'),'BC program not misrepresented as zeros');
      change('hb-city','Vancouver');change('hb-program','30-year amortization');
      // Expand archived context so its keyboard controls and plots remain testable.
      el('renter-context').open=true;
      return {failures,provincial_map_visible:true,price_limits:true,meaningful_cash_positions:true,cash_income:true,sensitivities:true,programs:true,waiting:true,bank_audit:true};
    })()`);
    if(hbCheck.failures.length)throw new Error('Homebuying checks failed '+JSON.stringify(hbCheck));
    const displayedIncome=await evaluate('document.getElementById("hb-bars").textContent');
    const oracle=hbExpected.cases.find(r=>r.city==='Vancouver'&&r.profile==='couple'&&r.year===2023&&r.scenario==='baseline');
    if(!displayedIncome.includes(Math.round(oracle.required_gross_income).toLocaleString('en-CA')))throw new Error('Saved-data/UI mismatch');
    result.homebuying??=[];result.homebuying.push({width,...hbCheck});
    if(width===1440){
      const matrix=hbExpected.cases.filter(r=>r.year===2023).map(({city,profile,scenario,cash_position_label,income_position_label,profile_cash,cash_target,profile_income,required_gross_income})=>({city,profile,scenario,cash_position_label,income_position_label,profile_cash,cash_target,profile_income,required_gross_income}));
      const programMatrix=hbExpected.programs.map(p=>Object.fromEntries(["city","profile","program","applicable","metric_1_label","metric_1_before","metric_1_after","metric_2_label","metric_2_before","metric_2_after","metric_3_label","metric_3_before","metric_3_after"].map(k=>[k,p[k]])));
      const limits=hbExpected.price_limits;
      const audits=hbExpected.calculation_audit.map(a=>Object.fromEntries(["city","profile","scenario","variant","required_gross_income","income_understated","decision_label"].map(k=>[k,a[k]])));
      const latestRates=hbExpected.latest_rate_cases;
      const exhaustiveDisplay=await evaluate(`(()=>{
        const cases=${JSON.stringify(matrix)},programs=${JSON.stringify(programMatrix)},limits=${JSON.stringify(limits)},audits=${JSON.stringify(audits)},latestRates=${JSON.stringify(latestRates)};
        const el=id=>document.getElementById(id),failures=[];
        const change=(id,value)=>{el(id).value=value;el(id).dispatchEvent(new Event('change',{bubbles:true}));};
        const numeric=t=>Number(t.replace(/[^0-9.-]/g,''));
        for(const c of cases){
          change('hb-city',c.city);change('hb-profile',c.profile);change('hb-scenario',c.scenario);
          const bars=el('hb-bars');
          if(!bars.textContent.includes(c.cash_position_label)||!bars.textContent.includes(c.income_position_label))failures.push('positions '+JSON.stringify(c));
          const shown=[...bars.querySelectorAll('.hb-meter b')].map(b=>numeric(b.textContent));
          const expected=[c.profile_cash,c.cash_target,c.profile_income,c.required_gross_income];
          if(shown.length!==4||shown.some((n,i)=>Math.abs(n-expected[i])>.51))failures.push('bar values '+c.city+' '+c.profile+' '+c.scenario);
          change('hb-audit-scenario',c.scenario);
          const sourceRows=audits.filter(a=>a.city===c.city&&a.profile===c.profile&&a.scenario===c.scenario);
          const auditTable=el('hb-error-table');
          if(auditTable.querySelectorAll('tbody tr').length!==5)failures.push('audit row count '+c.city);
          for(const a of sourceRows){
            const tr=auditTable.querySelector('tr[data-variant="'+a.variant+'"]'),cells=[...tr.querySelectorAll('td')];
            if(Math.abs(numeric(cells[0].textContent)-a.required_gross_income)>.51||Math.abs(numeric(cells[1].textContent)-a.income_understated)>.51||cells[2].textContent!==a.decision_label)failures.push('audit display '+c.city+' '+c.profile+' '+c.scenario+' '+a.variant);
          }
        }
        change('hb-scenario','baseline');
        for(const p of programs){
          change('hb-city',p.city);change('hb-profile',p.profile);change('hb-program',p.program);
          const box=el('hb-program-result');
          if(!p.applicable){
            if(!box.textContent.includes('Not applicable')||box.querySelector('.hb-program-numbers'))failures.push('not applicable '+p.city);
          }else{
            const tiles=[...box.querySelectorAll('.hb-program-numbers>p')];
            if(tiles.length!==3)failures.push('missing program metrics '+p.program);
            for(let i=1;i<=3;i++){
              const tile=tiles[i-1],amounts=tile.querySelector('strong').textContent.split(' → ').map(numeric);
              if(tile.querySelector('span').textContent!==p['metric_'+i+'_label']||Math.abs(amounts[0]-p['metric_'+i+'_before'])>.51||Math.abs(amounts[1]-p['metric_'+i+'_after'])>.51)failures.push('program metric '+p.city+' '+p.profile+' '+p.program+' '+i);
            }
          }
        }
        for(const l of limits){
          change('hb-city',l.city);change('hb-profile',l.profile);
          if(el('hb-limit-price').textContent!==l.maximum_price_label||el('hb-limit-cash').textContent!==l.additional_cash_label)failures.push('threshold '+l.city+' '+l.profile);
        }
        change('hb-city','Vancouver');change('hb-profile','couple');change('hb-scenario','baseline');change('hb-program','30-year amortization');
        for(const r of latestRates){
          change('hb-city',r.city);change('hb-profile',r.profile);
          const tr=el('hb-latest').querySelector('tr[data-rate="latest"]'),cells=[...tr.querySelectorAll('td')];
          if(Math.abs(numeric(cells[0].textContent)-r.monthly_mortgage)>.51||Math.abs(numeric(cells[1].textContent)-r.required_gross_income)>.51||cells[2].textContent!==r.income_position_label)failures.push('latest-rate display '+r.city+' '+r.profile);
        }
        change('hb-city','Vancouver');change('hb-profile','couple');change('hb-audit-scenario','price10');
        if(!el('hb-error-table').querySelector('tr[data-variant="contract_rate"]').textContent.includes('False pass'))failures.push('worked false pass');
        if(!el('latest-rates').textContent.includes("not today's housing market"))failures.push('mixed-vintage scope');
        return {failures,purchase_cases:cases.length,program_comparisons:programs.length,price_limit_cases:limits.length,audit_calculations:audits.length,latest_rate_cases:latestRates.length};
      })()`);
      if(exhaustiveDisplay.failures.length)throw new Error('Displayed-data review failed '+JSON.stringify(exhaustiveDisplay));
      result.displayed_data_review=exhaustiveDisplay;
    }
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
      for(const [id,name] of [['buying','buyers'],['latest-rates','rates'],['audit-errors','calculation-audit'],['bank-audit','bank-audit'],['limits','limits'],['buyer-measures','programs'],['changes','scenarios'],['history','history'],['waiting','waiting'],['explore','map'],['story','trend'],['cash-heading','cash']]){
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
