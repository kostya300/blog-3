import torch
import warnings
from transformers import AutoTokenizer, AutoModelForCausalLM
import threading

# Игнорируем FutureWarning от huggingface_hub
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")


MODEL_PATH = "microsoft/Phi-3-mini-4k-instruct"
tokenizer = None
model = None
loaded = False
lock = threading.Lock()

def load_model():
    global tokenizer, model, loaded
    if loaded:
        return

    with lock:
        if loaded:
            return

        print("Загружаю модель Phi-3-mini...")
        try:
            # Токенизатор
            tokenizer = AutoTokenizer.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Основная модель
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="cpu",
                attn_implementation="eager",
                trust_remote_code=True
            )

            model.eval()
            loaded = True
            print("✅ Phi-3-mini успешно загружена!")

        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            raise

# ЗАГРУЗКА МОДЕЛИ ПРИ СТАРТЕ СКРИПТА
load_model()  # ← ключевое изменение: вызываем сразу

def generate_response(prompt, max_length=256):
    # Убираем проверку loaded и вызов load_model() — модель уже загружена

    # Формат для Phi-3 с использованием chat_template
    messages = [{"role": "user", "content": prompt}]
    full_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        full_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    ).to(model.device)

    try:
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_new_tokens=max_length,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=2,
                repetition_penalty=1.2
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        # Извлекаем только часть после последнего <|assistant|>
        if "<|assistant|>" in response:
            answer = response.split("<|assistant|>")[-1].strip()
        else:
            answer = response

        # Убираем специальные токены
        for special_token in ["<|end|>", "<|user|>", "<|assistant|>"]:
            answer = answer.replace(special_token, "")

        return answer.strip() if answer.strip() else "Я не понял вопрос. Попробуйте переформулировать."

    except Exception as e:
        print("Ошибка генерации:", e)
        return "Извините, произошла ошибка при генерации."
