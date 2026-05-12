import sqlite3
from datetime import datetime
from database import init_db


def start():
    # Создание бд
    init_db()
    conn = sqlite3.connect('guitars.db')
    cursor = conn.cursor()

    # Очистка таблицы, если есть какие-то данные вообще
    cursor.execute("DELETE FROM guitars")

    # Рыбное наполнение
    data = [
        ('Cort', 'KX307MS-OPBK', 'Черный', '#131215', 33557, 'https://avito.ru/1'),
        ('Cort', 'KX307MS-OPM', 'Красный', '#8A2F32', 34308, 'https://avito.ru/2'),
        ('Cort', 'KX507MS-Pale-Moon-NBB', 'Коричневый', '#302D2E-#B7966F', 64013, 'https://avito.ru/3'),

        ('Ibanez', 'GRG121DX', 'Walnut Flat', '#282118-##47260F', 24237, 'https://avito.ru/4'),
        ('Ibanez', 'GRG120QASP-BGD', 'Синий', '#27285E-#057E95', 39804, 'https://avito.ru/5'),
        ('Ibanez', 'RG450QMB-TGB', 'Черный', '#0B0B0B-#777C78', 92163, 'https://avito.ru/6'),
    ]

    # Запрос на добавление в бд
    for item in data:
        cursor.execute('''
            INSERT INTO guitars (brand, model, color_name, color_hex, price, url, added_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (*item, datetime.now()))
    conn.commit()
    conn.close()
    print("Таблица создана, наполнена тестовыми данными")

if __name__ == "__main__":
    start()