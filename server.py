from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import secrets

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for development

# Enhanced database setup with error handling
def init_db():
    try:
        conn = sqlite3.connect('chats.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                username TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
        ''')
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        raise

# Initialize database connection pool
db_conn = init_db()

@app.route('/api/create_chat', methods=['POST'])
def create_chat():
    try:
        chat_id = secrets.token_urlsafe(12)
        username = request.json.get('username', 'Anonymous')
        
        c = db_conn.cursor()
        c.execute("INSERT INTO chats (id) VALUES (?)", (chat_id,))
        db_conn.commit()
        
        return jsonify({
            "status": "success",
            "chat_id": chat_id,
            "share_url": f"{request.host_url}?join={chat_id}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_message():
    try:
        data = request.json
        required = ['chat_id', 'username', 'message']
        if not all(k in data for k in required):
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        c = db_conn.cursor()
        c.execute("""
            INSERT INTO messages (chat_id, username, message)
            VALUES (?, ?, ?)
        """, (data['chat_id'], data['username'], data['message']))
        db_conn.commit()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        chat_id = request.args.get('chat_id')
        if not chat_id:
            return jsonify({"status": "error", "message": "Missing chat_id"}), 400
        
        c = db_conn.cursor()
        c.execute("""
            SELECT username, message, timestamp 
            FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp
        """, (chat_id,))
        
        messages = [
            {
                "username": row[0],
                "message": row[1],
                "time": row[2][11:16]  # Extract HH:MM from timestamp
            } 
            for row in c.fetchall()
        ]
        
        return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)