from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
import pandas as pd
import os

def get_connection():
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@postgres:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def load_df(connection):
    df = pd.read_sql('''SELECT
         sf.market,
         sf.ticker,
         sf.date,
         sf.daily_variation_pct,
         sf.self_zscore,
         sf.daily_market_zscore
         FROM 
         gold.stock_features sf
         WHERE sf.rolling_observation = 14''', connection)

    return df

def split_by_market(df):
    df_brasil = df[df['market'] == "brasil"]
    df_eua = df[df['market'] == "eua"]

    return df_brasil, df_eua

def apply_isolation_forest(list_dfs):
    dfs_after = []
    for df in list_dfs:
        features = df[['daily_variation_pct', 'self_zscore', 'daily_market_zscore']]
        model = IsolationForest(contamination=0.03, random_state=42)
        model.fit(features)
        predicts = model.predict(features)
        scores = model.decision_function(features)
        df['anomaly_flag'] = predicts
        df['anomaly_score'] = scores
        dfs_after.append(df)
    return dfs_after

def load_final_df(list_dfs, connection, schema, table_name):
    final_df = pd.concat(list_dfs)
    final_df.to_sql(table_name, connection, schema=schema, if_exists='replace')

def main():
    conex = get_connection()
    full_df = load_df(conex)
    df_br, df_eua = split_by_market(full_df)
    isolation_dfs = apply_isolation_forest([df_br, df_eua])
    load_final_df(isolation_dfs, conex, 'gold', 'isolation_forest')

if __name__ == '__main__':
    main()