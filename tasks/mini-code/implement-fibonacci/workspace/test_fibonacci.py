from fibonacci import fibonacci

def test_base():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1

def test_small():
    assert fibonacci(10) == 55

def test_negative():
    try:
        fibonacci(-1)
    except ValueError:
        return
    raise AssertionError('negative should raise ValueError')
