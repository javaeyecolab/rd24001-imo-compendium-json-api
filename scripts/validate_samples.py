import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATASETS=[p for p in (ROOT/'samples/datasets').iterdir() if p.is_dir()]
assert len(DATASETS)==12, f"expected 12 datasets, got {len(DATASETS)}"

def valid_imo(v):
    return bool(re.fullmatch(r"\d{7}",v)) and sum(int(d)*w for d,w in zip(v[:6],[7,6,5,4,3,2]))%10==int(v[6])
expected=None
count=0
for ds in sorted(DATASETS):
    files=sorted(ds.glob('*.json'))
    assert len(files)==10, f"{ds.name}: expected 10, got {len(files)}"
    imos=[]
    for f in files:
        d=json.loads(f.read_text(encoding='utf-8'))
        imo=d['ship']['imoShipNumberId']['content']
        assert valid_imo(imo), f"invalid IMO {imo}"
        assert f.stem==imo
        assert d['sampleMetadata']['syntheticSample'] is True
        assert d['sampleMetadata']['imoCompendiumVersion']=='FAL.5/Circ.56'
        assert d['ship']['shipName']
        imos.append(imo); count+=1
    if expected is None: expected=imos
    assert imos==expected, f"ship set mismatch in {ds.name}"
print(f"OK: {len(DATASETS)} datasets, {len(expected)} ships, {count} source JSON samples")
