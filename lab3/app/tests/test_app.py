# -*- coding: utf-8 -*-
import os
import sys
import re
import pytest

# Добавляем корень проекта (lab3) в PYTHONPATH, чтобы при импорте модуля Flask всё находилось корректно.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Импортируем Flask-приложение (экземпляр app) из файла app/app.py
from app.app import app as application


@pytest.fixture
def client():
    """
    Фикстура тест-клиента Flask приложения.
    Включаем TESTING-режим и возвращаем test_client.
    """
    application.config['TESTING'] = True
    with application.test_client() as client:
        yield client


def extract_counter(html_text):
    """
    Извлекает значение счётчика посещений страницы из HTML.
    Шаблон в counter.html: «Вы посетили эту страницу {{ counter }} раз!»
    Ищем число после «Вы посетили эту страницу» и возвращаем его как int.
    """
    match = re.search(r"Вы посетили эту страницу\s+(\d+)\s+раз", html_text)
    assert match is not None, "Не найден счётчик на странице"
    return int(match.group(1))


def login(client, username, password, remember=False, next_page=None, follow_redirects=False):
    """
    Удобная функция для отправки POST-запроса на /login с учётными данными.
    """
    data = {
        'username': username,
        'password': password,
    }
    if remember:
        data['remember_me'] = 'on'
    if next_page:
        data['next'] = next_page
    return client.post('/login', data=data, follow_redirects=follow_redirects)


def test_counter_anonymous(client):
    """
    Проверяем, что анонимный пользователь при повторных заходах на /counter
    получает растущий счётчик: 1, затем 2, затем 3 и т.д.
    """
    # Первый анонимный запрос
    response1 = client.get('/counter')
    assert response1.status_code == 200
    html1 = response1.data.decode('utf-8')
    count1 = extract_counter(html1)
    assert count1 == 1, f"Ожидали 1 при первом визите, получили {count1}"

    # Второй анонимный запрос
    response2 = client.get('/counter')
    assert response2.status_code == 200
    html2 = response2.data.decode('utf-8')
    count2 = extract_counter(html2)
    assert count2 == count1 + 1, f"Ожидали {count1 + 1}, получили {count2}"

    # Третий анонимный запрос
    response3 = client.get('/counter')
    assert response3.status_code == 200
    html3 = response3.data.decode('utf-8')
    count3 = extract_counter(html3)
    assert count3 == count2 + 1, f"Ожидали {count2 + 1}, получили {count3}"


def test_counter_separation_anonymous_and_authenticated(client):
    """
    Убедимся, что счётчики для анонимного и авторизованного пользователя независимые.
    Логика:
    1) Аноним: первый визит → count_anon1
    2) Аноним: второй визит → count_anon2 = count_anon1 + 1
    3) Логинимся → первый визит авторизованного → count_user1 = 1
    4) Авторизованный: второй визит → count_user2 = count_user1 + 1
    5) Выход → снова аноним → следующий визит → count_anon3 = count_anon2 + 1
    """
    # 1) Аноним: первый визит
    r1 = client.get('/counter')
    assert r1.status_code == 200
    count_anon1 = extract_counter(r1.data.decode('utf-8'))

    # 2) Аноним: второй визит
    r2 = client.get('/counter')
    assert r2.status_code == 200
    count_anon2 = extract_counter(r2.data.decode('utf-8'))
    assert count_anon2 == count_anon1 + 1, f"Ожидали {count_anon1 + 1}, получили {count_anon2}"

    # 3) Логинимся как существующий пользователь (login='user', password='qwerty')
    login_resp = login(client, 'user', 'qwerty', follow_redirects=True)
    assert login_resp.status_code == 200

    # Первый визит авторизованного
    ru1 = client.get('/counter')
    assert ru1.status_code == 200
    count_user1 = extract_counter(ru1.data.decode('utf-8'))
    assert count_user1 == 1, f"Ожидали 1 при первом визите авторизованного, получили {count_user1}"

    # Второй визит авторизованного
    ru2 = client.get('/counter')
    assert ru2.status_code == 200
    count_user2 = extract_counter(ru2.data.decode('utf-8'))
    assert count_user2 == count_user1 + 1, f"Ожидали {count_user1 + 1}, получили {count_user2}"

    # 4) Выход
    client.get('/logout', follow_redirects=True)

    # 5) Опять аноним: следующий визит должен быть count_anon2 + 1
    r3 = client.get('/counter')
    assert r3.status_code == 200
    count_anon3 = extract_counter(r3.data.decode('utf-8'))
    assert count_anon3 == count_anon2 + 1, f"Ожидали {count_anon2 + 1}, получили {count_anon3}"


