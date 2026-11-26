# Tracker data builder (no LLM). Pulls Yahoo prices + quarterly financials (same endpoints the page uses live),
# merges hand-written config (ranges, tests, notes). Output: ../docs/data.json. Run from model/.
# Usage: python3 build_data.py            full refresh (prices + quarterly financials)
#        python3 build_data.py --prices   prices only; keeps the financials already in data.json
import json,subprocess,time,sys,os,datetime as d
B=json.load(open('own_history.json'))   # each company's own ten-year price/sales range (static)
OUTFILE='../docs/data.json';PRICES_ONLY='--prices' in sys.argv
OLD={}
if os.path.exists(OUTFILE):
    try:OLD={c['t']:c for c in json.load(open(OUTFILE))['companies']}
    except Exception:OLD={}
TYPES="quarterlyTotalRevenue,quarterlyGrossProfit,quarterlyOperatingCashFlow,quarterlyCapitalExpenditure,quarterlyStockBasedCompensation,quarterlyCashCashEquivalentsAndShortTermInvestments,quarterlyTotalDebt,quarterlyDilutedAverageShares,quarterlyOperatingIncome"
KEY=dict(quarterlyTotalRevenue='rev',quarterlyGrossProfit='gp',quarterlyOperatingCashFlow='ocf',quarterlyCapitalExpenditure='capex',quarterlyStockBasedCompensation='sbc',quarterlyCashCashEquivalentsAndShortTermInvestments='cash',quarterlyTotalDebt='debt',quarterlyDilutedAverageShares='sh',quarterlyOperatingIncome='oi')
def curl(u):
    for attempt in range(3):
        try:return json.loads(subprocess.run(['curl','-s','--max-time','30','-A','Mozilla/5.0',u],capture_output=True).stdout)
        except Exception:time.sleep(2+attempt*3)
    raise RuntimeError('fetch failed: '+u[:90])
def fin(t):
    p2=int(time.time());p1=p2-86400*800
    r=curl(f'https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{t}?type={TYPES}&period1={p1}&period2={p2}')['timeseries']['result']
    q={};cur='USD'
    for x in r:
        ty=x['meta']['type'][0]
        for v in x.get(ty) or []:
            if v:q.setdefault(v['asOfDate'],{})[KEY[ty]]=v['reportedValue']['raw'];cur=v.get('currencyCode') or cur if KEY[ty]=='rev' else cur
    return cur,[dict(d=k,**q[k]) for k in sorted(q) if 'rev' in q[k]][-5:]
def T(id,name,src,h,b,unit='%',low=False,core=False,note=None,lo=None,hi=None,v=None,asof=None):
    return dict(id=id,name=name,src=src,v=v,asof=asof,h=h,b=b,unit=unit,low=low,core=core,note=note,min=lo,max=hi)
Q3='Q3 2026 report'
def debt(h=2,b=4,core=False):return T('lev','Debt, in years of cash','lev',h,b,'yr',low=True,core=core,note='Net debt divided by a year of operating cash after stock pay. Below zero means more cash than debt.',lo=-2,hi=6)
G=lambda h,b,core=True,lo=0,hi=60,note=None:T('g','Sales growth','g',h,b,core=core,lo=lo,hi=hi,note=note)
OCM=lambda h,b,core=False:T('ocm','Owner-cash margin','ocm',h,b,core=core,note='Free cash flow minus stock pay, as a share of sales.',lo=0,hi=50)
SBC=lambda h,b,hi=35:T('sbc','Stock pay, share of sales','sbcm',h,b,low=True,note='Lower is better.',lo=0,hi=hi)
OUT=[]
def add(t,name,group,kind,top,bot,tests,why,catch,flag,basis,fair=None,disc=None,**extra):
    o=dict(t=t,name=name,group=group,kind=kind,top=round(top,3),bot=round(bot,3),disc=round(disc or top*1.43,3),fair=round(fair or top*1.77,3),tests=tests,why=why,catch=catch,flag=flag,basis=basis);o.update(extra);OUT.append(o)
