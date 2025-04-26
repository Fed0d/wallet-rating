import altair as alt
import streamlit as st

from extractor.feature_extractor import process_dataframe
from fetcher.data_fetcher import collect_all_to_dataframe
from predictor.rating_predictor import predict_ratings

st.title("Wallet Rating App!")

explorer = st.selectbox("Сервис данных:", ["Etherscan", "Arbiscan"])
api_key = st.text_input(f"API ключ для {explorer}:", type="password")
end_date = st.date_input("Сбор транзакций до:")

if not api_key:
    st.warning("Введите API ключ, чтобы продолжить.")
    st.stop()

mode = st.radio("Режим ввода адресов:", ["Один кошелек", "Файл с адресами"])
addresses = []
if mode == "Один кошелек":
    addr = st.text_input("Адрес кошелька:")
    if addr and addr.startswith("0x") and len(addr) == 42:
        addresses = [addr]
    elif addr:
        st.error("Некорректный Ethereum адрес")
else:
    uploaded = st.file_uploader(".txt файл с адресами", type=["txt"])
    if uploaded:
        lines = uploaded.getvalue().decode("utf-8").splitlines()
        addresses = [w.strip() for w in lines if w.strip()]

if addresses and st.button("Рассчитать рейтинг кошельков"):
    with st.spinner("Сбор данных и вычисление признаков..."):
        df = collect_all_to_dataframe(addresses, api_key, end_date.strftime("%Y-%m-%d"))
        feats_df = process_dataframe(df, end_date.strftime("%Y-%m-%d"))
    st.success(
        f"Найдено {len(df)} транзакций, рассчитано признаков для {len(feats_df)} адресов"
    )
    st.subheader("Транзакции")
    st.dataframe(df)
    st.subheader("Признаки Sybil")
    st.dataframe(feats_df)
    with st.spinner("Прогнозирование рейтинга..."):
        ratings_df = predict_ratings(feats_df)
    st.subheader("Рейтинг кошельков")

    def style_rating(val):
        mapping = {
            "A": "#d4edda",  # light green
            "B": "#fff3cd",  # light yellow
            "C": "#ffe5b4",  # light orange
            "D": "#f8d7da",  # light red
        }
        bg = mapping.get(val, "")
        # use black text for good contrast on light backgrounds
        return f"background-color: {bg}; color: black; font-weight: bold;"

    styled = ratings_df.style.applymap(style_rating, subset=["our_rating"])
    st.dataframe(styled)

    # --- Additional visualizations ---
    st.subheader("Распределение рейтингов")
    rating_counts = ratings_df["our_rating"].value_counts().sort_index()
    st.bar_chart(rating_counts)

    st.subheader("Гистограмма Sybil Score")
    hist = (
        alt.Chart(ratings_df)
        .mark_bar()
        .encode(
            alt.X("sybil_score", bin=alt.Bin(maxbins=20), title="Sybil Score"),
            alt.Y("count()", title="Количество кошельков"),
        )
    )
    st.altair_chart(hist, use_container_width=True)

    st.subheader("Зависимость Sybil Score от числа транзакций")
    merged = feats_df[["address", "tx_count"]].merge(ratings_df, on="address")
    scatter = (
        alt.Chart(merged)
        .mark_circle(size=60)
        .encode(
            x=alt.X("tx_count", title="Количество транзакций"),
            y=alt.Y("sybil_score", title="Sybil Score"),
            color="our_rating",
            tooltip=["address", "tx_count", "sybil_score", "our_rating"],
        )
    )
    st.altair_chart(scatter, use_container_width=True)
