"""Data-quality flag workbook. Usage: python build_dq.py 2026-Q3"""
import json,glob,re,datetime,collections,sys
from common import parse_quarter, workdir, tags, load_pages, pulldate
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
year,QN=parse_quarter(sys.argv[1]); WD=workdir(year,QN); CUR,PREV=tags(year,QN); TODAY=datetime.date.today(); PD=pulldate()
def load(ds): return load_pages(WD, ds)
def q(d):
    if not d: return None
    y,m=int(d[:4]),int(d[5:7]); return f'{y} Q{(m-1)//3+1}'
LEGACY={'1-10','1-24','100-499','500-999','1000+'}
REMOVE={'Individual Appointment','PPL','Do not offer procedure/service','Existing Client - Non-Sales Inquiry'}
PPL_RE=re.compile(r'^(ppl|pll|ppl\.|p\.p\.l|self|individual|me|myself|n/?a|none|personal|home care|homecare)$',re.I)
LEAD_FLAGS=[
 ('L01','Unqualified MQL with blank Unqualified Reason','Breaks the unqualified-reason table and the Net MQL bridge'),
 ('L02','Lost Lead MQL with blank Lost Lead Reason','Breaks the lost-reason table (speed-to-lead vs competitive split)'),
 ('L03','MQL with blank Lead Source','Channel attribution gap'),
 ('L04','MQL with Lead Category UNKNOWN or blank','Lands in the Unknown bucket on the channel charts'),
 ('L05','Legacy screening-size picklist value','1-10 / 1-24 / 100-499 / 500-999 / 1000+ need mapping to current buckets'),
 ('L06','MQL flagged Personal Email Likely','Likely individual, check whether it should be Net MQL'),
 ('L07','MQL whose Company reads as an individual (PPL / Self / N/A)','Should be unqualified as PPL or Individual Appointment'),
 ('L08','Converted MQL with no Converted Opportunity','Converted to account/contact only; counts as a conversion but adds $0 pipeline'),
 ('L09','Converted lead that is NOT an MQL','Shows in opportunity-side totals but not in MQL funnel'),
 ('L10','Converted MQL with SQL Count = 0','Carries an unqualified reason that removes it from Net MQL despite converting'),
 ('L11','MQL still in Needs Outreach (Not Aware)','Is MQL? true but never worked; inflates MQL count'),
 ('L12','Unqualified/Lost reason set but Status does not match','Reason field left over from a prior status'),
 ('L13','Lead with blank Email','Cannot be matched to HubSpot or de-duplicated'),
 ('L14','Net MQL = true but Status Unqualified with a removal reason','Net MQL formula and reason disagree; check MQL Override'),
]
OPP_FLAGS=[
 ('O01','Blank Lead Category','Created directly on the account; invisible in channel splits'),
 ('O02','Lead Category case/label variant (Organic, Other)','Will not roll into ORGANIC / OTHER unless normalized'),
 ('O03','Blank, zero or placeholder ($1) Amount','Distorts pipeline and deal-size averages'),
 ('O04','Closed Won with blank New Close Date','Falls out of revenue-by-period on New Close Date'),
 ('O05','Closed Won with future New Close Date','Not closed-to-date; exclude or footnote'),
 ('O06','Closed Won where Close Date quarter differs from New Close Date quarter','Standard vs New Close Date reconciliation item'),
 ('O07','Closed Lost / Lost Opportunity with blank New Close Date','Lost-in-period views on New Close Date will miss it'),
 ('O08','Blank Lead Source','Channel attribution gap'),
 ('O09','Open opportunity with Close Date in the past','Stale pipeline'),
 ('O10','Lost Opportunity with blank Lost Opportunity Reason','Win/loss reason table incomplete'),
 ('O11','Blank Type','New vs Upsell split incomplete. Note: Revenue Type (Ongoing / One Time) is blank on 100% of records in every dataset, so it is not flagged per record'),
 ('O12','Blank Account','Orphan opportunity'),
 ('O13','Is MQL? false but inbound Lead Source (Lead Gen Form / Qualified.com / Inbound Phone)','Rep-created inbound deal with no lead behind it; Lead reports undercount this'),
]
def lead_flags(r):
    f=[]; mql=bool(r['Is_MQL__c']); st=r['Status']
    if mql and st=='Unqualified' and not r['Unqualified_Reasons__c']: f.append(('L01',''))
    if mql and st=='Lost Lead' and not r['Lost_Lead_Reasons__c']: f.append(('L02',''))
    if mql and not r['LeadSource']: f.append(('L03',''))
    if mql and (r['Lead_Category__c'] in (None,'','UNKNOWN')): f.append(('L04',r['Lead_Category__c'] or '(blank)'))
    if r['Estimated_Employee_Size__c'] in LEGACY: f.append(('L05',r['Estimated_Employee_Size__c']))
    if mql and r.get('Personal_Email_Likely__c'): f.append(('L06',r.get('Email') or ''))
    c=(r.get('Company') or '').strip()
    if mql and (not c or PPL_RE.match(c)): f.append(('L07',c or '(blank)'))
    if mql and r['IsConverted'] and not r.get('ConvertedOpportunityId'): f.append(('L08',''))
    if (not mql) and r['IsConverted']: f.append(('L09',''))
    if mql and r['IsConverted'] and not (r.get('SQL_Count__c') or 0): f.append(('L10',r['Unqualified_Reasons__c'] or ''))
    if mql and st=='Not Aware': f.append(('L11',''))
    if (r['Unqualified_Reasons__c'] and st!='Unqualified') or (r['Lost_Lead_Reasons__c'] and st!='Lost Lead'):
        f.append(('L12',f"Status={st}; Unq={r['Unqualified_Reasons__c'] or ''}; Lost={r['Lost_Lead_Reasons__c'] or ''}"))
    if not r.get('Email'): f.append(('L13',''))
    if mql and st=='Unqualified' and r['Unqualified_Reasons__c'] in REMOVE and r['Net_MQL__c']: f.append(('L14',r['Unqualified_Reasons__c']))
    return f
