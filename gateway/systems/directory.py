"""Demo directory backend: the staff directory as static synthetic records."""

_USERS = {
    "ada@example.com": {"email": "ada@example.com", "name": "Ada Chen", "dept": "Engineering", "title": "Staff Engineer", "active": True},
    "bo@example.com": {"email": "bo@example.com", "name": "Bo Okafor", "dept": "Engineering", "title": "Engineer", "active": True},
    "cy@example.com": {"email": "cy@example.com", "name": "Cy Marsh", "dept": "Support", "title": "Support Lead", "active": True},
    "dee@example.com": {"email": "dee@example.com", "name": "Dee Novak", "dept": "Support", "title": "Support Engineer", "active": False},
    "eli@example.com": {"email": "eli@example.com", "name": "Eli Fontaine", "dept": "Finance", "title": "Controller", "active": True},
    "fay@example.com": {"email": "fay@example.com", "name": "Fay Iwata", "dept": "Operations", "title": "Ops Manager", "active": True},
}


def list_users(dept: str | None = None) -> list[dict]:
    users = list(_USERS.values())
    if dept is not None:
        users = [u for u in users if u["dept"].lower() == dept.lower()]
    return users


def get_user(email: str) -> dict | None:
    return _USERS.get(email)
