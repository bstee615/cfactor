import re

from refactorings.random_word import get_random_word, get_random_typename_value


def test_get_random_word():
    words = set()
    for _ in range(1000):
        w = get_random_word()
        words.add(w)
        assert all(c in '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM' for c in w), w
    assert len(words) > 990  # 0.1% collision rate


def test_get_random_typename_value():
    words = set()
    for _ in range(1000):
        t, v = get_random_typename_value()
        words.add((t, v))
        assert t in ('int', 'char', 'char *')
        if t == 'int':
            assert re.match(r'^[a-zA-Z0-9]+$', v), t + ' ' + v
        elif t == 'char':
            assert len(v) == 3, t + ' ' + v
            assert v[0] == "'", t + ' ' + v
            assert re.match(r'^[a-zA-Z0-9]$', v[1]), t + ' ' + v
            assert v[2] == "'", t + ' ' + v
        elif t == 'char *':
            assert v[1:-1].isalnum(), t + ' ' + v
    assert len(words) > 600  # 40% collision rate