# ---------------- growth software: company value / next-year sales
def growth(t,name,top,basis,why,catch,flag,more=()):
    add(t,name,'Growth software','sales',top,top*.66,[G(20,15)]+list(more)+[T('fcf','Free cash flow margin','fcfm',0.01,None,lo=-10,hi=40),SBC(22,25),T('nc','Cash minus debt','nc',0,None,'$B',note='Zero or more means it can repay its debt from cash.',lo=-5,hi=8)],why,catch,flag,basis)
NRR=lambda v,note='Spending by existing customers against a year ago.':T('nrr','Net retention','manual',110,105,note=note,lo=95,hi=135,v=v,asof=Q3)
growth('NET','Cloudflare',10,'Where the better software companies bottomed in 2022 to 2023 (6 to 10 times).','About a quarter of all websites sit behind it, and growth sped up to 39%.','The price assumes the bull case. Gross margin is slipping and its AI share of sales is undisclosed.','A large AI customer or a block of prepaid commitments cancels, or it stops reporting contracted growth.',
  more=[T('crpo','Contracted 12-month growth','manual',20,15,core=True,lo=0,hi=45,v=37,asof=Q3),NRR(122),T('gm','Gross margin','gm',69,67,core=True,note='Reported basis. The adjusted figure runs about a point higher.',lo=60,hi=80)])
OUT[-1].update(fair=17.7,disc=14.3,link='https://claude.ai/artifact/L8G51swtsNnrP5rsg4GZxx',linkLabel='Open the full Cloudflare tracker')
growth('DDOG','Datadog',8.9,'Its own multiple at the 2022 to 2023 low (8.9 times).','Sales are growing about 35% with real cash flow, and it holds far more cash than debt.','Its largest customer, an AI lab, cut usage in the third quarter. AI-native customers were 12% of sales a year earlier.','The largest customer falls below its contract minimum, or growth outside AI customers slows.',more=[NRR(120,'Reported as "low 120s". Spending by existing customers against a year ago.')])
growth('SNOW','Snowflake',9.2,'Its own multiple at the 2022 low (15.7 times), scaled down because growth is about 35% now against 60% then.','Product revenue is growing about 37% and existing customers spend 26% more than a year ago.','Stock pay takes about 30% of sales, so little cash is left for owners. Its AI-customer share is undisclosed.','Net retention falls below 115%, or stock pay stays above 30% of sales.',more=[NRR(126)])
growth('MDB','MongoDB',5.5,'Its own multiple at the 2022 low (6.0 times), scaled for slightly slower growth.','Sales are growing about 30% and it holds more cash than debt.','No retention or AI-customer figure is loaded yet.','Growth of Atlas, its cloud product, falls below 20% (29% at last report).',more=[T('atlas','Atlas growth','manual',20,15,lo=0,hi=45,v=29,asof='August 2026 report')])
growth('CRWD','CrowdStrike',7.8,'Its own multiple at the January 2023 low (7.8 times).','Record new business: net new recurring revenue grew 51% and recurring revenue 25%.','It trades far above the range.','Net new recurring revenue shrinks against a year earlier.',more=[T('arr','Recurring revenue growth','manual',20,15,lo=0,hi=50,v=25,asof='August 2026 report')])
# ---------------- application software: company value / owner cash
def app(t,name,top,why,catch,flag,gH=10,gB=8,more=(),**extra):
    add(t,name,'Application software','oc',top,top*.7,[G(gH,gB,hi=30)]+list(more)+[OCM(20,12,core=True),SBC(12,18,hi=25),debt()],why,catch,flag,extra.pop('basis',f'{top*.7:.0f} to {top:.0f} times owner cash, my judgment for a business growing at this rate.'),**extra)
