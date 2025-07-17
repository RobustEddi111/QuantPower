# -*- coding: UTF-8 -*-
import sqlite3
import csv

import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='qintao1997',
    database='sky_take_out',
    charset='utf8'
)

cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    name TEXT,
                    age TEXT,
                    email TEXT
                )''')

with open('test.CSV', 'r') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        cursor.execute('''INSERT INTO users (name, age, email) VALUES (%s, %s, %s)''',
                       (row['运行单位'], row['项目类型'], row['天气']))


conn.commit()
conn.close()
