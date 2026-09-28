import json, os, shutil, textwrap, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
# Regenerate only generated content; keep scripts/workflows/repository metadata intact.
for _sub in ('samples', 'docs'):
    _path = ROOT / _sub
    if _path.exists():
        shutil.rmtree(_path)

DATASETS = [
    ('fal1-general-declaration', 'FAL1', 'General Declaration', 'arrival-departure'),
    ('fal2-cargo-declaration', 'FAL2', 'Cargo Declaration', 'arrival-departure'),
    ('fal3-ships-stores-declaration', 'FAL3', "Ship's Stores Declaration", 'arrival-departure'),
    ('fal4-crews-effects-declaration', 'FAL4', "Crew's Effects Declaration", 'arrival'),
    ('fal5-crew-list', 'FAL5', 'Crew List', 'arrival-departure'),
    ('fal6-passenger-list', 'FAL6', 'Passenger List', 'arrival-departure'),
    ('fal7-dangerous-goods-manifest', 'FAL7', 'Dangerous Goods Manifest', 'arrival-departure'),
    ('delivery-bill-mail-consignment', 'MAIL', 'Delivery Bill for Mail Consignment', 'conditional'),
    ('maritime-declaration-health', 'MDH', 'Maritime Declaration of Health', 'arrival'),
    ('ship-sanitation-certificate', 'SSC', 'Ship Sanitation Certificate', 'arrival'),
    ('security-report', 'SEC', 'Security Report', 'pre-arrival'),
    ('advance-notification-waste-delivery', 'WASTE', 'Advance Notification for Waste Delivery', 'pre-arrival'),
]

# IMO number check digit: multiply first 6 digits by 7..2, modulo 10.
def make_imo(prefix6: str) -> str:
    assert len(prefix6) == 6 and prefix6.isdigit()
    check = sum(int(d) * w for d, w in zip(prefix6, [7,6,5,4,3,2])) % 10
    return prefix6 + str(check)

prefixes = ['930001','930002','930003','930004','930005','930006','930007','930008','930009','930010']
imos = [make_imo(p) for p in prefixes]

ports = [
    ('KRPUS','Busan, Republic of Korea','JPTYO','Tokyo, Japan','SGSIN','Singapore'),
    ('KRICN','Incheon, Republic of Korea','CNSHA','Shanghai, China','KRPUS','Busan, Republic of Korea'),
    ('SGSIN','Singapore','MYPKG','Port Klang, Malaysia','IDJKT','Jakarta, Indonesia'),
    ('JPTYO','Tokyo, Japan','KRPUS','Busan, Republic of Korea','CNSHA','Shanghai, China'),
    ('CNSHA','Shanghai, China','KRICN','Incheon, Republic of Korea','JPTYO','Tokyo, Japan'),
    ('NLRTM','Rotterdam, Netherlands','DEHAM','Hamburg, Germany','BEANR','Antwerp, Belgium'),
    ('USLAX','Los Angeles, United States','USOAK','Oakland, United States','JPTYO','Tokyo, Japan'),
    ('AUSYD','Sydney, Australia','AUMEL','Melbourne, Australia','SGSIN','Singapore'),
    ('AEJEA','Jebel Ali, United Arab Emirates','OMSLL','Salalah, Oman','SGSIN','Singapore'),
    ('GBSOU','Southampton, United Kingdom','NLRTM','Rotterdam, Netherlands','DEHAM','Hamburg, Germany'),
]
flags = [('KR','Korea'),('KR','Korea'),('SG','Singapore'),('JP','Japan'),('PA','Panama'),('NL','Netherlands'),('MH','Marshall Islands'),('AU','Australia'),('LR','Liberia'),('GB','United Kingdom')]
ship_types = [('70','Container ship'),('70','Container ship'),('79','General cargo ship'),('60','Passenger ship'),('80','Tanker'),('70','Container ship'),('70','Container ship'),('79','General cargo ship'),('80','Tanker'),('60','Passenger ship')]
names = ['RD HORIZON','RD BLUE WAVE','RD OCEAN LINK','RD PACIFIC STAR','RD ENERGY ONE','RD EUROPE LINK','RD AMERICA BRIDGE','RD SOUTHERN CROSS','RD GULF NAVIGATOR','RD CHANNEL STAR']


def c(value, **meta):
    obj = {'content': value}
    obj.update({k:v for k,v in meta.items() if v is not None})
    return obj

def ident(value, schemeId=None, schemeAgencyId=None):
    return c(value, schemeId=schemeId, schemeAgencyId=schemeAgencyId)

def code(value, listId=None, listAgencyId=None):
    return c(value, listId=listId, listAgencyId=listAgencyId)

def measure(value, unitCode):
    return c(value, unitCode=unitCode)

def dt(v):
    return c(v)

def text(v):
    return v