INBOUND={'Inbound Website (Lead Gen Form)','Qualified.com','Inbound Phone Call'}
def opp_flags(r):
    f=[]; st=r['StageName']; ncd=r.get('New_Close_Date__c'); cd=r.get('CloseDate'); amt=r.get('Amount'); lc=r.get('Lead_Category__c')
    if not lc: f.append(('O01','(blank)'))
    elif lc!=lc.upper(): f.append(('O02',lc))
    if amt is None or amt<=1: f.append(('O03','(blank)' if amt is None else amt))
    if st=='Closed Won' and not ncd: f.append(('O04',''))
    if st=='Closed Won' and ncd and ncd>TODAY.isoformat(): f.append(('O05',ncd))
    if st=='Closed Won' and ncd and cd and q(ncd)!=q(cd): f.append(('O06',f'CloseDate {cd} vs NewClose {ncd}'))
    if st in ('Closed Lost','Lost Opportunity') and not ncd: f.append(('O07',''))
    if not r.get('LeadSource'): f.append(('O08',''))
    if not r['IsClosed'] and cd and cd<TODAY.isoformat(): f.append(('O09',cd))
    if st=='Lost Opportunity' and not r.get('Lost_Opportunity_Reason__c'): f.append(('O10',''))
    if not r.get('Type'): f.append(('O11','(blank)'))
    if not r.get('AccountId'): f.append(('O12',''))
    if (not r.get('Is_MQL__c')) and r.get('LeadSource') in INBOUND: f.append(('O13',r['LeadSource']))
    return f
QL=f'Q{QN} {year}'; PL=f'Q{QN} {year-1}'
DS=[(f'lead_{CUR}',f'Leads {QL}','lead'),(f'lead_{PREV}',f'Leads {PL}','lead'),
    (f'opp_created_{CUR}',f'Opps created {QL}','opp'),(f'opp_closed_{CUR}',f'Opps closed {QL}','opp'),
    (f'opp_created_{PREV}',f'Opps created {PL}','opp'),(f'opp_closed_{PREV}',f'Opps closed {PL}','opp')]
