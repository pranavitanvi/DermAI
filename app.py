from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, stream_with_context
import sqlite3
import os
import secrets
from werkzeug.utils import secure_filename
from model.skin_model import predict_skin_lesion
from chatbot.ollama_chat import generate_chat_stream
import json

app = Flask(__name__)
app.secret_key = "dermai_secret_key_fixed"  # Fixed key to prevent session loss on server restart

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'database', 'dermai.db')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, take them to the dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, take them to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            
            # Auto-login after registration
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session['user_name'] = name
            
            conn.close()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Email already exists.')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/detect')
def detect():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('detect.html')

@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/hospitals')
def hospitals():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    city_filter = request.args.get('city')
    conn = get_db_connection()
    if city_filter:
        hospitals = conn.execute('SELECT * FROM hospitals WHERE city LIKE ? LIMIT 50', ('%' + city_filter + '%',)).fetchall()
    else:
        hospitals = conn.execute('SELECT * FROM hospitals LIMIT 50').fetchall()
    conn.close()
    
    return render_template('hospitals.html', hospitals=hospitals, city_filter=city_filter)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    predictions = conn.execute('SELECT * FROM predictions WHERE user_id = ? ORDER BY timestamp DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('history.html', predictions=predictions)

@app.route('/predict_api', methods=['POST'])
def predict_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Call prediction model
    result_data = predict_skin_lesion(filepath)
    
    # Save to SQLite
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO predictions (user_id, image_path, prediction_result, confidence_score, risk_level, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], filename, result_data['prediction'], result_data['confidence'], result_data['risk_level'], result_data['recommendation']))
    conn.commit()
    conn.close()
    
    return jsonify(result_data)

@app.route('/chat_api', methods=['POST'])
def chat_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
        
    conn = get_db_connection()
    
    # Save user message
    conn.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', (session['user_id'], 'user', user_message))
    
    # Retrieve last 5 history for context
    history_records = conn.execute('SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id ASC', (session['user_id'],)).fetchall()
    messages_history = [{'role': row['role'], 'content': row['content']} for row in history_records[-5:]]
    conn.commit()
    conn.close()
    
    def generate():
        full_response = ""
        for chunk in generate_chat_stream(messages_history, user_message):
            if chunk:
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save AI response
        db_conn = get_db_connection()
        db_conn.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', (session['user_id'], 'ai', full_response))
        db_conn.commit()
        db_conn.close()
        yield "data: [DONE]\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
