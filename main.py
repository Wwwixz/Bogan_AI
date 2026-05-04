from flask import Flask, render_template, request, redirect, url_for
from AI import ask_ai
from datetime import datetime

app = Flask(__name__)

chat_history = []

def get_current_time():
    return datetime.now().strftime('%H:%M')

@app.route('/', methods=['GET', 'POST'])
def main():
    global chat_history
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'new_chat':
            chat_history = []
        else:
            user_message = request.form.get('message', '').strip()
            if user_message:
                chat_history.append({'role': 'user', 'content': user_message, 'time': get_current_time()})
                try:
                    ai_response = ask_ai(user_message)
                    chat_history.append({'role': 'assistant', 'content': ai_response, 'time': get_current_time()})
                except Exception as e:
                    chat_history.append({'role': 'assistant', 'content': f'Ошибка: {str(e)}', 'time': get_current_time()})
        return redirect(url_for('main'))
    return render_template('index.html', messages=chat_history)

if __name__ == '__main__':
    app.run(port=8086, host='127.0.0.1', use_reloader=False)
