import os
from dotenv import load_dotenv
import pandas as pd

# OpenAI API Key 설정
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.environ.get('API_KEY')
embedding_model = {"encode": os.environ}

# 데이터 폴더 경로
folder_path = 'data'

# 모든 엑셀 파일을 읽어서 데이터를 합침
all_data = []

from konlpy.tag import Okt
# Kkma 객체 생성
okt = Okt()
for file_name in os.listdir(folder_path):
    if file_name.endswith('.xlsx'):  # 엑셀 파일만 선택
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_excel(file_path)
        
        # 각 파일에서 필요한 데이터 처리
        for _, row in df.iterrows():
            questions = row['질문'].split('|')  # 질문이 여러 개인 경우, '|'로 구분
            answer = row['답변']
            link = row['링크']
            category = row['카테고리']
            all_data.append({
                "questions": questions,
                "answer": answer,
                "link": link,
                "category": category
            })

print(f"총 {len(all_data)}개의 질문-답변 쌍이 있습니다.")

# index 저장 경로 설정
index_storage_path = './index_storage'

from llama_index.core import VectorStoreIndex, Document, SimpleDirectoryReader, StorageContext, load_index_from_storage

# 문서 목록 생성
documents = []
for qa in all_data:
    for question in qa["questions"]:
        content = f"질문: {question}\n답변: {qa['answer']}\n링크: {qa['link']}\n카테고리: {qa['category']}"
        doc = Document(text=content)
        # print(doc)
        documents.append(doc)

# 기존 저장된 인덱스가 있으면 로드, 없으면 새로 생성 -> 임베딩을 생성할 때 발생하는 비용 방지 (모델 재학습 필요시 index_storage 삭제 후 코드 실행)
if os.path.exists(index_storage_path):
    print("저장된 인덱스를 로드합니다...")
    storage_context = StorageContext.from_defaults(persist_dir=index_storage_path)
    index = load_index_from_storage(storage_context)
else:
    print("새로운 인덱스를 생성합니다...")
    # 문서 로드 및 벡터 생성
    documents = SimpleDirectoryReader('./data').load_data()
    # 생성된 벡터를 인덱스에 저장
    index = VectorStoreIndex.from_documents(documents)
    
    # 생성된 인덱스 저장
    index.storage_context.persist(index_storage_path)
    print("인덱스가 저장되었습니다!")

print("모델 학습 완료!")

#########################################

from flask import Flask, request, jsonify
from flask_cors import CORS

main = Flask(__name__)
CORS(main, resources={r"/api/*": {"origins": "*"}})

# from gensim.models import Word2Vec
# 디디 하우스 -> 디디하우스로 인식하도록  (사용자 사전으로 명사 추가) : noun/names.txt에 명사 단어 추가 완료
import konlpy
print(konlpy.__file__)

# 문장 데이터를 기반으로 단어 임베딩 학습
sentences = [
    ["원룸", "정투룸", "미투룸", "쓰리룸"],
    ["매물", "원룸", "방", "방만"],
    ["특정 지역", "흥해읍", "양덕동", "장성동", "창포동"],
    ["최초등록일", "접수일"],
    ["전화번호", "전번", "연락처"],
]
# word2vec_model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
# 커스텀 매핑을 위한 데이터 생성
main_word_map = {}
for sentence in sentences:
    main_word = sentence[0]  # 첫 번째 단어를 메인 단어로 설정
    for word in sentence[1:]:  # 나머지 단어들에 대해 메인 단어를 매핑
        main_word_map[word] = main_word

# 쿼리 확장 함수
def expand_query(question):
    words = question.split()
    expanded_query = []

    for word in words:
        # 커스텀 룰: 메인 단어로 매핑
        if word in main_word_map:
            expanded_query.append(main_word_map[word])
        # # Word2Vec 유사도 기반 확장
        # elif word in word2vec_model.wv:  
        #     similar_words = [sim_word for sim_word, _ in word2vec_model.wv.most_similar(word, topn=top_n)]
        #     expanded_query.append(similar_words)
        #     print("similar_words : " , similar_words)
        else:
            expanded_query.append(word)  # 매핑할 단어가 없으면 원래 단어 유지
            print("word : " , word)
    return " ".join(expanded_query)
  
stopwords = ['의','서','에','들','는','잘','걍','과','도','를','으로','한','하다','!','<','>','(',')','[',']','|','#','.']
def handle_chatbot_question(user_question):
    # 질문 조건 확인
    if "누구" in user_question:
        response = (
            "'안녕하세요. 부동산 공인중개사가 매물을 편리하게 관리할 수 있도록 도와주는 웹/앱 서비스'인 디디하우스 상담 챗봇입니다. 디디하우스 사이트를 이용하시면서 궁금한 부분에 대해서 질문해주시면 친절하게 답변드리겠습니다. 전화 상담을 원하시는 경우에는 고객센터(054-254-0732)에 문의주시면 됩니다.'라고 응대해."
        )
    else:
        # 일반 질문 처리
        user_question = okt.morphs(user_question)
        user_question = [word for word in user_question if not word in stopwords]
        morphed_question = " ".join(user_question)
        response = expand_query(morphed_question)    
    return response

