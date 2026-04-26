import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.serving import make_server

app = Flask(__name__)
DB_PATH = '/root/todo-app/todos.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        completed INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def get_todos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute('SELECT * FROM todos')
    todos = [dict(row) for row in cur.fetchall()]
    conn.close()
    return todos

def add_todo(task):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO todos (task) VALUES (?)', (task,))
    conn.commit()
    conn.close()

def delete_todo(todo_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()

def toggle_todo(todo_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE todos SET completed = NOT completed WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Todo App</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
              background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: white; 
                     border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        header { background: #4a90d9; color: white; padding: 20px; text-align: center; }
        h1 { margin: 0; font-size: 24px; font-weight: 500; }
        form { display: flex; padding: 15px; background: #fafafa; border-bottom: 1px solid #eee; }
        input[type="text"] { flex: 1; padding: 12px; border: 1px solid #ddd; 
                           border-radius: 4px; font-size: 16px; outline: none; }
        input[type="text"]:focus { border-color: #4a90d9; }
        button { padding: 12px 20px; background: #4a90d9; color: white; border: none; 
                 border-radius: 4px; font-size: 16px; cursor: pointer; margin-left: 10px; }
        button:hover { background: #357abd; }
        ul { list-style: none; margin: 0; padding: 0; }
        li { display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }
        li:last-child { border-bottom: none; }
        .checkbox { width: 20px; height: 20px; margin-right: 15px; cursor: pointer; }
        .task { flex: 1; font-size: 16px; color: #333; }
        .task.completed { text-decoration: line-through; color: #999; }
        .delete { color: #dc3545; text-decoration: none; padding: 5px 10px; 
                  border-radius: 4px; }
        .delete:hover { background: #fee; }
        .empty { padding: 40px; text-align: center; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>Todo App</h1></header>
        <form method="post" action="{{ url_for('add') }}">
            <input type="text" name="todo" placeholder="What needs to be done?" required autofocus>
            <button type="submit">Add</button>
        </form>
        <ul>
            {% for todo in todos %}
            <li>
                <form action="{{ url_for('toggle', todo_id=todo.id) }}" method="post" style="display:flex;align-items:center;flex:1">
                    <input type="checkbox" class="checkbox" {% if todo.completed %}checked{% endif %} 
                           onchange="this.form.submit()">
                    <span class="task {% if todo.completed %}completed{% endif %}">{{ todo.task }}</span>
                </form>
                <a href="{{ url_for('delete', todo_id=todo.id) }}" class="delete">Delete</a>
            </li>
            {% else %}
            <li class="empty">No todos yet. Add one above!</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, todos=get_todos())

@app.route('/add', methods=['POST'])
def add():
    task = request.form.get('todo', '').strip()
    if task:
        add_todo(task)
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    delete_todo(todo_id)
    return redirect(url_for('index'))

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle(todo_id):
    toggle_todo(todo_id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    server = make_server('0.0.0.0', 7890, app)
    server.serve_forever()