ships=[]
base_dt = datetime(2026,9,28,3,0,tzinfo=timezone.utc)
for i, imo in enumerate(imos):
    arr_code, arr_name, dep_code, dep_name, next_code, next_name = ports[i]
    flag_code, flag_name = flags[i]
    type_code, type_name = ship_types[i]
    ships.append({
        'imo': imo,
        'name': names[i],
        'callSign': f'DR{i+1:04d}',
        'mmsi': f'{440000001+i:09d}',
        'flagCode': flag_code,
        'flagName': flag_name,
        'shipTypeCode': type_code,
        'shipTypeName': type_name,
        'voyageNumber': f'RD26-{i+1:03d}',
        'arrivalPortCode': arr_code,
        'arrivalPortName': arr_name,
        'departurePortCode': dep_code,
        'departurePortName': dep_name,
        'nextPortCode': next_code,
        'nextPortName': next_name,
        'eta': (base_dt + timedelta(hours=i*7)).isoformat().replace('+00:00','Z'),
        'etd': (base_dt + timedelta(hours=i*7+14)).isoformat().replace('+00:00','Z'),
    })

VERIFIED_COMMON = {
    'messageHeader.messageFunctionCode': 'IMO0305',
    'messageHeader.arrivalDepartureCode': 'IMO0013',
    'messageHeader.authenticationDateTime': 'IMO0014',
    'ship.imoShipNumberId': 'IMO0140',
    'ship.shipName': 'IMO0142',
    'ship.callSignId': 'IMO0136',
    'ship.mmsiNumberId': 'IMO0326',
    'ship.flagStateId': 'IMO0138',
    'voyage.portOfArrivalCode': 'IMO0108',
    'voyage.portOfArrivalName': 'IMO0109',
    'voyage.estimatedArrivalDateTime': 'IMO0064',
}

SPECIAL_REFS = {
 'FAL2': {
    'cargoDeclaration.cargoItems[].hsCodeId':'IMO0025',
    'cargoDeclaration.cargoItems[].grossWeightMeasure':'IMO0024',
    'cargoDeclaration.cargoItems[].grossVolumeMeasure':'IMO0023',
    'cargoDeclaration.cargoItems[].transportEquipmentId':'IMO0021',
    'cargoDeclaration.cargoItems[].numberOfPackages':'IMO0028',
    'cargoDeclaration.cargoItems[].packageTypeCode':'IMO0029',
    'cargoDeclaration.transportContractId':'IMO0170',
 },
 'FAL7': {
    'dangerousGoodsManifest.items[].stowagePositionId':'IMO0045',
    'dangerousGoodsManifest.items[].transportEquipmentId':'IMO0021',
    'dangerousGoodsManifest.items[].shipperReferenceId':'IMO0056',
 },
 'MAIL': {
    'messageHeader.messageId':'IMO0277',
    'mailDeliveryBill.originOfficeId':'IMO1232',
    'mailDeliveryBill.originOfficeName':'IMO1233',
    'mailDeliveryBill.destinationOfficeId':'IMO1234',
    'mailDeliveryBill.destinationOfficeName':'IMO1235',
    'mailDeliveryBill.numberOfLetterPostReceptacles':'IMO1180',
    'mailDeliveryBill.numberOfParcelReceptacles':'IMO1181',
    'mailDeliveryBill.numberOfEmptyBagSacks':'IMO1182',
    'mailDeliveryBill.letterPostGrossWeightMeasure':'IMO1183',
    'mailDeliveryBill.parcelGrossWeightMeasure':'IMO1184',
    'mailDeliveryBill.emptyReceptacleGrossWeightMeasure':'IMO1185',
 },
 'MDH': {
    'maritimeDeclarationHealth.illnessCases[].illness':'IMO0220',
    'maritimeDeclarationHealth.illnessCases[].symptomsOnsetDateTime':'IMO0221',
    'maritimeDeclarationHealth.illnessCases[].reportedIndicator':'IMO0222',
    'maritimeDeclarationHealth.illnessCases[].healthStatusCode':'IMO0223',
    'maritimeDeclarationHealth.illnessCases[].caseDispositionCode':'IMO0224',
    'maritimeDeclarationHealth.illnessCases[].treatment':'IMO0227',
    'maritimeDeclarationHealth.visitedAffectedAreaIndicator':'IMO0203',
    'maritimeDeclarationHealth.personDiedIndicator':'IMO0206',
 },
 'SSC': {
    'shipSanitationCertificate.certificateTypeCode':'IMO0307',
    'shipSanitationCertificate.extensionExpirationDate':'IMO1191',
    'shipSanitationCertificate.controlMeasuresAppliedIndicator':'IMO1208',
    'shipSanitationCertificate.controlMeasuresAppliedComments':'IMO1209',
    'shipSanitationCertificate.conditionComments':'IMO1211',
 },
 'SEC': {
    'securityReport.validCertificateIndicator':'IMO0067',
    'securityReport.certificateIssuerFlagStateId':'IMO0070',
    'securityReport.shipToShipActivities[].sequenceNumber':'IMO0165',
    'securityReport.shipToShipActivities[].description':'IMO0162',
    'securityReport.shipToShipActivities[].activityTypeCode':'IMO0161',
 }
}