app('ADBE','Adobe',20,'It turns about a third of sales into owner cash and raised its full-year guide.','Growth is about 13%, AI-first products are about 2% of recurring revenue, and a new chief executive starts December 1.','Sales growth below 8% for two quarters running.')
app('INTU','Intuit',20,'A high owner-cash margin, far below its high.','I have not researched why it fell. It dropped 20% in a day in May and 13% on November 20.','Sales growth below 8% for two quarters running.')
app('NOW','ServiceNow',20,'Subscription revenue is growing 21% and contracted backlog 20.5%.','It fell 27% on October 29 and my sources disagree on why. Stock pay is about 15% of sales.','Contracted backlog growth falls below 15%.',15,10,more=[T('crpo','Contracted 12-month backlog growth','manual',15,10,lo=0,hi=30,v=20.5,asof=Q3)])
app('CRM','Salesforce',15,'A solid owner-cash margin at a modest multiple.','Growth of about 11% includes an acquisition, and it carries real debt.','Growth without acquisitions falls below 7%.',8,5,more=[T('crpo','Contracted 12-month backlog growth','manual',10,7,note='Constant currency.',lo=0,hi=25,v=14,asof='August 2026 report')])
# ---------------- cloud and platform owners: company value / operating cash after stock pay
def cloud(t,name,why,catch,flag,more=()):
    add(t,name,'Cloud and platform owners','ocf',15,10,[G(10,5,hi=40)]+list(more)+[T('ocfm','Operating cash after stock pay, share of sales','ocfm',25,15,core=True,lo=0,hi=60),T('capex','Building spend, share of sales','capexm',25,40,low=True,note='Capital spending. Lower is better, and in a bust it can be cut.',lo=0,hi=55),T('fcfs','Free cash after stock pay, share of sales','ocm',0.01,None,note='What is left after the building spend.',lo=-15,hi=30),debt(1,3)],why,catch,flag,'10 to 15 times operating cash after stock pay. This measure ignores building spend, on the view that a bust lets these companies cut it.')
cloud('MSFT','Microsoft','It funds its AI build from its own cash flow and fell least on the bad days.','Building spend is a large share of sales, and much of its backlog depends on OpenAI.','Operating cash flow falls against a year earlier.')
cloud('GOOGL','Alphabet','Far more cash than debt, and Cloud revenue roughly doubled.','Search grew 12% and missed estimates because AI answers earn less. Free cash flow was negative in the third quarter.','Search growth falls below 5%.',more=[T('search','Search revenue growth','manual',8,4,lo=0,hi=20,v=12,asof=Q3)])
cloud('AMZN','Amazon','A record 13.9% operating margin, with its cloud unit growing 39%.','Building spend of about $220B leaves free cash flow negative. Two AI labs are estimated to be most of its AI revenue.','Cloud growth halves, or a large AI customer cannot pay.',more=[T('aws','Cloud revenue growth','manual',15,8,lo=0,hi=45,v=39,asof=Q3),T('om','Operating margin','manual',10,6,lo=0,hi=20,v=13.9,asof=Q3)])
cloud('META','Meta','Ad revenue grew 26%, with gains it attributes to its AI ranking.','Building spend is so large that almost no free cash is left.','Ad growth falls below 10% while building spend stays above 35% of sales.',more=[T('ads','Ad revenue growth','manual',10,5,lo=0,hi=35,v=26,asof=Q3)])
# ---------------- chip tools and chokepoints
CH='Chip tools and chokepoints'
def tool(t,name,why,catch,flag,more=(),basis='About 15 to 22 times owner cash, my judgment for a business with a backlog and few rivals.',**extra):
    add(t,name,CH,'oc',22,15.4,[G(10,5)]+list(more)+[OCM(18,10,core=True),SBC(12,18,hi=25),debt()],why,catch,flag,basis,**extra)
