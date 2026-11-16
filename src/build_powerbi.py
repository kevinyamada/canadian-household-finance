import base64
import json
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed'
BI=ROOT/'powerbi'
REPORT=BI/'HouseholdFinance.Report'
MODEL=BI/'HouseholdFinance.SemanticModel'
BASE='https://developer.microsoft.com/json-schemas/fabric/'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def table(name,frame,measures=None):
    frame=frame.copy()
    columns=[]
    types=[]
    for col in frame:
        numeric=pd.api.types.is_numeric_dtype(frame[col])
        integer=pd.api.types.is_integer_dtype(frame[col])
        dtype='dateTime' if col=='date' else 'int64' if integer else 'double' if numeric else 'string'
        mtype='type datetime' if col=='date' else 'Int64.Type' if integer else 'type number' if numeric else 'type text'
        columns.append({'name':col,'dataType':dtype,'sourceColumn':col,'summarizeBy':'none'})
        types.append('{'+json.dumps(col)+', '+mtype+'}')
    encoded=base64.b64encode(frame.to_json(orient='records',double_precision=12).encode()).decode()
    expression=['let',f'    Source = Table.FromRecords(Json.Document(Binary.FromText("{encoded}", BinaryEncoding.Base64))),',
                '    Typed = Table.TransformColumnTypes(Source, {'+', '.join(types)+'}, "en-CA")', 'in','    Typed']
    value={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expression}}]}
    if measures:value['measures']=measures
    return value


def measure(name,expression,fmt='0.00'):
    return {'name':name,'expression':expression,'formatString':fmt}


def field(table_name,col,kind='Column'):
    return {kind:{'Expression':{'SourceRef':{'Entity':table_name}},'Property':col}}


def projection(table_name,col,kind='Column'):
    label={'group':'Household group','control':'Control','exceptions':'Exceptions','status':'Status','tolerance':'Review threshold','income_change_pct':'Income change (%)','payment_change_pct':'Payment change (%)','quarter':'Quarter','method':'Review method','year':'Year','income_less_consumption':'Income less consumption','pension':'Pension adjustment','saving':'Reported net saving','home_price_label':'Purchase price','closing_allowance_pct':'Closing allowance (%)','closing_allowance_label':'Closing allowance'}.get(col,col)
    if col.endswith(' debt ratio'):label='Debt to income (%)'
    if col.endswith(' income gap'):label='Income less consumption (CAD)'
    return {'field':field(table_name,col,kind),'queryRef':table_name+'.'+col,'nativeQueryRef':col,'displayName':label}


def literal(value):
    if isinstance(value,bool):value='true' if value else 'false'
    elif isinstance(value,(int,float)):value=str(value)+'D'
    else:value="'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':value}}}


