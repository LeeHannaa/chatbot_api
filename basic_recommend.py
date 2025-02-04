import mysql.connector
import pandas as pd

local = mysql.connector.connect(
	host="localhost",
    user="root",
    password="!",
    database="ddhouse"
)

# TODO : 전처리한 customer_memo 데이터 포함 유사도 분석 실시 (일단 엑셀로 접근)
# db에서 필요한 데이터 가져오기
cur = local.cursor(buffered=True)
cur.execute("SELECT id, location, apt_name, floor, area, bargain, bargain_m, charter_m, month_security, monthly_m, sale_price FROM apt")
apt_data = cur.fetchall()
cur.execute("SELECT apt_name, avg_bargain_m FROM avg_bargain")
avg_data = cur.fetchall()

selected_columns = ['id', 'location', 'apt_name', 'floor', 'area', 'bargain', 'bargain_m', 'charter_m', 'month_security', 'monthly_m', 'sale_price']
apt_df = pd.DataFrame(apt_data, columns=selected_columns)

selected_columns = ['apt_name', 'avg_bargain_m']
avg_df = pd.DataFrame(avg_data, columns=selected_columns)
# print(avg_df)


# print(f"데이터프레임 크기: {apt_df.shape}")
apt_df = apt_df.dropna()
avg_df = avg_df.dropna()
# 1. apt_df와 avg_df 병합
merged_df = apt_df.merge(avg_df, on='apt_name', how='left')
# print(apt_df.head())


from sklearn.feature_extraction.text import TfidfVectorizer

# TF-IDF 변환을 위한 벡터화 객체 생성
tfidf_vectorizer = TfidfVectorizer(lowercase=True, max_features=1000)

merged_df['weighted_location'] = merged_df['location'] * 3  # location을 3배 가중치
merged_df['basic_apt'] = (
    merged_df['weighted_location'] + ' ' +
    ' area : ' + merged_df['area'].astype(str) + ' ' +
    ' bargain : ' + merged_df['bargain'].astype(str) + ' ' +
    ' bargain_m : ' + merged_df['bargain_m'].astype(str)
)
# print("apt_data check \n", merged_df['basic_apt'])

# TF-IDF 행렬 생성
tfidf_matrix = tfidf_vectorizer.fit_transform(merged_df['basic_apt'])
# print(tfidf_matrix)

from sklearn.metrics.pairwise import cosine_similarity
# basic_apt 기반 필터링
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 사용자가 설정한 조건이 없는 경우 : 기본 추천 조건 우선 순위
def basic_apt_based_filtering(id):
    # 입력된 id에 해당하는 매물 정보 찾기
    selected_apt = merged_df[merged_df['id'] == id].iloc[0]
    
    # 입력된 id와 유사도 측정
    idx = merged_df[merged_df['id'] == id].index[0]
    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix)[0]

    # 유사도에 따라 정렬 (자기 자신 제외)
    sim_scores = sorted(list(enumerate(sim_scores)), key=lambda x: x[1], reverse=True)[1:]
    
    # 결과 리스트 생성
    result_str = ""
    # 먼저 입력된 id에 해당하는 정보 추가
    price = f"{selected_apt['bargain_m']}만원 (매매) / {selected_apt['charter_m']}만원 (전세) / 보증금 : {selected_apt['month_security']} | {selected_apt['monthly_m']} (월세) / {selected_apt['sale_price']}원 (분양)"
    result_str += f"{selected_apt['id']}번 {selected_apt['apt_name']} : {selected_apt['location']}, {selected_apt['area']}평, {price}, {selected_apt['floor']}층 \n\n\n"

    seen_apt_names = set()
    seen_apt_names.add(selected_apt['apt_name'])

    # 최대 8개의 서로 다른 아파트를 추천
    count = 0
    for i, score in sim_scores:
        row = merged_df.iloc[i]
        
        # 이미 추천된 아파트는 건너뛰기
        if row['apt_name'] in seen_apt_names:
            continue
        
        # 아파트 이름 추가
        seen_apt_names.add(row['apt_name'])
        
        # 가격 정보 처리
        price = f"{row['bargain_m']}만원 (매매) / {row['charter_m']}만원 (전세) / 보증금 : {row['month_security']} | {row['monthly_m']} (월세) / {row['sale_price']}원 (분양)"
        result_str += f"{row['id']}번 {row['apt_name']} : {row['location']}, {row['area']}평, {price}, {row['floor']}층 \n"
        
        # 8개의 서로 다른 아파트만 추천
        count += 1
        if count >= 8:
            break
    
    return result_str.strip()  # 마지막 줄바꿈 제거


from flask import Flask, jsonify, request
from flask_cors import CORS

main = Flask(__name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})
# 예시 - 매물 id로 api 요청
@main.route('/api/recommend/<int:id>', methods=['GET'])
def recommend(id):
    try:
        result = basic_apt_based_filtering(id)
        print("------------------------------- 결과 ------------------------------")
        print(result)
        return jsonify(str(result))
    except Exception as e:
        # 예외가 발생하면 에러 메시지 반환
        print("에러 발생:", str(e)) 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    main.run(debug=True)