def common(doc_code, dataset_name, slug, s, index):
    arrival_departure = 'A' if doc_code not in ('MAIL',) else None
    mh = {
        'messageFunctionCode': code('9', listId='1225', listAgencyId='UN/EDIFACT'),
        'authenticationDateTime': dt(s['eta']),
        'messageId': ident(f'{doc_code}-{s["imo"]}-{index+1:02d}', schemeId='RD24001-SAMPLE'),
    }
    if arrival_departure:
        mh['arrivalDepartureCode'] = code(arrival_departure, listId='IMO-ArrivalDeparture')
    return {
        'sampleMetadata': {
            'syntheticSample': True,
            'profileId': 'RD24001-IMO-FAL-UNCEFACT-JSON-SAMPLE-1.0',
            'imoCompendiumVersion': 'FAL.5/Circ.56',
            'datasetCode': doc_code,
            'datasetName': dataset_name,
            'datasetSlug': slug,
            'note': 'Synthetic demonstration payload; not an official IMO normative JSON message.'
        },
        'messageHeader': mh,
        'ship': {
            'imoShipNumberId': ident(s['imo'], schemeId='IMOShipNumber', schemeAgencyId='IMO'),
            'shipName': s['name'],
            'callSignId': ident(s['callSign']),
            'mmsiNumberId': ident(s['mmsi'], schemeId='MMSI'),
            'flagStateId': ident(s['flagCode'], schemeId='ISO3166-1-alpha2'),
            'shipTypeCode': code(s['shipTypeCode'], listId='UNECE-Rec28'),
            'shipTypeName': s['shipTypeName'],
        },
        'voyage': {
            'voyageId': ident(s['voyageNumber']),
            'portOfDepartureCode': code(s['departurePortCode'], listId='UNLOCODE'),
            'portOfDepartureName': s['departurePortName'],
            'portOfArrivalCode': code(s['arrivalPortCode'], listId='UNLOCODE'),
            'portOfArrivalName': s['arrivalPortName'],
            'estimatedArrivalDateTime': dt(s['eta']),
            'estimatedDepartureDateTime': dt(s['etd']),
            'nextPortCode': code(s['nextPortCode'], listId='UNLOCODE'),
            'nextPortName': s['nextPortName'],
        },
        'imoDataReferences': {**VERIFIED_COMMON, **SPECIAL_REFS.get(doc_code,{})}
    }

