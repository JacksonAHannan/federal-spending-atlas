"""Reconcile derived data against preserved source records and boundary IDs."""
import csv, json, pathlib
from decimal import Decimal
ROOT=pathlib.Path(__file__).resolve().parents[1]
def check():
    geo=json.loads((ROOT/'dist/data/districts.geojson').read_text())
    ids=[f['properties']['GEOID'] for f in geo['features']]
    assert len(ids)==len(set(ids))==441
    spending=json.loads((ROOT/'dist/data/spending.json').read_text())
    for year,data in spending['years'].items():
        records={r['id']:r for r in data['districts']}
        assert set(records)==set(ids)
        for kind in ['grants','contracts']:
            raw=json.loads((ROOT/f'data/raw/usaspending-{year}-{kind}.json').read_text())
            assert raw['request']['spending_level']=='transactions'
            assert raw['request']['scope']=='place_of_performance'
            source=raw['response']['results']
            assert len({r['shape_code'] for r in source})==len(source)
            for row in source:
                if row['shape_code'] in records:
                    assert records[row['shape_code']][kind]==row['aggregated_amount']
                else:assert row in data['unmapped'][kind]
            original=sum(Decimal(str(r['aggregated_amount'])) for r in source)
            derived=sum(Decimal(str(r[kind])) for r in records.values())+sum(Decimal(str(r['aggregated_amount'])) for r in data['unmapped'][kind])
            assert original==derived
    # Independent combined FY2025 endpoint request verifies that disjoint type sums reconcile.
    probe=json.loads((ROOT/'data/raw/usaspending-probe.json').read_text())
    for row in probe['results']:
        match=next((r for r in spending['years']['2025']['districts'] if r['id']==row['shape_code']),None)
        if match:assert abs(Decimal(str(match['grants']))+Decimal(str(match['contracts']))-Decimal(str(row['aggregated_amount'])))<Decimal('.02')
    earmarks=json.loads((ROOT/'dist/data/earmarks.json').read_text())
    with (ROOT/'data/raw/gao-1. Overall data.csv').open(encoding='utf-8-sig',newline='') as f:source=list(csv.DictReader(f))
    projects={p['id']:p for p in earmarks['projects']}
    assert len(projects)==len(source)==20294
    for row in source:
        p=projects[row['OV_GAO_ID']]
        assert Decimal(row['Amount'])==p['amount']
        assert row['Location']==p['location']
        assert row['Requesting Member Info']==p['requesters']
    assert sum(p['amount'] for p in projects.values())==earmarks['totals']['amount']==38957547994
    assert sum(s['amount'] for s in earmarks['states'].values())+earmarks['multistate']['amount']==earmarks['totals']['amount']
    assert sum(s['projects'] for s in earmarks['states'].values())+earmarks['multistate']['projects']==20294
    assert earmarks['multistate']['projects']==47
    from period_data_check import check_cycles,check_payments
    check_cycles(spending);check_payments()
    print('PASS: 441 district joins across 5 years; 10 raw-response reconciliations; independent combined-type reconciliation; 20,294 GAO unique-project/source/partition checks.')
if __name__=='__main__':check()
