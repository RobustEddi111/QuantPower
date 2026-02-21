import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=13306,
    user="ptrader",
    password="2744798981",
    charset="utf8mb4",
    connect_timeout=5,
)

with conn.cursor() as cur:
    cur.execute("SELECT VERSION();")
    print(cur.fetchone())

conn.close()
print("OK")
