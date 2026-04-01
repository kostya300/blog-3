#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Конфигурация
MODEL_PATH = "google/gemma-2b-it"
MODEL_LOADED = False
tokenizer = None
model = None

def load_llama_model():
    """Ленивая загрузка модели — только когда нужно."""
    global tokenizer, model, MODEL_LOADED

    if MODEL_LOADED:
        return

    try:
        print(f"Загружаю модель {MODEL_PATH}...")

        # Универсальная загрузка токенизатора и модели
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        MODEL_LOADED = True
        print("Модель успешно загружена!")
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        raise


def generate_response(prompt, max_length=512):
    """Генерация ответа от модели."""
    if not MODEL_LOADED:
        load_llama_model()

    # Токенизация входного текста
    inputs = tokenizer(prompt, return_tensors="pt")

    # Генерация ответа
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids.to(model.device),
            max_length=max_length,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    # Декодирование сгенерированного текста
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def main():
    """Run administrative tasks."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "Course_FirstProject.settings"

    # Альтернативный вариант (если setdefaultenv недоступен):
    # os.environ["DJANGO_SETTINGS_MODULE"] = "Course_FirstProject.settings"

    # Проверяем, не вызывается ли команда для работы с моделью
    if len(sys.argv) > 1 and sys.argv[1] == 'chat_with_llama':
        handle_llama_command()
        return

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)

def handle_llama_command():
    """Обработка специальной команды для чата с моделью."""
    print("Запуск чата с TinyLlama (для выхода введите 'quit'):")
    load_llama_model()  # Загружаем модель только при необходимости

    while True:
        try:
            user_input = input("\nВы: ")
            if user_input.lower() in ['quit', 'exit', 'выход']:
                print("До свидания!")
                break
            response = generate_response(user_input)
            print(f"Модель: {response}")
        except KeyboardInterrupt:
            print("\nДо свидания!")
            break
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
