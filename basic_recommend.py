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
cur.execute("SELECT id, location, apt_name, area, customer_memo, 매매금액, 전세금액, 월세보중금, 월세금액, words FROM test0206")
apt_data = cur.fetchall()

selected_columns = ['id', 'location', 'apt_name', 'area', 'customer_memo', '매매금액', '전세금액', '월세보중금', '월세금액', 'words']
apt_df = pd.DataFrame(apt_data, columns=selected_columns)
# print(avg_df)
# print(f"데이터프레임 크기: {apt_df.shape}")
apt_df = apt_df.dropna()

from sklearn.preprocessing import MinMaxScaler
# 가격과 면적 정규화 -> 최소값을 0으로, 최대값을 1로 변환 (숫자로 표기할 경우 각 항목에 대한 인식이 안됨, 단순히 숫자를 텍스트로 생각하고 비교함)
scaler = MinMaxScaler()
apt_df[['매매금액', '전세금액', '월세보중금', '월세금액', 'area']] = scaler.fit_transform(
    apt_df[['매매금액', '전세금액', '월세보중금', '월세금액', 'area']]
)

apt_df['location'] = apt_df['location'] * 2 # location을 2배 가중치
apt_df['words'] = apt_df['words'].astype(str) * 2
# 텍스트 데이터 생성 (TF-IDF 입력용)
apt_df['basic_apt'] = (
    'location: ' + apt_df['location'] + ' ' +
    'words: ' + apt_df['words'].astype(str)
)

# TF-IDF 벡터 변환
from sklearn.feature_extraction.text import TfidfVectorizer
tfidf_vectorizer = TfidfVectorizer(lowercase=True)
tfidf_matrix = tfidf_vectorizer.fit_transform(apt_df['basic_apt'])

# 가격 벡터 생성 (유클리드 거리 계산용)
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
price_features = apt_df[['매매금액', '전세금액', '월세보중금', '월세금액']]
price_distances = euclidean_distances(price_features)
area_features = apt_df[['area']]
area_distances = euclidean_distances(area_features)


# 기본 추천 조건 우선 순위
def basic_apt_based_filtering(id):
    # 입력된 id에 해당하는 매물 정보 찾기
    selected_apt = apt_df[apt_df['id'] == id].iloc[0]
    
    # 입력된 id와 유사도 측정
    idx = apt_df[apt_df['id'] == id].index[0]
    # 텍스트 기반 유사도 (코사인 유사도)
    text_sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix)[0]
    # 가격 기반 유사도 (유클리드 거리 → 반비례)
    price_sim_scores = 1 - price_distances[idx]
    # 면적 기반 유사도 (유클리드 거리 → 반비례)
    area_sim_scores = 1 - area_distances[idx]
    # 최종 유사도
    final_similarity = 0.2 * text_sim_scores + 0.55 * price_sim_scores + 0.25 * area_sim_scores

    # 유사도에 따라 정렬 (자기 자신 제외)
    sim_scores = sorted(list(enumerate(final_similarity)), key=lambda x: x[1], reverse=True)[1:]
    
    # 먼저 입력된 id에 해당하는 정보 추가
    recommended_apts = []
    recommended_apts.append({
        'id': int(selected_apt['id']),
        'location': selected_apt['location'],
        'apt_name': selected_apt['apt_name'],
        'area': float(selected_apt['area']),
        '매매금액': float(selected_apt['매매금액']),
        '전세금액': float(selected_apt['전세금액']),
        '월세보중금': float(selected_apt['월세보중금']),
        '월세금액': float(selected_apt['월세금액']),
        'words': selected_apt['words']
    })
    seen_apt_names = set()
    seen_apt_names.add(selected_apt['apt_name'])
    # 최대 10개의 서로 다른 아파트를 추천
    count = 0
    print("------------------------------- 결과 ------------------------------")
    for i, score in sim_scores:
        row = apt_df.iloc[i]
        if row['apt_name'] in seen_apt_names:
            continue

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
            'similarity': float(score)
        })
        print(recommended_apts[count], " \n\n")

        count += 1
        if count >= 10:
            break
    
    return recommended_apts


from flask import Flask, jsonify, request
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
    
    
    