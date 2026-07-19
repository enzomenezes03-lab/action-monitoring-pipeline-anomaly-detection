import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
import pandas as pd
import dotenv
import os
import plotly.graph_objects as go

def get_connection():
    dotenv.load_dotenv()
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def load_dashboard_data(connection):
    df = pd.read_sql('''SELECT
                    sf.ticker,
                    sf.date,
                    sf.market,
                    sf.today_close,
                    sf.daily_variation_pct,
                    sf.self_zscore,
                    sf.daily_market_zscore,
                    isf.anomaly_flag,
                    isf.anomaly_score
                FROM gold.stock_features sf
                JOIN gold.isolation_forest isf
                    ON sf.ticker = isf.ticker AND sf.date = isf.date''', connection)

    df['date'] = pd.to_datetime(df['date'])

    return df

def render_summary(df):
    st.title('Quão comum é a ocorrência de anomalias nas principais ações da B3 e S&P?')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total de Anomalias:', len(df[df['anomaly_flag'] == -1]))
    with col2:
        st.metric('Anomalias na B3:', len(df[(df['anomaly_flag'] == -1) & (df['market'] == 'brasil')]))
    with col3:
        st.metric('Anomalias na S&P:', len(df[(df['anomaly_flag'] == -1) & (df['market'] == 'eua')]))
    st.caption('Últimos 12 meses de pregão para ações da S&P e 3 meses para B3')

def render_filters(df):
    st.sidebar.header("Filtros")

    mercados = sorted(df["market"].unique().tolist())
    mercado_selecionado = st.sidebar.selectbox("Mercado", mercados)

    tickers_disponiveis = sorted(df[df["market"] == mercado_selecionado]["ticker"].unique().tolist())

    tickers_selecionados = st.sidebar.multiselect("Ticker", tickers_disponiveis, default=tickers_disponiveis)

    data_min = df["date"].min()
    data_max = df["date"].max()
    intervalo_datas = st.sidebar.date_input("Intervalo de datas", value=(data_min, data_max), min_value=data_min, max_value=data_max)

    return mercado_selecionado, tickers_selecionados, intervalo_datas

def filter_data(df, mercado, tickers, intervalo_datas):
    df_filtrado = df.copy()

    df_filtrado = df_filtrado[df_filtrado["market"] == mercado]

    df_filtrado = df_filtrado[df_filtrado["ticker"].isin(tickers)]

    data_inicio, data_fim = intervalo_datas
    df_filtrado = df_filtrado[(df_filtrado["date"] >= pd.Timestamp(data_inicio)) & (df_filtrado["date"] <= pd.Timestamp(data_fim))]

    return df_filtrado

def render_chart(df_filtrado):
    st.subheader('Comportamento das ações e anomalias no período especificado: ')
    fig = px.line(df_filtrado, x="date", y="today_close", color="ticker")

    anomalias = df_filtrado[df_filtrado["anomaly_flag"] == -1]

    fig.add_trace(go.Scatter(
        x=anomalias["date"],
        y=anomalias["today_close"],
        mode="markers",
        marker=dict(size=10, color="red", symbol="circle"),
        name="Anomalia"
    ))

    st.plotly_chart(fig)

def render_table(df_filtrado):
    st.subheader("Anomalias detectadas")

    anomalias = df_filtrado[df_filtrado["anomaly_flag"] == -1]

    colunas = ["ticker", "date", "today_close", "daily_variation_pct", "self_zscore", "daily_market_zscore", "anomaly_score"]
    anomalias = anomalias[colunas].sort_values("anomaly_score")

    st.dataframe(anomalias)

if __name__ == '__main__':
    con = get_connection()
    df = load_dashboard_data(con)
    render_summary(df)
    st.divider()
    market, tickers, date_interval = render_filters(df)
    df_filtrado = filter_data(df, market, tickers, date_interval)
    render_chart(df_filtrado)
    render_table(df_filtrado)