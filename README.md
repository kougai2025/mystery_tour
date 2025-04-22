
pip install -r requirements.txt
python app.py

`http://127.0.0.1:5000/login` 

password.txtは絶対見ないでください。。。

＜テーブルを立てる方法＞

with app.app_context():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS access_log (
            username TEXT,
            page TEXT,
            PRIMARY KEY (username, page)
        );
    ''')
    db.commit()



