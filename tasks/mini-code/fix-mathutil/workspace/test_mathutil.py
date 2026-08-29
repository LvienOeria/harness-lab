from mathutil import mean, median

def test_mean():
    assert mean([1, 2, 3]) == 2.0

def test_mean_empty_error():
    try:
        mean([])
    except ZeroDivisionError:
        return
    raise AssertionError("empty list should raise ZeroDivisionError")

def test_median_odd():
    assert median([3, 1, 2]) == 2

def test_median_even():
    assert median([4, 1, 3, 2]) == 2.5
