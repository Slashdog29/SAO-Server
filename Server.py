import sys
import subprocess
import os
import time
from datetime import datetime
import getpass

# --- BLOQUE DE AUTO-INSTALACIÓN (PACMAN NATIVO PARA ARCH) ---
def ensure_dependencies():
    # Definimos las dependencias: { "modulo_python": "paquete_pacman" }
    requirements = {
        "psutil": "python-psutil",
        "PyQt6": "python-pyqt6"
    }
    
    missing_packages = []
    
    # 1. Verificar módulos de Python
    for module, package in requirements.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
            
    # 2. Verificar binarios esenciales de sistema
    essential_tools = {"git": "git", "wget": "wget", "curl": "curl"}
    for tool, package in essential_tools.items():
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            missing_packages.append(package)

    if missing_packages:
        print(f"\n[SYSTEM] INITIATING NEURAL LINK SYNC... (Missing: {', '.join(missing_packages)})")
        try:
            # Instalación automática usando pacman
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "--needed"] + missing_packages, check=True)
            print("[SUCCESS] Sync Complete. Restarting Script...\n")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"[ERROR] Sync Failed: {e}")
            print("[HINT] Asegúrate de tener conexión a internet y privilegios de sudo.")
            sys.exit(1)

ensure_dependencies()

import psutil
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QProgressBar, QTextEdit, QFrame, QGridLayout, 
                             QInputDialog, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor

# --- DISEÑO GLASS-SAO PREMIUM (QSS) ---
SAO_GLASS_QSS = """
QMainWindow { background-color: transparent; }

QWidget#MainContainer {
    background-color: rgba(15, 15, 22, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 20px;
}

QFrame#GlassCard {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

QLabel { color: #ffffff; font-family: 'Inter', sans-serif; }

QProgressBar {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: rgba(0, 0, 0, 0.5);
    height: 18px;
    text-align: center;
    color: white;
    font-size: 10px;
    font-weight: bold;
    border-radius: 4px;
}
QProgressBar::chunk { width: 2px; }

QPushButton {
    background-color: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 10px;
    color: white;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 10px;
    border-radius: 5px;
}
QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }

QPushButton#LinkStart {
    border: 2px solid #00ffcc;
    color: #00ffcc;
    background-color: rgba(0, 255, 204, 0.05);
}
QPushButton#LinkStart:hover { background-color: #00ffcc; color: #000; }

QPushButton#LogOut {
    border: 2px solid #ff7f00;
    color: #ff7f00;
    background-color: rgba(255, 127, 0, 0.05);
}
QPushButton#LogOut:hover { background-color: #ff7f00; color: #000; }

QPushButton#FolderBtn {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px dashed #ff7f00;
    color: #ff7f00;
}

QDialog#DependencyDialog {
    background-color: rgba(10, 10, 15, 0.98);
    border: 2px solid #00ffcc;
    border-radius: 15px;
}

QLabel#CriticalLabel { color: #ff4444; font-weight: bold; font-size: 11px; }
QLabel#RecommendedLabel { color: #00ccff; font-weight: bold; font-size: 11px; }

QPushButton#ActionBtn {
    min-width: 120px;
    height: 30px;
    border: 1px solid #00ffcc;
    background: rgba(0, 255, 204, 0.1);
    color: #00ffcc;
}

QPushButton#ProjectBtn {
    background-color: rgba(0, 255, 204, 0.1);
    border: 1px solid #00ffcc;
    color: #00ffcc;
}

QComboBox {
    background-color: rgba(0, 0, 0, 0.6);
    border: 1px solid #00ffcc;
    border-radius: 4px;
    padding: 5px;
    color: #00ffcc;
    font-weight: bold;
}

QTextEdit#YuiTerminal {
    background-color: rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: #00ffcc;
    font-family: 'Fira Code', monospace;
    font-size: 11px;
    border-radius: 8px;
}
"""

class YuiMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.terminal = QTextEdit()
        self.terminal.setObjectName("YuiTerminal")
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal)

    def log(self, text, color="#00ffcc"):
        now = datetime.now().strftime("%H:%M:%S")
        self.terminal.append(f"<span style='color: #555;'>[{now}]</span> <span style='color: {color};'>&gt; {text}</span>")
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())