tool('SNPS','Synopsys','Chip designers pay it by subscription with multi-year backlogs, and I found no critic calling it an AI proxy.','It trades far above the range, and its growth may include an acquisition.','Backlog shrinks, or a large chip-design customer fails.')
tool('CDNS','Cadence','Record backlog of $7.8B at the end of 2025, sold by subscription to chip designers.','It trades far above the range.','Backlog shrinks, or a large chip-design customer fails.')
GM=lambda h,b,core=True:T('gm','Gross margin','gm',h,b,core=core,lo=30,hi=90)
add('ASML','ASML',CH,'op',18,12.6,[G(10,5),GM(50,45),T('opm','Operating margin','opm',30,20,core=True,lo=0,hi=50),debt()],'The only maker of the most advanced chip-printing machines, with more cash than debt.','Its sales are cyclical: they fell by roughly half in 2009. China was about a fifth of system sales.','A major chipmaker cuts orders, or export limits widen.','About 13 to 18 times operating profit, which matches the 15 to 22 times owner cash used for its group. Operating profit is used because customer prepayments make its cash flow jump around.',gBase=0.10,gBear=0.02)
tool('TSM','TSMC','It makes most of the world\'s leading-edge chips at a gross margin near 66%.','About 68% of sales now come from high-performance computing, and it spends heavily on new plants.','A large AI chip customer cuts orders, or plant spending outruns cash flow.',more=[GM(55,48),T('hpc','High-performance computing share of sales','manual',60,80,low=True,note='Concentration. Lower is safer.',lo=30,hi=100,v=68,asof=Q3),T('capex','Building spend, share of sales','capexm',35,45,low=True,note='Lower is better.',lo=0,hi=60)],cur='TWD',basis='About 15 to 22 times owner cash. Owner cash here is after its heavy plant spending.',gBase=0.12,gBear=0.03)
add('NVDA','Nvidia',CH,'oc',20,14,[GM(65,55),T('dc','Data-center share of sales','manual',60,85,low=True,note='Concentration. Lower is safer.',lo=30,hi=100,v=93,asof=Q3),OCM(25,15),G(0.01,-20,core=False,lo=-40,hi=120,note='For a cyclical supplier, wait until sales have actually fallen before trusting a low price.')],
 'Sales roughly doubled in a year at a gross margin near 75%.','About 93% of sales come from data centers, four customers were 61% of sales a year ago, and it carries $279B of supply commitments.','A major customer cannot pay, or the $108.5B of guarantees it has given are called.','20 times owner cash after cutting that cash by 40%. Chip-equipment sales fell about 60% in 2001 to 2002, so a cut is assumed. Deep prices only.',ocFactor=0.6,measureNote='after a 40% cut',gBase=0.10,gBear=0.0)
# ---------------- tech-side users
NOAI='I found no disclosed AI gain for it. It is here because it produces cash and does not pay for the AI build.'
def user(t,name,top,why,catch,flag):
    p=B[t].get('pctile');add(t,name,'Tech-side users','oc',top,top*.7,[G(8,3,lo=-5,hi=40),OCM(15,8,core=True),SBC(8,14,hi=20),debt()],why,catch,flag,f'{top*.7:.1f} to {top} times owner cash, my judgment for its growth rate.'+(f' On November 24 it also sat in the bottom {max(1,round(p*100))}% of its own ten-year price-to-sales range.' if p is not None else ''))