# api 부분
@main.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        # 클라이언트로부터 질문을 JSON 형식으로 받음
        user_question = request.json.get('question')

        # 질문이 없다면 에러 메시지 반환
        if not user_question:
            return jsonify({"error": "question is required"}), 400

        # 사용자 질문 전처리
        modified_question = handle_chatbot_question(user_question)
        print("modified_question : ", modified_question)
        
        # 데이터를 백터 형태로 변경 후 사용자 질문과 관련된 데이터 반환
        retriever = index.as_retriever()
        results = retriever.retrieve(modified_question)
        
        # 유사도가 0.86 이상인 결과만 필터링
        filtered_results = [node_with_score for node_with_score in results if node_with_score.score >= 0.86]
        
        # 필터링된 결과가 있을 경우, 해당 문서 사용
        if filtered_results:
            # 쿼리를 던질 때 같이 줄 데이터 전처리
            extracted_data = []
            for node_with_score in filtered_results:
                node_content = str(node_with_score.node)
                question = ""
                answer = ""
                link = ""

                print(f"Processing line: {node_content}")  # 각 줄 출력하여 디버깅
                print("-" * 30) 
                
                # 정확도 향상을 위한 데이터 범위 지정
                start_idx = node_content.find('질문:') + len('질문:')
                end_idx = node_content.find('답변:')
                question = node_content[start_idx:end_idx].strip()
                start_idx = node_content.find('답변:') + len('링크:')
                end_idx = node_content.find('링크:')
                answer = node_content[start_idx:end_idx].strip()
                start_idx = node_content.find('링크:') + len('카테고리:')
                end_idx = node_content.find('카테고리:')
                link = node_content[start_idx:end_idx].strip()
                extracted_data.append({"질문": question, "답변": answer, "링크": link})

            # for data in extracted_data:
            #     print(f"질문: {data['질문']}")
            #     print(f"답변: {data['답변']}")
            #     print(f"링크: {data['링크']}")
            #     print("-" * 30)
            toapi = (
                f"질문: {modified_question}\n\n"
                f"참고 정보:\n{extracted_data}\n\n"
                f"위 정보를 바탕으로 가장 적절한 답변을 한국어로 존댓말을 사용해 제공해 주세요. 그리고 적절한 링크가 있다면 항상 꼭 첨부해주세요."
            )    
            # 유사도 0.86 이상인 문서를 기반으로 쿼리 엔진 실행
            query_engine = index.as_query_engine()
            response = query_engine.query(toapi)
            
            # 응답 중 고객센터 연락 내용 여부
            customer_service_number = "054-254-0732"
            closing_statement = f"더 궁금한 사항이 있다면 고객센터({customer_service_number})에 문의주시면 친절하게 도와드리겠습니다."
            if "054" not in str(response):
                response_with_closing = f"{str(response)} {closing_statement}"
                print(response_with_closing)
                return jsonify(str(response_with_closing))
            else:
                print(response)
                return jsonify(str(response))
        else:
            # 유사도 0.86 미만인 경우 다른 답변 제공
            print("유사도가 낮아 다른 답변을 제공합니다.")
            return jsonify("죄송합니다. 현재 정보가 부족하여 정확한 답변을 드리기 어려운 상황입니다. 구체적인 질문을 주시면 최대한 노력해 답변드리겠습니다. 전화 상담을 원하시는 경우, 고객센터(054-254-0732)로 연락 부탁드립니다.")
            
    except Exception as e:
        # 예외가 발생하면 에러 메시지 반환
        print("에러 발생:", str(e)) 
        return jsonify({"error": str(e)}), 500

@main.route('/api/question', methods=['POST'])
def question():
    try:
        # 클라이언트로부터 질문을 JSON 형식으로 받음
        user_questionId = request.json.get('id')
        user_question = request.json.get('question')
        print(user_questionId, " : ", user_question)
        
        # 질문이 없다면 에러 메시지 반환
        if not user_question:
            return jsonify({"error": "question is required"}), 400
        
        # redis에 일차 점검 후 gpt 모델 쿼리 요청
        import redis
        r = redis.Redis(
            host='localhost',
            port=6380,
            db = 0
        )
        print(r.ping())
        if(r.get(user_questionId)):
            # get
            answer = r.get(user_questionId).decode('utf-8')
            print("redis에 저장해놓았던 경우 : ", answer)
        else:
            # 질문을 수정하여 응답 준비
            modified_question = f"{user_question}? 한국어로 친절하게 존댓말을 사용해. 적절한 링크가 있다면 항상 꼭 넣어줘. "
            print(modified_question)
        
            query_engine = index.as_query_engine()
            answer = query_engine.query(modified_question)
                
            print(answer)
            r.set(user_questionId, str(answer).encode('utf-8'))
        
        return jsonify(str(answer))
 
    except Exception as e:
        # 예외가 발생하면 에러 메시지 반환
        print("에러 발생:", str(e)) 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    main.run(debug=True)