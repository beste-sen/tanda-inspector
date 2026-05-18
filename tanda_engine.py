
import pandas as pd
import numpy as np

def _num(x, default=0):
    try:
        if pd.isna(x): return default
        return float(x)
    except Exception:
        return default

def load_tracks(path='tango_tracks_dj_enriched_v2.csv'):
    df = pd.read_csv(path)
    for c in ['title','orchestra','singer','genre','style_tags']:
        if c in df.columns:
            df[c] = df[c].fillna('').astype(str)
    return df

def find_tracks(df, query, limit=20):
    q = str(query).lower().strip()
    if not q:
        return df.head(limit)
    mask = df['title'].str.lower().str.contains(q, na=False) | df['orchestra'].str.lower().str.contains(q, na=False) | df['singer'].str.lower().str.contains(q, na=False)
    return df[mask].head(limit)

def score_tanda(tanda):
    """tanda: DataFrame with 3-4 rows from track database."""
    if tanda is None or len(tanda) < 3:
        return {'score':0,'warnings':['En az 3 parça gerekli.'],'strengths':[],'metrics':{}}
    warnings=[]; strengths=[]
    n=len(tanda)
    orchestras=tanda['orchestra'].fillna('').astype(str).unique().tolist()
    genres=tanda['genre'].fillna('').astype(str).unique().tolist()
    singers=[s for s in tanda.get('singer',pd.Series(['']*n)).fillna('').astype(str).unique().tolist() if s]
    years=pd.to_numeric(tanda.get('year'), errors='coerce')
    energies=pd.to_numeric(tanda.get('energy'), errors='coerce')
    drams=pd.to_numeric(tanda.get('dramatic_level'), errors='coerce')
    walks=pd.to_numeric(tanda.get('walking_quality'), errors='coerce')
    rhy=pd.to_numeric(tanda.get('rhythmic_level'), errors='coerce')

    score=100
    if len(genres)>1:
        score-=45; warnings.append('Genre karışıyor: tango/vals/milonga aynı tandada olmamalı.')
    else:
        strengths.append('Genre tutarlı.')
    if len(orchestras)>1:
        score-=35; warnings.append('Orkestra tutarsızlığı var; tanda kimliği zayıflar.')
    else:
        strengths.append('Aynı orkestra kullanılmış.')
    if len(singers)>1 and len(singers)<n:
        score-=8; warnings.append('Solist değişimi var; vokal atmosferini kontrol et.')
    elif len(singers)==1:
        strengths.append('Solist atmosferi tutarlı.')
    if years.notna().sum()>=2:
        spread=int(years.max()-years.min())
        if spread>8:
            score-=18; warnings.append(f'Yıl aralığı geniş ({spread} yıl); kayıt estetiği kopabilir.')
        elif spread<=4:
            strengths.append('Dönem yakınlığı iyi.')
    else:
        spread=None
    def rng(s):
        s=s.dropna(); return float(s.max()-s.min()) if len(s) else 0
    e_rng=rng(energies); d_rng=rng(drams); w_avg=float(walks.mean()) if walks.notna().sum() else 0
    if e_rng>3:
        score-=14; warnings.append('Enerji sıçraması yüksek; şarkı sırası veya seçim gözden geçirilmeli.')
    if d_rng>4:
        score-=12; warnings.append('Dramatik yoğunluk çok dalgalı; embrace ve hikaye kopabilir.')
    if w_avg and w_avg<6:
        score-=12; warnings.append('Yürüme kalitesi düşük; sosyal pist için zor olabilir.')
    if float(drams.mean())>=8.5:
        score-=10; warnings.append('Tüm tanda çok dramatik; geç saat/deneyimli kitle dışında riskli.')
    if float(energies.mean())>=8.8:
        score-=8; warnings.append('Tüm tanda çok yüksek enerjili; pist yorgunluğu yaratabilir.')
    # sequence risk
    e=list(energies.fillna(energies.mean() if energies.notna().any() else 0))
    if len(e)>=3:
        drops=[e[i]-e[i+1] for i in range(len(e)-1)]
        if max(drops)>2:
            score-=8; warnings.append('Enerji akışında sert düşüş var; daha yumuşak sıralama denenebilir.')
    if not warnings:
        strengths.append('Belirgin risk bulunmadı; yine de pist bağlamı önemli.')
    score=max(0,min(100,int(round(score))))
    return {'score':score,'warnings':warnings,'strengths':strengths,'metrics':{'orchestras':orchestras,'genres':genres,'year_spread':spread,'energy_range':round(e_rng,2),'dramatic_range':round(d_rng,2),'avg_walking':round(w_avg,2)}}

def suggest_order(tanda):
    if tanda is None or len(tanda)==0: return tanda
    # start accessible, build energy, avoid most dramatic as opener, keep strongest/most resolved closer
    df=tanda.copy()
    df['_sort'] = pd.to_numeric(df['energy'], errors='coerce').fillna(5)*0.55 + pd.to_numeric(df['walking_quality'], errors='coerce').fillna(5)*0.25 + pd.to_numeric(df['dramatic_level'], errors='coerce').fillna(5)*0.20
    return df.sort_values('_sort').drop(columns=['_sort'])

def analyze_milonga(tandas):
    """tandas: list of tanda DataFrames."""
    rows=[]; warnings=[]
    prev_orch=None
    for i,t in enumerate(tandas,1):
        if t is None or len(t)==0: continue
        res=score_tanda(t)
        orch=t['orchestra'].mode().iloc[0] if 'orchestra' in t and len(t['orchestra'].mode()) else ''
        genre=t['genre'].mode().iloc[0] if 'genre' in t and len(t['genre'].mode()) else ''
        energy=float(pd.to_numeric(t['energy'],errors='coerce').mean())
        dramatic=float(pd.to_numeric(t['dramatic_level'],errors='coerce').mean())
        rows.append({'tanda_no':i,'genre':genre,'orchestra':orch,'score':res['score'],'avg_energy':round(energy,2),'avg_dramatic':round(dramatic,2),'warnings':' | '.join(res['warnings'])})
        if prev_orch and prev_orch==orch:
            warnings.append(f'{i-1}. ve {i}. tanda aynı orkestra: {orch}. Art arda kullanım riskli olabilir.')
        prev_orch=orch
    flow=pd.DataFrame(rows)
    if not flow.empty:
        # TTVTTM rough check per 6 tandas
        expected=['TANGO','TANGO','VALS','TANGO','TANGO','MILONGA']
        g=list(flow['genre'].str.upper())[:6]
        if len(g)>=6 and g!=expected:
            warnings.append('İlk 6 tanda klasik T-T-V-T-T-M akışından sapıyor; bilinçli tercih mi kontrol et.')
        if (flow['avg_energy'].rolling(3).mean()>8.3).any():
            warnings.append('Üst üste yüksek enerji blokları var; recovery tanda gerekebilir.')
        if (flow['avg_dramatic'].rolling(2).mean()>8.5).any():
            warnings.append('Dramatik yoğunluk kümeleniyor; pistte emosyonel yorgunluk yaratabilir.')
    return flow, warnings
