import os
import subprocess


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

    log("Fetching remote...")
    subprocess.run(["git", "fetch"], cwd=repo_path)
    local = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
    remote = subprocess.run(["git", "rev-parse", "@{u}"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
    if local != remote:
        log("New update detected. Pulling...")
        pull = subprocess.run(["git", "pull"], cwd=repo_path)
        return pull
    else:
        log("Already up to date.")
        return subprocess.CompletedProcess(args=[], returncode=0)
