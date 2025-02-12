import mysql.connector
import pandas as pd

local = mysql.connector.connect(
	host="localhost",
    user="root",
    password="!",
    database="ddhouse"
)

# db에서 필요한 데이터 가져오기
cur = local.cursor(buffered=True)
cur.execute("SELECT id, location, apt_name, area, customer_memo, 매매금액, 전세금액, 월세보중금, 월세금액, words FROM ddapt")
apt_data = cur.fetchall()

selected_columns = ['id', 'location', 'apt_name', 'area', 'customer_memo', '매매금액', '전세금액', '월세보중금', '월세금액', 'words']
apt_df = pd.DataFrame(apt_data, columns=selected_columns)
# print(avg_df)
# print(f"데이터프레임 크기: {apt_df.shape}")
apt_df = apt_df.dropna()

# 원본 데이터 백업
original_apt_df = apt_df.copy()

# apt_df['location'] = apt_df['location'] * 2 # location을 2배 가중치
apt_df['words'] = apt_df['words'] * 2 # location을 2배 가중치

# 텍스트 데이터 생성 (TF-IDF 입력용)
apt_df['basic_apt'] = (
    'location: ' + apt_df['location'] + ' ' +
    'words: ' + apt_df['words'].astype(str)
)

# TF-IDF 벡터 변환~
from sklearn.feature_extraction.text import TfidfVectorizer
tfidf_vectorizer = TfidfVectorizer(lowercase=True)
tfidf_matrix = tfidf_vectorizer.fit_transform(apt_df['basic_apt'])

from sklearn.metrics.pairwise import cosine_similarity

# 기본 추천 조건 우선 순위
def basic_apt_based_filtering(id):
    # 입력된 id에 해당하는 매물 정보 찾기
    selected_apt = original_apt_df[original_apt_df['id'] == id].iloc[0] # 행번호로 id일치 매물 찾기
    
    # 기준 아파트 정보 출력
    print("\n[🔹 기준 아파트]")
    print(f"ID: {selected_apt['id']}, 위치: {selected_apt['location']}, 아파트명: {selected_apt['apt_name']}")
    print(f"면적: {selected_apt['area']}, 매매가: {selected_apt['매매금액']}, 전세가: {selected_apt['전세금액']}")
    print(f"보증금: {selected_apt['월세보중금']}, 월세: {selected_apt['월세금액']}")
    print(f"설명: {selected_apt['words']} \n")

    filtered_apts = original_apt_df[
        (abs(original_apt_df['매매금액'] - selected_apt['매매금액']) <= 1000) &
        (abs(original_apt_df['전세금액'] - selected_apt['전세금액']) <= 1000) &
        (abs(original_apt_df['월세보중금'] - selected_apt['월세보중금']) <= 1000) &
        (abs(original_apt_df['월세금액'] - selected_apt['월세금액']) <= 500) &
        (abs(original_apt_df['area'] - selected_apt['area']) <= 4)
    ].copy() 
    
    idx_list = apt_df[apt_df['id'] == id].index.tolist()
    idx = idx_list[0]
    #코사인 유사도를 이용해 텍스트 유사도 계산
    text_sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix)[0]
    # 필터링된 매물에 대해 유사도 매핑 (예외 처리 추가)
    def get_similarity(x):
        matching_idx = apt_df[apt_df['id'] == x].index.tolist()
        return text_sim_scores[matching_idx[0]] if matching_idx else 0

    filtered_apts['similarity'] = filtered_apts['id'].apply(get_similarity)
    
    # 이미 출력된 아파트를 추적하는 set
    seen_apt_names = set()
    seen_apt_names.add(selected_apt['apt_name'])
    recommended_apts = []
    
    # 유사도 0.1 이상인 서로 다른 아파트를 추천 (최대 10개)
    count = 0
    print("\n[🏡 추천 매물 리스트]")
    for _, row in filtered_apts.sort_values(by='similarity', ascending=False).iterrows():
        # 자기 자신은 제외
        if row['id'] == id:
            continue
        
        # 같은 아파트명은 제외
        if row['apt_name'] in seen_apt_names:
            continue
        
        count += 1
        if float(row['similarity']) < 0.1 or count > 10:
            break
        
        # 새로운 아파트만 추가
        seen_apt_names.add(row['apt_name'])
        recommended_apts.append({
            'id': int(row['id']),
            'location': row['location'],
            'apt_name': row['apt_name'],
            'area': float(row['area']),
            '매매금액': float(row['매매금액']),
            '전세금액': float(row['전세금액']),
            '월세보중금': float(row['월세보중금']),
            '월세금액': float(row['월세금액']),
            'words': row['words'],
            'similarity': float(row['similarity'])
        })
        
        print(f"[{count}] ID: {row['id']}, 위치: {row['location']}, 아파트명: {row['apt_name']}")
        print(f"면적: {row['area']}, 매매가: {row['매매금액']}, 전세가: {row['전세금액']}")
        print(f"보증금: {row['월세보중금']}, 월세: {row['월세금액']}, 유사도: {row['similarity']:.4f}")
        print(f"설명: {row['words']} \n")

    return recommended_apts

from flask import Flask, jsonify
from flask_cors import CORS

main = Flask(__name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})
# 예시 - 매물 id로 api 요청
@main.route('/api/recommend/<int:id>', methods=['GET'])
def recommend(id):
    try:
        result = basic_apt_based_filtering(id)
        # print(result)
        return jsonify(str(result))
    except Exception as e:
        # 예외가 발생하면 에러 메시지 반환
        print("에러 발생:", str(e)) 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    main.run(debug=True) 