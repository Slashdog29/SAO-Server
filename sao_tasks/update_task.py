import os
import subprocess
import socket
import time


def run_update(repo_path=None, logger=None):
    """Ejecuta el script de actualización `scripts/update.sh` si existe,
    o realiza un `git pull` en `repo_path` como fallback.
    logger: función opcional para registrar mensajes (logger(msg, color)).
    """
    cwd = repo_path or os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(cwd, "scripts", "update.sh")
    script = os.path.normpath(script)

    def log(msg, color="#00ffcc"):
        if logger:
            try:
                logger(msg, color)
            except:
                pass

    def _check_network(host="github.com", timeout=3, retries=3, backoff=1):
        """Verifica resolución/conectividad hacia host antes de operaciones git remotas.
        Retorna True si puede resolver o conectar, False en caso contrario.
        """
        for attempt in range(1, retries + 1):
            try:
                # Intentar resolución DNS
                socket.getaddrinfo(host, 443)
                # Intentar conexión TCP rápida
                s = socket.create_connection((host, 443), timeout)
                s.close()
                return True
            except Exception:
                log(f"Network check failed (attempt {attempt}/{retries}).", "#ffbb33")
                if attempt < retries:
                    time.sleep(backoff * attempt)
        return False

    if os.path.exists(script):
        log(f"Running update script: {script}")
        res = subprocess.run([script], cwd=cwd)
        return res

    # Fallback: ejecutar git pull
    if not repo_path:
        repo_path = os.getcwd()

    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_path, capture_output=True).returncode != 0:
        log("Not a git repository. Update aborted.", "#ff4444")
        return subprocess.CompletedProcess(args=[], returncode=1)

    log("Checking network connectivity to github.com...")
    if not _check_network():
        log("Network unreachable: cannot contact github.com. Update aborted.", "#ff4444")
        return subprocess.CompletedProcess(args=[], returncode=2)

    log("Fetching remote...")
    subprocess.run(["git", "fetch"], cwd=repo_path)
    local = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
    remote = subprocess.run(["git", "rev-parse", "@{u}"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
    if local != remote:
        log("New update detected. Pulling...")
        pull = subprocess.run(["git", "pull"], cwd=repo_path)
        if pull.returncode == 0:
            return pull
        # Si falla por autenticación, intentar fallback con token
        token = os.environ.get("SAO_GIT_TOKEN")
        token_file = os.path.expanduser("~/.sao_server_token")
        if not token and os.path.exists(token_file):
            try:
                with open(token_file, "r") as tf:
                    token = tf.read().strip()
            except: token = None

        if token:
            # Construir URL HTTPS temporal
            origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
            # Extraer repo path
            repo_path_remote = origin.split("github.com")[-1].lstrip(':/')
            https_url = f"https://x-access-token:{token}@github.com/{repo_path_remote}"
            log("Attempting token-based pull via HTTPS...")
            pull2 = subprocess.run(["git", "pull", https_url, "HEAD"], cwd=repo_path)
            return pull2
        return pull
    else:
        log("Already up to date.")
        return subprocess.CompletedProcess(args=[], returncode=0)
