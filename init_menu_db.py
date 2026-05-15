import pandas as pd
import re
import os
import time
from openai import OpenAI
import urllib.parse
from app import app, db, MenuItem

# ================= 1. 初始化硅基流动 API 客户端 =================
# ================= 1. 初始化客户端 =================
# 即使 app.py 用本地模型，这里依然建议用云端 API 快速分类
client = OpenAI(
    api_key="sk-imxdtfltmmsvkzdqaiebprsomaqqiotehjdiggooznviqoun",
    base_url="https://api.siliconflow.cn/v1"
)

# 🌟 AI 记忆缓存字典
category_cache = {}


def ai_guess_category(dish_name):
    """使用 Qwen2.5 语义大模型精准识别特色菜品分类"""
    # 如果已经识别过，直接从缓存读取，节省 API 调用
    if dish_name in category_cache:
        return category_cache[dish_name]

    system_prompt = """你是一个极其严谨的中国校园餐饮分类专家。
    请根据菜名判断其分类，你必须且只能从 [主食, 荤菜, 素菜, 小吃, 汤羹] 中选择一个返回。
    不要返回任何额外解释或标点符号！

    【分类铁律与学习案例】
    1. 米饭、面条、馒头、花卷、水饺等纯纯的主食 -> [主食]
    2. 含有肉类（猪牛羊鸡鸭鱼虾等）的菜品（如：肉沫茄子、木须肉、白灼虾） -> [荤菜]
    3. 纯蔬菜、豆制品、菌菇类的菜品（如：炒青菜、麻婆豆腐、蒜蓉西兰花） -> [素菜]
    4. 带有大量油脂和碳水性质的非正餐点心（如：麻团、葱油饼、韭菜盒子、炸菜角、煎饼果子） -> [小吃]
    5. 各种咸甜汤类以及水吧提供的杯装液体（如：紫菜蛋花汤、番茄鸡蛋汤、咸奶茶、原味豆浆、现榨果汁） -> [汤羹]
    """

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"菜名：{dish_name}"}
            ],
            temperature=0.1
        )

        # 提取分类结果并去除多余的首尾空格
        category = response.choices[0].message.content.strip()

        # 去除大模型可能自带的方括号，确保落库数据干净
        category = category.replace("[", "").replace("]", "")

        # 存入缓存
        category_cache[dish_name] = category
        return category

    except Exception as e:
        print(f"  ⚠️ 分类 API 异常 ({dish_name}): {e}")
        return "素菜"  # 发生异常时的默认安全后备选项

def generate_image_url(dish_name):
    """修复版：生成支持中文字体的图片，或者使用统一的精美占位图"""

    # 将中文菜名进行安全编码，防止乱码报错
    encoded_name = urllib.parse.quote(dish_name)

    # 换用支持中文 Noto 字体的稳定服务器 (fakeimg)
    return f"https://fakeimg.pl/200x150/FF9800/FFFFFF/?text={encoded_name}&font=noto"


def parse_dish_text(text):
    try:
        lines = text.split('\n')
        name = lines[0].strip()

        price = re.search(r'￥(\d+(\.\d+)?)', text)
        calories = re.search(r'热量\s*(\d+)', text)
        carbs = re.search(r'碳水\s*(\d+(\.\d+)?)', text)
        protein = re.search(r'蛋白\s*(\d+(\.\d+)?)', text)
        fat = re.search(r'脂肪\s*(\d+(\.\d+)?)', text)

        return {
            "name": name,
            "price": float(price.group(1)) if price else 0.0,
            "calories": int(calories.group(1)) if calories else 0,
            "carbs": float(carbs.group(1)) if carbs else 0.0,
            "protein": float(protein.group(1)) if protein else 0.0,
            "fat": float(fat.group(1)) if fat else 0.0,
            "image": generate_image_url(name)
        }
    except Exception:
        return None


# ================= 2. 批量导入配置库 =================
files_to_import = [
    {"file": "formatted_北区一楼.csv", "campus": "北区", "floor": "一楼"},
    {"file": "formatted_北区二楼.csv", "campus": "北区", "floor": "二楼"},
    {"file": "formatted_南区一楼.csv", "campus": "南区", "floor": "一楼"},
    {"file": "formatted_南区二楼.csv", "campus": "南区", "floor": "二楼"},
    {"file": "formatted_西区一楼.csv", "campus": "西区", "floor": "一楼"},
    {"file": "formatted_西区二楼.csv", "campus": "西区", "floor": "二楼"}
]

