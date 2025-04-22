import sqlite3
import os
import secrets
from flask import Flask, render_template, request, redirect, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATABASE = 'database.db'

WEIGHTS = {
    'A.html': 1,
    'B.html': 2,
    '2A.html': 3,
    '2B.html': 4,
    '3A.html': 5,
    '3B.html': 6,
    '4A.html': 7,
    '4B.html': 8,
}

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
            password_hash TEXT NOT NULL
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS access_log (
            username TEXT,
            page TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            ('1', 'A9kL2mQz'),
            ('2', 'bT7xM1cV'),
            ('3', 'R5pN0yLu'),
            ('4', 'qE6vZa8D'),
            ('5', 'J4rC9nTw'),
            ('6', 'uY3wXb7K'),
            ('7', 'Z0vLh1pN'),
            ('8', 'eD8Km2RQ'),
            ('9', 'Hn5cPz3W'),
            ('10', 'xT2L9qYm'),
            ('11', 'Wf1BvA6r'),
            ('12', 'mP7dZx0Q'),
            ('13', 'gC4WnR2y'),
            ('14', 'Lz8aKv1T'),
            ('15', 'B0qTm3Xu'),
            ('16', 'sY9WrLc5'),
            ('17', 'N3xZvPt1'),
            ('18', 'Ey7qBL0m'),
            ('19', 'tC2nRk6W'),
            ('20', 'dP5MzVa3'),
            ('21', 'Qx0LnUY7'),
            ('22', 'vB8pKT2c'),
            ('23', 'oM3zXyW9'),
            ('24', 'K6tQr1NB'),
        ]
        for username, password in users:
            password_hash = generate_password_hash(password)
            db.execute("INSERT INTO user_data (username, password_hash) VALUES (?, ?)", (username, password_hash))
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
            session['valid_keys'] = {}
            session['just_logged_in'] = True  # ⭐ ログイン直後フラグ

            logs = db.execute('SELECT page FROM access_log WHERE username = ?', (username,)).fetchall()
            max_page = None
            max_weight = -1
            for row in logs:
                page_name = row['page'].split('/')[-1]
                weight = WEIGHTS.get(page_name, 0)
                if weight > max_weight:
                    max_weight = weight
                    max_page = row['page']

            if max_page:
                return redirect(max_page)
            else:
                return redirect(f'/{username}/A.html')
        else:
            return render_template('login.html', error="ログイン失敗")

    return render_template('login.html')

@app.route('/')
def index():
    if 'username' in session:
        return redirect(f'/{session["username"]}/A.html')
    return redirect('/login')

@app.route('/<user_dir>/<page>')
def serve_page(user_dir, page):
    username = session.get('username')
    if not username:
        return redirect('/login')

    if str(username) != user_dir:
        return "アクセス権がありません", 403

    current_path = f"{user_dir}/{page}"
    key = request.args.get("key")

    if page != "A.html":
        if session.pop("just_logged_in", False):
            pass
        elif not key or session.get("valid_keys", {}).get(current_path) != key:
            return render_template("error.html", redirect_url=f"../login"), 403
        session["valid_keys"].pop(current_path, None)

    # ✅ 修正箇所：絶対パスで存在確認
    template_full_path = os.path.join(app.root_path, 'templates', user_dir, page)
    if not os.path.exists(template_full_path):
        return "ページが見つかりません", 404

    db = get_db()
    db.execute('INSERT OR IGNORE INTO access_log (username, page) VALUES (?, ?)', (username, f'/{user_dir}/{page}'))
    db.commit()

    return render_template(f"{user_dir}/{page}", username=username)


@app.route('/generate_link/<user_dir>/<page>')
def generate_link(user_dir, page):
    if session.get('username') != user_dir:
        return "不正アクセス", 403

    token = secrets.token_urlsafe(16)
    full_path = f"{user_dir}/{page}"

    if "valid_keys" not in session:
        session["valid_keys"] = {}
    session["valid_keys"][full_path] = token
    session.modified = True  # セッション更新通知

    return redirect(f'/{user_dir}/{page}?key={token}')

@app.route('/admin/status')
def access_status():
    db = get_db()
    users = [str(i) for i in range(1, 25)]
    page_names = list(WEIGHTS.keys())

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


