import sqlite3
from datetime import datetime

# название бд
DB_NAME = 'guitars.db'

# подключение к бд
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# инициализация бд (и создание таблицы, если ее нет)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guitars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            color_name TEXT,
            color_hex TEXT,
            price INTEGER,
            url TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# получение всех производителей для списка
def get_brands(column, filters=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT {column} FROM guitars"
    params = []

    if filters:
        active_filters = {k: v for k, v in filters.items() if v is not None}
        if active_filters:
            conditions = [f"{k} = ?" for k in active_filters.keys()]
            query += " WHERE " + " AND ".join(conditions)
            params = list(active_filters.values())

    cursor.execute(query, params)
    values = [row[0] for row in cursor.fetchall()]
    conn.close()
    return values

# получение кодов цветов
def get_colors_with_hex(brand, model):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT DISTINCT color_name, color_hex FROM guitars WHERE brand = ? AND model = ?"
    cursor.execute(query, (brand, model))
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row['color_name'], "hex": row['color_hex']} for row in rows]

# поиск
def final_search(brand, model, color, max_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT brand, model, color_name, price, url 
        FROM guitars 
        WHERE brand = ? AND model = ? AND color_name = ? AND price <= ?
        ORDER BY price ASC
    '''
    cursor.execute(query, (brand, model, color, max_price))
    results = cursor.fetchall()
    conn.close()
    return results