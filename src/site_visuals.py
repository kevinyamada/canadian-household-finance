"""Prepare regional estimates and SVG chart coordinates for the website."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw/site_visuals"
TENURE="Tenure including first-time homebuyer and social and affordable housing status"
STAT="Core housing need statistics"
POINT="Percentage of households in core housing need"
LOW="Low 95% confidence interval, percentage of households"
HIGH="High 95% confidence interval, percentage of households"
NATIONAL="Canada (provinces only)"
SOURCE_URL="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610008501"


def load_inputs(root=ROOT):
    raw=root/"data/raw/site_visuals"
    manifest=json.loads((raw/"manifest.json").read_text(encoding="utf-8"))
    for item in manifest["sources"]:
        assert hashlib.sha256((raw/item["file"]).read_bytes()).hexdigest()==item["sha256"],item["file"]
    with zipfile.ZipFile(raw/"46100085-eng.zip") as z:
        frame=pd.read_csv(z.open("46100085.csv"),low_memory=False)
    geometry=json.loads(gzip.decompress((raw/"provinces_2021_3347.json.gz").read_bytes()))
    return frame,geometry,manifest


def usable_number(row):
    if row is None:return None
    status="" if pd.isna(row.STATUS) else str(row.STATUS)
    if status in ["x","..","F","..."] or pd.isna(row.VALUE):return None
    value=float(row.VALUE)
    if not math.isfinite(value):return None
    assert 0<=value<=100,(row.GEO,row[STAT],value)
    return value


def regional_data(frame,geometry):
    features=geometry["features"]
    names={str(f["attributes"]["PRUID"]):f["attributes"]["PRENAME"] for f in features}
    assert len(names)==13 and len(set(names.values()))==13
    selected=frame[(frame[TENURE]=="Renter") & frame[STAT].isin([POINT,LOW,HIGH]) & frame.GEO.isin([NATIONAL,*names.values()])].copy()
    assert not selected.duplicated(["REF_DATE","GEO",STAT]).any(),"Regional source keys must be unique"
    assert selected.UOM.eq("Percent").all() and selected.SCALAR_FACTOR.eq("units").all()
    selected["year"]=selected.REF_DATE.astype(int)
    lookup={(int(row.year),row.GEO,row[STAT]):row for _,row in selected.iterrows()}
    years=sorted(selected.year.unique().tolist())
    assert years==[2018,2021,2022,2024]
    national={}
    records={}
    csv_rows=[]
    for year in years:
        national_value=usable_number(lookup.get((year,NATIONAL,POINT)))
        assert national_value is not None,"Use the published national estimate, not an average of provinces"
        national[str(year)]={"value":national_value,"low":usable_number(lookup.get((year,NATIONAL,LOW))),"high":usable_number(lookup.get((year,NATIONAL,HIGH)))}
        rows={}
        for code,name in names.items():
            row=lookup.get((year,name,POINT))
            value=usable_number(row) if int(code)<60 else None
            low=usable_number(lookup.get((year,name,LOW))) if value is not None else None
            high=usable_number(lookup.get((year,name,HIGH))) if value is not None else None
            if value is not None and low is not None and high is not None:assert low<=value<=high
            status="" if row is None or pd.isna(row.STATUS) else str(row.STATUS)
            note="Outside the survey's provincial coverage" if int(code)>=60 else "Suppressed by the source" if status in ["x","F"] else "Not available for this period" if value is None else ""
            fraction=0 if value is None else min(value/50,1)
            def blend(a,b):return "#"+"".join(f"{round(x+(y-x)*fraction):02x}" for x,y in zip(a,b))
            record={"code":code,"name":name,"year":year,"value":value,"low":low,"high":high,"status":status,"note":note,
                "difference_pp":None if value is None else round(value-national_value,1),
                "bar_pct":None if value is None else round(value/50*100,3),
                "fill_light":None if value is None else blend([218,234,219],[153,77,42]),
                "fill_dark":None if value is None else blend([54,92,72],[226,155,105])}
            rows[code]=record
            csv_rows.append({**{k:record[k] for k in ["code","name","year","value","low","high","status","note","difference_pp"]},
                "source_vector":None if row is None else row.VECTOR,"unit":"Percent of renter households","measure":POINT})
        records[str(year)]=rows
    return {"years":years,"latest_year":max(years),"national":national,"records":records,"source_url":SOURCE_URL,
        "measure":"Renter households in core housing need","scale_max":50,
        "definition":"Housing below cost, size or condition standards, with no affordable local alternative.",
        "coverage":"Canadian Housing Survey, ten provinces; territories are outside this survey's coverage.",
        "source_period_note":"Survey reference years are separate from the national saving-account periods."},pd.DataFrame(csv_rows)


def simplify_open(points,epsilon):
    if len(points)<=2:return points
    keep=np.zeros(len(points),dtype=bool);keep[[0,-1]]=True
    stack=[(0,len(points)-1)]
    while stack:
        a,b=stack.pop()
        if b<=a+1:continue
        segment=points[b]-points[a];norm=float(np.dot(segment,segment))
        subset=points[a+1:b]
        if norm==0:dist=np.sum((subset-points[a])**2,axis=1)
        else:
            t=np.clip(((subset-points[a])@segment)/norm,0,1)
            dist=np.sum((subset-(points[a]+t[:,None]*segment))**2,axis=1)
        index=int(np.argmax(dist));maximum=float(dist[index])
        if maximum>epsilon**2:
            middle=a+1+index;keep[middle]=True;stack.extend([(a,middle),(middle,b)])
    return points[keep]


def simplify_ring(points,epsilon=.55):
    if len(points)<4:return None
    far=int(np.argmax(np.sum((points-points[0])**2,axis=1)))
    if far==0:return None
    first=simplify_open(points[:far+1],epsilon)
    second=simplify_open(points[far:],epsilon)
    result=np.vstack([first[:-1],second])
    return result if len(result)>=4 else None


def map_paths(geometry):
    assert geometry["spatialReference"]["wkid"]==3347
    features=geometry["features"]
    all_points=np.vstack([np.asarray(r,dtype=float)[:,:2] for f in features for r in f["geometry"]["rings"]])
    assert np.isfinite(all_points).all()
    minimum=all_points.min(axis=0);maximum=all_points.max(axis=0)
    width,height,pad=760,650,16
    scale=min((width-2*pad)/(maximum[0]-minimum[0]),(height-2*pad)/(maximum[1]-minimum[1]))
    offset=np.array([(width-(maximum[0]-minimum[0])*scale)/2,(height-(maximum[1]-minimum[1])*scale)/2])
    output=[];total_before=0;total_after=0
    for feature in features:
        attrs=feature["attributes"];code=str(attrs["PRUID"])
        rings=[];areas=[]
        for ring in feature["geometry"]["rings"]:
            array=np.asarray(ring,dtype=float)[:,:2]
            total_before+=len(array)
            points=np.column_stack([(array[:,0]-minimum[0])*scale+offset[0],(maximum[1]-array[:,1])*scale+offset[1]])
            area=abs(float(np.sum(points[:-1,0]*points[1:,1]-points[1:,0]*points[:-1,1])))/2
            rings.append(points);areas.append(area)
        largest=int(np.argmax(areas))
        projected=np.vstack(rings)
        lo=projected.min(axis=0);hi=projected.max(axis=0)
        paths=[]
        for index,points in enumerate(rings):
            if areas[index]<.15 and index!=largest:continue
            simple=simplify_ring(points)
            if simple is None:
                if index==largest:simple=points
                else:continue
            total_after+=len(simple)
            paths.append("M"+"L".join(f"{x:.2f},{y:.2f}" for x,y in simple)+"Z")
        assert paths,"Every province and territory must retain geometry"
        output.append({"code":code,"name":attrs["PRENAME"],"abbr":attrs["PREABBR"],"path":"".join(paths),
            "box":[round(float(lo[0]),2),round(float(lo[1]),2),round(float(hi[0]-lo[0]),2),round(float(hi[1]-lo[1]),2)],
            "center":[round(float((lo[0]+hi[0])/2),2),round(float((lo[1]+hi[1])/2),2)]})
    provincial=[item for item in output if int(item["code"])<60]
    x0=max(0,min(p["box"][0] for p in provincial)-10);y0=max(0,min(p["box"][1] for p in provincial)-10)
    x1=min(width,max(p["box"][0]+p["box"][2] for p in provincial)+10);y1=min(height,max(p["box"][1]+p["box"][3] for p in provincial)+10)
    return {"width":width,"height":height,"view_all":[0,0,width,height],"view_provinces":[round(x0,2),round(y0,2),round(x1-x0,2),round(y1-y0,2)],
        "features":sorted(output,key=lambda x:x["code"]),"projection":"Statistics Canada Lambert, EPSG:3347","boundary_year":2021,
        "display_tolerance_px":.55,"input_vertices":total_before,"display_vertices":total_after,
        "source_url":"https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/0"}


def trend_data(root):
    annual=pd.read_csv(root/"data/processed/renter_annual_saving.csv").sort_values("year")
    assert annual.quarter_count.eq(4).all()
    width,height=760,300
    x=lambda year:70+(int(year)-int(annual.year.min()))/(int(annual.year.max())-int(annual.year.min()))*650
    y=lambda value:245-(float(value)-50000)/30000*215
    records=[]
    for row in annual.itertuples():
        records.append({"year":int(row.year),"income":float(row.income),"consumption":float(row.consumption),"gap":float(row.income_less_consumption),
            "saving":float(row.saving),"pension":float(row.pension),"x":round(x(row.year),2),"income_y":round(y(row.income),2),"consumption_y":round(y(row.consumption),2)})
    def line(items,key):return "M"+"L".join(f"{item['x']},{item[key]}" for item in items)
    return {"width":width,"height":height,"records":records,"income_path":line(records,"income_y"),"consumption_path":line(records,"consumption_y"),
        "gap_area":line(records,"income_y")+"L"+"L".join(f"{r['x']},{r['consumption_y']}" for r in records[::-1])+"Z",
        "ticks":[{"value":v,"y":round(y(v),2),"label":f"{v//1000}k"} for v in [50000,60000,70000,80000]],
        "unit":"Nominal CAD per household; full-year sums of quarterly estimates","source_url":"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610066201"}


def cash_data(root):
    cases=pd.read_csv(root/"data/processed/home_purchase_cash_cases.csv")
    x=lambda price:70+(price-300000)/1700000*650
    y=lambda total:245-total/500000*215
    series={}
    for allowance,group in cases.groupby("closing_allowance_pct"):
        records=[]
        for row in group.sort_values("home_price").itertuples():
            records.append({"price":int(row.home_price),"down":float(row.minimum_down_payment),"closing":float(row.closing_allowance),
                "total":float(row.upfront_cash_scenario),"allowance":float(allowance),"x":round(x(row.home_price),3),"y":round(y(row.upfront_cash_scenario),3),
                "down_share_pct":round(row.minimum_down_payment/row.upfront_cash_scenario*100,3),
                "closing_share_pct":round(row.closing_allowance/row.upfront_cash_scenario*100,3)})
        groups=[[r for r in records if r["price"]<1500000],[r for r in records if r["price"]>=1500000]]
        series[f"{allowance:g}"]={"records":records,"paths":["M"+"L".join(f"{r['x']},{r['y']}" for r in values) for values in groups]}
    return {"width":760,"height":300,"series":series,"allowances":sorted(cases.closing_allowance_pct.unique().tolist()),
        "prices":sorted(int(v) for v in cases.home_price.unique()),"default_price":600000,"default_allowance":2.5,"threshold_x":round(x(1500000),3),
        "x_ticks":[{"x":round(x(v),2),"label":label} for v,label in [(300000,"300k"),(600000,"600k"),(1000000,"1m"),(1500000,"1.5m"),(2000000,"2m")]],
        "y_ticks":[{"y":round(y(v),2),"label":f"{v//1000}k"} for v in [0,100000,200000,300000,400000,500000]],
        "rule_date":"2026-11-16","scope":"Illustrative upfront cash only; prices and closing allowances are assumptions."}


def generate(root=ROOT):
    frame,geometry,manifest=load_inputs(root)
    regional,table=regional_data(frame,geometry)
    payload={"version":1,"regional":regional,"map":map_paths(geometry),"trend":trend_data(root),"cash":cash_data(root)}
    target=root/"docs/assets/visuals-data.json"
    target.write_text(json.dumps(payload,separators=(",",":"),ensure_ascii=False,allow_nan=False),encoding="utf-8")
    table.to_csv(root/"data/processed/regional_housing_need.csv",index=False)
    record={"file":"docs/assets/visuals-data.json","sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"bytes":target.stat().st_size,
        "map_source":SOURCE_URL,"housing_release_date":"2026-09-21","survey_years":regional["years"],"regions_with_geometry":13,
        "covered_provinces":10,"uncovered_territories":3,"boundary_year":2021,"map_vertices":payload["map"]["display_vertices"],
        "execution":"Prepared with local Python in VS Code; browser interaction displays saved figures and coordinates"}
    (root/"data/processed/website_visuals_manifest.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps({**record,"latest_regional_values":regional["records"]["2024"],"national":regional["national"]},indent=2),flush=True)
    return payload


if __name__=="__main__":
    generate()
