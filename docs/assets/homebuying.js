/* Display saved desktop-Python scenarios. Lending rules are not reimplemented here. */
(() => {
  "use strict";
  const el=id=>document.getElementById(id);
  const esc=value=>String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const money=value=>(value<0?"−":"")+"CAD "+Math.abs(value).toLocaleString("en-CA",{maximumFractionDigits:0});
  const opts=(id,items,value)=>{const s=el(id);s.replaceChildren(...items.map(([v,label])=>{const o=document.createElement("option");o.value=v;o.textContent=label;return o;}));s.value=value;s.disabled=false;};
  const svg=(body,label)=>'<svg viewBox="0 0 760 300" role="img" aria-label="'+esc(label)+'">'+body+'</svg>';
  const text=(x,y,value,anchor="middle")=>'<text class="axis-label" x="'+x+'" y="'+y+'" text-anchor="'+anchor+'">'+esc(value)+'</text>';
  const axes=labels=>{
    let body="";
    for(const tick of [0,50000,100000,150000,200000,250000]){
      const y=250-tick/250000*215;
      body+='<line class="grid-line" x1="70" x2="710" y1="'+y+'" y2="'+y+'"/>'+text(60,y+4,tick===0?"0":tick/1000+"k","end");
    }
    body+=text(70,15,"Annual gross income · CAD","start");
    labels.forEach(([x,label])=>body+=text(x,276,label));
    return body;
  };
  async function init(){
    const response=await fetch("assets/homebuying-data.json?v=3");
    if(!response.ok)throw new Error("The saved buyer comparisons could not be loaded.");
    const data=await response.json();
    let city="Vancouver",profile="couple",scenario="baseline",program="30-year amortization",rent="0.03";
    opts("hb-city",Object.keys(data.cities).map(c=>[c,c]),city);
    opts("hb-profile",data.profiles.map(p=>[p.id,p.name]),profile);
    opts("hb-scenario",data.scenarios.map(s=>[s.id,s.label]),scenario);
    opts("hb-program",[...new Set(data.programs.map(p=>p.program))].map(p=>[p,p]),program);
    opts("hb-rent",[["0","0%"],["0.03","3%"],["0.06","6%"]],rent);
    const lookup=(s=scenario)=>data.cases.find(r=>r.city===city&&r.profile===profile&&r.year===2023&&r.scenario===s);
    const markerLabels={Vancouver:{dx:60,dy:-35},Victoria:{dx:60,dy:35},Halifax:{dx:-140,dy:30}};
    el("hb-map").innerHTML='<svg id="hb-city-map" viewBox="'+data.map.view_provinces.join(" ")+'" role="group" aria-label="Choose Vancouver, Victoria or Halifax">'+data.map.features.map(f=>'<path class="hb-land" d="'+f.path+'" fill-rule="evenodd"/>').join("")+
      data.map.markers.map(m=>{const o=markerLabels[m.city];return '<g class="hb-city-marker" role="button" tabindex="0" aria-pressed="false" data-city="'+m.city+'"><title>'+m.city+'</title><path class="hb-leader" d="M'+m.x+','+m.y+'l'+o.dx+','+o.dy+'"/><circle cx="'+m.x+'" cy="'+m.y+'" r="7"/><rect x="'+(m.x+o.dx-6)+'" y="'+(m.y+o.dy-19)+'" width="126" height="28" rx="3"/><text x="'+(m.x+o.dx)+'" y="'+(m.y+o.dy)+'">'+m.city+'</text></g>';}).join("")+'</svg>';
    const updateCity=e=>{
      const marker=e.target.closest(".hb-city-marker");
      if(marker&&(e.type==="click"||e.key==="Enter"||e.key===" ")){
        if(e.type==="keydown")e.preventDefault();
        city=marker.dataset.city;el("hb-city").value=city;render();
      }
    };
    el("hb-map").addEventListener("click",updateCity);el("hb-map").addEventListener("keydown",updateCity);
    function meter(label,available,needed,availablePct,neededPct,gap){
      return '<div class="hb-meter"><div class="hb-meter-title"><strong>'+label+'</strong><span>'+(gap>0?money(gap)+" short":"Within modeled limit")+'</span></div>'+
        '<div class="hb-meter-line"><span>Profile</span><div><i style="width:'+availablePct+'%"></i></div><b>'+money(available)+'</b></div>'+
        '<div class="hb-meter-line required"><span>Needed</span><div><i style="width:'+neededPct+'%"></i></div><b>'+money(needed)+'</b></div></div>';
    }
    function render(){
      const row=lookup(),buyer=data.profiles.find(p=>p.id===profile),base=lookup("baseline");
      if(!row||!base)throw new Error("A saved comparison is missing.");
      const words={"Income":"Cash is enough. Income is the hurdle.","Cash":"Income fits. Cash is the hurdle.","Both cash and income":"Both cash and income fall short.","Within modeled limits":"Both modeled checks are within limits."};
      el("hb-place").textContent=city+" / "+buyer.name+" / "+row.scenario_label;
      el("hb-verdict").textContent=words[row.barrier];el("hb-verdict").dataset.barrier=row.barrier;
      el("hb-price").textContent=money(row.price)+" purchase price · "+row.amortization_years+"-year amortization · "+row.contract_rate.toFixed(2)+"% contract benchmark";
      el("hb-bars").innerHTML=meter("Cash to close + reserve",row.profile_cash,row.cash_target,row.cash_available_pct,row.cash_needed_pct,row.cash_gap)+
        meter("Annual gross income",row.profile_income,row.required_gross_income,row.income_available_pct,row.income_needed_pct,row.income_gap);
      el("hb-income-scope").textContent=row.income_scope+". Income screen uses "+row.qualifying_rate.toFixed(2)+"%, including the stress-test buffer.";
      el("hb-budget").textContent="Modeled monthly outgoings: "+money(row.modeled_monthly_outgoings)+", before living costs and income tax. This amount is different from the debt-service screen.";
      el("hb-assumptions").innerHTML='<p>Profile before scenario changes: '+money(buyer.gross_income)+' gross income/year; '+money(buyer.liquid_cash)+' liquid cash; '+money(buyer.monthly_debt)+' monthly debt; '+money(buyer.monthly_saving)+' initially saved/month; '+money(buyer.monthly_rent)+' rent/month.</p>'+
        '<p>Cash target: '+money(row.minimum_down)+' minimum down + '+money(row.transfer_tax)+' net transfer tax + '+money(row.closing_allowance)+' closing allowance + '+money(row.reserve)+' reserve. Available cash above costs and reserve is used toward the loan.</p>'+
        '<p>Assumed monthly heat '+money(row.heating)+'; condo fees '+money(row.condo_fee)+' (50% in the ratios); insurance '+money(buyer.home_insurance)+'; maintenance '+money(buyer.maintenance_monthly)+'. Assessment is an explicit share of price, not a verified tax bill. '+esc(row.tax_basis)+'.</p>'+
        '<p>Eligible resident first-time buyer of an owner-occupied resale property; BC relief conditions assumed met. Traditional down-payment funds; no borrower credit file. The common screen uses 39% GDS and 44% TDS. Actual lender and insurer rules, costs and eligibility need verification.</p>';
      el("hb-city-map").querySelectorAll(".hb-city-marker").forEach(m=>{m.setAttribute("aria-pressed",String(m.dataset.city===city));});
      const show=["baseline","price10","price20","rate1","cash25","income20","amort30","hbp"];
      el("hb-sensitivity").querySelector("tbody").innerHTML=show.map(s=>{const r=lookup(s);return '<tr'+(s===scenario?' class="selected"':"")+'><th scope="row">'+esc(r.scenario_label)+'</th><td>'+money(r.cash_gap)+'</td><td>'+money(r.income_gap)+'</td><td>'+esc(r.barrier)+'</td></tr>';}).join("");
      const audit=data.bank_audit.filter(a=>a.city===city&&a.profile===profile);
      el("hb-audit-conclusion").textContent=city+" · "+buyer.name+" · "+audit[0].review_conclusion+".";
      el("hb-audit-controls").innerHTML=audit.map(a=>'<article><div><h3>'+esc(a.control)+'</h3><span class="hb-status">'+esc(a.status)+'</span></div><p>'+esc(a.result)+'</p><p class="small"><strong>Evidence needed:</strong> '+esc(a.evidence_needed)+'</p></article>').join("");
      const lines=data.history_lines[city];
      el("hb-history-caption").textContent=city+": income needed at the minimum down payment";
      el("hb-history").innerHTML=svg(axes([[70,"2020*"],[283.33,"2021"],[496.67,"2022"],[710,"2023"]])+
        '<path class="hb-line required" d="'+lines.legacy_required_path+'" stroke-dasharray="5 5"/><path class="hb-line observed" d="'+lines.legacy_observed_path+'" stroke-dasharray="5 5"/>'+
        '<path class="hb-line required" d="'+lines.required_path+'"/><path class="hb-line observed" d="'+lines.observed_path+'"/>'+
        lines.points.map(p=>'<circle class="hb-dot" cx="'+p.x+'" cy="'+p.required_y+'" r="4"><title>'+p.year+": "+money(p.required_income)+" modeled income needed; price "+money(p.price)+'</title></circle>').join(""),city+" income needed and observed buyer-family median income, 2020 to 2023");
      const latest=lines.points.at(-1);
      el("hb-history-readout").textContent="2023: "+money(latest.required_income)+" modeled income needed; "+money(latest.buyer_family_income)+" observed buyer-family median. These are different populations and measures.";
      el("hb-decomposition").innerHTML='<dl class="hb-factors">'+data.decomposition.filter(d=>d.city===city).map(d=>'<div><dt>'+esc({price:"Purchase price",rates:"Mortgage rates",income:"Buyer-family income"}[d.factor])+'</dt><dd>'+money(d.contribution_cad)+'</dd></div>').join("")+'</dl>';
      const replay=data.rate_replay.find(r=>r.city===city&&r.profile===profile);
      el("hb-rate-replay").textContent="For this buyer, replacing 2023 rates with observed 2025 averages changes required income from "+money(replay.required_income_2023_rates)+" to "+money(replay.required_gross_income)+". Result: "+replay.barrier+".";
      const p=data.programs.find(p=>p.city===city&&p.profile===profile&&p.program===program);
      el("hb-program-result").innerHTML='<div class="hb-program-numbers"><p><span>Cash shortfall</span><strong>'+money(p.cash_gap_before)+' → '+money(p.cash_gap_after)+'</strong></p><p><span>Income needed / year</span><strong>'+money(p.required_income_before)+' → '+money(p.required_income_after)+'</strong></p><p><span>Monthly mortgage</span><strong>'+money(p.monthly_payment_before)+' → '+money(p.monthly_payment_after)+'</strong></p><p><span>First five years’ interest</span><strong>'+money(p.five_year_interest_before)+' → '+money(p.five_year_interest_after)+'</strong></p></div><p>'+esc(p.note)+'</p><p class="small">Result after: '+esc(p.barrier_after)+'. '+(p.hbp_draw?"Future annual HBP repayment when due: "+money(p.hbp_future_annual_repayment)+".":"")+'</p>';
      const wait=data.waiting_lines[city+"|"+profile+"|"+rent];
      el("hb-wait-caption").textContent=city+" · "+buyer.name+": income needed after more time saving";
      let plot=axes([[70,"Baseline"],[390,"12 months"],[710,"24 months"]])+'<path class="hb-profile-line" d="'+wait.profile_path+'"/>';
      for(const series of wait.series)plot+='<path class="hb-line '+series.style+'" d="'+series.path+'"/>'+series.points.map(p=>'<circle class="hb-dot '+series.style+'" cx="'+p.x+'" cy="'+p.y+'" r="4"><title>'+esc(series.label)+"; "+p.months+" months: "+money(p.income)+" needed; "+p.barrier+'</title></circle>').join("");
      el("hb-wait-chart").innerHTML=svg(plot,"Income needed under three hypothetical price paths");
      el("hb-wait-readout").innerHTML=wait.series.map(s=>'<span><strong>'+esc(s.label)+'</strong><br>24 months: '+money(s.points.at(-1).income)+' income needed<br>'+esc(s.points.at(-1).barrier)+'</span>').join("");
      document.documentElement.dataset.homebuying="ready";
    }
    el("hb-city").addEventListener("change",e=>{city=e.target.value;render();});
    el("hb-profile").addEventListener("change",e=>{profile=e.target.value;render();});
    el("hb-scenario").addEventListener("change",e=>{scenario=e.target.value;render();});
    el("hb-program").addEventListener("change",e=>{program=e.target.value;render();});
    el("hb-rent").addEventListener("change",e=>{rent=e.target.value;render();});
    render();
  }
  init().catch(error=>{document.documentElement.dataset.homebuying="error";const e=el("hb-error");e.hidden=false;e.textContent=error.message+" You can read all results in the linked CSV files.";});
})();
