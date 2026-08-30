import json
from pathlib import Path

def _load(ws):
    return json.loads((ws / "tickets.json").read_text())

def _save(ws, state):
    (ws / "tickets.json").write_text(json.dumps(state))

def get_ticket(workspace: Path, ticket_id: str):
    state = _load(workspace)
    if ticket_id not in state:
        return json.dumps({"error": f"unknown ticket {ticket_id}"})
    return json.dumps({"ticket_id": ticket_id, "severity": state[ticket_id]})

def set_ticket_status(workspace: Path, ticket_id: str, status: str):
    state = _load(workspace)
    if ticket_id not in state:
        return json.dumps({"error": f"unknown ticket {ticket_id}"})
    state.setdefault("statuses", {})[ticket_id] = status
    _save(workspace, state)
    return json.dumps({"ticket_id": ticket_id, "status": status})

HANDLERS = {"get_ticket": get_ticket, "set_ticket_status": set_ticket_status}
