import os
import mysql.connector
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "db"),
        user=os.environ.get("MYSQL_USER", "calculator"),
        password=os.environ.get("MYSQL_PASSWORD", "calculator_pass"),
        database=os.environ.get("MYSQL_DATABASE", "calculator_db"),
    )

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                expression VARCHAR(255) NOT NULL,
                result VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB init warning: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    expression = data.get("expression", "")

    try:
        result = eval(expression)
    except Exception:
        return jsonify({"error": "Invalid expression"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO calculations (expression, result) VALUES (%s, %s)",
            (expression, str(result)),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB insert warning: {e}")

    return jsonify({"expression": expression, "result": result})

@app.route("/history")
def history():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT expression, result, created_at FROM calculations ORDER BY created_at DESC LIMIT 20"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