user('BKNG','Booking',15,'A high owner-cash yield with little debt. '+NOAI,'Sales growth has slowed sharply in the latest quarter.','AI travel agents start taking bookings away from it.')
OUT[-1]['tests'][0]=T('g','Sales growth, adjusted','manual',8,3,core=True,note='Reported sales fell 1% because of a one-off $900M cut tied to a regulator case. Without it sales grew 9%.',lo=-5,hi=40,v=9,asof=Q3)
OUT[-1]['catch']='Reported sales fell 1% on a one-off regulatory charge; without it they grew 9%. Growth is guided to slow next quarter.'
user('UBER','Uber',20,'A solid owner-cash yield, well below its high. '+NOAI,'Self-driving rivals could bypass its network.','A self-driving rival launches at scale without it.')
user('NFLX','Netflix',20,'Double-digit growth with a healthy owner-cash margin, far below its high. '+NOAI,'It is still above the range.','Subscriber or ad growth stalls.')
user('PYPL','PayPal',15,'A low multiple of owner cash with little debt.','Sales are barely growing. It is cheap for a reason.','Sales shrink.')
user('ACN','Accenture',15,'Record bookings and more cash than debt.','Clients are demanding that AI savings be passed on in lower prices.','Sales shrink for two quarters as prices fall.')
add('AAPL','Apple','Tech-side users','oc',20,14,[G(5,0,lo=-10,hi=30),GM(42,38,core=False),OCM(20,12,core=True),SBC(8,14,hi=20),debt()],'A huge installed base of devices and services, with very little spent on the AI build. '+NOAI,'It trades far above the range, close to its 52-week high.','iPhone sales fall for a year, or a court ruling cuts its App Store or search-deal income.','14 to 20 times owner cash, my judgment for its growth rate.')
# ---------------- blue chips: price / sales against own ten years
REF='It is a refuge today, so it only becomes a fat pitch if the bust turns into a credit crisis.'
def blue(t,name,why,catch,flag,group='Blue chips',gH=2,gB=0):
    r=B[t];add(t,name,group,'ps',r['hlo'],r['hlo']*.75,[G(gH,gB,lo=-10,hi=30),OCM(10,6),debt(3,4,core=True),T('yld','Owner-cash yield','yld',4,2,note='Owner cash divided by company value. Higher is cheaper.',lo=0,hi=10)],why,catch,flag,
        f'Its own range since 2016. The fat pitch starts at the low tenth ({r["hlo"]:.1f} times sales) and the middle is {r["hmed"]:.1f}.',fair=r['hmed'],disc=(r['hlo']+r['hmed'])/2)
blue('PG','Procter & Gamble','Steady sales and very little debt.',REF,'Debt rises above 3 years of cash, or sales shrink.')
blue('MA','Mastercard','A very high owner-cash margin, double-digit growth and little debt.',REF,'Payment volume shrinks, or a rival payment rail takes share.',gH=8,gB=4)
blue('LMT','Lockheed Martin','A good owner-cash yield and modest debt.',REF,'A large program is cancelled.')
blue('UNP','Union Pacific','A railroad with a high owner-cash margin.',REF+' Its debt sits near the edge of my limit.','Debt rises above 4 years of cash.')
blue('CVX','Chevron','A high owner-cash yield and little debt.','Its price-to-sales swings with the oil price, so this measure is weaker here.','Oil falls far enough that the dividend is not covered.')
blue('MCO','Moody\'s','A high owner-cash margin and modest debt.','Its bond-rating revenue is riding AI debt issuance, so a credit event would hit it directly.','Debt issuance dries up.')
blue('KO','Coca-Cola','A high owner-cash margin and a brand that came through every bust I checked.','In 2000 it was also expensive, and it took 8 years to regain its high.','Debt rises above 3 years of cash.')
blue('JNJ','Johnson & Johnson','Little debt, and it rose 66% during the dot-com bust.','It is priced near the top of its ten-year range.','A legal charge large enough to add debt.')
blue('UNH','UnitedHealth','Near the bottom of its own ten-year range.','Sales growth has stopped, and I have not researched why.','Sales shrink, or margins fall again.',group='Cheap, with a problem')
blue('NKE','Nike','Near the bottom of its own ten-year range, with little debt.','Sales are falling and owner cash is thin.','Sales keep falling for another year.',group='Cheap, with a problem')
# ---------------- grid and electrical
def grid(t,name,why,catch,flag):
    add(t,name,'Grid and electrical','oc',20,14,[G(8,0,lo=-10,hi=70),OCM(10,5),debt(3,4,core=True)],why,catch,flag,'14 to 20 times owner cash, my judgment for an industrial with a backlog.')
