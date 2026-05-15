import sqlite3
import pandas as pd
import os

# 你的数据库路径
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cafeteria.db')

try:
    conn = sqlite3.connect(db_path)
    # 读取 MenuItem 表里的菜名和图片路径
    df = pd.read_sql_query("SELECT name, image FROM menu_item LIMIT 20", conn)
    print("🍽️ 数据库菜单图片路径核对：")
    print("-" * 50)
    print(df)
    conn.close()
except Exception as e:
    print(f"❌ 读取数据库失败: {e}")