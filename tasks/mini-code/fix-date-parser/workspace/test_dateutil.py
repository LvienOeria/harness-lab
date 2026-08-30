from dateutil import parse_iso

def test_parse():
    assert parse_iso('2024-08-30') == {'year': 2024, 'month': 8, 'day': 30}

def test_invalid():
    try:
        parse_iso('bad')
    except ValueError:
        return
    raise AssertionError('should raise ValueError')
