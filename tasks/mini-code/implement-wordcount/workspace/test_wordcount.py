from wordcount import count_words

def test_simple():
    assert count_words('hello world') == 2

def test_whitespace():
    assert count_words('  one   two  three ') == 3

def test_empty():
    assert count_words('') == 0
