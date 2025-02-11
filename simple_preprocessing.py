import re
import pandas as pd

# 한글, 숫자, 공백만 남기고 나머지 문자 제거하는 정규 표현
non_korean_pattern = re.compile(r"[^가-힣0-9\s.,\(\)]|(?<!\d)[,.]|[,.](?!\d)")
# 휴대폰 번호 패턴 (010 뒤에 숫자 8개, 띄어쓰기 허용)
smartphone_pattern = re.compile(r"010\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d")
smartphonedot_pattern = re.compile(r"010(\.\d{4}){2}")
phone_pattern = re.compile(r"054\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d\s*\d")

# 지울 단어 리스트
remove_keywords = ["중개사무소", "전화", "연락", "부동산", "문의", "소장", "중개사", "사무소", "공인"]
# 지울 단어들의 정규 표현식 생성
remove_pattern = re.compile(r"(" + "|".join([re.escape(keyword) for keyword in remove_keywords]) + r")\S*")

# 키워드 추출 함수 정의
def extract_keywords(text):
    text = str(text) if pd.notna(text) else ''  # NaN 방지
    if not text.strip():  # 빈 문자열이면 빈 리스트 반환
        return ""

    # 한글이 아닌 모든 문자 제거
    text = non_korean_pattern.sub(" ", text)
    
    # 010-XXXX-XXXX 패턴 삭제
    text = smartphone_pattern.sub("", text)
    text = smartphonedot_pattern.sub("", text)
    text = phone_pattern.sub("", text)
    
    # 지정한 단어들 제거
    text = remove_pattern.sub("", text)
    
    # 연속된 공백을 하나로 줄이기
    text = re.sub(r"\s+", " ", text).strip()
    
    print(text)
    return text


# 데이터 처리
data = pd.read_excel("asset.xlsx")
data['1-gram'] = data['customer_memo'].apply(lambda x: extract_keywords(x))
data.to_excel("output.xlsx", index=False)

print("완료! output.xlsx 파일이 생성되었습니다.")
