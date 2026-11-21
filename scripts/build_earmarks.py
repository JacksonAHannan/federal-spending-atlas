"""Rebuild GAO JSON from preserved official Overall CSV; never sum requester rows."""
import csv, datetime, hashlib, json, pathlib
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1]
def bucket():return {'amount':0,'projects':0,'years':{}}
def add(group,project):
    group['amount']+=project['amount'];group['projects']+=1
    year=group['years'].setdefault(str(project['year']),{'amount':0,'projects':0})
    year['amount']+=project['amount'];year['projects']+=1

def main():
    projects=[]
    with (ROOT/'data/raw/gao-1. Overall data.csv').open(encoding='utf-8-sig',newline='') as file:
        for row in csv.DictReader(file):
            amount=Decimal(row['Amount'])
            assert amount==amount.to_integral_value()
            projects.append({'id':row['OV_GAO_ID'],'year':int(row['Fiscal Year of Appropriation']),'amount':int(amount),'agency':row['Agency'],'project':row['Project/Recipient'],'location':row['Location'],'requesters':row['Requesting Member Info']})
    assert len({p['id'] for p in projects})==len(projects)
    total=bucket();states={};multistate=bucket();multistate['locations']={}
    for p in projects:
        add(total,p)
        if ',' in p['location'] or '&' in p['location']:
            add(multistate,p);add(multistate['locations'].setdefault(p['location'],bucket()),p)
        else:add(states.setdefault(p['location'],bucket()),p)
    prior=json.loads((ROOT/'dist/data/earmarks.json').read_text())
    metadata=prior['metadata']
    metadata['zip_sha256']=hashlib.sha256((ROOT/'data/raw/gao-2022-2024.zip').read_bytes()).hexdigest()
    result={'metadata':metadata,'totals':{'amount':total['amount'],'projects':total['projects']},'years':total['years'],'states':states,'multistate':multistate,'projects':projects}
    assert result['totals']==prior['totals'],'Unexpected source totals; review before replacing snapshot'
    (ROOT/'dist/data/earmarks.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False))
    print(f'Rebuilt {len(projects):,} unique GAO projects; ${total["amount"]:,}.')
if __name__=='__main__':main()
