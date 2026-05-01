from flask import Flask, render_template, request, redirect, url_for
from AI import ask_ai

app = Flask(__name__)

# Временное хранилище истории сообщений (один общий список для всех пользователей — только для демонстрации!)
chat_history = []

@app.route('/', methods=['GET', 'POST'])
def main():
    global chat_history
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        if user_message:
            # Добавляем сообщение пользователя в историю
            chat_history.append({'role': 'user', 'content': user_message})
            # Получаем ответ от ИИ
            try:
                ai_response = ask_ai(user_message)
                chat_history.append({'role': 'assistant', 'content': ai_response})
            except Exception as e:
                chat_history.append({'role': 'assistant', 'content': f'Ошибка: {str(e)}'})
        # Редирект на GET, чтобы избежать повторной отправки при обновлении страницы
        return redirect(url_for('main'))

    # GET-запрос — показываем страницу с историей
    return render_template('index.html', messages=chat_history)

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
