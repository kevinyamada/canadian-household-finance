/* A fixed, fictional audit file. All financial results are prepared in desktop Python. */
(() => {
  "use strict";
  const el=id=>document.getElementById(id);
  const esc=value=>String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const money=n=>"CAD "+Number(n).toLocaleString("en-CA",{maximumFractionDigits:0});
  async function init(){
    const response=await fetch("assets/mortgage-file-data.json?v=1");
    if(!response.ok)throw new Error("The saved training file could not be loaded.");
    const data=await response.json();
    if(data.synthetic!==true)throw new Error("This section requires an explicitly fictional training file.");
    let stage="submitted";
    function render(){
      const r=data.stages.find(s=>s.stage_id===stage);
      el("mf-stage-label").textContent=r.stage_label+" · "+money(r.price)+" hypothetical price";
      el("mf-screen").textContent=r.financial_result;
      el("mf-outcome").textContent=r.review_outcome;
      el("mf-explanation").textContent=r.stage_explanation;
      el("mf-income").textContent=r.income_position_label;
      el("mf-income-detail").textContent=money(r.profile_income)+" gross income / year; "+money(r.required_gross_income)+" required.";
      el("mf-cash").textContent=r.cash_position_label;
      el("mf-cash-detail").textContent=money(r.profile_cash)+" available; "+money(r.cash_target)+" minimum including reserve.";
      el("mf-context").textContent=money(r.monthly_debt)+" other debt / month · "+r.qualifying_rate.toFixed(2)+"% rate used in the screen · "+r.corrected_discrepancies+" discrepancies corrected in simulation.";
      el("mf-external").textContent=r.open_external_controls+" external-evidence controls remain open. No actual approval is supplied.";
      for(const b of document.querySelectorAll("[data-file-stage]")){
        const selected=b.dataset.fileStage===stage;
        b.setAttribute("aria-pressed",String(selected));b.classList.toggle("selected",selected);
      }
      el("mf-findings").querySelector("tbody").innerHTML=data.findings.map(f=>'<tr data-finding="'+esc(f.finding_id)+'"><th scope="row">'+esc(f.finding)+'<span class="small mf-unit">'+esc(f.unit)+'</span></th><td>'+esc(f.declared_label)+'</td><td>'+esc(f.supported_label)+'</td><td>'+esc(f.difference_label)+'</td><td>'+esc(f.evidence_ids.replaceAll("|",", "))+'</td></tr>').join("");
      el("mf-checks").innerHTML=data.open_evidence.map(c=>'<li><strong>'+esc(c.control)+':</strong> '+esc(c.needed)+'</li>').join("");
      document.documentElement.dataset.mortgageFile="ready";
      document.documentElement.dataset.mortgageFileStage=stage;
    }
    for(const b of document.querySelectorAll("[data-file-stage]"))b.addEventListener("click",()=>{stage=b.dataset.fileStage;render();});
    render();
  }
  init().catch(error=>{document.documentElement.dataset.mortgageFile="error";el("mf-error").hidden=false;el("mf-error").textContent=error.message;});
})();