class DependencyDialog(QDialog):
    def __init__(self, missing_crit, missing_recom, parent=None):
        super().__init__(parent)
        self.setObjectName("DependencyDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 350)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("CORE DEPENDENCY SCAN")
        title.setStyleSheet("font-size: 18px; color: #00ffcc; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        if missing_crit:
            layout.addWidget(QLabel("CRITICAL (Missing Installation):", objectName="CriticalLabel"))
            for pkg in missing_crit:
                layout.addWidget(QLabel(f" • {pkg}"))
        
        if missing_recom:
            layout.addSpacing(10)
            layout.addWidget(QLabel("RECOMMENDED:", objectName="RecommendedLabel"))
            for pkg in missing_recom:
                layout.addWidget(QLabel(f" • {pkg}"))
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_ignore = QPushButton("IGNORE")
        self.btn_install = QPushButton("INSTALL AUTOMATICALLY")
        self.btn_install.setObjectName("ActionBtn")
        
        self.btn_ignore.clicked.connect(self.reject)
        self.btn_install.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_ignore)
        btn_layout.addWidget(self.btn_install)
        layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

class SudoDialog(QInputDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AUTHENTICATION REQUIRED")
        self.setLabelText("Enter Neural Link Admin Password (SUDO):")
        self.setTextEchoMode(QLineEdit.EchoMode.Password)
        self.setStyleSheet(SAO_GLASS_QSS + """
            QInputDialog { background-color: rgba(15, 15, 22, 0.98); border: 2px solid #ff7f00; }
            QLineEdit { background-color: #000; color: #ff7f00; border: 1px solid #ff7f00; padding: 5px; }
            QPushButton { min-width: 80px; }
        """)

class Kirito(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAO FORGE DIRECTORY - ARCH ADMIN")
        self.resize(1100, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.sudo_password = None
        self.service_status_dots = {}
        self.git_repo_url = "git@github.com:Slashdog29/SAO-Server.git"
        self.critical_deps = ["php", "apache", "mariadb", "php-apache", "php-gd"]
        self.recommended_deps = ["vte3", "mailpit"]

        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        self.yui = YuiMonitor()
        self.init_ui()
        
        # Iniciar monitoreo de métricas reales
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.refresh_real_stats)
        self.stats_timer.timeout.connect(self.poll_services_status)
        self.stats_timer.start(2000)
        
        # Cargar versiones de PHP instaladas
        self.detect_php_versions()
        self.refresh_projects()
        
        self.setStyleSheet(SAO_GLASS_QSS)
        self.yui.log("Neural Link Established. System Metrics: Online.", "#00ffcc")
        
        # Ejecutar verificación de dependencias al inicio
        QtCore.QTimer.singleShot(500, self.check_system_dependencies)

    def get_sudo_auth(self):
        if self.sudo_password:
            return True
        
        dialog = SudoDialog(self)
        if dialog.exec():
            password = dialog.textValue()
            # Validar contraseña con un comando simple
            check = subprocess.run(["sudo", "-S", "true"], input=f"{password}\n", text=True, capture_output=True, env=os.environ.copy())
            if check.returncode == 0:
                self.sudo_password = password
                self.yui.log("Sudo Authentication: SUCCESSFUL", "#00ffcc")
                return True
            else:
                self.yui.log("Sudo Authentication: FAILED. Invalid Password.", "#ff4444")
                self.sudo_password = None
                return False
        return False

    def run_cmd(self, args, use_sudo=False, capture=True):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        if use_sudo:
            if not self.get_sudo_auth():
                return None
            full_cmd = ["sudo", "-S"] + args
            input_data = f"{self.sudo_password}\n"
        else:
            full_cmd = args
            input_data = None

        try:
            result = subprocess.run(
                full_cmd, 
                input=input_data, 
                capture_output=capture, 
                env=env,
                text=True
            )
            return result
        except Exception as e:
            self.yui.log(f"Execution Error: {e}", "#ff4444")
            return None

    def check_system_dependencies(self):
        """Escanea pacman para verificar el entorno y despliega el diálogo si falta algo"""
        # Pausamos el monitoreo para evitar conflictos de UI durante el check modal
        self.stats_timer.stop()
        
        missing_crit = [p for p in self.critical_deps if subprocess.run(["pacman", "-Qi", p], capture_output=True).returncode != 0]
        missing_recom = [p for p in self.recommended_deps if subprocess.run(["pacman", "-Qi", p], capture_output=True).returncode != 0]
        
        if missing_crit or missing_recom:
            self.yui.log("Integrity Scan: Gaps detected in local environment.", "#ff7f00")
            diag = DependencyDialog(missing_crit, missing_recom, self)
            if diag.exec():
                self.yui.log("Initiating Automated Deployment of dependencies...", "#00ccff")
                all_missing = missing_crit + missing_recom
                res = self.run_cmd(["pacman", "-S", "--noconfirm", "--needed"] + all_missing, True)
                if res and res.returncode == 0:
                    self.yui.log("Deployment Complete. All modules are online.", "#00ffcc")
                else:
                    self.yui.log("Deployment Failed. Check manual logs.", "#ff4444")
            else:
                self.yui.log("Warning: User ignored missing dependencies. System may be unstable.", "#ff7f00")
        else:
            self.yui.log("Integrity Scan: System is 100% compliant.", "#00ffcc")
            
        # Reanudamos el monitoreo una vez cerrado el diálogo
        self.stats_timer.start(2000)

    def init_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(35, 35, 35, 35)
        main_layout.setSpacing(20)

        # --- 1. ENCABEZADO (Métricas y Carpeta) ---
        header = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title = QLabel("SAO DIRECTORY v0.1 Beta/ SERVERS")
        title.setStyleSheet("font-size: 24px; font-weight: 900; letter-spacing: 5px;")

        self.btn_php_folder = QPushButton("⚙️ Config PHP")
        self.btn_php_folder.setObjectName("FolderBtn")
        self.btn_php_folder.clicked.connect(self.open_php_config)

        self.btn_localhost = QPushButton("🌐 Localhost Root")
        self.btn_localhost.setObjectName("FolderBtn")
        self.btn_localhost.clicked.connect(self.open_localhost)

        title_vbox.addWidget(title)
        title_vbox.addLayout(self._create_header_buttons())

        stats_grid = QGridLayout()
        self.bar_cpu = QProgressBar()
        self.bar_ram = QProgressBar()

        stats_grid.addWidget(QLabel("CPU HEALTH:"), 0, 0)
        stats_grid.addWidget(self.bar_cpu, 0, 1)
        stats_grid.addWidget(QLabel("RAM ENERGY:"), 1, 0)
        stats_grid.addWidget(self.bar_ram, 1, 1)

        header.addLayout(title_vbox, 55)
        header.addLayout(stats_grid, 45)
        main_layout.addLayout(header)

        # --- 2. SELECTORES DE INVENTARIO (PHP DINÁMICO) ---
        inv_frame = QFrame()
        inv_frame.setObjectName("GlassCard")
        inv_layout = QVBoxLayout(inv_frame)
        
        selectors_row = QHBoxLayout()
        self.php_sel = QComboBox()
        self.db_sel = QComboBox()
        self.db_sel.addItems(["MySQL 8.0", "PostgreSQL", "MariaDB"])
        
        selectors_row.addWidget(QLabel("PHP:"))
        selectors_row.addWidget(self.php_sel)
        selectors_row.addSpacing(20)
        selectors_row.addWidget(QLabel("DB:"))
        selectors_row.addWidget(self.db_sel)
        selectors_row.addStretch()

        project_row = QHBoxLayout()
        self.project_sel = QComboBox()
        self.btn_open_project = QPushButton("🚀 Open Project")
        self.btn_open_project.setObjectName("ProjectBtn")
        self.btn_open_project.clicked.connect(self.open_selected_project)
        
        project_row.addWidget(QLabel("PROJECT INDEX:"))
        project_row.addWidget(self.project_sel, 1)
        project_row.addWidget(self.btn_open_project)

        inv_layout.addLayout(selectors_row)
        inv_layout.addLayout(project_row)
        main_layout.addWidget(inv_frame)

        # --- 3. SERVICIOS Y ACCIONES GLOBALES ---
        mid_layout = QHBoxLayout()
        serv_vbox = QVBoxLayout()
        self.row_kirito = self.create_service_row("Kirito Unit (Apache)", "httpd")
        self.row_asuna = self.create_service_row("Asuna Unit (MariaDB)", "mysqld")
        
        global_btns = QHBoxLayout()
        self.btn_link_start = QPushButton("⚡ LINK START")
        self.btn_link_start.setObjectName("LinkStart")
        self.btn_link_start.setFixedHeight(50)
        self.btn_link_start.clicked.connect(self.link_start_init)
        
        self.btn_log_out = QPushButton("🛑 LOG OUT")
        self.btn_log_out.setObjectName("LogOut")
        self.btn_log_out.setFixedHeight(50)
        self.btn_log_out.clicked.connect(self.log_out_stop)
        
        global_btns.addWidget(self.btn_link_start)
        global_btns.addWidget(self.btn_log_out)

        serv_vbox.addWidget(self.row_kirito)
        serv_vbox.addWidget(self.row_asuna)
        serv_vbox.addLayout(global_btns)
        mid_layout.addLayout(serv_vbox, 65)

        tools_frame = QFrame()
        tools_frame.setObjectName("GlassCard")
        t_grid = QGridLayout(tools_frame)
        
        btn_fix = QPushButton("Fix Apache")
        btn_verify = QPushButton("Verify DB")
        btn_repair = QPushButton("Repair Panel")
        btn_sync = QPushButton("🔄 Sync")
        btn_perms = QPushButton("Fix Perms")
        
        btn_sync.clicked.connect(self.sync_repository)
        btn_repair.clicked.connect(self.repair_panel)
        btn_fix.clicked.connect(lambda: self.run_cmd(["systemctl", "reset-failed", "httpd"], True))
        btn_verify.clicked.connect(lambda: self.run_cmd(["mariadb-check", "--all-databases"], True))
        btn_perms.clicked.connect(self.fix_http_permissions)

        t_grid.addWidget(btn_fix, 0, 0)
        t_grid.addWidget(btn_verify, 0, 1)
        t_grid.addWidget(btn_repair, 1, 0)
        t_grid.addWidget(btn_sync, 1, 1)
        t_grid.addWidget(btn_perms, 2, 0, 1, 2)

        mid_layout.addWidget(tools_frame, 35)
        main_layout.addLayout(mid_layout)

        # --- 4. TERMINAL YUI ---
        main_layout.addWidget(self.yui)

    def _create_header_buttons(self):
        layout = QHBoxLayout()
        layout.addWidget(self.btn_php_folder)
        layout.addWidget(self.btn_localhost)
        return layout

    def detect_php_versions(self):
        """Escanea /etc/ en busca de directorios de PHP instalados (estándar en Arch)"""
        self.php_sel.clear()
        found_versions = []
        
        try:
            # Lista directorios que empiezan por 'php' en /etc/
            if os.path.exists("/etc/"):
                items = os.listdir("/etc/")
                # Filtrar directorios como 'php', 'php81', 'php74', etc.
                php_dirs = [d for d in items if d.startswith("php") and os.path.isdir(os.path.join("/etc", d))]
                
                for d in sorted(php_dirs, reverse=True):
                    # Formatear el nombre para que se vea bien (ej: php82 -> PHP 8.2)
                    version_label = d.replace("php", "").strip()
                    if not version_label:
                        found_versions.append("PHP (System Default)")
                    else:
                        # Si es formato '82', poner '.' en medio
                        if len(version_label) == 2:
                            version_label = f"{version_label[0]}.{version_label[1]}"
                        found_versions.append(f"PHP {version_label}")
        except Exception as e:
            self.yui.log(f"Detection Error: {e}", "#ff4444")

        if found_versions:
            self.php_sel.addItems(found_versions)
            self.yui.log(f"Detected {len(found_versions)} PHP versions in /etc/.")
        else:
            self.yui.log("Warning: No PHP configurations detected in /etc/php*.", "#ff4444")

    def refresh_projects(self):
        """Escanea /srv/http/ en busca de carpetas de proyectos"""
        self.project_sel.clear()
        path = "/srv/http/"
        if os.path.exists(path):
            try:
                projects = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                if projects:
                    self.project_sel.addItems(sorted(projects))
                    self.yui.log(f"Project Index updated: {len(projects)} found.")
                else:
                    self.project_sel.addItem("No projects detected")
            except Exception as e:
                self.yui.log(f"Scan Error: {e}", "#ff4444")
        else:
            self.project_sel.addItem("Localhost root missing")

    def create_service_row(self, label_text, service_name):
        f = QFrame(); f.setObjectName("GlassCard")
        l = QHBoxLayout(f)
        dot = QLabel(); dot.setFixedSize(12, 12)
        dot.setStyleSheet("background-color: #ff4444; border-radius: 6px;")
        self.service_status_dots[service_name] = dot
        
        l.addWidget(dot)
        l.addWidget(QLabel(label_text.upper()))
        l.addStretch()
        
        btn_start = QPushButton("START")
        btn_stop = QPushButton("STOP")
        
        btn_start.clicked.connect(lambda: self.manage_service(service_name, "start"))
        btn_stop.clicked.connect(lambda: self.manage_service(service_name, "stop"))
        
        l.addWidget(btn_start)
        l.addWidget(btn_stop)
        return f

    def manage_service(self, service, action):
        self.yui.log(f"Requesting {action.upper()} for {service}...", "#ff7f00")
        res = self.run_cmd(["systemctl", action, service], True)
        if res and res.returncode == 0:
            self.yui.log(f"Service {service} {action}ed successfully.", "#00ffcc")
        else:
            self.yui.log(f"Error managing {service}: {res.stderr if res else 'Unknown'}", "#ff4444")

    def poll_services_status(self):
        try:
            for srv, dot in self.service_status_dots.items():
                res = subprocess.run(["systemctl", "is-active", srv], capture_output=True, text=True)
                color = "#00ffcc" if res.stdout.strip() == "active" else "#ff4444"
                dot.setStyleSheet(f"background-color: {color}; border-radius: 6px; border: 1px solid white;")
        except Exception as e:
            print(f"Service Polling Error: {e}")

    def link_start_init(self):
        self.yui.log("LINK START: Initiating System Validation...", "#00ffcc")

        # 1. Verificar si falta algo antes de arrancar
        missing = [p for p in self.critical_deps if subprocess.run(["pacman", "-Qi", p], capture_output=True).returncode != 0]
        if missing:
            self.yui.log(f"Critical components missing ({', '.join(missing)}). Deploying now...", "#ff7f00")
            self.run_cmd(["pacman", "-S", "--noconfirm", "--needed"] + missing, True)

        # 2. MariaDB Init
        if not os.path.exists("/var/lib/mysql/mysql"):
            self.yui.log("Initializing MariaDB Data Directory...", "#ff7f00")
            self.run_cmd(["mariadb-install-db", "--user=mysql", "--basedir=/usr", "--datadir=/var/lib/mysql"], True)

        # 3. Start Services
        self.manage_service("httpd", "start")
        self.manage_service("mysqld", "start")
        
        # 4. Fix Permissions automatically
        self.fix_http_permissions()
        self.yui.log("LINK START COMPLETE. Welcome to Aincrad.", "#00ffcc")

    def log_out_stop(self):
        self.yui.log("LOG OUT: Terminating Units...", "#ff7f00")
        self.manage_service("httpd", "stop")
        self.manage_service("mysqld", "stop")

    def sync_repository(self):
        self.yui.log("SYNC: Checking for updates in Aincrad...", "#00ccff")
        
        # Verificar si es un repo git
        if self.run_cmd(["git", "rev-parse", "--is-inside-work-tree"]).returncode != 0:
            self.yui.log("Error: Current directory is not a Git repository.", "#ff4444")
            return

        # Asegurar URL SSH
        self.run_cmd(["git", "remote", "set-url", "origin", self.git_repo_url])
        
        # Fetch
        self.yui.log("Fetching remote data...", "#555")
        fetch = self.run_cmd(["git", "fetch"])
        
        if fetch and fetch.returncode == 0:
            local = self.run_cmd(["git", "rev-parse", "HEAD"]).stdout.strip()
            remote = self.run_cmd(["git", "rev-parse", "@{u}"]).stdout.strip()
            
            if local != remote:
                self.yui.log("NEW UPDATE DETECTED. Pulling changes...", "#ff7f00")
                pull = self.run_cmd(["git", "pull"])
                if pull.returncode == 0:
                    self.yui.log("System updated to latest version.", "#00ffcc")
                else:
                    self.yui.log(f"Pull failed: {pull.stderr}", "#ff4444")
            else:
                self.yui.log("System is already up to date.", "#00ffcc")
        else:
            self.yui.log("Sync failed. Check SSH keys and connection.", "#ff4444")

    def repair_panel(self):
        self.yui.log("REPAIR: Initiating integrity recovery...", "#ff7f00")
        
        if self.run_cmd(["git", "rev-parse", "--is-inside-work-tree"]).returncode != 0:
            self.yui.log("Fatal: Not a git repository. Repair aborted.", "#ff4444")
            return

        # Identificar versión actual
        version = self.run_cmd(["git", "describe", "--tags"]).stdout.strip()
        if not version:
            version = self.run_cmd(["git", "rev-parse", "HEAD"]).stdout.strip()

        self.yui.log(f"Restoring to version: {version}...", "#555")
        
        # Reset hard y clean
        res = self.run_cmd(["git", "reset", "--hard", version])
        if res.returncode == 0:
            self.run_cmd(["git", "clean", "-fd"])
            self.yui.log("REPAIR COMPLETE: Integrity restored.", "#00ffcc")
        else:
            self.yui.log("REPAIR FAILED: System manual intervention required.", "#ff4444")

    def open_php_config(self):
        """Abre la carpeta de configuración de la versión de PHP seleccionada"""
        selected = self.php_sel.currentText()
        if "Default" in selected or not selected:
            path = "/etc/php"
        else:
            # De "PHP 8.2" a "php82"
            ver = selected.replace("PHP ", "").replace(".", "")
            path = f"/etc/php{ver}"
        
        if not os.path.exists(path):
            path = "/etc/php"

        self.yui.log(f"Opening PHP Config: {path}", "#00ccff")
        subprocess.run(["xdg-open", path])

    def open_localhost(self):
        """Abre la raíz del localhost"""
        path = "/srv/http/"
        
        if not os.path.exists(path):
            self.yui.log(f"Localhost path {path} not found. Creating...", "#ff7f00")
            res = self.run_cmd(["mkdir", "-p", path], True)
            if not res or res.returncode != 0:
                self.yui.log("Failed to create directory.", "#ff4444")
                return
        
        self.fix_http_permissions()
        self.yui.log(f"Accessing Localhost: {path}", "#00ccff")
        subprocess.run(["xdg-open", path])

    def fix_http_permissions(self):
        """Otorga permisos al usuario actual y al grupo 'http' sobre la carpeta del servidor"""
        self.yui.log("Granting permissions for /srv/http/...", "#ff7f00")
        path = "/srv/http/"
        user = getpass.getuser()
        
        # chown -R user:http /srv/http
        res1 = self.run_cmd(["chown", "-R", f"{user}:http", path], True)
        # chmod -R 775 /srv/http (Lectura/Escritura para dueño y grupo)
        res2 = self.run_cmd(["chmod", "-R", "775", path], True)
        
        if res1 and res1.returncode == 0 and res2 and res2.returncode == 0:
            self.yui.log("PERMISSIONS FIXED: Folder is now writeable by you.", "#00ffcc")
        else:
            self.yui.log("Error granting permissions. Check Sudo.", "#ff4444")

    def open_selected_project(self):
        """Abre la carpeta del proyecto seleccionado en el combo box"""
        project = self.project_sel.currentText()
        if project and " " not in project: # Evitar mensajes de error o vacíos
            path = os.path.join("/srv/http/", project)
            if os.path.exists(path):
                self.yui.log(f"Opening Project: {project}", "#00ffcc")
                subprocess.run(["xdg-open", path])
            else:
                self.yui.log(f"Error: Project folder {project} not found.", "#ff4444")
        else:
            self.yui.log("Please select a valid project from the index.", "#ff7f00")

    def refresh_real_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.bar_cpu.setValue(int(cpu))
            self.bar_cpu.setFormat(f"CPU HEALTH: {cpu}%")
            self.bar_ram.setValue(int(ram))
            self.bar_ram.setFormat(f"RAM ENERGY: {ram}%")
            
            color_cpu = "#ff4444" if cpu > 80 else "#00ffcc"
            color_ram = "#ff4444" if ram > 85 else "#00ccff"
            self.bar_cpu.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color_cpu}; }}")
            self.bar_ram.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color_ram}; }}")
        except Exception as e:
            print(f"Stats Refresh Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Inter", 10))
    kirito_ui = Kirito()
    kirito_ui.show()
    sys.exit(app.exec())