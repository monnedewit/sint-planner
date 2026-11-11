import docx, re, json, datetime, uuid
MAANDEN={'november':11,'december':12}
t=docx.Document('/mnt/user-data/uploads/OVERZICHTSLIJST_SINT.docx').tables[0]
def cells(r):
    out=[];prev=None
    for c in r.cells:
        if c._tc is prev: continue
        prev=c._tc; out.append(c.text)
    return out
def lines(s): return [l.strip() for l in s.split('\n') if l.strip()]
def tm(s):
    m=re.search(r'(\d{1,2})[.:](\d{2})',s or '')
    return f"{int(m[1]):02d}:{m[2]}" if m else None
routes=[];datum=None;soort='regulier';vol=0
for r in t.rows[1:]:
    c=cells(r); first=' '.join(c[0].split())
    m=re.match(r'^(?:\w+dag)\s+(\d+)\s+(\w+)$',first)
    if len(c)==1 or (len(set(c))==1 and first):
        if m: datum=datetime.date(2026,MAANDEN[m[2]],int(m[1])).isoformat(); soort='regulier'
        elif first.lower().startswith('gezinnen'):
            soort='gezinnen'; g=re.search(r'(\d+)\s*[xX]',first)
        continue
    if len(c)<7 or not datum: continue
    loc_lines=lines(c[5]); plaats_lines=lines(c[4])
    if not (loc_lines or [l for l in lines(c[6]) if l not in('S','C','P1','P2')] or tm(c[2])): 
        if not any(re.match(r'[SCP]\d*;\s*\d',l) for l in lines(c[1])): 
            # lege rij in gezinnenblok = nog in te vullen route
            if not (soort=='gezinnen' and lines(c[1])): continue
    vol+=1
    aanw={}
    for l in lines(c[1]):
        m2=re.match(r'([SCP]);?:?\s*(.*)',l)
        if m2 and tm(m2[2]) and m2[1] not in aanw: aanw[m2[1]]=tm(m2[2])
    plekken=[];extra=[]
    cnt={'S':0,'C':0,'P':0}
    for l in lines(c[6]):
        m3=re.match(r'^([SCP])(\d*)\s*(.*)$',l)
        if not m3: extra.append(l); continue
        rol,nr,rest=m3[1],m3[2],re.sub(r'\s+',' ',m3[3]).strip()
        if rest.startswith('t/m') or re.match(r'^\d+\s*x',rest):
            extra.append(l); continue
        cnt[rol]+=1
        n=int(nr) if nr else cnt[rol]
        low=rest.lower().replace('.','')
        if low in('n v t','nvt','n.v.t','n.v.t.') or low.endswith('nvt'): st,p,vt='niet_nodig',None,None
        elif low in('eigen','zelf'): st,p,vt='eigen',None,None
        elif rest=='': st,p,vt='open',None,None
        else:
            if re.match(r'^[A-Z][a-z]+\s+[A-Za-z]',rest) and rol in('S','C','P') and not rest.lower() in('vader','zoon') and ' ' in rest and not rest.startswith(('eigen','vader','zoon')):
                st,p,vt='ingevuld',re.sub(r'\s*\?+','',rest),('?' if '?' in rest else None)
            else: st,p,vt='ingevuld',None,rest
        plekken.append(dict(rol=rol,nummer=n,status=st,persoon=p,vrije_tekst=vt))
    opm=' / '.join([' '.join(loc_lines[1:])]+extra).strip(' /')
    plaats=plaats_lines[0] if plaats_lines else None
    if len(plaats_lines)>1: opm=(opm+' / '+' '.join(plaats_lines[1:])).strip(' /')
    ag=re.search(r'\+\s*(\d+)\s*gezinnen',opm or '')
    routes.append(dict(datum=datum,soort=('regulier' if loc_lines else 'gezinnen'),aantal_gezinnen=int(ag[1]) if ag else None,volgorde=vol,locatie=(loc_lines[0] if loc_lines else None),
      plaats=plaats,aanwezig=aanw,vertrek=tm(c[2]),terug=tm(c[3]),terugkomst=tm(c[9]) if len(c)>9 else None,
      opmerking=opm or None,plekken=plekken))
json.dump(routes,open('data/routes.json','w'),ensure_ascii=False,indent=1)
# seed.sql
def q(v): return 'null' if v is None else "'"+str(v).replace("'","''")+"'"
personen={}
for r in routes:
    for p in r['plekken']:
        if p['persoon']: personen.setdefault(p['persoon'],set()).add({'S':'sint','C':'chauffeur','P':'piet'}[p['rol']])
sql=["-- Seed Nicolaasactie 2026 (gegenereerd uit OVERZICHTSLIJST_SINT.docx)","begin;",
"insert into acties(id,naam,jaar) values ('00000000-0000-0000-0000-0000000000a1','Nicolaasactie 2026',2026);"]
pid={}
for n,rl in sorted(personen.items()):
    pid[n]=str(uuid.uuid5(uuid.NAMESPACE_DNS,n))
    sql.append(f"insert into personen(id,naam,rollen) values ('{pid[n]}',{q(n)},'{{{','.join(sorted(rl))}}}');")
for r in routes:
    rid=str(uuid.uuid4()); a=r['aanwezig']
    sql.append(f"insert into routes(id,actie_id,datum,soort,volgorde,locatie,plaats,aanwezig_p,aanwezig_s,aanwezig_c,vertrek,terug,terugkomst,aantal_gezinnen,opmerking) values ('{rid}','00000000-0000-0000-0000-0000000000a1','{r['datum']}','{r['soort']}',{r['volgorde']},{q(r['locatie'])},{q(r['plaats'])},{q(a.get('P'))},{q(a.get('S'))},{q(a.get('C'))},{q(r['vertrek'])},{q(r['terug'])},{q(r['terugkomst'])},{q(r['aantal_gezinnen'])},{q(r['opmerking'])});")
    for p in r['plekken']:
        pp=f"'{pid[p['persoon']]}'" if p['persoon'] else 'null'
        sql.append(f"insert into plekken(route_id,rol,nummer,status,persoon_id,vrije_tekst) values ('{rid}','{p['rol']}',{p['nummer']},'{p['status']}',{pp},{q(p['vrije_tekst'])});")
sql.append("commit;")
open('db/seed.sql','w').write('\n'.join(sql)+'\n')
from collections import Counter
print(len(routes),'routes',len(personen),'personen')
print(Counter(r['soort'] for r in routes))
print('open C:',sum(1 for r in routes for p in r['plekken'] if p['rol']=='C' and p['status']=='open'))
print('open S:',sum(1 for r in routes for p in r['plekken'] if p['rol']=='S' and p['status']=='open'))
for r in routes[:3]+routes[-2:]: print(r['datum'],r['locatie'],r['plaats'],r['aanwezig'],[(p['rol']+str(p['nummer']),p['status'],p['persoon']) for p in r['plekken']])
