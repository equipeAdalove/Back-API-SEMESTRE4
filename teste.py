import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="api4ads",
        user="postgres",
        password="1234",
        options="-c client_encoding=UTF8"
    )
    print("✅ Conexão OK forçando UTF-8")
    conn.close()
except Exception as e:
    print("❌ Erro ao conectar:", e)