grid('ETN','Eaton','Backlog up 33%, across many kinds of electrical work.','It trades far above the range and does not disclose its data-center share.','Data-center orders are cancelled and backlog shrinks.')
grid('PWR','Quanta','A record backlog of about $64B, led by utilities.','It trades far above the range, and some data-center projects were reported sliding.','Backlog shrinks for two quarters.')
add('GEV','GE Vernova','Grid and electrical','op',18,12.6,[G(8,0,lo=-10,hi=60),T('opm','Operating margin','opm',8,4,core=True,note='Operating profit as a share of sales. It is rising fast from a low base.',lo=0,hi=25),
  T('firm','Gas pipeline that is firm orders','manual',60,40,note='Firm orders as a share of firm orders plus slot reservations: 64 of 122 gigawatts. Reservations can be cancelled.',lo=0,hi=100,v=52,asof=Q3),
  T('dc','Data-center share of gas customers','manual',30,50,low=True,note='Lower is safer in an AI bust.',lo=0,hi=100,v=20,asof=Q3),
  T('svc','Services backlog growth','manual',8,0,note='The steadier half of the business: about $93B of contracted service work, up 14% in a year. Service billings depend on how much the turbines run, and services revenue grew about 7% this year.',lo=-10,hi=30,v=14,asof=Q3),
  T('wind','Wind segment margin','manual',0.01,-8,note='Adjusted profit margin of the wind unit, its weak spot.',lo=-15,hi=15,v=2.6,asof=Q3),debt(3,4,core=True)],
 'Orders nearly doubled and its backlog is $197B, with about 80% of gas-turbine customers outside data centers.','Its cash flow is mostly customer deposits: $5.3B of the $5.4B free cash flow last quarter. On operating profit it trades far above the range. 58 gigawatts of its gas pipeline are reservations, not firm orders.','Turbine slot reservations are cancelled or fail to convert to firm orders, or a large data-center customer pulls out.',
 'About 13 to 18 times operating profit. Operating profit is used because customer deposits make its cash flow look far larger than its earnings.',gBase=0.25,gBear=0.08)
# ---------------- scout: a wider list screened with generic tests
SCOUT={'PEP':'PepsiCo','WMT':'Walmart','COST':'Costco','MCD':"McDonald's",'MO':'Altria','PM':'Philip Morris','CL':'Colgate-Palmolive','KMB':'Kimberly-Clark','GIS':'General Mills','MDLZ':'Mondelez','HSY':'Hershey','ABT':'Abbott','MRK':'Merck','PFE':'Pfizer','LLY':'Eli Lilly','ABBV':'AbbVie','AMGN':'Amgen','TMO':'Thermo Fisher','DHR':'Danaher','MDT':'Medtronic','XOM':'Exxon Mobil','COP':'ConocoPhillips','CSX':'CSX','WM':'Waste Management','RSG':'Republic Services','CAT':'Caterpillar','DE':'Deere','HON':'Honeywell','MMM':'3M','RTX':'RTX','GD':'General Dynamics','ADP':'ADP','HD':'Home Depot','LOW':"Lowe's",'SBUX':'Starbucks','DIS':'Disney','CMCSA':'Comcast','VZ':'Verizon','T':'AT&T','LIN':'Linde','SHW':'Sherwin-Williams','ECL':'Ecolab','V':'Visa','SPGI':'S&P Global','MSCI':'MSCI','CME':'CME Group','ICE':'Intercontinental Exchange','AAPL':'Apple','ABNB':'Airbnb','DASH':'DoorDash','SHOP':'Shopify','FICO':'Fair Isaac','VRSK':'Verisk','VEEV':'Veeva','ISRG':'Intuitive Surgical','IBM':'IBM','DUOL':'Duolingo','AXON':'Axon','AVGO':'Broadcom','AMD':'AMD','MRVL':'Marvell','ANET':'Arista','CSCO':'Cisco','AMAT':'Applied Materials','LRCX':'Lam Research','KLAC':'KLA','APH':'Amphenol','ZS':'Zscaler','PANW':'Palo Alto Networks','FTNT':'Fortinet','WDAY':'Workday','ORCL':'Oracle','VRT':'Vertiv','GEV':'GE Vernova'}
CYCLICAL={'XOM','COP','CAT','DE','AMAT','LRCX','KLAC','AMD','MRVL','AVGO','ANET','APH','VRT'}   # profits swing with a commodity or an investment cycle
have={o['t'] for o in OUT}
for t,name in SCOUT.items():
    if t in have:continue
    add(t,name,'Scout','oc',20,14,[G(3,0,lo=-10,hi=60),OCM(10,5,core=True),SBC(12,18,hi=30),debt(3,4,core=True)],'Not researched. It is on the wider list that the page screens with generic tests.','Generic tests can miss what matters for this company.','A problem specific to this company that the generic tests miss.','A generic 14 to 20 times owner cash. A company added to the watchlist gets its own range.',scout=True,cyc=t in CYCLICAL)
