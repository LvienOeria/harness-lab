import json
from pathlib import Path

STATE = "inventory.json"


def get_inventory(workspace: Path):
    return json.dumps(json.loads((workspace / STATE).read_text()), indent=2)


def update_stock(workspace: Path, item: str, quantity: int):
    data = json.loads((workspace / STATE).read_text())
    if item not in data:
        return f"error: unknown item {item!r}"
    if not isinstance(quantity, int) or quantity < 0:
        return "error: quantity must be a non-negative integer"
    data[item] = quantity
    (workspace / STATE).write_text(json.dumps(data, indent=2))
    return json.dumps({"updated": item, "quantity": quantity})


HANDLERS = {"get_inventory": get_inventory, "update_stock": update_stock}
