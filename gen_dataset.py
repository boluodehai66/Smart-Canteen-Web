import sqlite3
import json
import random
import os


def gen():
    # 🌟 绝对路径锁死：确保百分百能找到你的数据库
    db_path = r'D:\pycharm\pycharm project\yida_web\cafeteria.db'

    if not os.path.exists(db_path):
        print(f"❌ 找不到数据库文件，请检查路径：{db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 尝试读取数据
    try:
        cursor.execute("SELECT name, price, calories, carbs, protein, fat, category, campus, floor FROM menu_item")
        all_items = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ 数据库读取失败，可能是表名不对：{e}")
        return
    finally:
        conn.close()

    dataset = []
    # 生成 500 条数据
    for _ in range(500):
        campus = random.choice(["北区", "南区", "西区"])
        floor = random.choice(["一楼", "二楼"])
        budget = random.randint(12, 25)

        local_menu = [i for i in all_items if i['campus'] == campus and i['floor'] == floor]
        if len(local_menu) < 5: continue

        mains = [i for i in local_menu if i['category'] == '主食']
        meats = [i for i in local_menu if i['category'] == '荤菜']
        veggies = [i for i in local_menu if i['category'] == '素菜']

        if not (mains and meats and veggies): continue
        s1 = random.choice(mains);
        s2 = random.choice(meats);
        s3 = random.choice(veggies)

        # 🌟 完美的标准答案格式（不带加粗，带中括号）
        ans = f"### 方案一：营养均衡搭配\n- [主食] {s1['name']} ￥{s1['price']} ({s1['calories']}kcal, 碳水{s1['carbs']}g/蛋白{s1['protein']}g/脂肪{s1['fat']}g)\n"
        ans += f"- [荤菜] {s2['name']} ￥{s2['price']} ({s2['calories']}kcal, 碳水{s2['carbs']}g/蛋白{s2['protein']}g/脂肪{s2['fat']}g)\n"
        ans += f"- [素菜] {s3['name']} ￥{s3['price']} ({s3['calories']}kcal, 碳水{s3['carbs']}g/蛋白{s3['protein']}g/脂肪{s3['fat']}g)\n"
        ans += f"💡 点评：这是一套专为您在{campus}{floor}定制的餐食。"

        dataset.append({
            "messages": [
                {"role": "system", "content": f"你是一个校园AI营养师。当前位置：{campus}{floor}。"},
                {"role": "user", "content": f"我想在{campus}{floor}吃一顿{budget}元左右的饭。"},
                {"role": "assistant", "content": ans}
            ]
        })

    # 保存到 LlamaFactory 的 data 目录下
    out_path = r'D:\pycharm\pycharm project\yida_web\LlamaFactory-main\data\meal_dataset.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功！500条炼丹数据已生成至：{out_path}")


if __name__ == "__main__":
    gen()