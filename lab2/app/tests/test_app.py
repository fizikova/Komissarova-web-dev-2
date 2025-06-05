import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_args_no_params(client):
    rv = client.get('/args')
    text = rv.get_data(as_text=True)
    assert '<table' in text
    assert '<td>' not in text

def test_headers_display(client):
    custom_headers = {'X-Test-Header': 'TestValue', 'User-Agent': 'pytest-agent'}
    rv = client.get('/headers', headers=custom_headers)
    text = rv.get_data(as_text=True)
    assert '<table' in text
    assert '<td>X-Test-Header</td>' in text
    assert '<td>TestValue</td>' in text
    assert '<td>User-Agent</td>' in text
    assert '<td>pytest-agent</td>' in text

def test_cookies_set_and_delete(client):
    rv1 = client.get('/cookies')
    headers1 = rv1.headers
    assert 'Set-Cookie' in headers1
    assert 'name=Bob' in headers1['Set-Cookie']

    rv2 = client.get('/cookies', headers={'Cookie': 'name=Bob'})
    headers2 = rv2.headers
    assert 'Set-Cookie' in headers2
    set_cookie_header_2 = headers2['Set-Cookie']
    assert 'Expires' in set_cookie_header_2 or 'Max-Age=0' in set_cookie_header_2

def test_form_get_and_post(client):
    rv_get = client.get('/form')
    text_get = rv_get.get_data(as_text=True)
    assert '<form' in text_get
    assert 'name=' in text_get

    data = {'field1': 'value1', 'field2': 'value2'}
    rv_post = client.post('/form', data=data)
    text_post = rv_post.get_data(as_text=True)
    assert '<td>field1</td>' in text_post or 'field1:' in text_post
    assert '<td>value1</td>' in text_post or 'value1' in text_post
    assert '<td>field2</td>' in text_post or 'field2:' in text_post
    assert '<td>value2</td>' in text_post or 'value2' in text_post

def test_phone_form_get_shows_input(client):
    rv = client.get('/phone_form')
    text = rv.get_data(as_text=True)
    assert 'name="phone"' in text
    assert '<button' in text

@pytest.mark.parametrize("phone_input, expected_error", [
    ("123-abc-4567", "Недопустимый ввод. В номере телефона встречаются недопустимые символы."),
    ("+7(123)4567xyz", "Недопустимый ввод. В номере телефона встречаются недопустимые символы."),
])
def test_phone_form_invalid_chars(client, phone_input, expected_error):
    rv = client.post('/phone_form', data={'phone': phone_input})
    text = rv.get_data(as_text=True)
    assert expected_error in text

@pytest.mark.parametrize("phone_input", [
    "1234567",
    "123456789012",
    "+9 (123) 456-78-90",
    "91234567890",
])
def test_phone_form_invalid_length(client, phone_input):
    rv = client.post('/phone_form', data={'phone': phone_input})
    text = rv.get_data(as_text=True)
    assert "Недопустимый ввод. Неверное количество цифр." in text

@pytest.mark.parametrize("phone_input, expected_formatted", [
    ("+7 (123) 456-75-90", "8-123-456-75-90"),
    ("8(123)4567590",       "8-123-456-75-90"),
    ("123.456.75.90",       "8-123-456-75-90"),
    ("81234567890",         "8-123-456-78-90"),
    ("1234567890",          "8-123-456-78-90"),
    ("8 (912) 345 67 89",   "8-912-345-67-89"),
])
def test_phone_form_valid_numbers(client, phone_input, expected_formatted):
    rv = client.post('/phone_form', data={'phone': phone_input})
    text = rv.get_data(as_text=True)
    assert expected_formatted in text

def test_phone_form_multiple_invalid_cases(client):
    rv_empty = client.post('/phone_form', data={'phone': ''})
    text_empty = rv_empty.get_data(as_text=True)
    assert "Недопустимый ввод" in text_empty

    rv_no_digits = client.post('/phone_form', data={'phone': '()- .+'})
    text_no_digits = rv_no_digits.get_data(as_text=True)
    assert "Недопустимый ввод" in text_no_digits

    rv_exact10 = client.post('/phone_form', data={'phone': '0987654321'})
    text_exact10 = rv_exact10.get_data(as_text=True)
    assert "8-098-765-43-21" in text_exact10

    rv_11_with_chars = client.post('/phone_form', data={'phone': '8 (777) 555 33 22'})
    text_11_with_chars = rv_11_with_chars.get_data(as_text=True)
    assert "8-777-555-33-22" in text_11_with_chars
