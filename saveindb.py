import pandas as pd
import pymysql

# DB 정보
host = "localhost"
user = "root"
password = "!"
database = "ddhouse"

# TODO : 준공년도, 방향, 아파트 좌표 등 엑셀 파일의 추가 데이터를 db에 넣을 때 추가해주면 됨
# 엑셀 파일 불러오기
df = pd.read_excel("output.xlsx")
# NaN 값 처리 (빈 문자열 또는 0으로 변환)
df = df.fillna({
    "customer_memo": "",
    "words": "",
    "area": 0.0,
    "매매금액": 0,
    "전세금액": 0,
    "월세보중금": 0,
    "월세금액": 0,
    "연세보증금": 0,
    "연세금액": 0,
})

# DB 연결
conn = pymysql.connect(host=host, user=user, password=password, db=database)
curs = conn.cursor(pymysql.cursors.DictCursor)

# DB insert
sql = 'INSERT INTO ddapt (location, apt_name, area, customer_memo, 매매금액, 전세금액, 월세보중금, 월세금액, 연세보증금, 연세금액, words) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

for idx in range(len(df)):
	curs.execute(sql, tuple(df.values[idx]))

conn.commit()

#종료
curs.close()
conn.close()