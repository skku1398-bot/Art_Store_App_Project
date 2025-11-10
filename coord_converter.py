import pandas as pd
from geopy.geocoders import Nominatim

# 1. 파일 로드 및 준비
try:
    df = pd.read_csv('art_stores_original.csv', dtype=str, keep_default_na=False)
    # 컬럼 이름의 앞뒤 공백(space) 및 숨겨진 문자 제거
    df.columns = df.columns.str.strip() 
except FileNotFoundError:
    print("오류: 'art_stores_original.csv' 파일을 찾을 수 없습니다. 원본 데이터 파일을 확인하세요.")
    exit()

# 지오코더 설정
geolocator = Nominatim(user_agent="art_store_finder")

# 2. 좌표 변환 함수
def geocode_address(address):
    """주소를 위도와 경도로 변환합니다."""
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"오류 발생 ({address}): {e}")
        return None, None

# 3. 새로운 좌표 컬럼 생성 및 적용
df['lat'] = None
df['lon'] = None
for index, row in df.iterrows():
    if pd.notna(row['address']):
        lat, lon = geocode_address(row['address'])
        df.loc[index, 'lat'] = lat
        df.loc[index, 'lon'] = lon

# 4. 좌표를 찾지 못한 행 제거
df = df.dropna(subset=['lat', 'lon'])

# 5. 최종 파일 저장
df.to_csv('art_stores_with_coords.csv', index=False, encoding='utf-8-sig')

print("✅ 좌표 변환 및 중간 파일(art_stores_with_coords.csv) 생성이 완료되었습니다.")