import os

MODEL_PATH = ".c"
required_files = [
    "config.json",
    "tokenizer.json",  # или tokenizer.model
    "pytorch_model.bin"  # или model.safetensors
]

print("Проверка файлов модели в папке:", MODEL_PATH)
for file in required_files:
    full_path = os.path.join(MODEL_PATH, file)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path) / (1024 * 1024)  # в МБ
        print(f"✓ {file} найден ({size:.2f} МБ)")
    else:
        print(f"❌ {file} отсутствует!")
