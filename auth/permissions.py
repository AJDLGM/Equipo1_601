ROLE_LEVELS = {
    "externo": 4,
    "operativo": 3,
    "coordinador": 2,
    "admin": 1
}

PERMISSIONS = {
    4: ["consult"],
    3: ["consult", "edit"],
    2: ["consult", "edit", "authorize"],
    1: ["consult", "edit", "authorize", "templates"]
}

def get_permissions(role):
    level = ROLE_LEVELS.get(role)
    return PERMISSIONS.get(level, [])

def has_permission(role, permission):
    return permission in get_permissions(role)