def payload_for(doc_code, s, i):
    if doc_code == 'FAL1':
        return {'generalDeclaration': {
            'master': {'familyName': f'Master{i+1}', 'givenName': 'Alex', 'roleCode': code('MASTER')},
            'agentAtPort': {'partyId': ident(f'AGT-KR-{i+1:03d}'), 'name': f'RD Port Agency {i+1}', 'email': f'agent{i+1}@example.invalid', 'telephone': f'+82-51-555-{1000+i:04d}'},
            'crewCount': 18+i%5,
            'passengerCount': 0 if s['shipTypeCode'] != '60' else 120+i*5,
            'briefCargoDescription': 'Containerized general cargo' if s['shipTypeCode']=='70' else 'Mixed cargo and stores',
            'grossTonnageMeasure': measure(42000+i*1350,'GT'),
            'netTonnageMeasure': measure(22000+i*800,'NT')
        }}
    if doc_code == 'FAL2':
        return {'cargoDeclaration': {
            'transportContractId': ident(f'BL-{s["imo"]}-{i+1:03d}'),
            'cargoItems': [
                {'itemSequenceNumber':1,'description':'Machinery parts','hsCodeId':ident('848790'),'marksAndNumbers':'RD-A01','grossWeightMeasure':measure(12500+i*100,'KGM'),'grossVolumeMeasure':measure(24.5+i,'MTQ'),'numberOfPackages':20+i,'packageTypeCode':code('CT','UNECE-Rec21'),'transportEquipmentId':ident(f'RDCU{i+1:07d}')},
                {'itemSequenceNumber':2,'description':'Electronic components','hsCodeId':ident('854239'),'marksAndNumbers':'RD-B01','grossWeightMeasure':measure(6200+i*80,'KGM'),'grossVolumeMeasure':measure(12.2+i/2,'MTQ'),'numberOfPackages':12+i,'packageTypeCode':code('BX','UNECE-Rec21'),'transportEquipmentId':ident(f'RDCU{i+11:07d}')}
            ]
        }}
    if doc_code == 'FAL3':
        return {'shipsStoresDeclaration': {'stores': [
            {'storeItemSequenceNumber':1,'description':'Marine gas oil','quantityMeasure':measure(32000+i*500,'LTR'),'locationOnBoard':'Engine room tank'},
            {'storeItemSequenceNumber':2,'description':'Lubricating oil','quantityMeasure':measure(1800+i*25,'LTR'),'locationOnBoard':'Engine store'},
            {'storeItemSequenceNumber':3,'description':'Provision - bottled water','quantityMeasure':measure(240+i*10,'EA'),'locationOnBoard':'Provision store'}
        ]}}
    if doc_code == 'FAL4':
        return {'crewsEffectsDeclaration': {'crewEffects': [
            {'crewMemberId':ident(f'CREW-{i+1:02d}-01'),'crewMemberFamilyName':'Kim','crewMemberGivenName':'Minjun','effectDescription':'Tobacco products','quantityMeasure':measure(2,'CT')},
            {'crewMemberId':ident(f'CREW-{i+1:02d}-02'),'crewMemberFamilyName':'Lee','crewMemberGivenName':'Jisoo','effectDescription':'Personal spirits','quantityMeasure':measure(1,'LTR')}
        ]}}
    if doc_code == 'FAL5':
        return {'crewList': {'crewMembers': [
            {'personId':ident(f'CREW-{i+1:02d}-01'),'familyName':'Kim','givenName':'Minjun','dateOfBirth':f'198{i%10}-02-14','nationalityId':ident('KR','ISO3166-1-alpha2'),'sexCode':code('M'),'rankOrRating':'Master','travelDocumentId':ident(f'M{i+1:07d}'),'embarkationPortCode':code(s['departurePortCode'],'UNLOCODE')},
            {'personId':ident(f'CREW-{i+1:02d}-02'),'familyName':'Lee','givenName':'Jisoo','dateOfBirth':f'199{i%10}-07-08','nationalityId':ident('KR','ISO3166-1-alpha2'),'sexCode':code('F'),'rankOrRating':'Chief Officer','travelDocumentId':ident(f'C{i+1:07d}'),'embarkationPortCode':code(s['departurePortCode'],'UNLOCODE')},
            {'personId':ident(f'CREW-{i+1:02d}-03'),'familyName':'Park','givenName':'Seojun','dateOfBirth':f'199{i%10}-11-23','nationalityId':ident('KR','ISO3166-1-alpha2'),'sexCode':code('M'),'rankOrRating':'Chief Engineer','travelDocumentId':ident(f'E{i+1:07d}'),'embarkationPortCode':code(s['departurePortCode'],'UNLOCODE')}
        ]}}
    if doc_code == 'FAL6':
        return {'passengerList': {'passengers': [
            {'personId':ident(f'PAX-{i+1:02d}-01'),'familyName':'Choi','givenName':'Yuna','dateOfBirth':'1992-04-11','nationalityId':ident('KR','ISO3166-1-alpha2'),'sexCode':code('F'),'travelDocumentId':ident(f'P{i+1:07d}'),'embarkationPortCode':code(s['departurePortCode'],'UNLOCODE'),'disembarkationPortCode':code(s['arrivalPortCode'],'UNLOCODE'),'transitIndicator':False},
            {'personId':ident(f'PAX-{i+1:02d}-02'),'familyName':'Han','givenName':'Daniel','dateOfBirth':'1988-09-19','nationalityId':ident('KR','ISO3166-1-alpha2'),'sexCode':code('M'),'travelDocumentId':ident(f'Q{i+1:07d}'),'embarkationPortCode':code(s['departurePortCode'],'UNLOCODE'),'disembarkationPortCode':code(s['arrivalPortCode'],'UNLOCODE'),'transitIndicator':False}
        ]}}
    if doc_code == 'FAL7':
        return {'dangerousGoodsManifest': {'items': [
            {'itemSequenceNumber':1,'unNumberId':ident('UN1203'),'properShippingName':'GASOLINE','dangerousGoodsClassCode':code('3'),'packingGroupCode':code('II'),'emsCode':code('F-E,S-E'),'flashPointMeasure':measure(-43,'CEL'),'marinePollutantIndicator':False,'stowagePositionId':ident(f'BAY-{10+i:02d}-02-82'),'transportEquipmentId':ident(f'RDGU{i+1:07d}'),'shipperReferenceId':ident(f'DG-{s["imo"]}-{i+1:02d}')}
        ]}}
    if doc_code == 'MAIL':
        return {'mailDeliveryBill': {
            'originOfficeId':ident(f'KR{i+1:04d}'),'originOfficeName':f'Origin Exchange Office {i+1}',
            'destinationOfficeId':ident(f'DS{i+1:04d}'),'destinationOfficeName':f'Destination Exchange Office {i+1}',
            'mailCategoryCode':code('A'),'transportEquipmentId':ident(f'MAILU{i+1:07d}'),'sealId':ident(f'SEAL-{i+1:05d}'),
            'numberOfLetterPostReceptacles':30+i,'numberOfParcelReceptacles':10+i,'numberOfEmptyBagSacks':4+i,
            'letterPostGrossWeightMeasure':measure(420.5+i*5,'KGM'),'parcelGrossWeightMeasure':measure(650.0+i*7,'KGM'),'emptyReceptacleGrossWeightMeasure':measure(35.2+i,'KGM'),
            'observations':'Synthetic UPU mail consignment sample.'
        }}
    if doc_code == 'MDH':
        illness = []
        if i in (2,7):
            illness=[{'personId':ident(f'CREW-{i+1:02d}-02'),'illness':'Acute gastro-intestinal symptoms','symptomsOnsetDateTime':dt((base_dt-timedelta(hours=12)).isoformat().replace('+00:00','Z')),'reportedIndicator':True,'healthStatusCode':code('ILL'),'caseDispositionCode':code('ONB'),'treatment':'Oral rehydration and observation','comments':'Synthetic training case.'}]
        return {'maritimeDeclarationHealth': {
            'visitedAffectedAreaIndicator':False,'personDiedIndicator':False,'illPersonOnBoardIndicator':bool(illness),
            'illnessCases':illness,'medicalOfficerContactedIndicator':bool(illness),'sanitaryMeasuresApplied':'Routine sanitation procedures maintained.'
        }}
    if doc_code == 'SSC':
        return {'shipSanitationCertificate': {
            'certificateId':ident(f'SSC-{s["imo"]}-2026'),'certificateTypeCode':code('SSC'),'issueDate':'2026-06-15','expiryDate':'2026-12-15','issueLocationCode':code(s['departurePortCode'],'UNLOCODE'),
            'extensionExpirationDate':None,'controlMeasuresAppliedIndicator':False,'controlMeasuresAppliedComments':'No additional control measures required.','conditionComments':'No evidence of public-health risk observed in synthetic inspection sample.'
        }}
    if doc_code == 'SEC':
        return {'securityReport': {
            'currentSecurityLevelCode':code('1'),'shipSecurityPlanApprovedIndicator':True,'validCertificateIndicator':True,'certificateIssuerFlagStateId':ident(s['flagCode'],'ISO3166-1-alpha2'),
            'internationalShipSecurityCertificateId':ident(f'ISSC-{s["imo"]}'),'companySecurityOfficer':{'name':f'CSO Sample {i+1}','telephone':f'+82-2-555-{2000+i:04d}','email':f'cso{i+1}@example.invalid'},
            'previousPortSecurityLevels':[{'portCode':code(s['departurePortCode'],'UNLOCODE'),'securityLevelCode':code('1')}],
            'shipToShipActivities':[{'sequenceNumber':1,'activityTypeCode':code('NONE'),'description':'No ship-to-ship security-relevant activity in sample period.'}]
        }}
    if doc_code == 'WASTE':
        return {'advanceNotificationWasteDelivery': {
            'lastWasteDeliveryPortCode':code(s['departurePortCode'],'UNLOCODE'),'nextWasteDeliveryPortCode':code(s['arrivalPortCode'],'UNLOCODE'),'wasteDeliveryPlannedIndicator':True,
            'wasteEntries':[{'wasteTypeCode':code('MARPOL-I'),'description':'Oily bilge water','onBoardQuantityMeasure':measure(3.2+i*0.1,'MTQ'),'maximumStorageCapacityMeasure':measure(12.0,'MTQ'),'plannedDeliveryQuantityMeasure':measure(3.0+i*0.1,'MTQ'),'estimatedRemainingQuantityMeasure':measure(0.2,'MTQ')},
                            {'wasteTypeCode':code('MARPOL-V'),'description':'Domestic waste','onBoardQuantityMeasure':measure(1.1+i*0.05,'MTQ'),'maximumStorageCapacityMeasure':measure(5.0,'MTQ'),'plannedDeliveryQuantityMeasure':measure(1.0+i*0.05,'MTQ'),'estimatedRemainingQuantityMeasure':measure(0.1,'MTQ')}]
        }}
    raise KeyError(doc_code)