# ---------------- pull data
syms=[o['t'] for o in OUT]
px={}
for i in range(0,len(syms)+2,18):
    chunk=(syms+['EURUSD=X','TWD=X'])[i:i+18]
    if chunk:
        got=curl('https://query1.finance.yahoo.com/v8/finance/spark?symbols='+','.join(chunk)+'&range=1y&interval=1wk')
        if 'spark' in got and not got.get(chunk[0]):raise RuntimeError('price source refused: '+json.dumps(got)[:200])
        px.update(got)
fx=dict(EUR=px['EURUSD=X']['close'][-1],TWD=1/px['TWD=X']['close'][-1])
fails=0
for o in OUT:
    old=OLD.get(o['t'])
    if o['t'] in px and [x for x in px[o['t']]['close'] if x]:
        c=[x for x in px[o['t']]['close'] if x];o['price']=round(c[-1],2);o['hi']=round(max(c),2);o['w']=[round(x,2) for x in c]
    elif old:o['price'],o['hi'],o['w']=old['price'],old['hi'],old.get('w',[])
    else:print('  no price',o['t']);o['drop']=True;continue
    q=None
    if not PRICES_ONLY:
        try:
            cur,q=fin(o['t']);time.sleep(.15)
            if len(q)<4:q=None
        except Exception as ex:print('  no financials',o['t'],repr(ex)[:60]);fails+=1
    if q:o['cur']=cur;o['q']=q
    elif old and old.get('q'):o['cur']=old.get('cur','USD');o['q']=old['q']
    else:print('  dropped (no financials)',o['t']);o['drop']=True
if fails>len(OUT)/2:raise RuntimeError('financial source failed for most companies; keeping the old file')
OUT=[o for o in OUT if not o.get('drop')]
import os,glob
RS={}
for f in glob.glob('../notes/research/*.json'):
    try:
        j=json.load(open(f))
        for x in (j if isinstance(j,list) else [j]):
            if isinstance(x,dict) and x.get('t'):RS.setdefault(x['t'],{}).update(x)
    except Exception as ex:print('  bad research file',f,repr(ex)[:60])
for o in OUT:
    x=RS.get(o['t'])
    if x:o['rs']=x
now=d.datetime.now(d.timezone.utc)
prev={}
if os.path.exists(OUTFILE):
    try:prev=json.load(open(OUTFILE))
    except Exception:prev={}
fin_at=prev.get('finUpdated') if PRICES_ONLY else now.isoformat(timespec='seconds')
json.dump(dict(asof=now.date().isoformat(),updated=now.isoformat(timespec='seconds'),finUpdated=fin_at,fx=fx,companies=OUT),open(OUTFILE,'w'),separators=(',',':'))
print(len(OUT),'companies','prices only' if PRICES_ONLY else 'full',fx,'bytes',os.path.getsize(OUTFILE))
