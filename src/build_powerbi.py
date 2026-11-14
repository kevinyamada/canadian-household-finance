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
    return {'field':field(table_name,col,kind),'queryRef':table_name+'.'+col,'nativeQueryRef':col}


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
    caches=[MODEL/'.pbi',REPORT/'.pbi']
    present=[path for path in caches if path.exists()]
    if present:
        backup=ROOT/'.powerbi_cache_backup'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup.mkdir(parents=True)
        for path in present:
            shutil.move(str(path),str(backup/path.parent.name))
        print('Preserved the previous Power BI local cache:',backup)
    panel=pd.read_csv(OUT/'quarterly_panel.csv')
    changes=pd.read_csv(OUT/'recent_changes.csv')
    panel=panel.merge(changes[['quarter','dsr_qoq_pp','dsr_yoy_pp']],on='quarter',validate='one_to_one')
    backtest=pd.read_csv(OUT/'selected_predictions.csv')
    baseline=pd.read_csv(OUT/'holdout_predictions.csv')
    baseline=baseline[baseline.model=='Persistence'][['quarter','prediction']].rename(columns={'prediction':'baseline'})
    backtest=backtest.merge(baseline,on='quarter',validate='one_to_one')
    backtest['covered']=backtest['covered'].astype(int)
    dates=pd.DataFrame({'quarter':sorted(set(panel.quarter)|set(backtest.quarter))})
    dates['date']=pd.PeriodIndex(dates.quarter,freq='Q').to_timestamp().strftime('%Y-%m-%dT00:00:00')
    dates['year']=dates.quarter.str[:4].astype(int)
    dates['quarter_number']=dates.quarter.str[-1].astype(int)
    audit=json.loads((OUT/'model_audit.json').read_text())
    measures=[]
    for name,col,fmt in [('Debt service ratio','dsr','0.00"%"'),('Mortgage ratio','mortgage_dsr','0.00"%"'),
                         ('Other debt ratio','other_dsr','0.00"%"'),('Income growth','income_growth','0.00"%"'),
                         ('Payment growth','payment_growth','0.00"%"'),('Quarterly change','dsr_qoq_pp','+0.00;-0.00;0.00'),
                         ('Interest ratio','interest_dsr','0.00"%"'),('Principal ratio','principal_dsr','0.00"%"')]:
        measures.append(measure(name,f'MAXX(TOPN(1, Household, Household[quarter], DESC), Household[{col}])',fmt))
    measures.append(measure('Latest quarter','MAX(Household[quarter])',''))
    measures.append(measure('Policy rate','MAX(Household[policy_rate])','0.00"%"'))
    tables=[table('Quarter',dates),table('Household',panel,measures),
            table('Backtest',backtest,[measure('Observed','MAX(Backtest[actual])'),measure('Model estimate','MAX(Backtest[prediction])'),
                                      measure('Persistence estimate','MAX(Backtest[baseline])'),measure('Test MAE','AVERAGE(Backtest[absolute_error])'),
                                      measure('Band coverage','AVERAGE(Backtest[covered])','0.0%')]),
            table('Scores',pd.read_csv(OUT/'holdout_scores.csv'),[measure('Mean absolute error','IF(HASONEVALUE(Scores[model]), MAX(Scores[mae]))','0.000'),measure('Root mean squared error','IF(HASONEVALUE(Scores[model]), MAX(Scores[rmse]))','0.000')]),
            table('Scenarios',pd.read_csv(OUT/'scenarios.csv'),[measure('Scenario ratio','IF(HASONEVALUE(Scenarios[income_change_pct]) && HASONEVALUE(Scenarios[payment_change_pct]), MAX(Scenarios[scenario_dsr]))','0.00"%"')]),
            table('Contributions',pd.read_csv(OUT/'latest_decomposition.csv'),[measure('Contribution','SUM(Contributions[contribution_pp])')]),
            table('Estimate',pd.read_csv(OUT/'next_estimate.csv'))]
    relationships=[{'name':'Household_Quarter','fromTable':'Household','fromColumn':'quarter','toTable':'Quarter','toColumn':'quarter','crossFilteringBehavior':'oneDirection'},
                   {'name':'Backtest_Quarter','fromTable':'Backtest','fromColumn':'quarter','toTable':'Quarter','toColumn':'quarter','crossFilteringBehavior':'oneDirection'}]
    write(MODEL/'model.bim',{'name':'HouseholdFinance','compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3',
                   'sourceQueryCulture':'en-CA','tables':tables,'relationships':relationships,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([x['name'] for x in tables])}]}})
    write(MODEL/'definition.pbism',{'version':'1.0','settings':{}})
    write(REPORT/'definition.pbir',{'$schema':BASE+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../HouseholdFinance.SemanticModel'}}})
    write(BI/'HouseholdFinance.pbip',{'$schema':BASE+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'HouseholdFinance.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition/report.json',{'$schema':BASE+'item/report/definition/report/1.0.0/schema.json','layoutOptimization':'None','themeCollection':{'customTheme':{'name':'HouseholdTheme','reportVersionAtImport':'5.59','type':'RegisteredResources'}},
            'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'HouseholdTheme','path':'HouseholdTheme.json','type':'CustomTheme'}]}],
            'settings':{'useEnhancedTooltips':True}})
    write(REPORT/'definition/version.json',{'$schema':BASE+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    pages=[('overview','Household pressure'),('models','Model evaluation'),('scenarios','Payment scenarios')]
    write(REPORT/'definition/pages/pages.json',{'$schema':BASE+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages],'activePageName':'overview'})
    for name,label in pages:
        write(REPORT/'definition/pages'/name/'page.json',{'$schema':BASE+'item/report/definition/page/1.0.0/schema.json','name':name,'displayName':label,
                  'displayOption':'FitToPage','width':1280,'height':720,
                  'objects':{'background':[{'properties':{'color':{'solid':{'color':literal('#F2F5F4')}},'transparency':literal(0)}}]}})
    text('overview','header',24,10,950,55,'Canadian household borrowing pressure',25)
    text('overview','subtitle',24,65,1210,45,'Income growth eased the latest ratio even as required payments rose. Canada | Quarterly | 1990 to 2026Q2',12)
    for index,(name,title) in enumerate([('Debt service ratio','Debt service ratio'),('Quarterly change','Quarterly change, pp'),('Income growth','Income growth, QoQ'),('Payment growth','Payment growth, QoQ')]):
        visual('overview','kpi'+str(index),'card',24+index*310,120,296,100,title,{'Values':[projection('Household',name,'Measure')]})
    visual('overview','history','lineChart',24,240,780,270,'Share of income devoted to debt payments',
           {'Category':[projection('Quarter','date')],'Y':[projection('Household',m,'Measure') for m in ['Debt service ratio','Mortgage ratio','Other debt ratio']]},field('Quarter','date'))
    visual('overview','decomp','clusteredColumnChart',824,240,432,270,'Latest change: accounting contributions, pp',
           {'Category':[projection('Contributions','driver')],'Y':[projection('Contributions','Contribution','Measure')]})
    visual('overview','quarter_filter','slicer',24,530,380,125,'Choose quarters',{'Values':[projection('Quarter','quarter')]})
    text('overview','note',425,535,810,105,'National aggregates, not TD customer data. Ratios use income before interest. Contributions always show the latest quarter. Dollar series are annual rates in CAD millions. Sources: Statistics Canada 11-10-0065-01; Bank of Canada V39079.',11)
    text('models','header',24,10,1200,55,'Can a model beat the previous quarter?',25)
    text('models','subtitle',24,65,1210,60,f'{audit["selected_model"]} was selected using 2007 to 2018. The final test is 2019Q1 to 2026Q2. Persistence had slightly lower test MAE; the difference is uncertain.',12)
    visual('models','forecast','lineChart',24,145,800,340,'Observed and estimated debt service ratio (%)',
           {'Category':[projection('Quarter','date')],'Y':[projection('Backtest',m,'Measure') for m in ['Observed','Model estimate','Persistence estimate']]},field('Quarter','date'))
    visual('models','score','clusteredBarChart',844,145,412,235,'Test MAE, percentage points',
           {'Category':[projection('Scores','model')],'Y':[projection('Scores','Mean absolute error','Measure')]})
    visual('models','coverage','card',844,400,412,85,'Calibration band: observed test coverage',{'Values':[projection('Backtest','Band coverage','Measure')]})
    visual('models','detail','tableEx',24,505,680,160,'Test results',{'Values':[projection('Scores','model'),projection('Scores','n'),projection('Scores','Mean absolute error','Measure'),projection('Scores','Root mean squared error','Measure')]})
    text('models','limit',730,520,505,145,'Revised vintage retrospective test. Household releases arrive in the following quarter. This is not a real time validation. A 90% calibration band has no guaranteed coverage. No borrower default predictions.',12)
    text('scenarios','header',24,10,1200,55,'What if payments grow faster than income?',25)
    text('scenarios','subtitle',24,65,1220,60,'Illustrative accounting scenarios based on 2026Q2. These are assumptions, not policy rate forecasts.',13)
    visual('scenarios','scenario_matrix','pivotTable',24,150,780,440,'Debt service ratio (%) by assumed income and payment changes',
           {'Rows':[projection('Scenarios','income_change_pct')],'Columns':[projection('Scenarios','payment_change_pct')],'Values':[projection('Scenarios','Scenario ratio','Measure')]})
    visual('scenarios','payment_select','slicer',830,150,420,180,'Assumed payment change (%)',{'Values':[projection('Scenarios','payment_change_pct')]})
    visual('scenarios','income_select','slicer',830,350,420,180,'Assumed income change (%)',{'Values':[projection('Scenarios','income_change_pct')]})
    text('scenarios','equation',24,610,1210,75,'Scenario ratio = 100 × current payments × (1 + payment change) / [current income × (1 + income change)]. No causal link from policy rates is assumed. Clear slicers to show every scenario.',12)
    write(BI/'theme.json',{'name':'Household Finance','dataColors':['#176B61','#D38136','#6579A4','#4B5563'],'background':'#F2F5F4','foreground':'#183D40','tableAccent':'#176B61','textClasses':{'title':{'fontSize':12,'fontFace':'Segoe UI','color':'#183D40'},'label':{'fontSize':11,'fontFace':'Segoe UI','color':'#35444A'},'header':{'fontSize':12,'fontFace':'Segoe UI','color':'#183D40'},'callout':{'fontSize':28,'fontFace':'Segoe UI','color':'#183D40'}}})
    write(REPORT/'StaticResources/RegisteredResources/HouseholdTheme.json',json.loads((BI/'theme.json').read_text()))
    print('Power BI project generated:',BI/'HouseholdFinance.pbip')

if __name__=='__main__':build()