# dirs
for p in ['samples/datasets','docs/api/v1/ships','docs/api/v1/datasets','docs/schemas','scripts']:
    (ROOT/p).mkdir(parents=True, exist_ok=True)
(ROOT/'.nojekyll').write_text('', encoding='utf-8')
(ROOT/'docs/.nojekyll').write_text('', encoding='utf-8')

manifest = {'profile':'RD24001-IMO-FAL-UNCEFACT-JSON-SAMPLE-1.0','imoCompendiumVersion':'FAL.5/Circ.56','syntheticSamples':True,'shipCount':10,'datasetCount':len(DATASETS),'sampleFileCount':10*len(DATASETS),'datasets':[]}
ship_index = []

# create data
for si, s in enumerate(ships):
    ship_entry = {'imo':s['imo'],'shipName':s['name'],'flagState':s['flagCode'],'shipTypeName':s['shipTypeName'],'indexUrl':f'./{s["imo"]}/index.json'}
    ship_index.append(ship_entry)
    ship_docs_dir = ROOT/'docs/api/v1/ships'/s['imo']
    ship_docs_dir.mkdir(parents=True, exist_ok=True)
    per_ship = {'imo':s['imo'],'shipName':s['name'],'syntheticSample':True,'reports':[]}
    for slug, code_, name, phase in DATASETS:
        d = common(code_, name, slug, s, si)
        d.update(payload_for(code_, s, si))
        # source sample
        sd = ROOT/'samples/datasets'/slug
        sd.mkdir(parents=True, exist_ok=True)
        (sd/f'{s["imo"]}.json').write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
        # ship api copy
        (ship_docs_dir/f'{slug}.json').write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
        per_ship['reports'].append({'datasetCode':code_,'datasetName':name,'datasetSlug':slug,'url':f'./{slug}.json'})
    (ship_docs_dir/'index.json').write_text(json.dumps(per_ship, ensure_ascii=False, indent=2), encoding='utf-8')

