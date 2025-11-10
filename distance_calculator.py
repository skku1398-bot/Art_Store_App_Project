import pandas as pd
from geopy.distance import great_circle

# 1. 출발지 설정 (혜화역 기준)
START_COORDS = (37.582236, 127.001967) # (위도, 경도)

try:
    # 2. 좌표 변환이 완료된 데이터 파일 로드
    df = pd.read_csv('art_stores_with_coords.csv')
except FileNotFoundError:
    print("오류: 'art_stores_with_coords.csv' 파일을 찾을 수 없습니다. 좌표 변환을 완료하세요.")
    exit()

# 3. 거리 계산 함수 정의
def calculate_distance(row):
    """지점 좌표와 출발지 좌표 간의 거리를 계산합니다 (Km)."""
    store_coords = (row['lat'], row['lon'])
    return great_circle(START_COORDS, store_coords).km

# 4. 거리 계산 적용
df['distance_km'] = df.apply(calculate_distance, axis=1)

# 5. 거리 기준으로 순위 매기기
df = df.sort_values(by='distance_km')

# 6. 최종 파일 저장 (모든 컬럼 포함)
df.to_csv('final_ranked_art_stores.csv', index=False, encoding='utf-8-sig')

print("✅ 거리 계산 및 최종 파일(final_ranked_art_stores.csv) 생성이 완료되었습니다.")