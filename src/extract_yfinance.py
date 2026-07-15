import yfinance as yf
from sqlalchemy import create_engine
import json
import os

DIR = os.path.dirname(__file__)
TICKERS_PATH = os.path.join(DIR, "..", "config", "tickers.json")

def extract_yfinance_data():
    with open(TICKERS_PATH, 'r') as arq_leitura:
        tickers = json.load(arq_leitura)
        eua_tickers = tickers["eua"]
    df = yf.download(eua_tickers, period='12mo')
    df = df.stack(future_stack=True)
    df.index.names = ['date', 'ticker']  # nomeia os dois níveis do índice
    df = df.reset_index()
    return df

def get_connection():
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@postgres:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def load_to_bronze(table_name, con, df):
    df.to_sql(table_name, con, schema='bronze', if_exists='replace')

def main():
    con = get_connection()
    df = extract_yfinance_data()
    load_to_bronze('yfinance', con, df)

if __name__ == '__main__':
    main()