wb=Workbook(); F=Font(name='Arial',size=10); H=Font(name='Arial',size=10,bold=True,color='FFFFFF'); HF=PatternFill('solid',fgColor='1F3864')
summ=wb.active; summ.title='Summary'
detail_sheets={}
for ds,title,kind in DS:
    rows=load(ds); ws=wb.create_sheet(title[:31]); detail_sheets[ds]=ws
    if kind=='lead':
        hdr=['Flag code','Flag','Lead Id','Name','Company','Created Date (UTC)','Status','Lead Category','Lead Source','Is MQL?','Net MQL','Converted','Flagged value']
    else:
        hdr=['Flag code','Flag','Opp Id','Opportunity Name','Stage','Amount','Created Date (UTC)','Close Date','New Close Date','Lead Category','Lead Source','Type','Flagged value']
    ws.append(hdr)
    fl=dict((c,(d)) for c,d,_ in (LEAD_FLAGS if kind=='lead' else OPP_FLAGS))
    n=0
    for r in rows:
        for code,val in (lead_flags(r) if kind=='lead' else opp_flags(r)):
            n+=1
            if kind=='lead':
                ws.append([code,fl[code],r['Id'],r.get('Name'),r.get('Company'),r['CreatedDate'][:19].replace('T',' '),r['Status'],r.get('Lead_Category__c'),r.get('LeadSource'),bool(r['Is_MQL__c']),bool(r['Net_MQL__c']),bool(r['IsConverted']),val])
            else:
                ws.append([code,fl[code],r['Id'],r.get('Name'),r['StageName'],r.get('Amount'),r['CreatedDate'][:19].replace('T',' '),r.get('CloseDate'),r.get('New_Close_Date__c'),r.get('Lead_Category__c'),r.get('LeadSource'),r.get('Type'),val])
    for c in ws[1]: c.font=H; c.fill=HF
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font=F
    widths=[9,52,20,32,30,20,20,14,28,9,9,10,40] if kind=='lead' else [9,52,20,44,22,12,20,12,14,14,28,10,40]
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    if kind=='opp':
        for row in ws.iter_rows(min_row=2,min_col=6,max_col=6):
            for c in row: c.number_format='$#,##0'
    print(title,'records',len(rows),'flag rows',n)
# Summary
summ.append([f'Data quality flags: {QL} Marketing Recap static exports (pulled {PD})']); summ['A1'].font=Font(name='Arial',size=12,bold=True)
summ.append(['Counts are COUNTIF formulas against each detail tab. One row per record per flag, so a record can appear under several flags.'])
summ.append([])
hdr=['Code','Flag','Why it matters']+[t for _,t,_ in DS]
summ.append(hdr)
hr=summ.max_row
for c in summ[hr]: c.font=H; c.fill=HF
def add(flags,kinds):
    for code,desc,why in flags:
        row=[code,desc,why]
        for ds,title,kind in DS:
            if kind in kinds:
                row.append(f"=COUNTIF('{title[:31]}'!$A:$A,\"{code}\")")
            else: row.append('')
        summ.append(row)
summ.append(['LEAD FLAGS']); summ.cell(summ.max_row,1).font=Font(name='Arial',size=10,bold=True)
add(LEAD_FLAGS,{'lead'})
summ.append(['OPPORTUNITY FLAGS']); summ.cell(summ.max_row,1).font=Font(name='Arial',size=10,bold=True)
add(OPP_FLAGS,{'opp'})
summ.append([])
summ.append(['Records in dataset','','']+[len(load(ds)) for ds,_,_ in DS])
summ.append(['Total flag rows','','']+[f"=COUNTA('{t[:31]}'!A:A)-1" for _,t,_ in DS])
for row in summ.iter_rows(min_row=5):
    for c in row:
        if c.font!=H and not c.font.bold: c.font=F
for i,w in enumerate([8,62,70,14,14,16,16,16,16],1): summ.column_dimensions[get_column_letter(i)].width=w
for row in summ.iter_rows(min_row=4):
    for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
summ.freeze_panes='A5'
wb.save(f'{WD}/out/data_quality_flags_{PD}.xlsx'); print('saved', f'{WD}/out/data_quality_flags_{PD}.xlsx')
