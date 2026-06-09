import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="CCTV 범죄 예방 효용성 대시보드", layout="wide")
st.title("<우리 구에서 어떤 범죄에 CCTV가 가장 효과적일까요?>")

# 2. 데이터 불러오기
@st.cache_data
def load_data():
    df_raw = pd.read_excel("crime.xlsx", header=[0, 1, 2, 3])
    df_corr = pd.read_excel("corr.xlsx")
    
    df_map = pd.DataFrame()
    df_map['구'] = df_raw.iloc[:, 1]
    df_map['총범죄발생수'] = df_raw.iloc[:, -5:].sum(axis=1)
    df_map = df_map[df_map['구'] != '소계']
    
    return df_raw, df_map, df_corr

df_raw, df_map, df_corr = load_data()

# 3. 지도 시각화
st.subheader("1. 서울 자치구별 2024년 5대 범죄 발생 현황 (지도)")
seoul_gu_coords = {
    '강남구': [37.5172, 127.0473], '강동구': [37.5297, 127.1257], '강북구': [37.6416, 127.0142],
    '강서구': [37.5509, 126.8495], '관악구': [37.4784, 126.9517], '광진구': [37.5388, 127.0827],
    '구로구': [37.4954, 126.8582], '금천구': [37.4568, 126.8956], '노원구': [37.6542, 127.0569],
    '도봉구': [37.6688, 127.0471], '동대문구': [37.5744, 127.0396], '동작구': [37.5124, 126.9390],
    '마포구': [37.5662, 126.9016], '서대문구': [37.5794, 126.9367], '서초구': [37.4838, 127.0326],
    '성동구': [37.5635, 127.0365], '성북구': [37.5894, 127.0167], '송파구': [37.5145, 127.1064],
    '양천구': [37.5255, 126.8732], '영등포구': [37.5262, 126.8967], '용산구': [37.5325, 126.9903],
    '은평구': [37.6027, 126.9293], '종로구': [37.5703, 126.9895], '중구': [37.5637, 126.9976], '중랑구': [37.5959, 127.0934]
}
df_coords = pd.DataFrame.from_dict(seoul_gu_coords, orient='index', columns=['위도', '경도']).reset_index().rename(columns={'index': '구'})
df_merged = pd.merge(df_map, df_coords, on='구', how='left')

min_val, max_val = df_merged['총범죄발생수'].min(), df_merged['총범죄발생수'].max()
fig_map = px.scatter_mapbox(df_merged, lat="위도", lon="경도", hover_name="구", 
                            size="총범죄발생수", color="총범죄발생수",
                            color_continuous_scale="inferno", range_color=[min_val, max_val],
                            size_max=100, zoom=10, mapbox_style="carto-positron", height=600)
fig_map.update_layout(coloraxis_colorbar=dict(tickformat="d"))
st.plotly_chart(fig_map, use_container_width=True, key="map_chart")

# 2. 분석 대상 선택
st.subheader("2. 분석 대상 선택")
selected_gu = st.selectbox("분석할 구를 선택하세요:", df_map['구'].unique())

# 3. 선택한 구의 주요 5대 범죄 발생 빈도 (부드러운 카드 디자인)
st.subheader(f"3. {selected_gu}의 주요 5대 범죄 발생 빈도")
gu_crime_data = df_raw[df_raw.iloc[:, 1] == selected_gu].iloc[:, -5:]
gu_crime_data.columns = ['살인', '강도', '강간', '절도', '폭력']
crime_series = gu_crime_data.iloc[0].sort_values(ascending=False)

cols = st.columns(5)
for i, (crime, count) in enumerate(crime_series.items()):
    with cols[i]:
        st.markdown(f"""
            <div style="background-color: #f9fafb; padding: 20px; border-radius: 20px; text-align: center; 
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 5px;">{i+1}위</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #374151; margin-bottom: 10px;">{crime}</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #6366f1;">{int(count):,}건</div>
            </div>
        """, unsafe_allow_html=True)

# 4. 선택한 구의 죄 종류별 CCTV 효용 분석
st.subheader(f"4. {selected_gu}의 범죄 종류별 CCTV 효용 분석(2017~2024)")
gu_corr_data = df_corr[df_corr['구'] == selected_gu].copy()
gu_corr_data['효과여부'] = gu_corr_data['상관계수'].apply(lambda x: '효과 없음 (빨강)' if x >= 0 else '효과 있음 (초록)')
color_map = {'효과 없음 (빨강)': '#FF3131', '효과 있음 (초록)': '#00FF41'}

fig_bar = px.bar(gu_corr_data, x='범죄유형', y='상관계수', color='효과여부', color_discrete_map=color_map)
st.plotly_chart(fig_bar, use_container_width=True, key="corr_chart")

for index, row in gu_corr_data.iterrows():
    corr = row['상관계수']
    color = "#00FF41" if corr < 0 else "#FF3131"
    status = "예방 효과 있음" if corr < 0 else "예방 효과 낮음"
    icon = "✅" if corr < 0 else "⚠️"
    st.markdown(f"- **{icon} {row['범죄유형']}**: 상관계수 <span style='color:{color}; font-weight:bold;'>{corr:.4f}</span> → **{status}**", unsafe_allow_html=True)