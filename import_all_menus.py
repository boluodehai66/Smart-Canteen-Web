import pandas as pd
import re
from app import app, db, MenuItem

# 待处理的文件列表及对应的校区/楼层
files_to_import = [
    {"file": "formatted_北区一楼.csv", "campus": "北区", "floor": "一楼"},
    {"file": "formatted_北区二楼.csv", "campus": "北区", "floor": "二楼"},
    {"file": "formatted_南区二楼.csv", "campus": "南区", "floor": "二楼"},
    {"file": "formatted_西区一楼.csv", "campus": "西区", "floor": "一楼"},
    {"file": "formatted_西区二楼.csv", "campus": "西区", "floor": "二楼"}
]


def parse_dish_info(text):
    if not text or text == '-': return None
    try:
        # 正则提取：名称、价格、热量、碳水、蛋白、脂肪
        name = text.split('\n')[0].strip()
        price = float(re.search(r'￥(\d+(\.\d+)?)', text).group(1))
        cal = int(re.search(r'热量(\d+)kcal', text).group(1))
        carbs = float(re.search(r'碳水(\d+(\.\d+)?)g', text).group(1))
        protein = float(re.search(r'蛋白(\d+(\.\d+)?)g', text).group(1))
        fat = float(re.search(r'脂肪(\d+(\.\d+)?)g', text).group(1))
        return name, price, cal, carbs, protein, fat
    except:
        return None


with app.app_context():
    db.drop_all()  # 慎用：这会清空旧数据
    db.create_all()

    for config in files_to_import:
        print(f"正在导入: {config['file']}...")
        df = pd.read_csv(config['file'])

        for day in df.columns:  # 遍历周一到周日
            for cell in df[day]:
                info = parse_dish_info(str(cell))
                if info:
                    name, price, cal, carb, pro, fat = info
                    item = MenuItem(
                        name=name, price=price, calories=cal,
                        carbs=carb, protein=pro, fat=fat,
                        day=day, campus=config['campus'], floor=config['floor'],
                        category="特色菜品"
                    )
                    db.session.add(item)

    db.session.commit()
    print("✅ 所有校区菜单导入成功！")