def test_login_success_flash_and_redirect(client):
    """
    Проверяем успешный логин:
    - После POST /login возвращается статус 302 (редирект).
    - Если follow_redirects=True, на целевой странице есть flash-сообщение об успешной аутентификации.
    """
    resp = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty'},
        follow_redirects=True
    )
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert 'Вы успешно аутентифицированы' in html, "Flash-сообщение не найдено на странице после логина"


def test_login_failure_shows_error(client):
    """
    Проверяем неудачную попытку входа:
    - Остаёмся на странице /login.
    - Отображается сообщение об ошибке «Пользователь не найден».
    """
    resp = client.post(
        '/login',
        data={'username': 'user', 'password': 'wrongpass'},
        follow_redirects=True
    )
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert 'Пользователь не найден' in html, "Сообщение об ошибке не найдено при неверном пароле"


def test_secret_requires_login_and_redirect(client):
    """
    Проверяем, что анонимный при попытке доступа к /secret
    редиректится на /login?next=/secret
    """
    resp = client.get('/secret')
    # Ожидаем перенаправление (302) на /login?next=/secret
    assert resp.status_code in (301, 302)
    location = resp.headers.get('Location', '')
    assert '/login' in location
    assert 'next=%2Fsecret' in location or 'next=/secret' in location


def test_secret_access_authenticated(client):
    """
    Авторизованный пользователь может зайти на /secret и получить статус 200.
    """
    # Логинимся
    login(client, 'user', 'qwerty', follow_redirects=True)
    resp = client.get('/secret')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    # В шаблоне secret.html есть хотя бы какой-то контент, например смайлик «:(:»
    assert ':(:' in html, "Контент секретной страницы не найден"


def test_redirect_to_next_after_login(client):
    """
    При попытке доступа к /secret неавторизованным:
    1) получаем редирект на /login?next=/secret
    2) после логина с тем же next получаем редирект обратно на /secret
    """
    # Шаг 1: аноним идёт на /secret
    r1 = client.get('/secret', follow_redirects=False)
    assert r1.status_code in (301, 302)
    loc1 = r1.headers.get('Location', '')
    assert '/login' in loc1
    assert 'next=%2Fsecret' in loc1 or 'next=/secret' in loc1

    # Шаг 2: делаем POST /login с передачей next=/secret
    r2 = client.post(
        '/login',
        data={'username': 'user', 'password': 'qwerty', 'next': '/secret'},
        follow_redirects=False
    )
    # Ожидаем редирект (302) на /secret
    assert r2.status_code in (301, 302)
    assert r2.headers.get('Location', '').endswith('/secret')


def test_remember_me_sets_cookie(client):
    """
    При логине с remember_me в header Set-Cookie должна присутствовать 'remember_token='
    """
    r = login(client, 'user', 'qwerty', remember=True, follow_redirects=False)
    sc = r.headers.get('Set-Cookie', '')
    assert 'remember_token=' in sc, "Cookie remember_token не установлена"


def test_navbar_links_for_anonymous(client):
    """
    Проверяем навигационное меню для гостя (анонимного пользователя):
    - Есть ссылка на /login
    - Нет ссылок на /secret и /logout
    """
    resp = client.get('/')
    html = resp.data.decode('utf-8')
    assert 'href="/login"' in html, "Ссылка на /login не найдена для анонима"
    assert 'href="/secret"' not in html, "Ссылка на /secret не должна отображаться для анонима"
    assert 'href="/logout"' not in html, "Ссылка на /logout не должна отображаться для анонима"


def test_navbar_links_for_authenticated(client):
    """
    Проверяем навигационное меню для авторизованного пользователя:
    - Есть ссылки на /secret и /logout
    - Нет ссылки на /login
    """
    # Сначала авторизуемся
    login(client, 'user', 'qwerty', follow_redirects=True)
    resp = client.get('/')
    html = resp.data.decode('utf-8')
    assert 'href="/secret"' in html, "Ссылка на /secret должна быть видна после входа"
    assert 'href="/logout"' in html, "Ссылка на /logout должна быть видна после входа"
    assert 'href="/login"' not in html, "Ссылка на /login не должна отображаться после входа"
