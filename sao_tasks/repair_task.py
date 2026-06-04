import os
import subprocess
from datetime import datetime
from .version_info import get_panel_info


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

    # Intentar usar la versión instalada (no la última del remoto)
    info = get_panel_info(repo_path=cwd)
    version = info.get("version")

    # Si no hay versión explícita, buscar commit corto
    if not version:
        version = info.get("commit")

    # Si aún no hay versión, caer a describe/HEAD como último recurso
    if not version:
        proc = subprocess.run(["git", "describe", "--tags"], cwd=cwd, capture_output=True, text=True)
        version = proc.stdout.strip()
        if not version:
            version = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()

    # Hacer respaldo tar.gz del estado de trabajo actual (incluye archivos no trackeados)
    try:
        backups_dir = os.path.join(cwd, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        archive_name = os.path.join(backups_dir, f"backup_before_repair_{ts}.tar.gz")
        log(f"Creando backup: {archive_name}")
        subprocess.run(["tar", "-czf", archive_name, "-C", cwd, "."], check=True)
    except Exception as e:
        log(f"Backup falló: {e}", "#ff7f00")

    # Revisar si hay cambios locales no confirmados
    status = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    if status:
        # Crear una rama de backup y commitear los cambios locales (incluye no rastreados)
        import time
        ts = time.strftime("%Y%m%d%H%M%S")
        backup_branch = f"sao-autobackup-{ts}"
        log(f"Uncommitted changes detected. Creating backup branch: {backup_branch}")
        # Crear rama desde HEAD
        subprocess.run(["git", "branch", backup_branch], cwd=cwd)
        # Añadir y commitear todos los cambios
        add = subprocess.run(["git", "add", "-A"], cwd=cwd)
        if add.returncode == 0:
            commit = subprocess.run(["git", "commit", "-m", f"Autobackup before repair {ts}"], cwd=cwd)
            if commit.returncode == 0:
                log(f"Backup saved on branch {backup_branch}")
            else:
                log("Backup commit failed — attempting to stash instead.", "#ffbb33")
                subprocess.run(["git", "stash", "push", "-u", "-m", f"autobackup-{ts}"], cwd=cwd)
        else:
            log("git add failed — attempting to stash instead.", "#ffbb33")
            subprocess.run(["git", "stash", "push", "-u", "-m", f"autobackup-{ts}"], cwd=cwd)

    log(f"Restaurando a la versión: {version}...")

    # Intentar verificar que la versión/tag exista localmente; si no, traer tags del remoto
    verify = subprocess.run(["git", "rev-parse", "--verify", "--quiet", version], cwd=cwd, capture_output=True)
    if verify.returncode != 0:
        log("Versión no encontrada localmente — intentando traer tags desde el remoto...", "#ffbb33")
        subprocess.run(["git", "fetch", "--tags", "origin"], cwd=cwd)

    res = subprocess.run(["git", "reset", "--hard", version], cwd=cwd)
    if res.returncode == 0:
        subprocess.run(["git", "clean", "-fd"], cwd=cwd)
        log("REPAIR COMPLETE: Integrity restored.", "#00ffcc")
        return res
    else:
        log("REPAIR FAILED: System manual intervention required.", "#ff4444")
        return res