def visual(page,name,kind,x,y,w,h,title,roles=None,sort=None,objects=None):
    v={'visualType':kind,'visualContainerObjects':{'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(12),'bold':literal(True),'fontColor':{'solid':{'color':literal('#183D40')}}}}],
         'background':[{'properties':{'show':literal(True),'color':{'solid':{'color':literal('#FFFFFF')}}}}]}}
    if roles:
        v['query']={'queryState':{role:{'projections':items} for role,items in roles.items()}}
        if sort:v['query']['sortDefinition']={'sort':[{'field':sort,'direction':'Ascending'}]}
    if kind=='textbox':
        v['visualContainerObjects']['title'][0]['properties']['show']=literal(False)
    if kind=='card':
        v['objects']={'categoryLabels':[{'properties':{'show':literal(False)}}]}
    if kind=='lineChart':
        v['objects']={'categoryAxis':[{'properties':{'axisType':literal('Scalar'),'labelColor':{'solid':{'color':literal('#35444A')}}}}]}
    if objects:v.setdefault('objects',{}).update(objects)
    container={'$schema':BASE+'item/report/definition/visualContainer/2.1.0/schema.json','name':name,
               'position':{'x':x,'y':y,'width':w,'height':h,'z':0,'tabOrder':0},'visual':v}
    write(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',container)


def text(page,name,x,y,w,h,content,size=13,color='#183D40'):
    objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':content,'textStyle':{'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':color}}]}]}}]}
    visual(page,name,'textbox',x,y,w,h,'',objects=objects)




def build():
    from housing_audit import generate as generate_audit
    summary = generate_audit(ROOT)
    backup = ROOT / '.powerbi_cache_backup' / ('housing_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for cache in [MODEL/'.pbi', REPORT/'.pbi']:
        if cache.exists():shutil.move(str(cache),str(backup/(cache.parent.name+'_cache')))
    pages_root=REPORT/'definition/pages'
    if pages_root.exists():shutil.move(str(pages_root),str(backup/'previous_pages'))
    annual=pd.read_csv(OUT/'renter_annual_saving.csv')
    quarters=pd.read_csv(OUT/'renter_quarterly_saving.csv')
    quarters=quarters[quarters.year==summary['latest_year']]
    purchase=pd.read_csv(OUT/'home_purchase_cash_cases.csv')
    controls=pd.read_csv(OUT/'housing_audit_checks.csv')
    claims=pd.read_csv(OUT/'housing_claim_register.csv')
    summary_frame=pd.DataFrame([{k:summary[k] for k in [
        'latest_year','annual_income','annual_consumption','annual_income_less_consumption','annual_pension','annual_net_saving',
        'quarterly_net_saving','minimum_down_payment','upfront_cash_scenario']}])
    money='"CAD "#,0;("CAD "#,0)'
    tables=[
        table('AuditSummary',summary_frame,[
            measure('Annual reported saving','MAX(AuditSummary[annual_net_saving])',money),
            measure('Latest quarter saving','MAX(AuditSummary[quarterly_net_saving])',money),
            measure('Illustrative minimum down','MAX(AuditSummary[minimum_down_payment])',money)]),
        table('SavingsAnnual',annual,[measure('Reported net saving','MAX(SavingsAnnual[saving])',money)]),
        table('LatestYearQuarters',quarters),
        table('AuditChecks',controls),
        table('DraftClaims',claims),
        table('PurchaseCases',purchase,[
            measure('Minimum down payment','IF(HASONEVALUE(PurchaseCases[home_price]), MAX(PurchaseCases[minimum_down_payment]))',money),
            measure('Closing cost allowance','IF(HASONEVALUE(PurchaseCases[home_price]) && HASONEVALUE(PurchaseCases[closing_allowance_pct]), MAX(PurchaseCases[closing_allowance]))',money),
            measure('Upfront cash scenario','IF(HASONEVALUE(PurchaseCases[home_price]) && HASONEVALUE(PurchaseCases[closing_allowance_pct]), MAX(PurchaseCases[upfront_cash_scenario]))',money)])]
    money_columns={'income','consumption','pension','saving','income_less_consumption','rounding_residual','home_price','minimum_down_payment','closing_allowance','upfront_cash_scenario'}
    for t in tables:
        for column in t['columns']:
            if column['name'] in money_columns and column['dataType']!='string':column['formatString']=money
            if column['name']=='year':column['formatString']='0'
        if t['name']=='PurchaseCases':
            next(c for c in t['columns'] if c['name']=='home_price_label')['sortByColumn']='home_price'
            next(c for c in t['columns'] if c['name']=='closing_allowance_label')['sortByColumn']='closing_allowance_pct'
    write(MODEL/'model.bim',{'name':'HouseholdFinance','compatibilityLevel':1600,'model':{
        'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-CA',
        'tables':tables,'relationships':[],'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([x['name'] for x in tables])}]}})
    write(MODEL/'definition.pbism',{'version':'1.0','settings':{}})
    write(REPORT/'definition.pbir',{'$schema':BASE+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../HouseholdFinance.SemanticModel'}}})
    write(BI/'HouseholdFinance.pbip',{'$schema':BASE+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'HouseholdFinance.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition/report.json',{'$schema':BASE+'item/report/definition/report/1.0.0/schema.json','layoutOptimization':'None',
        'themeCollection':{'customTheme':{'name':'HouseholdTheme','reportVersionAtImport':'5.59','type':'RegisteredResources'}},
        'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'HouseholdTheme','path':'HouseholdTheme.json','type':'CustomTheme'}]}],
        'settings':{'useEnhancedTooltips':True}})
    write(REPORT/'definition/version.json',{'$schema':BASE+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    pages=[('conclusion','Audit conclusion'),('saving','Savings evidence'),('purchase','Purchase cash check')]
    write(pages_root/'pages.json',{'$schema':BASE+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages],'activePageName':'conclusion'})
    for name,label in pages:
        write(pages_root/name/'page.json',{'$schema':BASE+'item/report/definition/page/1.0.0/schema.json','name':name,'displayName':label,'displayOption':'FitToPage','width':1280,'height':720,
            'objects':{'background':[{'properties':{'color':{'solid':{'color':literal('#F2F5F4')}},'transparency':literal(0)}}]}})
    text('conclusion','question',24,14,1232,100,summary['question'],27)
    text('conclusion','purpose',24,119,1232,60,'Audit whether the public saving figures support a claim that renters are building a down payment.',15)
    visual('conclusion','summary','tableEx',24,196,1232,109,
        f"{summary['latest_year']} annual saving | {summary['latest_quarter']} saving | CAD 600,000 example minimum down",
        {'Values':[projection('AuditSummary',name,'Measure') for name in ['Annual reported saving','Latest quarter saving','Illustrative minimum down']]},
        objects={'total':[{'properties':{'totals':literal(False)}}]})
    text('conclusion','verdict',24,331,1232,90,summary['verdict'],23)
    text('conclusion','reason',24,432,1232,98,'The annual total uses all four observed quarters. Net saving includes pension entitlements, and these national accounts are not a bank-account cash budget. A group average cannot establish an individual buyer\'s funds.',15)
    text('conclusion','action',24,547,1232,76,'Audit action: verify liquid funds, the full purchase budget and mortgage eligibility before signing off on a readiness claim.',17)
    text('conclusion','scope',24,640,1232,57,'Public renter group estimates, 2020–2025. No customer-level buying date or approval is estimated. The purchase price and closing-cost allowances are explicit scenarios.',11)
    text('saving','header',24,12,1232,58,'Does the saving claim survive reconciliation?',25)
    text('saving','subtitle',24,76,1232,55,'Full calendar years; nominal CAD per household. A positive final quarter does not establish positive annual saving or liquid funds.',13)
    visual('saving','annual','clusteredColumnChart',24,151,725,290,'Reported renter net saving, calendar-year sum (CAD)',
        {'Category':[projection('SavingsAnnual','year')],'Y':[projection('SavingsAnnual','Reported net saving','Measure')]},field('SavingsAnnual','year'))
    visual('saving','checks','tableEx',772,151,482,290,'Audit checks and missing evidence',
        {'Values':[projection('AuditChecks','control'),projection('AuditChecks','status')]},objects={'total':[{'properties':{'totals':literal(False)}}]})
    visual('saving','quarters','tableEx',24,469,725,194,f"{summary['latest_year']}: the four observed quarters",
        {'Values':[projection('LatestYearQuarters',c) for c in ['quarter','income_less_consumption','pension','saving']]},
        objects={'total':[{'properties':{'totals':literal(False)}}]})
    text('saving','bridge',772,469,482,115,f"{summary['latest_quarter']} example: CAD {summary['quarterly_income_less_consumption']:+,.0f} income less consumption + CAD {summary['quarterly_pension']:,.0f} pension adjustment = CAD {summary['quarterly_net_saving']:,.0f} net saving.",17)
    text('saving','meaning',772,592,482,92,'Pension entitlements are not verified deposit cash. Minor published rounding residuals are retained. Draft claim tests and source references are in the repository.',11)
    text('purchase','header',24,12,1232,58,'How much upfront cash does the purchase scenario need?',25)
    text('purchase','subtitle',24,78,1232,62,'Choose one price and one closing-cost allowance. Prices are illustrative, and the allowance is an assumption. This checks upfront cash only.',13)
    visual('purchase','price','slicer',24,159,389,190,'Choose one purchase price',{'Values':[projection('PurchaseCases','home_price_label')]})
    visual('purchase','allowance','slicer',438,159,389,190,'Choose one closing allowance (%)',{'Values':[projection('PurchaseCases','closing_allowance_label')]})
    visual('purchase','cash','tableEx',24,377,1232,107,'Selected scenario, CAD',
        {'Values':[projection('PurchaseCases',name,'Measure') for name in ['Minimum down payment','Closing cost allowance','Upfront cash scenario']]},
        objects={'total':[{'properties':{'totals':literal(False)}}]})
    text('purchase','rule',850,160,403,190,'Minimum down: 5% of the first CAD 500,000, then 10% of the balance below CAD 1.5 million. At CAD 1.5 million or more: 20%. Rules checked as of '+summary['rule_date']+'.',14)
    text('purchase','example',24,510,1232,78,'Example: CAD 600,000 price → CAD 35,000 minimum down. An assumed 2.5% closing allowance adds CAD 15,000 → CAD 50,000 in this cash scenario.',18)
    text('purchase','limits',24,612,1232,80,'This is not mortgage approval or a complete closing statement. Verified funds, borrower gross income, debts, credit, property-specific taxes, insurance and loan terms need separate evidence. Sources: CMHC, Finance Canada and FCAC; see the rule record.',12)
    theme={'name':'Household Finance','dataColors':['#176B61','#9D5C42','#6579A4','#4B5563'],'background':'#F2F5F4','foreground':'#183D40','tableAccent':'#176B61','textClasses':{
        'title':{'fontSize':12,'fontFace':'Segoe UI','color':'#183D40'},'label':{'fontSize':11,'fontFace':'Segoe UI','color':'#35444A'},'header':{'fontSize':12,'fontFace':'Segoe UI','color':'#183D40'},'callout':{'fontSize':28,'fontFace':'Segoe UI','color':'#183D40'}}}
    write(BI/'theme.json',theme)
    write(REPORT/'StaticResources/RegisteredResources/HouseholdTheme.json',theme)
    print('Generated the three-page housing-readiness audit:',BI/'HouseholdFinance.pbip')


if __name__=='__main__':
    build()
