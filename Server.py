#!/usr/bin/env python3
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
        try:
            # Instalación automática usando pacman
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "--needed"] + missing_packages, check=True)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            try:
                from PyQt6.QtWidgets import QApplication, QMessageBox
                temp_app = QApplication.instance() or QApplication(sys.argv)
                QMessageBox.critical(None, "SAO - Neural Link Error", 
                                     f"Critical Sync Failed: {e}\n\nAsegúrate de tener conexión a internet y privilegios de sudo.")
            except ImportError:
                pass
            sys.exit(1)

ensure_dependencies()

import psutil
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, QMenu,
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

QMenu {
    background-color: rgba(15, 15, 22, 0.98);
    border: 1px solid #00ffcc;
    color: white;
}
QMenu::item { padding: 8px 25px; background: transparent; }
QMenu::item:selected {
    background-color: rgba(0, 255, 204, 0.2);
    color: #00ffcc;
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

class MissingDepsDialog(QDialog):
    def __init__(self, missing_crit, missing_recom, parent=None):
        super().__init__(parent)
        self.setObjectName("DependencyDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("SISTEMA DE INTEGRIDAD: ESCANEO")
        title.setStyleSheet("font-size: 16px; color: #00ffcc; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        if missing_crit:
            layout.addSpacing(10)
            layout.addWidget(QLabel("ESTADO CRÍTICO (Faltan módulos base):", objectName="CriticalLabel"))
            for pkg in missing_crit:
                layout.addWidget(QLabel(f" • {pkg}"))
        
        if missing_recom:
            layout.addSpacing(15)
            layout.addWidget(QLabel("OPTIMIZACIÓN RECOMENDADA:", objectName="RecommendedLabel"))
            for pkg in missing_recom:
                layout.addWidget(QLabel(f" • {pkg}"))
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_ignore = QPushButton("IGNORAR")
        self.btn_install = QPushButton("INSTALAR AUTOMÁTICAMENTE")
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

class CloseSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DependencyDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("LOGOUT PROTOCOL")
        title.setStyleSheet("font-size: 18px; color: #ff7f00; font-weight: bold; letter-spacing: 3px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("Seleccione el método de desconexión del enlace neuronal:")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        layout.addStretch()
        
        self.btn_stop_exit = QPushButton("DETENER Y SALIR")
        self.btn_stop_exit.setObjectName("LogOut")
        self.btn_exit = QPushButton("SOLO SALIR")
        self.btn_cancel = QPushButton("CANCELAR")
        
        self.btn_stop_exit.clicked.connect(lambda: self.done(1))
        self.btn_exit.clicked.connect(lambda: self.done(2))
        self.btn_cancel.clicked.connect(lambda: self.done(0))
        
        layout.addWidget(self.btn_stop_exit)
        layout.addWidget(self.btn_exit)
        layout.addWidget(self.btn_cancel)

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
        self.setFixedSize(1100, 800)
        
        # Centrar la ventana en la pantalla disponible
        qr = self.frameGeometry()
        qr.moveCenter(QtGui.QGuiApplication.primaryScreen().availableGeometry().center())
        self.move(qr.topLeft())

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.sudo_password = None
        self.service_status_dots = {}
        self.git_repo_url = "git@github.com:Slashdog29/SAO-Server.git"
        
        # Credenciales internas para pruebas de conexión
        self.db_user = "root"
        self.db_pass = ""

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
        
        # Iniciar verificación de entorno tras carga
        QTimer.singleShot(1000, self.check_environment_dependencies)

    def request_sudo_password(self):
        """Muestra el diálogo SAO para obtener privilegios de administrador"""
        dialog = SudoDialog(self)
        if dialog.exec():
            password = dialog.textValue()
            # Validar con un comando rápido
            check = subprocess.run(["sudo", "-S", "true"], input=f"{password}\n", text=True, capture_output=True)
            if check.returncode == 0:
                self.sudo_password = password
                self.yui.log("Enlace Administrativo: AUTORIZADO", "#00ffcc")
                return True
        self.yui.log("Error de Autenticación: Acceso Denegado", "#ff4444")
        return False

    def run_as_sudo(self, command_list, capture=True):
        """Ejecuta comandos usando la contraseña guardada mediante sudo -S"""
        if not self.sudo_password and not self.request_sudo_password():
            return None
        
        return subprocess.run(
            ["sudo", "-S"] + command_list,
            input=f"{self.sudo_password}\n",
            capture_output=capture,
            text=True
        )

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def get_sudo_auth(self):
        return self.request_sudo_password() if not self.sudo_password else True

    def run_cmd(self, args, use_sudo=False, capture=True):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        if use_sudo:
            return self.run_as_sudo(args, capture)

        try:
            result = subprocess.run(
                args, 
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
                # Agregamos -Sy para asegurar que las bases de datos de paquetes estén frescas
                res = self.run_cmd(["pacman", "-Sy", "--noconfirm", "--needed"] + all_missing, True)
                if res and res.returncode == 0:
                    self.yui.log("Deployment Complete. All modules are online.", "#00ffcc")
                else:
                    error_msg = res.stderr if res else "Unknown Error (Check Sudo/Internet)"
                    self.yui.log(f"Deployment Failed: {error_msg}", "#ff4444")
            else:
                self.yui.log("Warning: User ignored missing dependencies. System may be unstable.", "#ff7f00")
        else:
            self.yui.log("Integrity Scan: System is 100% compliant.", "#00ffcc")
            
        # Reanudamos el monitoreo una vez cerrado el diálogo
        self.stats_timer.start(2000)

    def check_environment_dependencies(self):
        """Verifica dependencias del sistema y ofrece instalación automática"""
        self.yui.log("Escaneando integridad del entorno local...", "#555")
        
        missing_crit = [p for p in self.critical_deps if subprocess.run(["pacman", "-Qi", p], capture_output=True).returncode != 0]
        missing_recom = [p for p in self.recommended_deps if subprocess.run(["pacman", "-Qi", p], capture_output=True).returncode != 0]

        if missing_crit or missing_recom:
            diag = MissingDepsDialog(missing_crit, missing_recom, self)
            if diag.exec():
                self.yui.log("Iniciando despliegue de dependencias...", "#00ccff")
                all_missing = missing_crit + missing_recom
                res = self.run_as_sudo(["pacman", "-S", "--noconfirm", "--needed"] + all_missing)
                
                if res.returncode == 0:
                    self.yui.log("Sincronización de dependencias completa.", "#00ffcc")
                else:
                    self.yui.log(f"Fallo en el despliegue: {res.stderr}", "#ff4444")

    def init_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(35, 35, 35, 35)
        main_layout.setSpacing(25)

        # --- 1. ENCABEZADO (Métricas y Carpeta) ---
        header = QHBoxLayout()
        title_vbox = QVBoxLayout()
        
        # Título y Botones de Sistema (⋮ y X)
        title_row = QHBoxLayout()
        title = QLabel("SAO DIRECTORY v0.3 / SERVERS")
        title.setStyleSheet("font-size: 22px; font-weight: 900; letter-spacing: 4px; color: #00ffcc;")
        
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(35, 35)
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.clicked.connect(self.show_options_menu)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(35, 35)
        self.btn_close.setObjectName("LogOut")
        self.btn_close.clicked.connect(self.close)

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.btn_menu)
        title_row.addWidget(self.btn_close)

        # Accesos directos rápidos
        nav_row = QHBoxLayout()
        self.btn_php_folder = QPushButton("⚙️ CONFIG PHP"); self.btn_php_folder.setObjectName("FolderBtn")
        self.btn_localhost = QPushButton("🌐 LOCALHOST ROOT"); self.btn_localhost.setObjectName("FolderBtn")
        self.btn_php_folder.clicked.connect(self.open_php_config)
        self.btn_localhost.clicked.connect(self.open_localhost)
        
        nav_row.addWidget(self.btn_php_folder)
        nav_row.addWidget(self.btn_localhost)
        nav_row.addStretch()

        title_vbox.addLayout(title_row)
        title_vbox.addLayout(nav_row)

        stats_grid = QGridLayout()
        self.bar_cpu = QProgressBar()
        self.bar_ram = QProgressBar()
        stats_grid.addWidget(QLabel("CPU:"), 0, 0); stats_grid.addWidget(self.bar_cpu, 0, 1)
        stats_grid.addWidget(QLabel("RAM:"), 1, 0); stats_grid.addWidget(self.bar_ram, 1, 1)

        header.addLayout(title_vbox, 55)
        header.addLayout(stats_grid, 45)
        main_layout.addLayout(header)

        # --- 2. SELECTORES DE ENTORNO ---
        inv_frame = QFrame()
        inv_frame.setObjectName("GlassCard")
        inv_layout = QVBoxLayout(inv_frame)
        
        self.php_sel = QComboBox()
        self.project_sel = QComboBox()
        self.btn_open_project = QPushButton("🚀 OPEN PROJECT"); self.btn_open_project.setObjectName("ProjectBtn")
        self.btn_open_project.clicked.connect(self.open_selected_project)
        
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("PHP UNIT:")); sel_row.addWidget(self.php_sel, 1)
        sel_row.addWidget(QLabel("PROJECT:")); sel_row.addWidget(self.project_sel, 2)
        sel_row.addWidget(self.btn_open_project)
        inv_layout.addLayout(sel_row)
        main_layout.addWidget(inv_frame)

        # --- 3. SERVICES & SYSTEM TOOLS ---
        mid_layout = QHBoxLayout()
        
        # Panel de Servicios
        serv_panel = QVBoxLayout()
        serv_panel.addWidget(self.create_service_row("Apache Server", "httpd"))
        serv_panel.addWidget(self.create_service_row("MariaDB Engine", "mysqld"))
        
        btn_row = QHBoxLayout()
        self.btn_link_start = QPushButton("⚡ LINK START"); self.btn_link_start.setObjectName("LinkStart")
        self.btn_log_out = QPushButton("🛑 LOG OUT"); self.btn_log_out.setObjectName("LogOut")
        self.btn_link_start.setFixedHeight(45); self.btn_log_out.setFixedHeight(45)
        self.btn_link_start.clicked.connect(self.link_start_init)
        self.btn_log_out.clicked.connect(self.log_out_stop)
        
        btn_row.addWidget(self.btn_link_start)
        btn_row.addWidget(self.btn_log_out)
        serv_panel.addLayout(btn_row)
        mid_layout.addLayout(serv_panel, 60)

        # Panel de Herramientas (Grid)
        tools_frame = QFrame()
        tools_frame.setObjectName("GlassCard")
        t_grid = QGridLayout(tools_frame)
        t_grid.setSpacing(10)
        
        label_tools = QLabel("SYSTEM MAINTENANCE"); label_tools.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_tools.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        t_grid.addWidget(label_tools, 0, 0, 1, 2)

        # Implementación de botones solicitados
        tools = [
            ("Fix Apache", lambda: self.run_cmd(["systemctl", "reset-failed", "httpd"], True)),
            ("Verify DB", lambda: self.run_cmd(["mariadb-check", "--all-databases"], True)),
            ("Fix Perms", self.fix_http_permissions),
            ("Sync", self.sync_repository),
            ("Repair Panel", self.repair_panel)
        ]

        for i, (name, func) in enumerate(tools):
            btn = QPushButton(name)
            btn.setFixedSize(120, 35)
            btn.clicked.connect(func)
            t_grid.addWidget(btn, (i // 2) + 1, i % 2)

        mid_layout.addWidget(tools_frame, 40)
        main_layout.addLayout(mid_layout)

        main_layout.addWidget(self.yui)
        
    def manage_service(self, service, action, ask_sudo=True):
        """Versión mejorada: Permite ejecución silenciosa en LOG OUT"""
        self.yui.log(f"Requesting {action.upper()} for {service}...", "#ff7f00")
        if ask_sudo:
            res = self.run_cmd(["systemctl", action, service], True)
        else:
            # Intento silencioso para el cierre de app
            if self.sudo_password:
                res = subprocess.run(["sudo", "-S", "systemctl", action, service], 
                                     input=f"{self.sudo_password}\n", text=True, capture_output=True)
            else:
                res = subprocess.run(["sudo", "-n", "systemctl", action, service], capture_output=True)
        
        if res and res.returncode == 0:
            self.yui.log(f"Service {service} updated.", "#00ffcc")

    def log_out_stop(self):
        """Detiene servicios sin pedir clave si no está guardada"""
        self.yui.log("LOG OUT: Terminating Units (Silent Mode)...", "#ff7f00")
        self.manage_service("httpd", "stop", ask_sudo=False)
        self.manage_service("mysqld", "stop", ask_sudo=False)

    def detect_php_versions(self):
        """Escanea /etc/ en busca de directorios de PHP instalados (estándar en Arch)"""
        self.php_sel.clear()
        found_versions = []

        # 1. Detectar versión binaria activa (CLI)
        try:
            res = subprocess.run(["php", "-v"], capture_output=True, text=True)
            if res.returncode == 0:
                version_line = res.stdout.splitlines()[0]
                self.yui.log(f"Active Binary detected: {version_line}", "#00ffcc")
        except FileNotFoundError:
            self.yui.log("System PHP binary NOT found in PATH.", "#ff4444")
        
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

    def fix_php_extensions(self):
        """Habilita automáticamente extensiones críticas en php.ini"""
        self.yui.log("Fixing PHP Extensions: Enabling mysqli, pdo_mysql & mbstring...", "#ff7f00")
        php_ini = "/etc/php/php.ini"
        
        if os.path.exists(php_ini):
            # Descomenta las extensiones y asegura que el directorio de extensiones sea correcto
            cmd = ["sed", "-i", "-E", r"s/^\s*;\s*extension\s*=\s*(mysqli|pdo_mysql|mbstring)/extension=\1/g", php_ini]
            res = self.run_cmd(cmd, True)
            
            if res and res.returncode == 0:
                self.yui.log("PHP configuration updated. Restarting all units...", "#00ffcc")
                self.manage_service("httpd", "restart")
                self.manage_service("php-fpm", "restart")
                
                # Verificación de carga en CLI
                check = subprocess.run(["php", "-m"], capture_output=True, text=True)
                if "mysqli" in check.stdout:
                    self.yui.log("Verification: 'mysqli' module is now ACTIVE in CLI.", "#00ffcc")
                else:
                    self.yui.log("Critical: Extension enabled in .ini but not detected. Manual check required.", "#ff4444")
            else:
                error = res.stderr if res else "Sudo required"
                self.yui.log(f"Failed to modify php.ini: {error}", "#ff4444")
        else:
            self.yui.log("Critical: /etc/php/php.ini not found.", "#ff4444")

    def test_db_connection(self):
        """Verifica si MariaDB acepta las credenciales actuales"""
        self.yui.log(f"Testing connection for user: {self.db_user}...", "#ff7f00")
        cmd = ["mysqladmin", "-u", self.db_user]
        if self.db_pass:
            cmd.append(f"-p{self.db_pass}")
        cmd.append("ping")
        
        # No usamos run_cmd con sudo aquí porque queremos probar el acceso normal
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            self.yui.log("DATABASE CONNECTION: SUCCESSFUL", "#00ffcc")
        else:
            self.yui.log(f"DATABASE CONNECTION: FAILED. {res.stderr.strip()}", "#ff4444")
            self.yui.log("Tip: Check if the password matches or use 'DB Password' to reset it.", "#555")

    def manage_db_user(self):
        """Consulta y permite cambiar el nombre de usuario de la DB en el panel"""
        new_user, ok = QInputDialog.getText(self, "DB USER MANAGEMENT", 
                                          f"Current Managed User: {self.db_user}\nEnter new username:",
                                          QLineEdit.EchoMode.Normal, self.db_user)
        if ok and new_user:
            self.db_user = new_user
            self.yui.log(f"Panel will now use DB user: {self.db_user}", "#00ccff")

    def change_db_password(self):
        """Cambia la contraseña del usuario en MariaDB usando privilegios administrativos"""
        new_pass, ok = QInputDialog.getText(self, "DB SECURITY", 
                                          f"Set new password for {self.db_user}:",
                                          QLineEdit.EchoMode.Password)
        if ok:
            self.yui.log(f"Deploying new credentials for {self.db_user}...", "#ff7f00")
            
            # Comando SQL para cambiar la clave. Usamos ALTER USER que es el estándar moderno.
            sql = f"ALTER USER '{self.db_user}'@'localhost' IDENTIFIED BY '{new_pass}'; FLUSH PRIVILEGES;"
            
            # Ejecutamos vía sudo para saltarnos restricciones de permisos iniciales
            res = self.run_cmd(["mariadb", "-e", sql], True)
            
            if res and res.returncode == 0:
                self.db_pass = new_pass
                self.yui.log(f"DB PASSWORD UPDATED SUCCESSFULLY for {self.db_user}.", "#00ffcc")
                self.yui.log("Synchronizing panel credentials...", "#555")
                
                # Actualizar también los archivos PHP si es posible (Opcional, loggeamos el aviso)
                self.yui.log("HINT: Remember to update 'conexion.php' with the new password.", "#ffcc00")
            else:
                error_msg = res.stderr if res else "Unknown Error"
                self.yui.log(f"Failed to update DB password: {error_msg}", "#ff4444")

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

    def add_to_system_menu(self):
        """Crea un archivo .desktop para integrar el panel en el menú de aplicaciones de Linux"""
        try:
            script_path = os.path.abspath(__file__)
            desktop_dir = os.path.expanduser("~/.local/share/applications/")
            
            # Asegurar que el directorio existe
            os.makedirs(desktop_dir, exist_ok=True)
            
            file_path = os.path.join(desktop_dir, "sao-server.desktop")
            
            content = f"""[Desktop Entry]
Name=SAO Server Panel
Exec=python3 {script_path}
Icon=utilities-terminal
Type=Application
Categories=Development;System;
Terminal=false
"""
            with open(file_path, "w") as f:
                f.write(content)
            
            # Otorgar permisos de ejecución al archivo .desktop
            os.chmod(file_path, 0o755)
            
            self.yui.log("Acceso directo creado en el menú", "#00ffcc")
        except Exception as e:
            self.yui.log(f"Error al crear acceso directo: {e}", "#ff4444")

    def show_options_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(SAO_GLASS_QSS)
        
        root_act = menu.addAction("📂 Carpeta Raíz")
        app_menu_act = menu.addAction("🖥️ Añadir al Menú de Aplicaciones")
        php_act = menu.addAction("⚙️ Configuración PHP")
        clear_act = menu.addAction("🧹 Limpiar Logs")
        menu.addSeparator()
        about_act = menu.addAction("ℹ️ Acerca de")
        
        action = menu.exec(self.btn_menu.mapToGlobal(QtCore.QPoint(0, self.btn_menu.height())))
        
        if action == root_act: self.open_localhost()
        elif action == app_menu_act: self.add_to_system_menu()
        elif action == php_act: self.open_php_config()
        elif action == clear_act: self.yui.terminal.clear()
        elif action == about_act:
            self.yui.log("SAO ForgeStack Panel v0.2 - Admin Interface", "#00ffcc")
            self.yui.log("Desarrollado para la reconstrucción de Aincrad.", "#555")

    def closeEvent(self, event):
        diag = CloseSelectionDialog(self)
        result = diag.exec()
        
        if result == 1: # Detener y Salir
            self.log_out_stop()
            event.accept()
        elif result == 2: # Solo Salir
            event.accept()
        else: # Cancelar
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Inter", 10))
    kirito_ui = Kirito()
    kirito_ui.show()
    sys.exit(app.exec())
