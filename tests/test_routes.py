import pytest
from app import app

def test_home_redirect():
    with app.test_client() as c:
        res = c.get('/')
        assert res.status_code == 302  # redirect to login

def test_login_page():
    with app.test_client() as c:
        res = c.get('/login')
        assert b'Login' in res.data

def test_graph_protection():
    with app.test_client() as c:
        res = c.get('/graph')
        assert res.status_code == 302