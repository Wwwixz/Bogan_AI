#Импортируем библиотеку для отправки запросов ИИ
import requests
import os

#Берём токен и URL из переменных окружения (безопасно для Heroku)
API_KEY = os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("BASE_URL", "https://api.agentplatform.ru/v1")

def ask_ai(question):
    if not API_KEY:
        return "Ошибка: API-ключ не настроен на сервере."
    
    #Заголовки запроса (авторизация и тип данных)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    #Данные для отправки
    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "user", "content": question}
        ]
    }
    #Отправляем запрос к API
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "Ошибка: превышено время ожидания ответа от AI."
    except requests.exceptions.RequestException as e:
        return f"Ошибка соединения: {str(e)}"
    except (KeyError, IndexError):
        return "Ошибка: неожиданный формат ответа от AI."


if __name__ == "__main__":
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "!":
            break
        print("AI:", ask_ai(user_input))