# dataset APIs
for slug, code_, name, phase in DATASETS:
    dd = ROOT/'docs/api/v1/datasets'/slug
    dd.mkdir(parents=True, exist_ok=True)
    samples=[]
    for s in ships:
        src = ROOT/'samples/datasets'/slug/f'{s["imo"]}.json'
        dst = dd/f'{s["imo"]}.json'
        shutil.copyfile(src,dst)
        samples.append({'imo':s['imo'],'shipName':s['name'],'url':f'./{s["imo"]}.json'})
    idx={'datasetCode':code_,'datasetName':name,'datasetSlug':slug,'reportingPhase':phase,'syntheticSamples':True,'sampleCount':10,'samples':samples}
    (dd/'index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest['datasets'].append({'datasetCode':code_,'datasetName':name,'datasetSlug':slug,'reportingPhase':phase,'sampleCount':10,'indexUrl':f'./datasets/{slug}/index.json'})

(ROOT/'docs/api/v1/ships/index.json').write_text(json.dumps({'shipCount':10,'syntheticSamples':True,'ships':ship_index},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/api/v1/datasets/index.json').write_text(json.dumps({'datasetCount':len(DATASETS),'datasets':manifest['datasets']},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/api/v1/index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'samples/ships.json').write_text(json.dumps(ships,ensure_ascii=False,indent=2),encoding='utf-8')

# Schemas (implementation profile, intentionally not claiming official normative schema)
common_schema = {
 '$schema':'https://json-schema.org/draft/2020-12/schema',
 '$id':'https://example.invalid/rd24001/schemas/common.schema.json',
 'title':'RD24001 IMO Compendium Sample Common Envelope',
 'type':'object',
 'required':['sampleMetadata','messageHeader','ship','voyage','imoDataReferences'],
 'properties':{
  'sampleMetadata':{'type':'object','required':['syntheticSample','profileId','imoCompendiumVersion','datasetCode','datasetName'],'properties':{'syntheticSample':{'const':True},'profileId':{'type':'string'},'imoCompendiumVersion':{'const':'FAL.5/Circ.56'},'datasetCode':{'type':'string'},'datasetName':{'type':'string'}}},
  'messageHeader':{'type':'object'},'ship':{'type':'object','required':['imoShipNumberId','shipName']},'voyage':{'type':'object'},'imoDataReferences':{'type':'object'}
 },
 'additionalProperties':True
}
(ROOT/'docs/schemas/common.schema.json').write_text(json.dumps(common_schema,ensure_ascii=False,indent=2),encoding='utf-8')

for slug, code_, name, phase in DATASETS:
    prop = {
      'FAL1':'generalDeclaration','FAL2':'cargoDeclaration','FAL3':'shipsStoresDeclaration','FAL4':'crewsEffectsDeclaration',
      'FAL5':'crewList','FAL6':'passengerList','FAL7':'dangerousGoodsManifest','MAIL':'mailDeliveryBill','MDH':'maritimeDeclarationHealth','SSC':'shipSanitationCertificate','SEC':'securityReport','WASTE':'advanceNotificationWasteDelivery'
    }[code_]
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':f'https://example.invalid/rd24001/schemas/{slug}.schema.json','title':f'RD24001 {name} sample schema','type':'object','required':['sampleMetadata','messageHeader','ship','voyage','imoDataReferences',prop],'properties':{'sampleMetadata':common_schema['properties']['sampleMetadata'],'messageHeader':{'type':'object'},'ship':common_schema['properties']['ship'],'voyage':{'type':'object'},'imoDataReferences':{'type':'object'},prop:{'type':'object'}},'additionalProperties':False}
    (ROOT/'docs/schemas'/f'{slug}.schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')

# OpenAPI describing static GET paths
openapi = '''openapi: 3.1.0
info:
  title: RD24001 IMO Compendium Static JSON Sample API
  version: 1.0.0
  description: >-
    Static GET API for synthetic IMO Compendium FAL.5/Circ.56 sample payloads.
    Hosted on GitHub Pages; no POST/PUT/PATCH operations are provided.
servers:
  - url: ./
paths:
  /api/v1/index.json:
    get:
      summary: API metadata
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/ships/index.json:
    get:
      summary: List sample ships
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/ships/{imo}/index.json:
    get:
      summary: List all reports for one ship
      parameters:
        - {name: imo, in: path, required: true, schema: {type: string, pattern: '^[0-9]{7}$'}}
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/ships/{imo}/{dataset}.json:
    get:
      summary: Get one dataset sample by ship IMO number
      parameters:
        - {name: imo, in: path, required: true, schema: {type: string, pattern: '^[0-9]{7}$'}}
        - {name: dataset, in: path, required: true, schema: {type: string}}
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/datasets/index.json:
    get:
      summary: List datasets
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/datasets/{dataset}/index.json:
    get:
      summary: List 10 ship samples in a dataset
      parameters:
        - {name: dataset, in: path, required: true, schema: {type: string}}
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
  /api/v1/datasets/{dataset}/{imo}.json:
    get:
      summary: Get one ship sample from a dataset
      parameters:
        - {name: dataset, in: path, required: true, schema: {type: string}}
        - {name: imo, in: path, required: true, schema: {type: string, pattern: '^[0-9]{7}$'}}
      responses:
        '200': {description: OK, content: {application/json: {schema: {type: object}}}}
'''
(ROOT/'docs/openapi.yaml').write_text(openapi,encoding='utf-8')

# Static explorer page
html = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RD24001 IMO JSON API</title><style>body{font-family:system-ui,sans-serif;max-width:1080px;margin:40px auto;padding:0 20px;line-height:1.55}code,pre{background:#f4f4f4;padding:2px 5px;border-radius:4px}pre{padding:12px;overflow:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}a{color:#0645ad}</style></head><body><h1>RD24001 IMO Compendium JSON Sample API</h1><p>FAL.5/Circ.56 기반의 <strong>가상 시험 데이터</strong>입니다. 공식 IMO normative JSON 메시지가 아닙니다.</p><p><a href="api/v1/index.json">API metadata</a> · <a href="api/v1/ships/index.json">Ships</a> · <a href="api/v1/datasets/index.json">Datasets</a> · <a href="openapi.yaml">OpenAPI</a></p><h2>Datasets</h2><div id="datasets">Loading…</div><h2>Ships</h2><div id="ships">Loading…</div><script>async function load(){const d=await fetch('api/v1/datasets/index.json').then(r=>r.json());document.getElementById('datasets').innerHTML='<table><tr><th>Code</th><th>Name</th><th>Samples</th></tr>'+d.datasets.map(x=>`<tr><td>${x.datasetCode}</td><td><a href="api/v1/datasets/${x.datasetSlug}/index.json">${x.datasetName}</a></td><td>${x.sampleCount}</td></tr>`).join('')+'</table>';const s=await fetch('api/v1/ships/index.json').then(r=>r.json());document.getElementById('ships').innerHTML='<table><tr><th>IMO</th><th>Name</th><th>Reports</th></tr>'+s.ships.map(x=>`<tr><td>${x.imo}</td><td>${x.shipName}</td><td><a href="api/v1/ships/${x.imo}/index.json">index.json</a></td></tr>`).join('')+'</table>';}load();</script></body></html>'''
(ROOT/'docs/index.html').write_text(html,encoding='utf-8')

# README
readme = f'''# RD24001 IMO Compendium JSON Sample API

IMO Compendium **FAL.5/Circ.56 (FAL 50, 2026)**의 선박 입출항/FAL·MSW 관련 12개 데이터셋을 대상으로 만든 **합성(synthetic) JSON 샘플 저장소**입니다.

- 데이터셋: {len(DATASETS)}개
- 시험선: 10척
- 원본 샘플: {len(DATASETS)*10}개 JSON
- 조회 방식: 선박 IMO 번호 기준 / 데이터셋 기준
- 게시 방식: GitHub Pages 정적 JSON GET API
- JSON 표현: UN/CEFACT JSON Schema NDR의 방향(일관된 lowerCamelCase, CCTS형 값+메타데이터 표현)을 참고한 **RD24001 구현 프로파일**

> 중요: 이 저장소의 JSON 구조는 IMO가 발행한 공식 normative JSON syntax가 아닙니다. IMO Compendium의 데이터셋과 확인 가능한 데이터 요소를 바탕으로 API 실증을 위해 구성한 예제 프로파일입니다. 모든 선박·인명·연락처·화물 값은 가상 데이터입니다.

## 1. 데이터셋

| 코드 | 데이터셋 | 샘플 수 |
|---|---|---:|
'''
for slug, code_, name, phase in DATASETS:
    readme += f'| `{code_}` | {name} | 10 |\n'
readme += '''
## 2. 디렉터리

```text
samples/datasets/<dataset-slug>/<IMO>.json      # 데이터셋별 10개 원본 샘플
docs/api/v1/ships/<IMO>/<dataset-slug>.json    # 선박 중심 API
docs/api/v1/datasets/<dataset-slug>/<IMO>.json # 데이터셋 중심 API
docs/schemas/                                  # JSON Schema 예제
docs/openapi.yaml                              # 정적 GET API 설명
```

## 3. GitHub 업로드 및 Pages API 게시

이 저장소에는 `.github/workflows/pages.yml`이 포함되어 있어 `main` 브랜치에 push될 때:

1. `scripts/validate_samples.py`로 120개 샘플을 검증하고
2. `docs/` 폴더를 GitHub Pages artifact로 업로드한 뒤
3. GitHub Pages에 정적 JSON API를 배포합니다.

GitHub 저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정합니다.

Pages 주소가 `https://<USER>.github.io/<REPO>/`라면 API base URL은 다음과 같습니다.

```text
https://<USER>.github.io/<REPO>/api/v1
```

Windows에서 GitHub CLI(`gh`)가 설치되고 로그인되어 있다면 저장소 루트에서 다음 스크립트로 repository 생성/업로드/Pages 설정을 한 번에 수행할 수 있습니다.

```powershell
.\\scripts\\publish_to_github.ps1 -RepoName rd24001-imo-compendium-json-api -Visibility public
```

> GitHub Pages는 Python/FastAPI 서버를 실행하는 서비스가 아니므로 이 저장소의 API는 **read-only 정적 GET API**입니다. POST/검색/DB 연계가 필요하면 동일 JSON을 FastAPI 등의 런타임에 배포해야 합니다.

## 4. API 예시

전체 시험선:

```text
GET /api/v1/ships/index.json
```

특정 선박의 보고서 목록:

```text
GET /api/v1/ships/9300013/index.json
```

특정 선박의 Cargo Declaration:

```text
GET /api/v1/ships/9300013/fal2-cargo-declaration.json
```

Cargo Declaration 데이터셋의 10척 목록:

```text
GET /api/v1/datasets/fal2-cargo-declaration/index.json
```

Cargo Declaration에서 한 선박 조회:

```text
GET /api/v1/datasets/fal2-cargo-declaration/9300013.json
```

PowerShell 호출 예:

```powershell
$base = "https://<USER>.github.io/<REPO>/api/v1"
Invoke-RestMethod "$base/ships/index.json"
Invoke-RestMethod "$base/ships/9300013/fal1-general-declaration.json"
```

## 5. GitHub CLI 수동 업로드

자동 게시 스크립트를 사용하지 않는 경우 다음과 같이 직접 업로드할 수 있습니다.

```powershell
git init
git add .
git commit -m "Initial IMO Compendium JSON sample API"
git branch -M main
gh repo create rd24001-imo-compendium-json-api --public --source=. --remote=origin --push
```

업로드 후 **Settings → Pages → Source → GitHub Actions**를 선택합니다. 포함된 Pages workflow를 수동 실행하거나 `main`에 다시 push하면 배포됩니다.

## 6. 검증

```powershell
python .\\scripts\\validate_samples.py
```

검증 항목은 12개 데이터셋 각각 10개 파일 존재 여부, 동일 10개 IMO 번호 사용 여부, IMO 체크디지트, 공통 필드 및 `syntheticSample=true` 여부입니다.

## 7. 적용성 주의

12개 데이터셋이 한 항차에서 모두 항상 제출되는 것은 아닙니다. Passenger List, Dangerous Goods Manifest, Mail Consignment 등은 선박·화물·운항 상황에 따라 적용 여부가 달라집니다. 이 저장소는 API와 데이터 모델 실증을 위해 각 데이터셋에 10개 예시를 의도적으로 제공합니다.
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')

source_notes = '''# Source notes

## IMO Compendium

- Current baseline used: FAL.5/Circ.56, approved at FAL 50 (23-27 March 2026).
- IMO Compendium current site: https://imocompendium.imo.org/public/IMO-Compendium/Current/in1.htm
- Dataset contents: https://imocompendium.imo.org/public/IMO-Compendium/Current/content.htm

The 12 dataset scope used by this RD24001 package follows the project source material:
General Declaration; Cargo Declaration; Ship's Stores Declaration; Crew's Effects Declaration; Crew List; Passenger List; Dangerous Goods Manifest; Delivery Bill for Mail Consignment; Maritime Declaration of Health; Ship Sanitation Certificate; Security Report; Advance Notification for Waste Delivery.

Verified IMO Data Numbers included in `imoDataReferences` were taken from current/draft Compendium dataset pages where the element was directly visible. Fields without a verified Data Number are intentionally left without invented IMO numbers.

## UN/CEFACT JSON

- JSON Schema Naming and Design Rules v1.0: https://unece.org/trade/trade-facilitation-and-e-businessuncefact/json-schema-naming-and-design-rules

This repository uses an implementation profile inspired by the UN/CEFACT JSON NDR. It is not represented as an official UN/CEFACT or IMO normative schema.

## GitHub Pages

- GitHub Pages can publish static files from `/docs` on a branch.
- GitHub Pages does not run Python server-side applications; therefore this repository exposes read-only JSON GET endpoints as static files.
'''
(ROOT/'SOURCE_NOTES.md').write_text(source_notes,encoding='utf-8')

# validation script
validator = '''import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATASETS=[p for p in (ROOT/'samples/datasets').iterdir() if p.is_dir()]
assert len(DATASETS)==12, f"expected 12 datasets, got {len(DATASETS)}"

def valid_imo(v):
    return bool(re.fullmatch(r"\\d{7}",v)) and sum(int(d)*w for d,w in zip(v[:6],[7,6,5,4,3,2]))%10==int(v[6])
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
'''
(ROOT/'scripts/validate_samples.py').write_text(validator,encoding='utf-8')

# checksums
rows=[]
for f in sorted((ROOT/'samples/datasets').rglob('*.json')):
    h=hashlib.sha256(f.read_bytes()).hexdigest()
    rows.append(f'{h}  {f.relative_to(ROOT).as_posix()}')
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')

print('Generated', ROOT)
print('IMOs', imos)
print('source sample files', len(list((ROOT/'samples/datasets').rglob('*.json'))))
print('api json files', len(list((ROOT/'docs/api').rglob('*.json'))))
