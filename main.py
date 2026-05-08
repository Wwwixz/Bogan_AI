from flask import Flask, render_template, request, redirect, url_for
from AI import ask_ai
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def get_current_time():
    return datetime.now().strftime('%H:%M')

@app.route('/', methods=['GET', 'POST'])
def main():
    current_chat_id = request.cookies.get('current_chat_id')
    current_chat = None
    
    if current_chat_id:
        current_chat = Chat.query.get(int(current_chat_id))
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'new_chat':
            new_chat = Chat()
            db.session.add(new_chat)
            db.session.commit()
            response = redirect(url_for('main'))
            response.set_cookie('current_chat_id', str(new_chat.id))
            return response
        elif action == 'switch_chat':
            chat_id = request.form.get('chat_id')
            response = redirect(url_for('main'))
            response.set_cookie('current_chat_id', str(chat_id))
            return response
        else:
            user_message = request.form.get('message', '').strip()
            if user_message:
                if not current_chat:
                    current_chat = Chat()
                    db.session.add(current_chat)
                    db.session.commit()
                
                user_msg = Message(
                    chat_id=current_chat.id,
                    role='user',
                    content=user_message
                )
                db.session.add(user_msg)
                
                try:
                    ai_response = ask_ai(user_message)
                    ai_msg = Message(
                        chat_id=current_chat.id,
                        role='assistant',
                        content=ai_response
                    )
                    db.session.add(ai_msg)
                except Exception as e:
                    error_msg = Message(
                        chat_id=current_chat.id,
                        role='assistant',
                        content=f'Ошибка: {str(e)}'
                    )
                    db.session.add(error_msg)
                
                db.session.commit()
                response = redirect(url_for('main'))
                if not current_chat_id:
                    response.set_cookie('current_chat_id', str(current_chat.id))
                return response
        return redirect(url_for('main'))
    
    all_chats = Chat.query.order_by(Chat.created_at.desc()).all()
    
    messages = []
    if current_chat:
        for msg in current_chat.messages:
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'time': msg.created_at.strftime('%H:%M')
            })
    
    return render_template('index.html', messages=messages, all_chats=all_chats, current_chat=current_chat)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=8086, host='127.0.0.1', debug=False)
