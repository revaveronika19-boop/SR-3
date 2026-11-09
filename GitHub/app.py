"""Каталог книг, замовлення та REST API. Навчальний проєкт."""
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort

DB_DEFAULT = str(Path(__file__).with_name('library.db'))

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'local-development-only'), DATABASE=DB_DEFAULT)
    if test_config:
        app.config.update(test_config)

    def db():
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

    def initialize():
        with db() as con:
            con.executescript("""CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>0));
            CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL REFERENCES books(id), customer TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0));""")
            if con.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 0:
                con.executemany('INSERT INTO books(title,author,price) VALUES(?,?,?)', SAMPLE_BOOKS)

    @app.get('/')
    def index():
        with db() as con:
            books = [dict(r) for r in con.execute('SELECT * FROM books ORDER BY id')]
        return render_template('index.html', books=books, visits=session.get('visits', 0))

    @app.get('/visit')
    def visit():
        session['visits'] = session.get('visits', 0) + 1
        response = redirect(url_for('index'))
        response.set_cookie('preferred_language', 'uk', max_age=86400, samesite='Lax')
        return response

    @app.post('/books')
    def create_book():
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        try: price = int(request.form.get('price', ''))
        except ValueError: return 'Ціна має бути числом', 400
        if not title or not author or price <= 0: return 'Некоректні дані', 400
        with db() as con: con.execute('INSERT INTO books(title,author,price) VALUES(?,?,?)', (title,author,price))
        return redirect(url_for('index'))

    @app.post('/books/<int:book_id>/edit')
    def edit_book(book_id):
        title = request.form.get('title', '').strip()
        if not title: return 'Порожня назва', 400
        with db() as con:
            cur = con.execute('UPDATE books SET title=? WHERE id=?', (title,book_id))
            if cur.rowcount == 0: abort(404)
        return redirect(url_for('index'))

    @app.post('/books/<int:book_id>/delete')
    def delete_book(book_id):
        with db() as con:
            try: con.execute('DELETE FROM books WHERE id=?', (book_id,))
            except sqlite3.IntegrityError: return 'Книгу вже замовлено', 409
        return redirect(url_for('index'))

    @app.post('/orders')
    def order():
        customer = request.form.get('customer', '').strip()
        try:
            book_id = int(request.form.get('book_id', ''))
            quantity = int(request.form.get('quantity', '1'))
        except ValueError: return 'Некоректні числа', 400
        if not customer or quantity <= 0: return 'Некоректне замовлення', 400
        with db() as con:
            try: con.execute('INSERT INTO orders(book_id,customer,quantity) VALUES(?,?,?)', (book_id,customer,quantity))
            except sqlite3.IntegrityError: return 'Книгу не знайдено', 404
        return redirect(url_for('orders'))

    @app.get('/orders')
    def orders():
        with db() as con:
            rows = [dict(r) for r in con.execute('SELECT o.id,b.title,o.customer,o.quantity FROM orders o JOIN books b ON b.id=o.book_id ORDER BY o.id')]
        return render_template('orders.html', orders=rows)

    @app.get('/api/books')
    def api_books():
        query = request.args.get('q','').strip()
        with db() as con:
            rows = con.execute('SELECT * FROM books WHERE title LIKE ? ORDER BY id', ('%'+query+'%',)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route('/api/books/<int:book_id>', methods=['GET','PATCH','DELETE'])
    def api_book(book_id):
        with db() as con:
            row = con.execute('SELECT * FROM books WHERE id=?',(book_id,)).fetchone()
            if row is None: return jsonify(error='Не знайдено'),404
            if request.method == 'GET': return jsonify(dict(row))
            if request.method == 'DELETE':
                try: con.execute('DELETE FROM books WHERE id=?',(book_id,))
                except sqlite3.IntegrityError: return jsonify(error='Є замовлення'),409
                return '',204
            data = request.get_json(silent=True)
            if not isinstance(data,dict) or not isinstance(data.get('title'),str) or not data['title'].strip():
                return jsonify(error='Потрібна назва'),400
            con.execute('UPDATE books SET title=? WHERE id=?',(data['title'].strip(),book_id))
            return jsonify(id=book_id,title=data['title'].strip())

    initialize()
    return app

SAMPLE_BOOKS = [('Кобзар', 'Тарас Шевченко', 250), ('Лісова пісня', 'Леся Українка', 190)]
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
