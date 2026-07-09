from sqlalchemy import create_engine, text
import dotenv
import os

def get_connection():
    dotenv.load_dotenv()
    con_path = f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/{os.getenv("POSTGRES_DB")}'
    con = create_engine(con_path)
    return con

def model(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS gold.stock_features"))
        conn.execute(text(
            '''CREATE TABLE gold.stock_features AS WITH 
            first_metrics AS (
            SELECT 
            sto.ticker,
            sto.date,
            sto.market,
            sto.close AS today_close,
            LAG(sto.close, 1) OVER(PARTITION BY sto.ticker ORDER BY sto.date) AS yesterday_close
            FROM silver.all_stocks sto
            ),
            midle_metrics AS (
            SELECT
            fm.*,
            ROUND(CAST((fm.today_close - fm.yesterday_close) / fm.yesterday_close * 100 AS decimal), 2) AS daily_variation_pct
            FROM first_metrics fm
            ),
            last_metrics AS (
            SELECT
            md.*,
            AVG(md.daily_variation_pct) OVER(PARTITION BY md.ticker ORDER BY md.date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_avg_variation,
            STDDEV(md.daily_variation_pct) OVER(PARTITION BY md.ticker ORDER BY md.date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_stddev_variation,
            COUNT(md.daily_variation_pct) OVER(PARTITION BY md.ticker ORDER BY md.date ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_observation,
            SUM(md.daily_variation_pct) OVER(PARTITION BY md.market, md.date) AS sum_daily_market_variation_pct,
            COUNT(md.daily_variation_pct) OVER(PARTITION BY md.market, md.date) AS count_daily_market_variation_pct,
            SUM(POWER(md.daily_variation_pct, 2)) OVER(PARTITION BY md.market, md.date) AS sum_squared_daily_market_variation_pct
            FROM midle_metrics md
            ),
            pre_features AS (
            SELECT
            lm.*,
            ((lm.sum_daily_market_variation_pct - lm.daily_variation_pct ) / (lm.count_daily_market_variation_pct - 1)) AS exclusive_daily_market_variation_avg,
            ROUND(CAST((lm.daily_variation_pct - lm.rolling_avg_variation) / lm.rolling_stddev_variation AS decimal), 2) AS self_zscore
            FROM last_metrics lm
            ),
            midle_features AS (
            SELECT 
            pf.*,
            (pf.sum_squared_daily_market_variation_pct - POWER(pf.daily_variation_pct, 2)) / (pf.count_daily_market_variation_pct - 1) - POWER(pf.exclusive_daily_market_variation_avg, 2) AS exclusive_variancy
            FROM pre_features pf
            ),
            ready_features AS (
            SELECT 
            mf.*,
            SQRT(mf.exclusive_variancy) AS exclusive_market_stddev
            FROM midle_features mf
            )
            SELECT 
            rf.market, 
            rf.ticker,
            rf.date,
            rf.today_close, 
            rf.daily_variation_pct, 
            rf.self_zscore,
            rf.rolling_observation,
            ROUND(CAST((rf.daily_variation_pct - rf.exclusive_daily_market_variation_avg ) / rf.exclusive_market_stddev AS decimal), 2) AS daily_market_zscore
            FROM ready_features rf'''))
        conn.commit()

def main():
    con = get_connection()
    model(con)

if __name__ == '__main__':
    main()
