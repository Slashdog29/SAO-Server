import os
import subprocess
from datetime import datetime


def _run_git(cmd, cwd):
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def get_panel_info(repo_path=None):
    """Devuelve un diccionario con información de versión del panel.
    Campos: version, commit, branch, author, date, timestamp
    """
    repo_root = repo_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    info = {
        "version": None,
        "commit": None,
        "branch": None,
        "author": None,
        "date": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Prefer explicit VERSION file or environment override so the user can control displayed version
    version_file = os.path.join(repo_root, "VERSION")
    env_ver = os.environ.get("SAO_PANEL_VERSION")
    if env_ver:
        info["version"] = env_ver
    elif os.path.exists(version_file):
        try:
            with open(version_file, "r") as vf:
                info["version"] = vf.read().strip()
        except Exception:
            info["version"] = None
    else:
        # Tags / version from git
        ver = _run_git(["git", "describe", "--tags", "--always"], repo_root)
        if ver:
            info["version"] = ver

    # Commit
    commit = _run_git(["git", "rev-parse", "--short", "HEAD"], repo_root)
    if commit:
        info["commit"] = commit

    # Branch
    branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    if branch:
        info["branch"] = branch

    # Author and date
    author = _run_git(["git", "show", "-s", "--format=%an <%ae>" , "HEAD"], repo_root)
    if author:
        info["author"] = author
    date = _run_git(["git", "show", "-s", "--format=%ci", "HEAD"], repo_root)
    if date:
        info["date"] = date

    return info
