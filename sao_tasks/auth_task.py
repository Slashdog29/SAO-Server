import os


def save_token(token, path=None):
    """Guarda el token en ~/.sao_server_token con permiso 600 por seguridad."""
    if token is None:
        return None
    path = path or os.path.expanduser("~/.sao_server_token")
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(token.strip())
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return path


def read_token(path=None):
    path = path or os.path.expanduser("~/.sao_server_token")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None
