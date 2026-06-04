"""Módulo de notificaciones: avisa cuando hay un lanzamiento nuevo en GitHub.

Comportamiento:
- Detecta el `origin` remoto para inferir owner/repo en GitHub.
- Consulta la API de GitHub `releases/latest` (o `tags` si no hay releases).
- Compara la etiqueta remota con la versión local (archivo `VERSION` o `get_panel_info`).
- Si la versión remota difiere de la local y no fue notificada antes, llama a `notifier(msg)` y guarda el estado en `.sao_notifications.json`.

No requiere dependencias externas.
"""
import json
import os
import subprocess
import urllib.request
import urllib.error
from typing import Callable, Optional

from .version_info import get_panel_info


def _get_origin_repo(cwd: Optional[str] = None):
    cwd = cwd or os.getcwd()
    try:
        res = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd, capture_output=True, text=True)
        if res.returncode != 0:
            return None
        url = res.stdout.strip()
        # formatos: git@github.com:owner/repo.git o https://github.com/owner/repo.git
        if url.startswith("git@") and ":" in url:
            _, path = url.split(":", 1)
            if path.endswith(".git"):
                path = path[:-4]
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif url.startswith("http"):
            # quitar prefijo y posible .git
            if url.endswith(".git"):
                url = url[:-4]
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                return owner, repo
    except Exception:
        return None
    return None


def _github_api_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "sao-notifier"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8"), resp.getcode()


def get_latest_remote_tag(owner: str, repo: str):
    """Intenta obtener el último release (tag) desde GitHub.
    Devuelve la etiqueta como string o None.
    """
    api_release = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        body, status = _github_api_get(api_release)
        if status == 200:
            data = json.loads(body)
            tag = data.get("tag_name") or data.get("name")
            if tag:
                return tag
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # sin releases, intentar tags
            pass
        else:
            return None
    except Exception:
        return None

    # Fallback a tags list
    try:
        api_tags = f"https://api.github.com/repos/{owner}/{repo}/tags"
        body, status = _github_api_get(api_tags)
        if status == 200:
            data = json.loads(body)
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("name")
    except Exception:
        return None
    return None


def _state_file_path(repo_root: Optional[str] = None):
    repo_root = repo_root or os.getcwd()
    return os.path.join(repo_root, ".sao_notifications.json")


def check_and_notify(repo_path: Optional[str] = None, notifier: Optional[Callable[[str], None]] = None, logger: Optional[Callable[[str], None]] = None):
    """Comprueba si hay un nuevo release y notifica.

    - `notifier(msg)` recibe el mensaje a enviar (por defecto usa `print`).
    - `logger(msg)` se usa para mensajes internos.
    Devuelve un diccionario con el resultado.
    """
    repo_root = repo_path or os.getcwd()
    notifier = notifier or (lambda m: print(m))
    logger = logger or (lambda m: None)

    repo = _get_origin_repo(repo_root)
    if not repo:
        logger("No se pudo determinar remoto 'origin' — notificación cancelada.")
        return {"notified": False, "reason": "no_origin"}

    owner, repo_name = repo
    logger(f"Detected remote: {owner}/{repo_name}")

    latest = get_latest_remote_tag(owner, repo_name)
    if not latest:
        logger("No se pudo obtener la etiqueta/release remota.")
        return {"notified": False, "reason": "no_remote_tag"}

    # versión local preferida
    info = get_panel_info(repo_root)
    local_ver = info.get("version")

    state_file = _state_file_path(repo_root)
    state = {}
    try:
        if os.path.exists(state_file):
            with open(state_file, "r") as sf:
                state = json.load(sf)
    except Exception:
        state = {}

    last_notified = state.get("last_notified")

    # Notificar sólo si la etiqueta remota difiere de la versión local y no fue notificada antes
    if latest != local_ver and latest != last_notified:
        msg = f"Nuevo lanzamiento disponible: {latest} (instalada: {local_ver})"
        notifier(msg)
        # actualizar estado
        state["last_notified"] = latest
        try:
            with open(state_file, "w") as sf:
                json.dump(state, sf)
        except Exception:
            logger("No se pudo guardar el estado de notificación.")
        return {"notified": True, "latest": latest, "local": local_ver}

    return {"notified": False, "latest": latest, "local": local_ver}


if __name__ == "__main__":
    res = check_and_notify(repo_path=".")
    print(res)
