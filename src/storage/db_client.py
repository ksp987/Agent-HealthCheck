# src/storage/db_client.py

import psycopg2

try:
    conn = psycopg2.connect(
        host="adminonsyspg1.postgres.database.azure.com",
        port="5432",
        database="DB1",
        user="adminonsyspg1",
        password="NXIWTa6Zw8VtStrtwYlg#1"
    )
    cursor = conn.cursor()
    # Execute SQL queries
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
    cursor.close()
    conn.close()
except psycopg2.Error as e:
    print(f"Error connecting to PostgreSQL: {e}")