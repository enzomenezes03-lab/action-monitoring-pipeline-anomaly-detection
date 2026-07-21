import yfinance as yf
from db_connection import get_connection
import json
import os

DIR = os.path.dirname(__file__)
TICKERS_PATH = os.path.join(DIR, "..", "config", "tickers.json")

def extract_yfinance_data():
    with open(TICKERS_PATH, 'r') as arq_leitura:
        tickers = json.load(arq_leitura)
        eua_tickers = tickers["eua"]
    df = yf.download(eua_tickers, period='12mo')
    if df.empty:
        raise ValueError("Download carregou um DataFrame vazio!")
    df = df.stack(future_stack=True)
    df.index.names = ['date', 'ticker']
    df = df.reset_index()
    return df

def load_to_bronze(table_name, con, df):
    df.to_sql(table_name, con, schema='bronze', if_exists='replace')

def main():
    con = get_connection()
    df = extract_yfinance_data()
    load_to_bronze('yfinance', con, df)

if __name__ == '__main__':
    main()