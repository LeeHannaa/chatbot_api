# from keybert import KeyBERT
# from konlpy.tag import Okt


# print("시작~!")
# okt = Okt()

# text = "방3/거실넓음/화장실1, 인테리어예쁨, 현관중문 및 방문교체함"
# tokens = okt.morphs(text)  # 형태소 단위로 분리
# processed_text = " ".join(tokens)  # 공백 기준으로 다시 합치기
# print(processed_text)

# kw_model = KeyBERT()

# # 키워드 추출
# keywords_1 = kw_model.extract_keywords(processed_text, keyphrase_ngram_range=(1, 1), stop_words=None, top_n=10)
# keywords_2 = kw_model.extract_keywords(processed_text, keyphrase_ngram_range=(1, 2), stop_words=None)

# print("1-gram:", keywords_1)
# print("1~2-gram:", keywords_2)

import re
import pandas as pd
from keybert import KeyBERT
from konlpy.tag import Okt

# KeyBERT 및 형태소 분석기 초기화
kw_model = KeyBERT()
okt = Okt()

# 엑셀 파일 읽기
df = pd.read_excel("input.xlsx")  # 엑셀 파일명 변경 가능

# 합성어 리스트
compound_words = ["포세린", "알파룸", "에어컨", "붙박이장", "포쉐린타일", "가스레인지"] 
# 방향 관련 키워드 (남향, 동향 등)
direction_keywords = ["남향", "남서향", "동향", "북향", "동남향", "서향", "동북향", "서북향", "남동향", "북서향"]
# 방/화장실 관련 패턴
pattern = re.compile(r"(방\s*\d+\s*개|방\s*\d|큰 방\s*\d+\s*개|큰 방\s*\d|작은 방\s*\d+\s*개|작은 방\s*\d|큰방\s*\d+\s*개|큰방\s*\d|작은방\s*\d+\s*개|작은방\s*\d|화장실\s*\d+\s*개|화장실\s*\d|화\s*\d|화\s*\d+\s*개)")


# 조사나 불필요한 단어들을 제거하는 정규 표현식
def remove_particles(text):
    # 조사 및 불필요한 단어를 정규 표현식으로 제거
    text = re.sub(r'(는|은|이|가|을|를|에|에서|와|과|로|로서|도|의|으로|처럼|까지|만|부터|까지|의|에|에게|입니다|그냥|되어있습니다|있으면|팝니다|키우기|있습니다|있어요|주세요|두고요|내놓으려고|내놓습니다|해드립니다|부탁드립니다|합니다|들어오고|드리겠습니다|주세요|되어있어서|나옵니다|되어있)', '', text)
    return text

# 패턴 정형화
def preprocess_text(text):
    # 방/화장실 관련 표현 먼저 추출
    fixed_keywords = pattern.findall(text)
    text = pattern.sub(lambda x: x.group().replace(" ", ""), text)  # 공백 제거

    # 합성어와 방향 관련 표현을 따로 저장
    compound_found = []
    direction_found = []
    
    # 합성어 처리
    for word in compound_words:
        if word in text:
            compound_found.append(word)
            text = text.replace(word, " ") 
            
    # 방향 관련 표현 처리
    for direction in direction_keywords:
        if direction in text:
            direction_found.append(direction)
            text = text.replace(direction, " ")  # 방향 표현을 공백으로 치환
    
    # 형태소 분석, 조사 제거
    tokens = okt.morphs(text)
    tokens = [remove_particles(token) for token in tokens if not token.isdigit()]
    
    # 합성어를 다시 추가
    result_tokens = tokens + compound_found + direction_found
            
    # 결과 반환
    processed_text = " ".join(result_tokens)
    return processed_text, fixed_keywords

# 키워드 추출 함수
def extract_keywords(text):
    if pd.isna(text):  # NaN 값 처리
        return "", ""
    
    processed_text, fixed_keywords = preprocess_text(text)
    
    keywords_1 = kw_model.extract_keywords(processed_text, keyphrase_ngram_range=(1, 1), stop_words=None, top_n=10, use_mmr=True)
    # keywords_2 = kw_model.extract_keywords(processed_text, keyphrase_ngram_range=(1, 2), stop_words=None, top_n=5, use_mmr=True)
    
    # 기존 키워드 + 방/화장실 관련 표현 합치기
    keywords_1 = list(set(kw[0] for kw in keywords_1) | set(fixed_keywords))
    keywords_1 = [kw for kw in keywords_1 if not kw.isdigit()]
    # keywords_2 = list(set(kw[0] for kw in keywords_2) | set(fixed_keywords))
    # keywords_2 = [kw for kw in keywords_2 if not kw.isdigit()]

    print(keywords_1)
    # print(keywords_1, keywords_2)
    
    return keywords_1
    # return keywords_1, keywords_2

# customer_memo 컬럼에서 키워드 추출
df['1-gram'] = df['customer_memo'].apply(lambda x: extract_keywords(x))
# df[['1-gram', '1~2-gram']] = df['customer_memo'].apply(lambda x: pd.Series(extract_keywords(x)))

# 결과를 엑셀 파일로 저장
df.to_excel("output.xlsx", index=False)

print("완료! output.xlsx 파일이 생성되었습니다.")
