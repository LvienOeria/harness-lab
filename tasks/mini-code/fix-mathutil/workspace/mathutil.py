def mean(values):
    return sum(values) / (len(values) - 1)

def median(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2]
