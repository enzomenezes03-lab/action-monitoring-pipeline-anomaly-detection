from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import os

spark = SparkSession.builder \
    .appName("transform_silver") \
    .config("spark.jars", "/opt/spark_jars/postgresql-42.7.3.jar") \
    .config("spark.driver.extraClassPath", "/opt/spark_jars/postgresql-42.7.3.jar") \
    .getOrCreate()

def read_bronze_table(spark_con, table_name):
    df = spark_con.read.format("jdbc") \
        .option("url", f"jdbc:postgresql://postgres:5432/{os.getenv('POSTGRES_DB')}") \
        .option("dbtable", f"bronze.{table_name}") \
        .option("user", f"{os.getenv('POSTGRES_USER')}") \
        .option("password", f"{os.getenv('POSTGRES_PASSWORD')}") \
        .option("driver", "org.postgresql.Driver") \
        .load()

    return df

def transform(df_yfinance, df_brapi):
    for coluna in df_yfinance.columns:
        df_yfinance = df_yfinance.withColumnRenamed(f"{coluna}", f"{coluna.lower()}")
    df_yfinance = df_yfinance.withColumn('date', F.col('date').cast('date'))
    if "adj close" in df_yfinance.columns:
        df_yfinance = df_yfinance.drop('adj close')

    df_yfinance = df_yfinance.withColumn('market', F.lit("eua"))
    df_brapi = df_brapi.withColumn("market", F.lit("brasil"))

    df_brapi = df_brapi.withColumn('date', F.from_unixtime(F.col('date')).cast("date"))
    if "adjustedClose" in df_brapi.columns:
        df_brapi = df_brapi.drop('adjustedClose')

    union_df = df_brapi.unionByName(df_yfinance)
    return union_df

def load_to_silver(table_name, df):
    df.write \
        .format("jdbc") \
        .option("url", f"jdbc:postgresql://postgres:5432/{os.getenv('POSTGRES_DB')}") \
        .option("dbtable", f"silver.{table_name}") \
        .option("user", f"{os.getenv('POSTGRES_USER')}") \
        .option("password", f"{os.getenv('POSTGRES_PASSWORD')}") \
        .option("driver", "org.postgresql.Driver") \
        .mode("overwrite") \
        .save()

if __name__ == '__main__':
    df_yf = read_bronze_table(spark, 'yfinance')
    df_brapi = read_bronze_table(spark, 'brapi')
    df_union = transform(df_yf, df_brapi)
    load_to_silver('all_stocks', df_union)
