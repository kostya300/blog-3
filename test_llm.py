from blog.model_loader import generate_response

print("Тестирование LLM...")
test_prompts = [
    "Расскажи кратко о квантовых вычислениях.",
    "Напиши стихотворение про программирование.",
    "Объясни принцип работы нейронных сетей."
]

for prompt in test_prompts:
    print(f"\nЗапрос: {prompt}")
    response = generate_response(prompt)
    print(f"Ответ: {response}")
