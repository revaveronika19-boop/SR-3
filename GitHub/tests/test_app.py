import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    app = create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.db'),'SECRET_KEY':'test-key'})
    return app.test_client()

def test_home(client):
    assert client.get('/').status_code == 200

def test_api_list(client):
    assert len(client.get('/api/books').json) == 2

def test_create_book(client):
    response = client.post('/books',data={'title':'Нова книга','author':'Автор','price':'200'})
    assert response.status_code == 302
    assert len(client.get('/api/books').json) == 3

def test_invalid_book(client):
    assert client.post('/books',data={'title':'','author':'A','price':'-1'}).status_code == 400

def test_order(client):
    assert client.post('/orders',data={'book_id':'1','customer':'Олена','quantity':'2'}).status_code == 302
    assert 'Олена' in client.get('/orders').get_data(as_text=True)

def test_api_patch(client):
    assert client.patch('/api/books/1',json={'title':'Оновлена'}).status_code == 200
    assert client.get('/api/books/1').json['title'] == 'Оновлена'

def test_missing(client):
    assert client.get('/api/books/999').status_code == 404

def test_session(client):
    client.get('/visit')
    assert '1' in client.get('/').get_data(as_text=True)
