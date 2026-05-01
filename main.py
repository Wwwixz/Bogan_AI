from flask import Flask, render_template, request, jsonify
from Al import ask_ai


app = Flask(__name__)

@app.route('/')
def main():
    # Рендерим главную страницу чата
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Эндпоинт для общения с ИИ.
    Принимает JSON: {"message": "текст сообщения"}
    Возвращает JSON: {"response": "ответ ИИ"}
    """
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'Пустое сообщение'}), 400

    try:
        # Вызываем ИИ
        ai_response = ask_ai(user_message)
        return jsonify({'response': ai_response})
    except Exception as e:
        # Лучше залогировать ошибку, но пока просто вернём сообщение
        return jsonify({'error': 'Ошибка при обращении к ИИ'}), 500


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
