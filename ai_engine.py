from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch


class NutritionistAI:
    def __init__(self):
        print("🚀 正在唤醒 AI 营养师大脑，请稍候...")

        # 1. 这里填入你电脑里最原始的 Qwen2-1.5B 模型的本地路径
        # (例如: "D:\\models\\Qwen2-1.5B-Instruct")
        self.base_model_path = "你的原始Qwen模型路径"

        # 2. 这是你刚刚在 LLaMA-Factory 炼好的全校通杀版外挂路径
        self.lora_path = r"D:\pycharm\pycharm project\yida_web\LlamaFactory-main\saves\Qwen2-1.5B\lora\meal_lora_all_zones_final"

        # 加载分词器和基础模型
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float16,
            device_map="auto"  # 自动把模型放到显卡上
        )

        # ⭐️ 核心：将 LoRA 外挂“穿”在基础模型身上
        self.model = PeftModel.from_pretrained(base_model, self.lora_path)
        self.model.eval()
        print("✅ AI 营养师已就绪！")

    def get_recommendation(self, location, user_query):
        """
        传入地点和用户的话，返回 AI 的配餐结果
        """
        system_prompt = f"你是一个校园AI营养师。当前位置：{location}。"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        # 按照 Qwen2 的聊天模板拼接对话
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # 生成回答
        with torch.no_grad():
            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=512,
                temperature=0.7  # 控制随机性，0.7比较平衡
            )

        # 裁剪掉用户输入的部分，只保留 AI 的回答
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response


# 实例化这个类，供 app.py 调用
ai_nutritionist = NutritionistAI()