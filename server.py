from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

# DB Bağlantısı
def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn, conn.cursor()

@app.post("/register")
def register():
    conn, cursor = get_db()
    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        conn.close()
        return jsonify({"success": False, "message": "Eksik bilgi!"})

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Kayıt başarılı!"})
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": "Kullanıcı zaten var!"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": f"Hata: {str(e)}"})


@app.post("/login")
def login():
    conn, cursor = get_db()
    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    cursor.execute(
        "SELECT password FROM users WHERE username=%s",
        (username,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({"success": False, "message": "Kullanıcı yok!"})

    stored_password = result[0]

    if stored_password != password:
        conn.close()
        return jsonify({"success": False, "message": "Hatalı şifre!"})

    conn.close()
    return jsonify({"success": True, "message": "Giriş başarılı!"})


# İlk deployda tablo oluşturması için
@app.before_first_request
def setup():
    conn, cursor = get_db()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
