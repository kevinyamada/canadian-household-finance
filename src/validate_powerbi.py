import json
from pathlib import Path
import requests
from jsonschema import Draft7Validator
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.schema_cache'


def fetch(url):
    CACHE.mkdir(exist_ok=True)
    import hashlib
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if path.exists():return json.loads(path.read_text())
    response=requests.get(url.replace('schema.embedded.json','schema-embedded.json'),timeout=45)
    response.raise_for_status()
    path.write_text(response.text)
    return response.json()


def validate():
    count=0
    for path in (ROOT/'powerbi').rglob('*'):
        if '.pbi' in path.parts:continue
        if not path.is_file() or path.suffix not in ['.json','.pbip','.pbir']:continue
        document=json.loads(path.read_text(encoding='utf-8'))
        if '$schema' not in document:continue
        url=document['$schema'];schema=fetch(url)
        registry=Registry(retrieve=lambda uri: Resource.from_contents(fetch(uri)))
        errors=list(Draft7Validator(schema,registry=registry).iter_errors(document))
        if errors:
            raise ValueError(str(path.relative_to(ROOT))+': '+errors[0].message)
        count+=1
    model=json.loads((ROOT/'powerbi/HouseholdFinance.SemanticModel/model.bim').read_text())['model']
    measure_names=[m['name'].casefold() for t in model['tables'] for m in t.get('measures',[])]
    assert len(measure_names)==len(set(measure_names)), 'Measure names must be unique across the model'
    entities={t['name']:{c['name'] for c in t['columns']}|{m['name'] for m in t.get('measures',[])} for t in model['tables']}
    for table in model['tables']:
        names=[c['name'].casefold() for c in table['columns']]+[m['name'].casefold() for m in table.get('measures',[])]
        assert len(names)==len(set(names)), table['name']+' has conflicting field names'
    assert (ROOT/'powerbi/HouseholdFinance.Report/definition/version.json').exists()
    for path in (ROOT/'powerbi/HouseholdFinance.Report').rglob('visual.json'):
        document=json.loads(path.read_text())
        query=document['visual'].get('query',{}).get('queryState',{})
        for role in query.values():
            for projection in role['projections']:
                expression=next(iter(projection['field'].values()))
                assert expression['Property'] in entities[expression['Expression']['SourceRef']['Entity']]
    result={'schema_validated_files':count,'semantic_references_valid':True,'desktop_check':'Verify separately in Power BI Desktop'}
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':validate()
