# -*- coding: utf-8 -*-
"""
Custom Translator  —  Streamlit 올인원 웹 번역기
==================================================
구글 / 파파고 무료 웹 엔드포인트를 'urllib + json' 만으로 직접 호출합니다.
외부 번역 라이브러리(googletrans, deep-translator, pentago 등)를 전혀
임포트하지 않으므로, 파이썬 3.14 에서 'cgi' 모듈 삭제로 인한 임포트 에러가
원천적으로 발생하지 않습니다. API 키도 필요 없습니다.

[설치 / 실행]
  pip install streamlit
  streamlit run translator.py

[강조색(동그라미·드롭다운·입력창 테두리)을 파랑으로]
  이 색들은 Streamlit '테마 강조색'(기본=빨강)에서 나옵니다. 아래 둘 중 하나로 파랑이 됩니다.
  (1) translator.py 와 같은 폴더에  .streamlit/config.toml  파일을 만들고:
          [theme]
          primaryColor = "#2563EB"
  (2) 또는 파일 없이 실행 시 옵션으로:
          streamlit run translator.py --theme.primaryColor="#2563EB"
"""

import streamlit as st
import urllib.request
import urllib.parse
import urllib.error
import json
import uuid
import time
import hmac
import base64
import re

# ============================================================
# 지원 언어 (정적 데이터 — 런타임 외부 의존성 없음)  라벨 -> 코드
# ============================================================
GOOGLE_LANGS = {
    '한국어 (ko)': 'ko',
    '영어 (en)': 'en',
    '일본어 (ja)': 'ja',
    '중국어(간체) (zh-CN)': 'zh-CN',
    '중국어(번체) (zh-TW)': 'zh-TW',
    '간다어 (lg)': 'lg',
    '갈리시아어 (gl)': 'gl',
    '과라니어 (gn)': 'gn',
    '구자라트어 (gu)': 'gu',
    '그리스어 (el)': 'el',
    '남부 소토어 (st)': 'st',
    '냔자어 (ny)': 'ny',
    '네덜란드어 (nl)': 'nl',
    '네팔어 (ne)': 'ne',
    '노르웨이어 (no)': 'no',
    '덴마크어 (da)': 'da',
    '도그리어 (doi)': 'doi',
    '독일어 (de)': 'de',
    '디베히어 (dv)': 'dv',
    '라오어 (lo)': 'lo',
    '라트비아어 (lv)': 'lv',
    '라틴어 (la)': 'la',
    '러시아어 (ru)': 'ru',
    '루마니아어 (ro)': 'ro',
    '루샤이어 (lus)': 'lus',
    '룩셈부르크어 (lb)': 'lb',
    '르완다어 (rw)': 'rw',
    '리투아니아어 (lt)': 'lt',
    '링갈라어 (ln)': 'ln',
    '마니푸리어 (mni-Mtei)': 'mni-Mtei',
    '마라티어 (mr)': 'mr',
    '마오리어 (mi)': 'mi',
    '마이틸리어 (mai)': 'mai',
    '마케도니아어 (mk)': 'mk',
    '말라가시어 (mg)': 'mg',
    '말라얄람어 (ml)': 'ml',
    '말레이어 (ms)': 'ms',
    '몰타어 (mt)': 'mt',
    '몽골어 (mn)': 'mn',
    '바스크어 (eu)': 'eu',
    '밤바라어 (bm)': 'bm',
    '버마어 (my)': 'my',
    '베트남어 (vi)': 'vi',
    '벨라루스어 (be)': 'be',
    '벵골어 (bn)': 'bn',
    '보스니아어 (bs)': 'bs',
    '북부 소토어 (nso)': 'nso',
    '불가리아어 (bg)': 'bg',
    '사모아어 (sm)': 'sm',
    '산스크리트어 (sa)': 'sa',
    '서부 프리지아어 (fy)': 'fy',
    '세르비아어 (sr)': 'sr',
    '세부아노어 (ceb)': 'ceb',
    '소라니 쿠르드어 (ckb)': 'ckb',
    '소말리아어 (so)': 'so',
    '쇼나어 (sn)': 'sn',
    '순다어 (su)': 'su',
    '스와힐리어 (sw)': 'sw',
    '스웨덴어 (sv)': 'sv',
    '스코틀랜드 게일어 (gd)': 'gd',
    '스페인어 (es)': 'es',
    '슬로바키아어 (sk)': 'sk',
    '슬로베니아어 (sl)': 'sl',
    '신디어 (sd)': 'sd',
    '싱할라어 (si)': 'si',
    '아랍어 (ar)': 'ar',
    '아르메니아어 (hy)': 'hy',
    '아삼어 (as)': 'as',
    '아이마라어 (ay)': 'ay',
    '아이슬란드어 (is)': 'is',
    '아이티어 (ht)': 'ht',
    '아일랜드어 (ga)': 'ga',
    '아제르바이잔어 (az)': 'az',
    '아칸어 (ak)': 'ak',
    '아프리칸스어 (af)': 'af',
    '알바니아어 (sq)': 'sq',
    '암하라어 (am)': 'am',
    '에스토니아어 (et)': 'et',
    '에스페란토어 (eo)': 'eo',
    '에웨어 (ee)': 'ee',
    '오로모어 (om)': 'om',
    '오리야어 (or)': 'or',
    '요루바어 (yo)': 'yo',
    '우르두어 (ur)': 'ur',
    '우즈베크어 (uz)': 'uz',
    '우크라이나어 (uk)': 'uk',
    '웨일스어 (cy)': 'cy',
    '위구르어 (ug)': 'ug',
    '이그보어 (ig)': 'ig',
    '이디시어 (yi)': 'yi',
    '이로코어 (ilo)': 'ilo',
    '이탈리아어 (it)': 'it',
    '인도네시아어 (id)': 'id',
    '자바어 (jw)': 'jw',
    '조지아어 (ka)': 'ka',
    '줄루어 (zu)': 'zu',
    '체코어 (cs)': 'cs',
    '총가어 (ts)': 'ts',
    '카자흐어 (kk)': 'kk',
    '카탈로니아어 (ca)': 'ca',
    '칸나다어 (kn)': 'kn',
    '케추아어 (qu)': 'qu',
    '코르시카어 (co)': 'co',
    '코사어 (xh)': 'xh',
    '콘칸어 (gom)': 'gom',
    '쿠르드어 (ku)': 'ku',
    '크로아티아어 (hr)': 'hr',
    '크리오어 (kri)': 'kri',
    '크메르어 (km)': 'km',
    '키르기스어 (ky)': 'ky',
    '타갈로그어 (tl)': 'tl',
    '타밀어 (ta)': 'ta',
    '타지크어 (tg)': 'tg',
    '타타르어 (tt)': 'tt',
    '태국어 (th)': 'th',
    '텔루구어 (te)': 'te',
    '투르크멘어 (tk)': 'tk',
    '튀르키예어 (tr)': 'tr',
    '티그리냐어 (ti)': 'ti',
    '파슈토어 (ps)': 'ps',
    '펀잡어 (pa)': 'pa',
    '페르시아어 (fa)': 'fa',
    '포르투갈어 (pt)': 'pt',
    '폴란드어 (pl)': 'pl',
    '프랑스어 (fr)': 'fr',
    '핀란드어 (fi)': 'fi',
    '하와이어 (haw)': 'haw',
    '하우사어 (ha)': 'ha',
    '헝가리어 (hu)': 'hu',
    '호즈푸리어 (bho)': 'bho',
    '히몸어 (hmn)': 'hmn',
    '히브리어 (iw)': 'iw',
    '힌디어 (hi)': 'hi',
}

