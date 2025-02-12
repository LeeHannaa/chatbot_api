### 챗봇 서비스

1. **소개**
   - 디디하우스 FAQ에 대한 사용자들의 전화 상담 과정을 간편하게 하고자 기획한 챗봇 서비스
2. **기간**
   - 2024.12.30 ~ 2025.01.20
3. **챗봇 기능 개발 과정**
   - gpt3.5 Fine-Tunning : 정확도 낮음 (Fine-Tunning은 챗봇의 전반적인 스타일을 조정하는데 적합하다고 판단)
   - **[LlamaIndex 모델 학습 과정]**
     - 같은 질문을 여러 형태의 질문으로 학습 → 유사도 측면
     - 디디하우스 페르소나 적용
     - 관련된 답변에 적절한 링크가 있다면 제공
     - 유사 데이터 찾기 전 사용자 질문 전처리 → 질문 표준화 (단어 커스텀 매핑) / 형태소 추출 후 의미없는 형태소 제거
     - 학습된 데이터 내에 유사도 0.86 이상인 결과만 필터링 후 쿼리엔진 실행 → 학습되지 않은 질문에 대한 환각증상 막음
   - redis 사용하여 고정 컴포넌트에서 요청하는 질문 api에 대한 답변 시간 단축
4. **챗봇 api 기능 명세**
   - http://127.0.0.1:5000/api/chatbot (method = post)
     - 챗봇 FAQ 서비스로 질의응답 api
   - http://127.0.0.1:5000/api/question (method = post)
     - ui 질문 component로 redis 이용
5. **관련 파일**
   - 파이썬 코드 : main.py
   - 학습 데이터 : data 폴더
6. **데이터, 코드 사용법**
   - 질문, 답변, 링크, 카테고리로 xlsx에 데이터 저장
   - 질문에 유사 문장 삽입 시 ‘|’로 구분하여 저장
   - 동일하게 처리할 단어 (ex: **특정지역**, 양덕동, 흥해읍, 장성동)는 python 코드 내에서 메인 단어 설정 후 나머지 단어(양덕동, 흥해읍, 장성동)는 메인 단어(특정지역)로 매핑 되는 코드에 단어 추가 ⇒ 질문 데이터 학습 시 메인 단어만 학습하면 됨
     - ex: “양덕동에만 있는 매물을 보고 싶은데” → “특정지역에만 있는 매물을 보고 싶은데”
7. **테스트 [ui code](https://github.com/LeeHannaa/chatbot_csr.git) / [postman](https://leehannanaa.postman.co/workspace/My-Workspace~c627d9ef-7ce2-4938-8d37-46f1b9f1678f/collection/28908791-15e011e0-ca1c-4bb9-ac3d-9059e05136d1?origin=tab-menu)**
8. **세부 진행 과정 [Notion](https://www.notion.so/AI-15ecaaf36f6f80cfa452f2987ccdc817)**

#

### 매물 추천 서비스

1. **소개**
   - 디디하우스 사용자 매물 추천 서비스
2. **기간**
   - 2025.1.21 ~ 2025.02.12
3. **챗봇 기능 개발 과정**
   - [ customer_memo 데이터 전처리 최종 버전 ] - preprocessing.py
     - 한글, 숫자, 공백만 남기고 나머지 문자는 제거
     - 휴대폰 번호 패턴 (010, 054) 제거
     - 단어 삭제 리스트
       - 중개사무소, 부동산, 문의, 소장, 공인중개사 (미삭제시 유사도 검사에서 특정 대분류로 나뉘어지는 단어들)
     - 연속된 공백을 하나로 줄이기
   - [ 매물 유사도 측정 및 추천 최종 버전] - recommend.py
     - 금액, 면적에 대해서 추천 가능 범위를 지정
       - 범위내 1차 필터링 된 매물 중 추천하도록 설정
     - **TfidfVectorizer**를 사용해 location, 전처리한 memo 백터화 표현 (코사인 유사도를 사용하기 위함)
     - **cosine_similarity**를 사용해 텍스트 기반 유사도 측정
     - 최대 10개의 서로 다른 매물 추천 (유사도가 0.1 미만인 경우 더이상 추천하지 않도록 설정)
       - 같은 단지 내 아파트 추천 x
4. **챗봇 api 기능 명세**
   - http://127.0.0.1:5000/api/recommend/{id} (method = get)
     - 사용자 매물 추천 서비스 api
5. **관련 파일**
   - 파이썬 코드 : preprocessing.py (memo 데이터 전처리), saveindb.py (엑셀 데이터 db에 저장), recommend.py(매물 추천 기능)
6. **데이터, 코드 사용법**
   - .....
7. **테스트 [postman](https://leehannanaa.postman.co/workspace/My-Workspace~c627d9ef-7ce2-4938-8d37-46f1b9f1678f/request/28908791-fd66a48e-b445-439b-a5b4-38a83374e5d3)**
8. **세부 진행 과정 [Notion](https://www.notion.so/AI-18fcaaf36f6f80adbfb6d58871a11d0a?pvs=4)**
