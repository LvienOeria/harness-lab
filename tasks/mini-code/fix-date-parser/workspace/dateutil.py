def parse_iso(value):
    parts = value.split('-')
    return {'year': int(parts[0]), 'month': int(parts[1]), 'day': int(parts[1])}
