import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
st.set_page_config(layout="wide")
# --- 데이터 로드 ---
try:
    # final_ranked_art_stores.csv 파일에 모든 데이터가 들어있습니다.
    df = pd.read_csv('final_ranked_art_stores.csv')
    START_LAT = 37.582236  # 혜화역 좌표
    START_LON = 127.001967
    DATA_LOADED = True
except FileNotFoundError:
    st.error("오류: 'final_ranked_art_stores.csv' 파일을 찾을 수 없습니다. 거리 계산 단계를 완료해주세요.")
    DATA_LOADED = False

# --- 웹페이지 UI 구성 ---
if DATA_LOADED:
    st.set_page_config(layout="wide")
    st.title("최적의 미술재료 화방 찾기 (혜화역 기준)")
    st.markdown("---")

    col1, col2 = st.columns([1, 2.5]) 
    
    with col1:
        st.header("화방 찾기")
        
        # 1. 재료 및 화방 필터링 준비
        
        df_all = df.copy()
        df_filtered = df_all.copy()
        
        # 1-2. 전체 재료 목록 생성 (중복 제거)
        all_materials = set()
        for materials_str in df_all['materials'].dropna():
            if isinstance(materials_str, str):
                for material in materials_str.split(';'):
                    all_materials.add(material.strip())
        all_materials = sorted(list(all_materials))

        # 2. UI 필터링 요소
        # 다중 선택 필터
        selected_materials = st.multiselect("재료로 필터링하기 (다중 선택 가능)", all_materials)
        
        # 3. 필터링 적용
        # 카테고리 필터링 (기존 기능 유지)
        category_col = 'category'
        category_list = ['전체 카테고리'] + sorted(df_all[category_col].unique().tolist())
        selected_category = st.selectbox("유형으로 필터링하기", category_list)

        if selected_category != '전체 카테고리':
            df_filtered = df_filtered[df_filtered[category_col] == selected_category]
            
        # 재료 필터링 적용 (Multiselect OR 로직)
        if selected_materials:
            material_pattern = '|'.join(selected_materials)
            df_filtered = df_filtered[df_filtered['materials'].astype(str).str.contains(material_pattern, case=False, na=False)]

        
        # 4. 순위표 표시
        st.dataframe(
            df_filtered[['name', 'distance_km', 'category', 'review_score']],
            column_config={
                'name': '화방 이름',
                'distance_km': st.column_config.NumberColumn("거리 (Km)", format="%.2f Km"),
                'category': '유형',
                'review_score': st.column_config.NumberColumn("평점", format="%.1f / 5.0"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("상세 정보")
        
        # 상세 정보 표시 (df_filtered가 비어있지 않을 때만)
        if not df_filtered.empty:
            selected_store_name = st.selectbox(
                "상세 정보를 볼 화방을 선택하세요:",
                df_filtered['name'].tolist()
            )
        
            selected_store = df_filtered[df_filtered['name'] == selected_store_name].iloc[0]
            
            if not selected_store.empty:
                st.markdown(f"#### {selected_store_name}")
                
                # 주소 표시
                st.write(f"**주소:** {selected_store['address']}")
                
                # 전화번호 표시
                if selected_store['phone'] and selected_store['phone'] != '':
                    st.write(f"**전화번호:** {selected_store['phone']}")
                
                # 영업시간 표시
                if selected_store['opening_hours'] and selected_store['opening_hours'] != '':
                    st.write(f"**영업시간:** {selected_store['opening_hours']}")
                
                # 지하철역 표시
                if selected_store['nearest_station'] and selected_store['nearest_station'] != '':
                    st.write(f"**가까운 역:** {selected_store['nearest_station']}")

                # 리뷰 평점 표시
                if selected_store['review_score'] and selected_store['review_score'] != '':
                    st.write(f"**리뷰 평점:** {float(selected_store['review_score']):.1f} / 5.0")
                
                # materials의 NaN (float) 값 처리
                materials_value = selected_store['materials']
                if pd.isna(materials_value) or materials_value == '':
                    materials_display = "정보 없음"
                else:
                    materials_display = str(materials_value).replace(';', ', ')
                    
                st.write(f"취급 재료: **{materials_display}**")
                st.write(f"거리: **{selected_store['distance_km']:.2f} Km**")


    with col2:
        st.header("지도에서 위치 확인")
        
        # 지도의 중심은 전체 데이터(df)의 평균 좌표를 사용
        map_center_lat = (START_LAT + df['lat'].mean())/2
        map_center_lon = (START_LON + df['lon'].mean())/2
        m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=12)
        
        # 출발지(혜화역 근처) 마커는 항상 표시
        folium.Marker(
            [START_LAT, START_LON],
            tooltip="출발지: 혜화역 근처",
            icon=folium.Icon(color='blue', icon='home', prefix='fa')
        ).add_to(m)

        # 🚨 [핵심 수정] 필터링된 데이터프레임(df_filtered)만 사용하여 마커를 그립니다.
        for index, row in df_filtered.iterrows():
            is_key = row.get('is_key_store', False) == True
            
            popup_text = f"<b>{row['name']}</b><br>거리: {row['distance_km']:.2f} Km<br>유형: {row['category']}"
            
            # 마커 색상 구분 로직은 그대로 유지
            if is_key:
                color = 'green' if row['distance_km'] < 3 else ('orange' if row['distance_km'] < 6 else 'red')
            else:
                color = 'gray'
            
            folium.Marker(
                [row['lat'], row['lon']],
                tooltip=popup_text,
                icon=folium.Icon(color=color, icon='palette', prefix='fa')
            ).add_to(m)


        folium_static(m, width=700, height=450)

