import pymysql

connection = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="ecommerce",
    password="ecommerce_2026",
    database="ecommerce",
    charset="utf8mb4"
)

try:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT DATABASE(), VERSION()"
        )

        result = cursor.fetchone()

        print("数据库:", result[0])
        print("MySQL版本:", result[1])

finally:
    connection.close()
