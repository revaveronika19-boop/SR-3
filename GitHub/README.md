# СР №3 — онлайн-замовлення книг

Студент: Рева Вероніка, БІКСб2-25-4-0д.

## Запуск (Windows)
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Відкрити http://127.0.0.1:5000/ .

## Тести
`python -m pytest -v`

## Функції
SQLite: книги та замовлення; HTML: CRUD, замовлення; JSON REST API: GET /api/books, GET/PATCH/DELETE /api/books/<id>; сесія та cookie.

**Увага:** демонстраційний проєкт, не для публічного розгортання без CSRF, авторизації та безпечного SECRET_KEY.