PAPAGO_LANGS = {
    '한국어 (ko)': 'ko',
    '영어 (en)': 'en',
    '일본어 (ja)': 'ja',
    '중국어(간체) (zh-CN)': 'zh-CN',
    '중국어(번체) (zh-TW)': 'zh-TW',
    '독일어 (de)': 'de',
    '러시아어 (ru)': 'ru',
    '베트남어 (vi)': 'vi',
    '스페인어 (es)': 'es',
    '아랍어 (ar)': 'ar',
    '이탈리아어 (it)': 'it',
    '인도네시아어 (id)': 'id',
    '태국어 (th)': 'th',
    '포르투갈어 (pt)': 'pt',
    '프랑스어 (fr)': 'fr',
    '힌디어 (hi)': 'hi',
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"


# ============================================================
# 공통 HTTP 헬퍼 (순수 urllib)
# ============================================================
def _http_get(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _http_post(url, data_dict, headers=None, timeout=10):
    body = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


# ============================================================
# 1) Google Translate  (무료 엔드포인트, 키 불필요)
# ============================================================
def google_translate(text, source, target):
    params = urllib.parse.urlencode({
        "client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params
    raw = _http_get(url, headers={"User-Agent": UA})
    data = json.loads(raw)
    translated = "".join(seg[0] for seg in data[0] if seg and seg[0])
    detected = data[2] if len(data) > 2 and isinstance(data[2], str) else source
    return translated, detected


# ============================================================
# 2) Naver Papago  (무료 웹 엔드포인트, 키 불필요)
#    deviceId + timestamp 를 HMAC-MD5 로 서명한 PPG 인증 사용.
#    서명 키는 파파고 JS 번들에서 동적 추출.
# ============================================================
PAPAGO_BASE = "https://papago.naver.com"
PAPAGO_DECT = "https://papago.naver.com/apis/langs/dect"
PAPAGO_TRANS = "https://papago.naver.com/apis/n2mt/translate"
_papago_key_cache = None


def _papago_key(force=False):
    global _papago_key_cache
    if _papago_key_cache and not force:
        return _papago_key_cache
    home = _http_get(PAPAGO_BASE, headers={"User-Agent": UA})
    m = re.search(r"/main\.[a-zA-Z0-9]+\.chunk\.js", home)
    if not m:
        m = re.search(r"/[a-zA-Z0-9_.\-]+\.chunk\.js", home)
    if not m:
        raise RuntimeError("파파고 JS 번들 주소를 찾지 못했습니다.")
    js = _http_get(PAPAGO_BASE + m.group(0), headers={"User-Agent": UA})
    km = re.search(r"v\d+\.\d+\.\d+_[a-z0-9]+", js)
    if not km:
        raise RuntimeError("파파고 서명 키를 추출하지 못했습니다.")
    _papago_key_cache = km.group(0)
    return _papago_key_cache


def _papago_auth(api_url, key):
    device_id = str(uuid.uuid4())
    timestamp = str(int(time.time() * 1000))
    message = f"{device_id}\n{api_url}\n{timestamp}".encode()
    digest = hmac.digest(key.encode(), message, "MD5")
    signature = base64.b64encode(digest).decode()
    return device_id, timestamp, f"PPG {device_id}:{signature}"


def _papago_headers(device_id, timestamp, auth):
    return {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "device-type": "pc", "user-agent": UA,
        "authorization": auth, "timestamp": timestamp, "deviceId": device_id,
        "referer": PAPAGO_BASE, "x-apigw-partnerid": "papago",
    }


def _papago_detect(text, key):
    device_id, timestamp, auth = _papago_auth(PAPAGO_DECT, key)
    headers = _papago_headers(device_id, timestamp, auth)
    raw = _http_post(PAPAGO_DECT, {
        "authorization": auth, "timestamp": timestamp,
        "deviceId": device_id, "query": text,
    }, headers)
    return json.loads(raw).get("langCode")


def _papago_request(text, source, target, key):
    device_id, timestamp, auth = _papago_auth(PAPAGO_TRANS, key)
    headers = _papago_headers(device_id, timestamp, auth)
    data = {
        "authorization": auth, "timestamp": timestamp, "deviceId": device_id,
        "locale": "ko", "dict": "true", "dictDisplay": "30",
        "honorific": "false", "instant": "false", "paging": "true",
        "source": source, "target": target, "text": text,
    }
    raw = _http_post(PAPAGO_TRANS, data, headers)
    return json.loads(raw)["translatedText"]


def papago_translate(text, source, target):
    key = _papago_key()
    src = source
    if src == "auto":
        detected = _papago_detect(text, key)
        if detected and detected != "unk":
            src = detected
    try:
        translated = _papago_request(text, src, target, key)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            key = _papago_key(force=True)
            translated = _papago_request(text, src, target, key)
        else:
            raise
    return translated, src


# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(page_title="Custom Translator", page_icon="🌐", layout="centered")

# 스타일: 버튼 파란색 고정 / 라디오 동그라미 파란색 / 모바일 대응
st.markdown(
    """
    <style>
    /* 번역 버튼: 파란색 고정 (hover/클릭 시에도 색 변화 없음) */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"],
    .stButton > button[data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover,
    .stButton > button[kind="primary"]:active,
    .stButton > button[kind="primary"]:focus,
    .stButton > button[kind="primary"]:focus:not(:active) {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }

    /* 모바일: From/To 컬럼을 세로로 쌓아 좁은 화면에서도 편하게 */
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Custom Translator")
st.caption("구글 · 파파고 무료 웹 엔진을 직접 호출하는 올인원 번역기 (API 키 불필요)")

# ---- 1) 번역 엔진 선택 ----
engine = st.radio(
    "번역 엔진을 선택하세요",
    ["🌐  Google Translate", "🟢  Naver Papago"],
    horizontal=True,
)
is_google = "Google" in engine
engine_name = "Google Translate" if is_google else "Naver Papago"

# 엔진별 지원 언어 개수 안내 (구글=파란 info / 파파고=초록 success)
if is_google:
    st.info(f"선택된 엔진:  🌐  **Google Translate**  ·  지원 언어 {len(GOOGLE_LANGS)}개")
else:
    st.success(f"선택된 엔진:  🟢  **Naver Papago**  ·  지원 언어 {len(PAPAGO_LANGS)}개")

langs = GOOGLE_LANGS if is_google else PAPAGO_LANGS
from_options = ["자동 감지 (auto)"] + list(langs.keys())
to_options = list(langs.keys())
to_default = to_options.index("한국어 (ko)") if "한국어 (ko)" in to_options else 0

# ---- 2) 언어 선택 (좌우 배치) ----
col_from, col_to = st.columns(2)
with col_from:
    from_label = st.selectbox("원문 언어 (From)", from_options, index=0)
with col_to:
    to_label = st.selectbox("번역할 언어 (To)", to_options, index=to_default)

src_code = "auto" if from_label.startswith("자동 감지") else langs[from_label]
tgt_code = langs[to_label]

# ---- 3) 텍스트 입력 ----
text = st.text_area("번역할 내용을 입력하세요", height=160, placeholder="여기에 문장이나 긴 글을 입력...")

# ---- 4) 번역 버튼 + 결과 ----
if st.button("번역", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("⚠️  번역할 텍스트를 입력해 주세요.")
    elif src_code != "auto" and src_code == tgt_code:
        st.warning("⚠️  원문 언어와 번역할 언어가 같습니다. 다른 언어를 선택해 주세요.")
    else:
        with st.spinner(f"{engine_name} 로 번역 중입니다..."):
            try:
                if is_google:
                    translated, used_src = google_translate(text, src_code, tgt_code)
                else:
                    translated, used_src = papago_translate(text, src_code, tgt_code)
            except Exception as e:
                translated = None
                st.error(f"{engine_name} 번역 실패  →  {type(e).__name__}: {e}\n\n"
                         "비공식 웹 엔드포인트라 일시적으로 막혔을 수 있습니다. 잠시 후 다시 시도해 주세요.")

        if translated:
            badge = "🌐 Google Translate" if is_google else "🟢 Naver Papago"
            src_show = f"{used_src} (자동 감지)" if src_code == "auto" else used_src
            st.success(f"**{badge}**  ·  {src_show}  →  {tgt_code}")
            st.text_area("번역 결과", value=translated, height=160)

st.divider()
st.caption("※ 비공식 무료 웹 엔드포인트 기반 — 잦은 요청 시 일시 차단될 수 있습니다.")
st.markdown(
    "<div style='text-align:center; font-size:0.7rem; color:#9aa0a6; "
    "letter-spacing:0.5px; margin-top:0.4rem;'>PRODUCED BY 2712 · AI ASSISTED WEB PROJECT</div>",
    unsafe_allow_html=True,
)