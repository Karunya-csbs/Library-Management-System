from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_NAME = 'books.db'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Books
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            author TEXT,
            type TEXT,
            description TEXT,
            available TEXT DEFAULT 'Yes'
        )
    ''')

    # Transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT,
            student_name TEXT,
            date_time TEXT,
            action TEXT
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists!"
        conn.close()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', books=books)


@app.route('/insert', methods=['GET', 'POST'])
def insert_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        book_type = request.form['type']
        description = request.form['description']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (name, author, type, description) VALUES (?, ?, ?, ?)",
                       (name, author, book_type, description))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('insert_book.html')


@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/issue_return', methods=['GET', 'POST'])
def issue_return():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Handle delete request
    delete_id = request.args.get('delete')
    if delete_id:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (delete_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('issue_return'))

    # Handle issue/return form submission
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        student_name = request.form.get('student_name')
        action = request.form.get('action')
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if book_name and student_name and action:
            # Insert into transactions
            cursor.execute(
                "INSERT INTO transactions (book_name, student_name, date_time, action) VALUES (?, ?, ?, ?)",
                (book_name, student_name, date_time, action)
            )

            # Update availability
            new_status = 'No' if action == 'issue' else 'Yes'
            cursor.execute("UPDATE books SET available = ? WHERE name = ?", (new_status, book_name))

            conn.commit()

    # Fetch books and transactions
    cursor.execute("SELECT name FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    transactions = cursor.fetchall()
    conn.close()

    return render_template('issue_return.html', books=[b['name'] for b in books], transactions=transactions)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

