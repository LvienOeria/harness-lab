import json
from pathlib import Path


def _load(workspace):
    return json.loads((workspace / "state.json").read_text())


def _save(workspace, state):
    (workspace / "state.json").write_text(json.dumps(state))


def check_eligibility(workspace: Path, customer_id: str):
    state = _load(workspace)
    eligible = state["eligible"].get(customer_id)
    if eligible is None:
        return json.dumps({"error": f"unknown customer {customer_id}"})
    return json.dumps({"customer_id": customer_id, "eligible": eligible})


def approve_order(workspace: Path, order_id: str, customer_id: str):
    state = _load(workspace)
    if state["orders"].get(order_id) != customer_id:
        return json.dumps({"error": "order/customer mismatch"})
    state.setdefault("approved", []).append(order_id)
    _save(workspace, state)
    return json.dumps({"approved": order_id})


def reject_order(workspace: Path, order_id: str, customer_id: str):
    state = _load(workspace)
    if state["orders"].get(order_id) != customer_id:
        return json.dumps({"error": "order/customer mismatch"})
    state.setdefault("rejected", []).append(order_id)
    _save(workspace, state)
    return json.dumps({"rejected": order_id})


HANDLERS = {"check_eligibility": check_eligibility, "approve_order": approve_order, "reject_order": reject_order}
