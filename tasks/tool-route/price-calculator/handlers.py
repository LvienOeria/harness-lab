import json
from pathlib import Path

def _load(ws):
    return json.loads((ws / "state.json").read_text())

def _save(ws, state):
    (ws / "state.json").write_text(json.dumps(state))

def get_price(workspace: Path, item: str):
    prices = {"widget": 400.0}
    if item not in prices:
        return json.dumps({"error": f"unknown item {item}"})
    return json.dumps({"item": item, "price": prices[item]})

def apply_discount(workspace: Path, price: float, discount: float):
    if not 0 <= discount <= 1:
        return json.dumps({"error": "invalid discount"})
    return json.dumps({"discounted": round(price * (1 - discount), 2)})

def get_quote(workspace: Path, unit_price: float, quantity: int):
    state = _load(workspace)
    quote = {"unit_price": unit_price, "quantity": quantity, "total": round(unit_price * quantity, 2)}
    state.setdefault("quotes", []).append(quote)
    _save(workspace, state)
    return json.dumps(quote)

HANDLERS = {"get_price": get_price, "apply_discount": apply_discount, "get_quote": get_quote}
