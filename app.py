import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium
import numpy as np
from geopy.distance import geodesic

# =================================================================================
# ⭐️ 모바일 화면 최적화 (Wide Mode) 설정
st.set_page_config(layout="wide")
# =================================================================================

# 1. 데이터 로드
try:
    df = pd.read_csv("final_ranked_art_stores.csv")
except FileNotFoundError:
    st.error("데이터 파일을 찾을 수 없습니다. 'final_ranked_art_stores.csv' 파일이 필요합니다.")
    st.stop()

# 2. 지도 초기화 및 마커 함수
def create_map(filtered_df, user_location=None):
    # 서울 중심 좌표
    SEOUL_CENTER = [37.5665, 126.9780]
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11)

    # 사용자 위치 마커 추가
    if user_location:
        folium.Marker(
            user_location,
            tooltip="현재 위치",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)

    # 화방 마커 추가
    for idx, row in filtered_df.iterrows():
        # HTML 팝업 내용 생성
        html = f"""
        <b>{row['name']}</b><br>
        평점: {row['review_score']}<br>
        카테고리: {row['category']}<br>
        {row['address']}<br>
        """
        
        # is_key_store 여부에 따라 마커 색상 결정
        color = 'blue' if row['is_key_store'] == True else 'darkgreen'

        folium.Marker(
            [row['lat'], row['lon']],
            tooltip=row['name'],
            popup=folium.Popup(html, max_width=200),
            icon=folium.Icon(color=color)
        ).add_to(m)

    return m

# =================================================================================
# 5. 메인 페이지 UI 및 필터 설정 (사이드바 사용 안 함)
# =================================================================================
st.title("🗺️ 서울/경기 지역 예술용품점 찾기 앱")
st.markdown("---")

# 3. 필터 UI 설정 (모바일 최적화를 위해 메인 바디에 배치)
st.header("🔍 화방 검색 필터")

# 컬럼을 사용하여 가로로 배치 (PC에서는 보기 좋고, 모바일에서는 자동으로 세로로 쌓여서 길게 보입니다)
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📍 1. 내 위치 설정")
    user_input_location = st.text_input("현재 위치 (주소 입력)", value="", label_visibility="collapsed")
    
    distance_limit = st.slider("거리 제한 (Km)", min_value=1.0, max_value=50.0, value=15.0, step=1.0)

with col2:
    st.subheader("🏷️ 2. 카테고리 필터")
    categories = ['전체'] + df['category'].unique().tolist()
    selected_category = st.selectbox("카테고리 선택", categories, label_visibility="collapsed")

with col3:
    st.subheader("🖌️ 3. 재료 필터")
    # materials 컬럼의 모든 재료를 유니크하게 추출
    all_materials = set()
    for materials in df['materials'].dropna():
        all_materials.update(materials.split(';'))
    all_materials = sorted(list(all_materials))
    selected_materials = st.multiselect("취급 재료로 필터링하기", all_materials, label_visibility="collapsed")

st.markdown("---")

# 4. 데이터 필터링 및 거리 계산 로직
filtered_df = df.copy()

# 4-1. 카테고리 필터 적용
if selected_category != '전체':
    filtered_df = filtered_df[filtered_df['category'] == selected_category]

# 4-2. 재료 필터 적용
if selected_materials:
    # 선택된 모든 재료를 포함하는 행만 필터링
    def filter_by_materials(materials_str):
        if pd.isna(materials_str):
            return False
        store_materials = set(materials_str.split(';'))
        return all(material in store_materials for material in selected_materials)
    
    filtered_df = filtered_df[filtered_df['materials'].apply(filter_by_materials)]

# 4-3. 거리 계산 및 필터
user_location_coords = None
if user_input_location:
    try:
        # Tmap API 호출 대신, '강남역' 또는 '홍대입구역' 등의 간단한 좌표만 가정 (배포 편의상)
        if '강남역' in user_input_location:
            user_lat, user_lon = 37.4979, 127.0276
        elif '홍대입구역' in user_input_location:
            user_lat, user_lon = 37.5574, 126.9248
        else:
            # 주소 변환이 복잡하므로, 일단 예외 처리
            user_lat, user_lon = None, None 

        if user_lat and user_lon:
            user_location_coords = (user_lat, user_lon)
            
            # 거리 계산 로직
            distances = []
            for _, row in filtered_df.iterrows():
                store_coords = (row['lat'], row['lon'])
                distance = geodesic(user_location_coords, store_coords).km
                distances.append(distance)
            
            filtered_df['distance_km'] = distances
            
            # 거리 제한 필터 적용
            filtered_df = filtered_df[filtered_df['distance_km'] <= distance_limit]
            
            # 거리 순으로 정렬
            filtered_df = filtered_df.sort_values(by='distance_km', ascending=True)

    except Exception as e:
        # 실제 API 호출 시 발생하는 오류 처리
        st.warning("위치 정보를 정확히 파악할 수 없습니다. 지도 표시가 부정확할 수 있습니다.")
        user_location_coords = None


# 5-1. 지도 출력
st.header("1. 화방 위치 지도")

# 지도 공간 확보를 위해 st.columns 사용
map_col, info_col = st.columns([3, 1])

with map_col:
    if not filtered_df.empty:
        # 필터링된 데이터와 사용자 위치로 지도 생성
        m = create_map(filtered_df, user_location_coords)
        folium_static(m, width=700, height=450)
    else:
        st.warning("선택된 조건에 맞는 화방이 없습니다. 필터를 조정해 주세요.")


# 5-2. 순위표 출력
st.header("2. 검색 결과 순위표")

# 표시할 컬럼 정의
display_cols = ['name', 'category', 'review_score', 'nearest_station']
if 'distance_km' in filtered_df.columns:
    display_cols.append('distance_km')
    # 거리 소수점 처리
    filtered_df['distance_km'] = filtered_df['distance_km'].round(1)

# 컬럼명 한글화
column_mapping = {
    'name': '화방 이름',
    'category': '카테고리',
    'review_score': '평점',
    'nearest_station': '가까운 역',
    'distance_km': '거리 (km)'
}

# 인덱스 제거 및 순위표 출력
st.dataframe(
    filtered_df[display_cols].rename(columns=column_mapping).reset_index(drop=True),
    hide_index=True
)

st.markdown("---")

# 5-3. 상세 정보 출력
st.header("3. 상세 정보")

if not filtered_df.empty:
    store_names = filtered_df['name'].tolist()
    selected_store_name = st.selectbox("상세 정보를 볼 화방을 선택하세요:", store_names)

    if selected_store_name:
        store_data = filtered_df[filtered_df['name'] == selected_store_name].iloc[0]

        st.subheader(f"✨ {store_data['name']} 상세 정보")
        
        # 상세 정보를 깔끔하게 보여주기 위해 2개의 컬럼 사용
        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown(f"**주소:** {store_data['address']}")
            st.markdown(f"**전화번호:** {store_data['phone']}")
            st.markdown(f"**가까운 역:** {store_data['nearest_station']}")
            st.markdown(f"**영업시간:** {store_data['opening_hours']}")

        with detail_col2:
            st.markdown(f"**평점:** ⭐ {store_data['review_score']}")
            st.markdown(f"**카테고리:** {store_data['category']}")
            
            # 재료 목록을 리스트로 표시
            if pd.notna(store_data['materials']):
                materials_list = store_data['materials'].split(';')
                st.markdown("**취급 재료:**")
                st.markdown("- " + "\n- ".join(materials_list))
            else:
                st.markdown("**취급 재료:** 정보 없음")

else:
    st.info("검색된 화방이 없습니다.")
