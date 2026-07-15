import pandas as pd
from sqlalchemy import create_engine
import os
import json
import requests as rq

DIR = os.path.dirname(__file__)
TICKERS_PATH = os.path.join(DIR, "..", "config", "tickers.json")

def extract_brapi_data():
    with open(TICKERS_PATH, 'r') as arq_leitura:
        tickers = json.load(arq_leitura)
        tickers_br = tickers["brasil"]

    list_dfs = []
    for ticker in tickers_br:
        http_answer = rq.get(f'https://brapi.dev/api/v2/stocks/historical?symbols={ticker}&range=3mo&interval=1d',
                            headers={"Authorization": f'Bearer {os.getenv("BRAPI_TOKEN")}'})
        data_json = http_answer.json()
        df = pd.DataFrame(data_json["results"][0]["data"]["historicalDataPrice"])
        df['ticker'] = ticker
        list_dfs.append(df)

    final_df = pd.concat(list_dfs)

    return final_df

def get_connection():
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@postgres:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def load_to_bronze(table_name, con, df):
    df.to_sql(table_name, con, schema='bronze', if_exists='replace')

def main():
    df = extract_brapi_data()
    con = get_connection()
    load_to_bronze('brapi', con, df)

if __name__ == "__main__":
    main()

