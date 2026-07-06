import pandas as pd
import streamlit as st

st.set_page_config(page_title="반려동물 동반 가능 시설 분석", layout="wide")

DATA_PATH = "pet_facilities_dedup.csv.gz"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="utf-8-sig", compression="gzip")
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")
    return df


df = load_data(DATA_PATH)

st.title("🐾 전국 반려동물 동반 가능 시설 분석")
st.caption("출처: 한국문화정보원 · 전국 반려동물 동반 가능 문화시설 위치 데이터 (2025-03-24 기준, 완전 중복행 제거됨)")

# ----------------------------- 사이드바 필터 -----------------------------
st.sidebar.header("필터")

sido_options = sorted(df["시도 명칭"].dropna().unique())
sel_sido = st.sidebar.multiselect("시도", sido_options)

cat2_options = sorted(df["카테고리2"].dropna().unique())
sel_cat2 = st.sidebar.multiselect("카테고리2", cat2_options)

cat3_options = sorted(df["카테고리3"].dropna().unique())
sel_cat3 = st.sidebar.multiselect("카테고리3", cat3_options)

pet_ok = st.sidebar.radio("반려동물 동반 가능여부", ["전체", "가능(Y)만", "불가능(N)만"])
parking = st.sidebar.radio("주차 가능여부", ["전체", "가능(Y)만", "불가능(N)만"])
indoor = st.sidebar.radio("실내 여부", ["전체", "실내(Y)", "실내아님(N)"])
outdoor = st.sidebar.radio("실외 여부", ["전체", "실외(Y)", "실외아님(N)"])

keyword = st.sidebar.text_input("시설명 검색")

filtered = df.copy()
if sel_sido:
    filtered = filtered[filtered["시도 명칭"].isin(sel_sido)]
if sel_cat2:
    filtered = filtered[filtered["카테고리2"].isin(sel_cat2)]
if sel_cat3:
    filtered = filtered[filtered["카테고리3"].isin(sel_cat3)]
if pet_ok == "가능(Y)만":
    filtered = filtered[filtered["반려동물 동반 가능정보"] == "Y"]
elif pet_ok == "불가능(N)만":
    filtered = filtered[filtered["반려동물 동반 가능정보"] == "N"]
if parking == "가능(Y)만":
    filtered = filtered[filtered["주차 가능여부"] == "Y"]
elif parking == "불가능(N)만":
    filtered = filtered[filtered["주차 가능여부"] == "N"]
if indoor == "실내(Y)":
    filtered = filtered[filtered["장소(실내) 여부"] == "Y"]
elif indoor == "실내아님(N)":
    filtered = filtered[filtered["장소(실내) 여부"] == "N"]
if outdoor == "실외(Y)":
    filtered = filtered[filtered["장소(실외)여부"] == "Y"]
elif outdoor == "실외아님(N)":
    filtered = filtered[filtered["장소(실외)여부"] == "N"]
if keyword:
    filtered = filtered[filtered["시설명"].str.contains(keyword, case=False, na=False)]

# ----------------------------- 요약 지표 -----------------------------
total = len(df)
total_filtered = len(filtered)
pet_yes = (filtered["반려동물 동반 가능정보"] == "Y").sum()
pet_ratio = pet_yes / total_filtered * 100 if total_filtered else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("전체 데이터 수", f"{total:,}")
c2.metric("필터 결과 수", f"{total_filtered:,}")
c3.metric("동반 가능(Y) 수", f"{pet_yes:,}")
c4.metric("동반 가능 비율", f"{pet_ratio:.1f}%")

tab1, tab2, tab3 = st.tabs(["📊 개요", "🗺️ 지도", "📋 데이터"])

# ----------------------------- 개요 -----------------------------
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("시도별 시설 수 (상위 15)")
        st.bar_chart(filtered["시도 명칭"].value_counts().head(15))
    with col2:
        st.subheader("카테고리3별 시설 수 (상위 15)")
        st.bar_chart(filtered["카테고리3"].value_counts().head(15))

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("반려동물 동반 가능 여부 (건수)")
        st.bar_chart(filtered["반려동물 동반 가능정보"].value_counts())
    with col4:
        st.subheader("실내 / 실외 시설 비교 (Y 개수)")
        io_df = pd.DataFrame(
            {
                "구분": ["실내", "실외"],
                "개수": [
                    (filtered["장소(실내) 여부"] == "Y").sum(),
                    (filtered["장소(실외)여부"] == "Y").sum(),
                ],
            }
        ).set_index("구분")
        st.bar_chart(io_df)

    st.subheader("입장 가능 동물 크기 분포 (상위 10)")
    st.bar_chart(filtered["입장 가능 동물 크기"].value_counts().head(10))

# ----------------------------- 지도 -----------------------------
with tab2:
    st.subheader("시설 위치 지도")
    map_df = filtered.dropna(subset=["위도", "경도"])
    map_df = map_df[map_df["위도"].between(33, 39) & map_df["경도"].between(124, 132)]
    st.write(f"지도에 표시되는 시설 수: {len(map_df):,}")

    if len(map_df) > 5000:
        st.info("표시 성능을 위해 5,000개를 무작위로 샘플링하여 표시합니다.")
        map_df = map_df.sample(5000, random_state=42)

    if len(map_df):
        st.map(map_df.rename(columns={"위도": "lat", "경도": "lon"})[["lat", "lon"]])
    else:
        st.warning("표시할 위치 데이터가 없습니다.")

# ----------------------------- 데이터 -----------------------------
with tab3:
    st.subheader("상세 데이터")
    default_cols = [
        "시설명",
        "카테고리2",
        "카테고리3",
        "시도 명칭",
        "시군구 명칭",
        "반려동물 동반 가능정보",
        "입장 가능 동물 크기",
        "전화번호",
        "도로명주소",
    ]
    show_cols = st.multiselect("표시할 컬럼 선택", df.columns.tolist(), default=default_cols)
    st.dataframe(filtered[show_cols] if show_cols else filtered, width="stretch", height=500)

    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("필터링된 데이터 CSV 다운로드", csv, "filtered_pet_facilities.csv", "text/csv")
