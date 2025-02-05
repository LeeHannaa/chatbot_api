import pandas as pd
import pymysql

# DB 정보
host = "localhost"
user = "root"
password = "!"
database = "ddhouse"

# 엑셀 파일 불러오기
df = pd.read_excel("output.xlsx", nrows=1000)
# NaN 값 처리 (빈 문자열 또는 0으로 변환)
df = df.fillna({
    "customer_memo": "",
    "words": "",
    "floor": 0,
    "area": 0.0,
    "매매금액": 0,
    "전세금액": 0,
    "월세보중금": 0,
    "월세금액": 0
})

# DB 연결
conn = pymysql.connect(host=host, user=user, password=password, db=database)
curs = conn.cursor(pymysql.cursors.DictCursor)

# DB insert
sql = 'INSERT INTO test0205 (location, apt_name, floor, area, customer_memo, 매매금액, 전세금액, 월세보중금, 월세금액, words) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

for idx in range(len(df)):
	curs.execute(sql, tuple(df.values[idx]))

conn.commit()

#종료
curs.close()
conn.close()