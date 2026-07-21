import os
import dotenv
from sqlalchemy import create_engine

dotenv.load_dotenv()

def get_connection():
    con_path = f'postgresql://{os.getenv("SUPABASE_USER")}:{os.getenv("SUPABASE_PASSWORD")}@{os.getenv("SUPABASE_HOST")}:5432/postgres'
    con = create_engine(con_path)
    return con