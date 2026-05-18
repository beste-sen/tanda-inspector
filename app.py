
import streamlit as st
import pandas as pd
from tanda_engine import load_tracks, find_tracks, score_tanda, suggest_order, analyze_milonga

st.set_page_config(page_title='Tanda Inspector v2', layout='wide')
st.title('Tanda Inspector v2')
st.caption('Kural bazlı tango DJ asistanı. Skorlar heuristic/sezgisel başlangıçtır; final karar DJ ve pist bağlamınındır.')

@st.cache_data
def get_data():
    return load_tracks('tango_tracks_dj_enriched_v2.csv')

df=get_data()

tab1, tab2, tab3, tab4 = st.tabs(['Tanda Inspector','Tanda Builder','Milonga Flow','Annotation'])

with tab1:
    st.subheader('Tanda Inspector')
    st.write('3-4 parça seç; engine uyum, risk ve sıralama önerisi versin.')
    selected=[]
    for i in range(1,5):
        q=st.text_input(f'{i}. parça ara', key=f'q{i}', placeholder='Örn: Bahia Blanca veya Di Sarli')
        if q:
            opts=find_tracks(df,q,30)
            labels=[f"{r.title} — {r.orchestra} — {r.singer or 'instr.'} — {r.year} — {r.genre}" for _,r in opts.iterrows()]
            choice=st.selectbox(f'{i}. parça seç', ['']+labels, key=f'sel{i}')
            if choice:
                idx=labels.index(choice)
                selected.append(opts.iloc[idx])
    if st.button('Tandayı analiz et'):
        tanda=pd.DataFrame(selected)
        if len(tanda)<3:
            st.error('En az 3 parça seç.')
        else:
            res=score_tanda(tanda)
            st.metric('Tanda Score', res['score'])
            c1,c2=st.columns(2)
            with c1:
                st.write('Warnings')
                for w in res['warnings']: st.warning(w)
            with c2:
                st.write('Strengths')
                for s in res['strengths']: st.success(s)
            st.write('Seçilen tanda')
            st.dataframe(tanda[['title','orchestra','singer','genre','year','energy','dramatic_level','walking_quality','confidence']], use_container_width=True)
            st.write('Önerilen sıralama')
            st.dataframe(suggest_order(tanda)[['title','orchestra','singer','genre','year','energy','dramatic_level','walking_quality']], use_container_width=True)

with tab2:
    st.subheader('Tanda Builder')
    orch=st.selectbox('Orkestra', sorted(df['orchestra'].dropna().unique()))
    genre=st.selectbox('Genre', ['TANGO','VALS','MILONGA'])
    years=st.slider('Yıl aralığı', int(df['year'].min()), int(df['year'].max()), (1935,1945))
    subset=df[(df['orchestra']==orch)&(df['genre']==genre)&(df['year'].between(years[0],years[1]))].copy()
    subset=subset.sort_values(['confidence','year','walking_quality','energy'], ascending=[False,True,False,False])
    st.write(f'{len(subset)} aday')
    st.dataframe(subset[['track_id','title','singer','year','energy','rhythmic_level','dramatic_level','walking_quality','beginner_friendly','recommended_slot']], use_container_width=True)
    st.info('Buradan 3-4 parça seçip Tanda Inspector ekranında test edebilirsin.')

with tab3:
    st.subheader('Milonga Flow Analyzer')
    st.write('Basit format: Her satıra track_id yaz. Boş satır tanda ayracı.')
    sample='\n'.join(df.head(4)['track_id'].astype(str).tolist())
    text=st.text_area('Playlist / tanda blokları', value=sample, height=220)
    if st.button('Akışı analiz et'):
        blocks=[b.strip().splitlines() for b in text.split('\n\n') if b.strip()]
        tandas=[]
        for block in blocks:
            ids=[x.strip() for x in block if x.strip()]
            tandas.append(df[df['track_id'].astype(str).isin(ids)])
        flow,warnings=analyze_milonga(tandas)
        st.dataframe(flow, use_container_width=True)
        for w in warnings: st.warning(w)
        if not flow.empty:
            st.line_chart(flow.set_index('tanda_no')[['avg_energy','avg_dramatic','score']])

with tab4:
    st.subheader('Annotation workflow')
    st.write('Bu ekran, gerçek DJ intelligence datası üretmek için hangi kayıtların gözden geçirileceğini gösterir.')
    confidence=st.multiselect('Confidence filtresi', ['low','medium','high'], default=['low','medium'])
    view=df[df['confidence'].isin(confidence)].head(500)
    st.dataframe(view[['track_id','title','orchestra','singer','genre','year','energy','rhythmic_level','dramatic_level','walking_quality','beginner_friendly','confidence','floor_risk','recommended_slot']], use_container_width=True)
    st.download_button('Annotation CSV indir', view.to_csv(index=False).encode('utf-8'), 'annotation_worklist.csv', 'text/csv')
