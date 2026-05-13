#Импортируем библиотеку для отправки запросов ИИ
import requests


#На сайте AgentPlatform берём токен и URL
API_KEY = "sk-yDtmJESUrtNOFZdZ-5Zs0w"
BASE_URL = "https://api.agentplatform.ru/v1"

def ask_ai(messages):
    """
    Отправляет список сообщений (историю) ИИ.
    messages: список словарей [{"role": "user/assistant/system", "content": "текст"}]
    """
    #Заголовки запроса (авторизация и тип данных)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Системный промпт, чтобы ИИ понимал свои возможности
    system_prompt = {
        "role": "system",
        "content": "Ты — полезный AI-ассистент Bogan AI. Твоя задача — отвечать на вопросы пользователя и помогать ему в решении различных задач."
    }
    
    # Добавляем системный промпт в начало, если его там нет
    full_messages = [system_prompt] + messages
    
    #Данные для отправки
    payload = {
        "model": "openai/gpt-4o",
        "messages": full_messages
    }
    try:
        #Отправляем запрос к API
        response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return "Ошибка: ИИ вернул пустой ответ."
            
    except requests.exceptions.RequestException as e:
        return f"Ошибка сети при запросе к ИИ: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Ошибка при разборе ответа ИИ: {str(e)}"
    except Exception as e:
        return f"Произошла непредвиденная ошибка: {str(e)}"


if __name__ == "__main__":
    chat_history = []
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "!":
            break
        chat_history.append({"role": "user", "content": user_input})
        response = ask_ai(chat_history)
        chat_history.append({"role": "assistant", "content": response})
