import streamlit as st
import pandas as pd
import altair as alt
import locale
import math

# 한국어 로케일 설정

# Streamlit Debug Mode 활성화
st.set_page_config(page_title='[무인양품] 부드러운 멀티 쿠션 시리즈 (소파쿠션) 리뷰 분석 대시보드 (10월 20일 업데이트)')

debug = True

# 파일 참조
st.title('[무인양품] 부드러운 멀티 쿠션 시리즈 (소파쿠션) 리뷰 분석 대시보드 (10월 20일 업데이트)')
st.markdown('---')

# 이미 존재하는 파일 참조
file_path = 'MUJI_reviews.xlsx'

# 파일 읽기
if file_path.endswith('csv'):
    df = pd.read_csv(file_path)
elif file_path.endswith('xlsx'):
    df = pd.read_excel(file_path)

# 날짜 컬럼을 datetime 형식으로 변환
df['리뷰 작성시간'] = pd.to_datetime(df['리뷰 작성시간'], format='%Y-%m-%d', errors='coerce')

# 추가 정보 값에 따른 카테고리 정의
category_mapping = {
    1: '포장 상태 및 배송 문제',
    2: '쿠션의 쿠션감 관련 불만',
    3: '재질 및 내구성',
    4: '냄새 및 오염 문제',
    5: '기능 및 사용성',
    6: '기타'
}
df['category'] = df['Additional'].map(category_mapping)

# 각 카테고리별 부정 리뷰 개수 및 최근 7일 평균 대비 변화량 계산
cols = st.columns(4)
with cols[0]:
    total_reviews_20 = len(df[(df['리뷰 작성시간'] >= pd.to_datetime('2024-10-14')) & (df['리뷰 작성시간'] <= pd.to_datetime('2024-10-20'))])
    st.metric(
        label='10월 20일 이전 7일 리뷰 개수 합',
        value=f'{total_reviews_20}'
    )

cols = st.columns(4)
summary_20 = []
for i, category in enumerate(category_mapping.values()):
    col = cols[i % len(cols)]
    category_df = df[df['category'] == category]
    count_20 = len(category_df[(category_df['리뷰 작성시간'] >= pd.to_datetime('2024-10-14')) & (category_df['리뷰 작성시간'] <= pd.to_datetime('2024-10-20'))])
    avg_count = len(category_df) / (len(category_df['리뷰 작성시간'].unique()) / 7) if len(category_df['리뷰 작성시간'].unique()) > 0 else 0
    delta = ((count_20 - avg_count) / avg_count * 100) if avg_count > 0 else 0
    summary_20.append(f'{category}: 최근 7일 리뷰 개수: {count_20}, 7일 평균 대비 변화: {delta:+.2f}%')

    with col:
        st.metric(
            label=f'{category} 최근 7일 리뷰 개수',
            value=f'{count_20}',
            delta=f'{delta:+.2f}%',
            delta_color='normal'
        )
        
# Streamlit에서 보기 간격 선택 버튼 추가
interval = st.radio('보기 간격 선택', ['1일 간격', '7일 간격', '1개월 간격'], index=1, horizontal=True)

# 선택된 간격에 따라 sentiment 값이 1인 데이터 집계
sentiment_1_df = df[df['sentiment'] == 1]
if interval == '1일 간격':
    all_dates = pd.date_range(start='2024-10-12', end='2024-10-20', freq='D')
    sentiment_1_count = sentiment_1_df.set_index('리뷰 작성시간').resample('D').size().reindex(all_dates, fill_value=0).reset_index(name='count')
    sentiment_1_count.rename(columns={'index': '리뷰 작성시간'}, inplace=True)
elif interval == '7일 간격':
    sentiment_1_count = sentiment_1_df.set_index('리뷰 작성시간').resample('W').size().reset_index(name='count')
elif interval == '1개월 간격':
    sentiment_1_count = sentiment_1_df.set_index('리뷰 작성시간').resample('M').size().reset_index(name='count')

# 데이터가 존재하는 범위 내에서만 그래프를 그리도록 수정
if not sentiment_1_count.empty:
    # Altair를 사용해 sentiment 값이 1인 리뷰 빈도수를 선 그래프로 표시 (주황색 선)
    sentiment_line_chart = alt.Chart(sentiment_1_count).mark_line(color='orange').encode(
        x=alt.X('리뷰 작성시간:T', title='날짜', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45, tickCount='day')),
        y=alt.Y('count:Q', title='부정적인 댓글 개수')
    ).properties(
        title='날짜별 부정적인 댓글 개수'
    )

    st.altair_chart(sentiment_line_chart, use_container_width=True)
else:
    st.warning("선택한 간격에 해당하는 데이터가 없습니다.")

# 카테고리 선택란 추가
selected_categories = st.multiselect('카테고리 선택', options=list(category_mapping.values()), default=list(category_mapping.values()))
filtered_df = df[df['category'].isin(selected_categories)]

# 선택된 간격에 따라 카테고리별 데이터 집계
if interval == '1일 간격':
    all_dates = pd.date_range(start='2024-10-12', end='2024-10-20', freq='D')
    category_count = filtered_df.set_index('리뷰 작성시간').groupby([pd.Grouper(freq='D'), 'category']).size().unstack(fill_value=0).reindex(all_dates, fill_value=0).stack().reset_index(name='count')
    category_count.rename(columns={'level_0': '리뷰 작성시간'}, inplace=True)
elif interval == '7일 간격':
    category_count = filtered_df.set_index('리뷰 작성시간').groupby([pd.Grouper(freq='W'), 'category']).size().reset_index(name='count')
elif interval == '1개월 간격':
    category_count = filtered_df.set_index('리뷰 작성시간').groupby([pd.Grouper(freq='M'), 'category']).size().reset_index(name='count')

# 데이터가 존재하는 범위 내에서만 그래프를 그리도록 수정
if not category_count.empty:
    # Altair를 사용해 각 카테고리의 빈도수를 누적 막대 그래프로 표시
    category_bar_chart = alt.Chart(category_count).mark_bar().encode(
        x=alt.X('리뷰 작성시간:T', title='날짜', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45)),
        y=alt.Y('count:Q', title='리뷰 빈도수', stack='zero'),
        color='category:N'
    ).properties(
        title='날짜별 리뷰 카테고리 빈도수 (누적 막대 그래프)'
    )

    st.altair_chart(category_bar_chart, use_container_width=True)

    # Altair를 사용해 각 카테고리의 빈도수를 선 그래프로 표시
    category_line_chart = alt.Chart(category_count).mark_line().encode(
        x=alt.X('리뷰 작성시간:T', title='날짜', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45)),
        y=alt.Y('count:Q', title='리뷰 빈도수'),
        color='category:N'
    ).properties(
        title='날짜별 리뷰 카테고리 빈도수 (선 그래프)'
    )

    st.altair_chart(category_line_chart, use_container_width=True)
else:
    st.warning("선택한 간격에 해당하는 데이터가 없습니다.")

# '기타' 카테고리의 10월 20일 데이터 필터링
etc_category_20_df = df[(df['category'] == '기타') & (df['리뷰 작성시간'].dt.date == pd.to_datetime('2024-10-20').date())]

# '기타' 카테고리의 10월 20일 데이터 테이블 표시
if not etc_category_20_df.empty:
    st.write("기타 카테고리의 10월 20일 추가된 리뷰:")
    st.dataframe(etc_category_20_df[['작성 리뷰 평점', '리뷰 내용']])
else:
    st.info("10월 20일에 추가된 '기타' 카테고리 데이터가 없습니다.")
