import pytest
from app import app

def test_submit_requires_login():
    with app.test_client() as c:
        res = c.post('/submit', data={'text': 'John Doe from Google'})
        assert res.status_code == 302