from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from AI import ask_ai
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
# Настройки приложения
app.config['SECRET_KEY'] = 'your-secret-key-here'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'chats.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- REST API Endpoints ---

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    chat_id = request.cookies.get('current_chat_id')
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
        
    current_chat = None
    if chat_id:
        current_chat = Chat.query.filter_by(id=int(chat_id), user_id=current_user.id).first()
        
    if not current_chat:
        current_chat = Chat(user_id=current_user.id)
        db.session.add(current_chat)
        db.session.commit()
    
    # Сохраняем сообщение пользователя
    user_msg = Message(
        chat_id=current_chat.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    try:
        # Собираем историю
        chat_history = []
        past_messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at.asc()).all()
        for msg in past_messages:
            chat_history.append({"role": msg.role, "content": msg.content})
        
        # Получаем ответ ИИ
        ai_response = ask_ai(chat_history)
        
        ai_msg = Message(
            chat_id=current_chat.id,
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_msg)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "ai_response": ai_response,
            "chat_id": current_chat.id,
            "user_time": user_msg.created_at.strftime('%H:%M'),
            "ai_time": ai_msg.created_at.strftime('%H:%M')
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    user_exists = User.query.filter_by(username=username).first()
    if user_exists:
        return jsonify({"error": "Username already exists"}), 400
    
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/me', methods=['GET'])
@login_required
def api_me():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username
    }), 200

# --- Web Routes ---

@app.route('/', methods=['GET', 'POST'])
@login_required
def main():
    current_chat_id = request.cookies.get('current_chat_id')
    current_chat = None
    
    if current_chat_id:
        try:
            current_chat = Chat.query.filter_by(id=int(current_chat_id), user_id=current_user.id).first()
        except (ValueError, TypeError):
            current_chat = None
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'new_chat':
            new_chat = Chat(user_id=current_user.id)
            db.session.add(new_chat)
            db.session.commit()
            response = redirect(url_for('main'))
            response.set_cookie('current_chat_id', str(new_chat.id), max_age=30*24*60*60) # Кука на 30 дней
            return response
        elif action == 'switch_chat':
            chat_id = request.form.get('chat_id')
            response = redirect(url_for('main'))
            response.set_cookie('current_chat_id', str(chat_id), max_age=30*24*60*60)
            return response
        else:
            # Традиционная отправка через форму (fallback)
            user_message = request.form.get('message', '').strip()
            
            if user_message:
                if not current_chat:
                    current_chat = Chat(user_id=current_user.id)
                    db.session.add(current_chat)
                    db.session.commit()
                
                user_msg = Message(chat_id=current_chat.id, role='user', content=user_message)
                db.session.add(user_msg)
                db.session.commit()
                
                try:
                    chat_history = []
                    past_messages = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at.asc()).all()
                    for msg in past_messages:
                        chat_history.append({"role": msg.role, "content": msg.content})
                    
                    ai_response = ask_ai(chat_history)
                    ai_msg = Message(chat_id=current_chat.id, role='assistant', content=ai_response)
                    db.session.add(ai_msg)
                except Exception as e:
                    db.session.add(Message(chat_id=current_chat.id, role='assistant', content=f'Ошибка: {str(e)}'))
                
                db.session.commit()
                response = redirect(url_for('main'))
                if not current_chat_id:
                    response.set_cookie('current_chat_id', str(current_chat.id), max_age=30*24*60*60)
                return response
        return redirect(url_for('main'))
    
    all_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    
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
