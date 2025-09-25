# src/storage/db_client.py

import psycopg2
import os
from dotenv import load_dotenv

# Load env vars from .env (local dev only)
load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            sslmode="require"  # Azure PostgreSQL requires SSL
        )
        return conn
    except psycopg2.Error as e:
        raise RuntimeError(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        print("PostgreSQL version:", cursor.fetchone())
        cursor.close()
        conn.close()
    except Exception as e:
        print(e)
