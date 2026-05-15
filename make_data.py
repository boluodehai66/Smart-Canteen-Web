import pandas as pd
import glob
import json
import re
import random
import os


# 解析菜品字符串的函数
def parse_food(food_str):
    if not isinstance(food_str, str) or food_str == '-' or food_str.strip() == '':
        return None
    # 匹配格式：菜名\n(￥价格 | 150g: 热量... 碳水... 蛋白... 脂肪...)
    match = re.search(
        r'(.*?)\n\(￥([\d\.]+)\s*\|\s*\d+g:\s*热量\s*([\d\.]+)kcal\s*碳水\s*([\d\.]+)g\s*蛋白\s*([\d\.]+)g\s*脂肪\s*([\d\.]+)g\)',
        food_str)
    if match:
        name = match.group(1).strip()
        price, cal, carb, prot, fat = map(float, match.group(2, 3, 4, 5, 6))
        formatted = f"{name} ￥{price} ({cal}kcal, 碳水{carb}g/蛋白{prot}g/脂肪{fat}g)"
        return {'name': name, 'price': price, 'cal': cal, 'carb': carb, 'prot': prot, 'fat': fat, 'str': formatted}
    return None


def run_conversion():
    # 1. 加载固定项（主食和汤），Windows 下 CSV 多为 gbk 编码
    try:
        fixed_df = pd.read_csv("formatted_固定.csv", encoding="gbk")
    except:
        fixed_df = pd.read_csv("formatted_固定.csv", encoding="utf-8")

    staples = []
    for item in fixed_df.get('主食', []).dropna():
        if p := parse_food(item): staples.append(p)

    all_data = []
    # 2. 扫描所有区域 CSV
    files = glob.glob("formatted_*区*.csv")
    for file in files:
        loc = os.path.basename(file).replace('formatted_', '').replace('.csv', '')
        try:
            df = pd.read_csv(file, encoding="gbk")
        except:
            df = pd.read_csv(file, encoding="utf-8")

        for day in df.columns:
            dishes = []
            for item in df[day].dropna():
                if p := parse_food(item): dishes.append(p)

            meats = [d for d in dishes if d['price'] >= 6.0]
            veggies = [d for d in dishes if d['price'] < 6.0]

            # 每个地点每天生成 30 条对话，丰富语料
            for _ in range(30):
                if not staples or not meats or not veggies: continue
                staple, meat, veg = random.choice(staples), random.choice(meats), random.choice(veggies)

                total_price = round(staple['price'] + meat['price'] + veg['price'], 1)
                system_prompt = f"你是一个校园AI营养师。当前位置：{loc}。"

                query_types = [
                    f"我想在{loc}吃一顿{total_price:g}元左右的饭。",
                    f"推荐一份{loc}{total_price:g}元的搭配。",
                    f"在{loc}预算{total_price:g}元，有什么好吃的？"
                ]
                query = random.choice(query_types)
                response = f"### 方案：营养均衡搭配\n- [主食] {staple['str']}\n- [荤菜] {meat['str']}\n- [素菜] {veg['str']}\n💡 点评：这是为您在{loc}定制的超值餐食。"

                all_data.append({
                    "instruction": query,
                    "input": "",
                    "output": response,
                    "system": system_prompt
                })

    # 3. 输出纯净的 JSON 列表（开头是 [，结尾是 ]）
    with open('all_meals_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 合成成功！共生成 {len(all_data)} 条剧本数据。")


if __name__ == "__main__":
    run_conversion()