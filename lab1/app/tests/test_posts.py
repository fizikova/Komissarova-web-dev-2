import pytest
from app.app import app, posts_list as real_posts_list
from flask import template_rendered
from contextlib import contextmanager


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def posts_list():
    return real_posts_list()


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

#Проверка страницы /posts
def test_posts_index(client):
    response = client.get("/posts")
    assert response.status_code == 200
    assert "Последние посты" in response.text

#Шаблон и контекст /posts
def test_posts_index_template(client, posts_list, mocker):
    with captured_templates(app) as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
        _ = client.get('/posts')
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'posts.html'
        assert context['title'] == 'Посты'
        assert len(context['posts']) == len(posts_list)

#Шаблон /about
def test_about_template(client):
    with captured_templates(app) as templates:
        response = client.get('/about')
        assert response.status_code == 200
        template, _ = templates[0]
        assert template.name == 'about.html'

#Шаблон /posts/<index>
def test_post_template(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    with captured_templates(app) as templates:
        response = client.get('/posts/0')
        assert response.status_code == 200
        template, context = templates[0]
        assert template.name == 'post.html'
        assert context['post'] == posts_list[0]

#Отображение данных поста
def test_post_content_rendering(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    response = client.get('/posts/0')
    post = posts_list[0]
    assert post['title'] in response.text
    assert post['author'] in response.text
    assert post['text'][:30] in response.text
    assert post['date'].strftime('%d.%m.%Y') in response.text

#Формат даты
def test_post_date_format(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    response = client.get('/posts/0')
    formatted = posts_list[0]['date'].strftime('%d.%m.%Y')
    assert formatted in response.text

#404 если поста нет
def test_post_404(client):
    response = client.get('/posts/999')
    assert response.status_code == 404

#Отображение комментариев
def test_comments_visible(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    response = client.get('/posts/0')
    for comment in posts_list[0]['comments']:
        assert comment['author'] in response.text
        assert comment['text'][:20] in response.text

#Ответы на комментарии
def test_comment_replies_visible(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    response = client.get('/posts/0')
    for comment in posts_list[0]['comments']:
        for reply in comment.get('replies', []):
            assert reply['author'] in response.text
            assert reply['text'][:20] in response.text

#Картинка поста
def test_post_image_displayed(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    img = posts_list[0]['image_id']
    response = client.get('/posts/0')
    assert f"images/{img}" in response.text

#Форма комментария
def test_post_form_displayed(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    response = client.get('/posts/0')
    assert "<form" in response.text
    assert "Оставьте комментарий" in response.text

#<title> на странице
def test_html_title(client):
    response = client.get('/posts')
    assert "<title>" in response.text

#Ссылки в навбаре
def test_navbar_links(client):
    response = client.get('/')
    assert "Задание" in response.text
    assert "Посты" in response.text
    assert "Об авторе" in response.text

#Содержимое футера
def test_footer_content(client):
    response = client.get('/')
    assert "Комиссарова Алена Сергеевна" in response.text
    assert "231-3213" in response.text

#Заголовки всех постов
def test_all_post_titles_present(client, posts_list, mocker):
    mocker.patch("app.posts_list", return_value=posts_list)
    for i, post in enumerate(posts_list):
        response = client.get(f'/posts/{i}')
        assert post['title'] in response.text
