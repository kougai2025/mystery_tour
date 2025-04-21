import sqlite3
import os
from flask import Flask, render_template, request, redirect, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            last_page TEXT
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS access_log (
            username TEXT,
            page TEXT,
            UNIQUE(username, page)
        )
    ''')
    db.commit()

def init_users():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) as cnt FROM user_data")
    row = cur.fetchone()
    if row['cnt'] == 0:
        users = [
            ('1', 'A9kL2mQz', '/1/A.html'),
            ('2', 'bT7xM1cV', '/2/A.html'),
            ('3', 'R5pN0yLu', '/3/A.html'),
            ('4', 'qE6vZa8D', '/4/A.html'),
            ('5', 'J4rC9nTw', '/5/A.html'),
            ('6', 'uY3wXb7K', '/6/A.html'),
            ('7', 'Z0vLh1pN', '/7/A.html'),
            ('8', 'eD8Km2RQ', '/8/A.html'),
            ('9', 'Hn5cPz3W', '/9/A.html'),
            ('10', 'xT2L9qYm', '/10/A.html'),
            ('11', 'Wf1BvA6r', '/11/A.html'),
            ('12', 'mP7dZx0Q', '/12/A.html'),
            ('13', 'gC4WnR2y', '/13/A.html'),
            ('14', 'Lz8aKv1T', '/14/A.html'),
            ('15', 'B0qTm3Xu', '/15/A.html'),
            ('16', 'sY9WrLc5', '/16/A.html'),
            ('17', 'N3xZvPt1', '/17/A.html'),
            ('18', 'Ey7qBL0m', '/18/A.html'),
            ('19', 'tC2nRk6W', '/19/A.html'),
            ('20', 'dP5MzVa3', '/20/A.html'),
            ('21', 'Qx0LnUY7', '/21/A.html'),
            ('22', 'vB8pKT2c', '/22/A.html'),
            ('23', 'oM3zXyW9', '/23/A.html'),
            ('24', 'K6tQr1NB', '/24/A.html'),
        ]
        for username, password, last_page in users:
            password_hash = generate_password_hash(password)
            db.execute("INSERT INTO user_data (username, password_hash, last_page) VALUES (?, ?, ?)",
                       (username, password_hash, last_page))
        db.commit()

@app.before_request
def setup():
    init_db()
    init_users()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.clear()
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM user_data WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['visited'] = [] 
            next_page = user['last_page'] or f'/{username}/A.html'
            return redirect(next_page)
        else:
            return render_template('login.html', error="ログイン失敗")

    return render_template('login.html')

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        db = get_db()
        user = db.execute('SELECT last_page FROM user_data WHERE username = ?', (username,)).fetchone()
        if user and user['last_page']:
            return redirect(user['last_page'])
        return redirect(f'/{username}/A.html')
    return redirect('/login')

@app.route('/<user_dir>/<page>')
def serve_page(user_dir, page):
    username = session.get('username')
    if not username:
        return redirect('/login')

    if str(username) != user_dir:
        return "アクセス権がありません", 403

    current_path = f"{user_dir}/{page}"

    if 'visited' not in session:
        session['visited'] = []

    if current_path in session['visited']:
        pass
    else:
        allowed_transitions = {
            'A.html': ['B.html'],
            'B.html': ['2A.html'],
            '2A.html': ['2B.html'],
            '2B.html': ['3A.html'],
            '3A.html': ['3B.html'],
            '3B.html': ['4A.html'],
            '4A.html': ['4B.html'],
        }

        last = session.get('previous_page')
        if last:
            last_page = last.split('/')[-1]
            allowed_next = allowed_transitions.get(last_page, [])
            if page not in allowed_next:
                return "このページにはまだ到達していません", 403
        else:
            if page not in allowed_transitions:
                return "最初のページ以外に直接アクセスできません", 403

        session['visited'].append(current_path)

    template_path = f"{user_dir}/{page}"
    if not os.path.exists(os.path.join('templates', template_path)):
        return "ページが見つかりません", 404

    session['previous_page'] = f"{user_dir}/{page}"
    db = get_db()
    db.execute('UPDATE user_data SET last_page = ? WHERE username = ?', (f'/{user_dir}/{page}', username))
    db.execute('INSERT OR IGNORE INTO access_log (username, page) VALUES (?, ?)', (username, f'/{user_dir}/{page}'))
    db.commit()

    return render_template(template_path, username=username)

@app.route('/admin/status')
def access_status():
    db = get_db()
    users = [str(i) for i in range(1, 25)]
    page_names = ['A.html', 'B.html', '2A.html', '2B.html', '3A.html', '3B.html', '4A.html', '4B.html']
    
    access_map = {user: {page: False for page in page_names} for user in users}

    logs = db.execute('SELECT username, page FROM access_log').fetchall()
    for row in logs:
        user = row['username']
        page = row['page'].split('/')[-1]
        if user in access_map and page in access_map[user]:
            access_map[user][page] = True

    return render_template('status.html', access_map=access_map, page_names=page_names)


if __name__ == '__main__':
    app.run(debug=True)
