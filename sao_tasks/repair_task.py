import os
import subprocess


def repair_panel(repo_path=None, logger=None, run_cmd=None):
    """Realiza reparación del panel: reset hard al HEAD o tag más reciente.
    - repo_path: ruta al repositorio
    - logger: función opcional logger(msg, color)
    - run_cmd: función opcional para ejecutar comandos privilegiados (run_cmd(list, use_sudo=False))
    """
    cwd = repo_path or os.getcwd()

    def log(msg, color="#00ffcc"):
        if logger:
            try:
                logger(msg, color)
            except:
                pass

    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd, capture_output=True).returncode != 0:
        log("Fatal: Not a git repository. Repair aborted.", "#ff4444")
        return subprocess.CompletedProcess(args=[], returncode=1)

    # Identificar versión actual
    proc = subprocess.run(["git", "describe", "--tags"], cwd=cwd, capture_output=True, text=True)
    version = proc.stdout.strip()
    if not version:
        version = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()

    log(f"Restoring to version: {version}...")

    res = subprocess.run(["git", "reset", "--hard", version], cwd=cwd)
    if res.returncode == 0:
        subprocess.run(["git", "clean", "-fd"], cwd=cwd)
        log("REPAIR COMPLETE: Integrity restored.", "#00ffcc")
        return res
    else:
        log("REPAIR FAILED: System manual intervention required.", "#ff4444")
        return res
