import yfinance as yf
from sqlalchemy import create_engine
import json
import os
import dotenv

def extract_yfinance_data():
    with open('config/tickers.json', 'r') as arq_leitura:
        tickers = json.load(arq_leitura)
        eua_tickers = tickers["eua"]
    df = yf.download(eua_tickers, period='12mo')
    df = df.stack(future_stack=True)
    df = df.reset_index()
    return df

def get_connection():
    dotenv.load_dotenv()
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def load_to_bronze(table_name, con, df):
    df.to_sql(table_name, con, schema='bronze', if_exists='replace')

if __name__ == '__main__':
    con = get_connection()
    df = extract_yfinance_data()
    load_to_bronze('yfinance', con, df)