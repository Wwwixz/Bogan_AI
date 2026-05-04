#Импортируем библиотеку для отправки запросов ИИ
import requests


#На сайте AgentPlatform берём токен и URL
API_KEY = "sk-yDtmJESUrtNOFZdZ-5Zs0w"
BASE_URL = "https://api.agentplatform.ru/v1"

def ask_ai(question):
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
    response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
    #Возвращаем ответ
    return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "!":
            break
        print("AI:", ask_ai(user_input))