ALL_CAMPUSES = ["北区", "南区", "西区"]
ALL_FLOORS = ["一楼", "二楼"]
ALL_DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def import_fixed_menu():
    """读取固定菜品：直接将文件表头作为分类，霸屏注入全校！"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    csv_path = os.path.join(basedir, "formatted_固定.csv")

    if not os.path.exists(csv_path):
        print(f"⚠️ 未找到 {csv_path}，跳过固定菜品导入。")
        return 0

    print(f"\n🚀 开始注入【全局固定菜品】(完全尊从文件自带分类)...")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception:
        try:
            df = pd.read_csv(csv_path, encoding='gbk')
        except Exception:
            # 兼容被修改了后缀的 Excel 文件
            df = pd.read_excel(csv_path, engine='openpyxl')

    fixed_count = 0

    # 🌟 核心修改：这里的 category_name 就是你文件里的“主食”、“汤羹”等表头！
    for category_name in df.columns:
        if "Unnamed" in str(category_name):
            continue

        for content in df[category_name].dropna():
            if str(content).strip() == "" or str(content) == '-':
                continue

            dish_info = parse_dish_text(str(content))
            if not dish_info:
                continue

            # 🚨 嵌套循环：每一天、每个校区、每一层都加上这道菜！
            for day in ALL_DAYS:
                for campus in ALL_CAMPUSES:
                    for floor in ALL_FLOORS:
                        new_item = MenuItem(
                            name=dish_info["name"],
                            price=dish_info["price"],
                            calories=dish_info["calories"],
                            carbs=dish_info["carbs"],
                            protein=dish_info["protein"],
                            fat=dish_info["fat"],
                            category=str(category_name).strip(),  # 👈 直接读取你的表头作为分类
                            image=dish_info["image"],
                            day=day,
                            campus=campus,
                            floor=floor
                        )
                        db.session.add(new_item)
                        fixed_count += 1

        print(f"  📌 [{category_name}] 类目已全局铺开！")

    return fixed_count


def import_all_menus():
    basedir = os.path.abspath(os.path.dirname(__file__))

    with app.app_context():
        print("🧹 正在清理旧数据库，准备开始多校区全量导入...")
        db.drop_all()
        db.create_all()

        total_imported = 0

        # 1. 优先导入常规的特色菜品（各区单独的 CSV 带有星期几表头的）
        for config in files_to_import:
            csv_path = os.path.join(basedir, config['file'])
            if not os.path.exists(csv_path):
                print(f"❌ 找不到文件跳过: {csv_path}")
                continue

            print(f"\n⏳ 开始导入特色菜 [{config['campus']} - {config['floor']}]...")

            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
            except Exception:
                try:
                    df = pd.read_csv(csv_path, encoding='gbk')
                except Exception:
                    df = pd.read_excel(csv_path, engine='openpyxl')

            for col_name in df.columns:
                actual_day = "周日" if col_name == "周天" else col_name

                for content in df[col_name].dropna():
                    if str(content).strip() == "" or "Unnamed" in str(content) or str(content) == '-':
                        continue

                    dish_info = parse_dish_text(str(content))
                    if not dish_info:
                        continue

                    # 🚀 特色菜呼叫 AI 进行分类
                    category = ai_guess_category(dish_info["name"])

                    new_item = MenuItem(
                        name=dish_info["name"],
                        price=dish_info["price"],
                        calories=dish_info["calories"],
                        carbs=dish_info["carbs"],
                        protein=dish_info["protein"],
                        fat=dish_info["fat"],
                        category=category,
                        image=dish_info["image"],
                        day=actual_day,
                        campus=config["campus"],
                        floor=config["floor"]
                    )
                    db.session.add(new_item)
                    total_imported += 1

                    if dish_info["name"] not in category_cache:
                        time.sleep(0.1)

                    print(f"  ✅ [{actual_day}] {dish_info['name']} -> {category}")

        # 2. 导入固定菜品（你已经分好类的 CSV）
        fixed_imported = import_fixed_menu()

        db.session.commit()

        print(f"\n🎉 完美！数据初始化完成！")
        print(f"🍔 各区特色菜导入: {total_imported} 份")
        print(f"🍚 固定款全校铺发: {fixed_imported} 份")
        print(f"🧠 本次运行 AI 总共独立识别了 {len(category_cache)} 种不同的菜品！")


if __name__ == '__main__':
    import_all_menus()