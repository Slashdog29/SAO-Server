#!/usr/bin/env python3
import sys
import subprocess
import os
import shutil
import time
import threading
import gc
import glob
import re
import json
import base64
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
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, QMenu,
                             QProgressBar, QTextEdit, QFrame, QGridLayout, 
                             QInputDialog, QLineEdit, QDialog)
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl
from PyQt6.QtGui import QFont, QColor

# Tasks refactor
from sao_tasks import update_task, repair_task, auth_task, version_info

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
QPushButton:hover { 
    background-color: rgba(255, 255, 255, 0.15); 
    border: 1px solid rgba(0, 255, 204, 0.5);
    color: #00ffcc;
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.05);
    padding-top: 11px;
    padding-bottom: 9px;
}

QPushButton#LinkStart {
    border: 2px solid #00ffcc;
    color: #00ffcc;
    background-color: rgba(0, 255, 204, 0.05);
}
QPushButton#LinkStart:hover { 
    background-color: #00ffcc; 
    color: #000;
    border: 2px solid #ffffff;
}
QPushButton#LinkStart:pressed { background-color: #008877; padding-top: 13px; padding-bottom: 7px; }

QPushButton#LogOut {
    border: 2px solid #ff7f00;
    color: #ff7f00;
    background-color: rgba(255, 127, 0, 0.05);
}
QPushButton#LogOut:hover { 
    background-color: #ff7f00; 
    color: #000;
    border: 2px solid #ffffff;
}
QPushButton#LogOut:pressed { background-color: #aa5500; padding-top: 13px; padding-bottom: 7px; }

QPushButton#FolderBtn {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px dashed #ff7f00;
    color: #ff7f00;
}
QPushButton#FolderBtn:hover {
    background-color: rgba(255, 127, 0, 0.2);
    border: 1px solid #ff7f00;
    color: #ffffff;
}
QPushButton#FolderBtn:pressed {
    background-color: rgba(255, 127, 0, 0.1);
    padding-top: 12px;
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
QPushButton#ActionBtn:hover {
    background: rgba(0, 255, 204, 0.3);
}
QPushButton#ActionBtn:pressed {
    padding-top: 5px;
    background: rgba(0, 255, 204, 0.05);
}

QPushButton#ProjectBtn {
    background-color: rgba(0, 255, 204, 0.1);
    border: 1px solid #00ffcc;
    color: #00ffcc;
}
QPushButton#ProjectBtn:hover {
    background-color: rgba(0, 255, 204, 0.2);
    color: #ffffff;
}
QPushButton#ProjectBtn:pressed {
    padding-top: 12px;
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

TRANSLATIONS = {
    "EN": {
        "title": "SAO FORGE DIRECTORY - ARCH ADMIN",
        "header_title": "SAO DIRECTORY / SERVERS",
        "php_unit": "PHP UNIT:",
        "project": "PROJECT:",
        "maintenance": "SYSTEM MAINTENANCE",
        "open_proj": "🚀 OPEN PROJECT",
        "link_start": "⚡ LINK START",
        "log_out": "🛑 LOG OUT",
        "yui_btn": "📄 ACTIVAR MONITOR DE LOGS (YUI TERMINAL)",
        "lang_menu": "🇺🇸 Change Language",
        "opt_root": "📂 Root Folder",
        "opt_add": "🖥️ Add to Menu",
        "opt_rm": "❌ Remove from Menu",
        "opt_php": "⚙️ PHP Config",
        "opt_clear": "🧹 Clear Logs",
        "opt_update_panel": "🔼 Update Panel",
        "opt_save_token": "🔐 Save Git Token",
        "opt_repair_panel": "🛠️ Repair Panel",
        "opt_about": "ℹ️ About",
        "opt_hide": "👻 Hide Panel",
        "opt_sync": "🔄 Sync Web Folder",
        "tools": ["Repair Apache", "Optimize RAM", "🐘 Change PHP", "📧 Mailpit", "🧹 Clear Logs", "⚙️ Config Root", "Hide Yui"],
        "tray_toggle": "Show/Hide Panel",
        "tray_start": "🚀 Link Start (Services)",
        "tray_stop": "💤 Log Out (Stop All)",
        "tray_open": "📂 Open Projects Root",
        "tray_exit": "❌ Exit SAO Server",
    },
    "ES": {
        "title": "DIRECTORIO SAO FORGE - ADMIN ARCH",
        "header_title": "DIRECTORIO SAO / SERVIDORES",
        "php_unit": "UNIDAD PHP:",
        "project": "PROYECTO:",
        "maintenance": "MANTENIMIENTO DEL SISTEMA",
        "open_proj": "🚀 ABRIR PROYECTO",
        "link_start": "⚡ LINK START",
        "log_out": "🛑 LOG OUT",
        "yui_btn": "📄 ACTIVAR MONITOR DE LOGS (TERMINAL YUI)",
        "lang_menu": "🇪🇸 Cambiar Idioma",
        "opt_root": "📂 Carpeta Raíz",
        "opt_add": "🖥️ Añadir al Menú",
        "opt_rm": "❌ Quitar del Menú",
        "opt_php": "⚙️ Configuración PHP",
        "opt_clear": "🧹 Limpiar Logs",
        "opt_update_panel": "🔼 Actualizar Panel",
        "opt_save_token": "🔐 Guardar Token Git",
        "opt_repair_panel": "🛠️ Reparar Panel",
        "opt_about": "ℹ️ Acerca de",
        "opt_hide": "👻 Ocultar Panel",
        "opt_sync": "🔄 Sincronizar Carpeta Web",
        "tools": ["Reparar Apache", "Optimizar RAM", "🐘 Cambiar PHP", "📧 Mailpit", "🧹 Vaciar Logs", "⚙️ Config Raíz", "Hide Yui"],
        "tray_toggle": "Mostrar/Ocultar Panel",
        "tray_start": "🚀 Link Start (Servicios)",
        "tray_stop": "💤 Log Out (Detener Todo)",
        "tray_open": "📂 Abrir Raíz Proyectos",
        "tray_exit": "❌ Salir de SAO Server",
    }
}

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
        self.btn_ignore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        
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
        self.btn_ignore.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_layout.addWidget(self.btn_ignore)
        btn_layout.addWidget(self.btn_install)
        layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

class SudoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DependencyDialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 220)
        self.parent_sao = parent
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Imagen lateral (sao.png)
        self.img_label = QLabel()
        path_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sao.png")
        if os.path.exists(path_img):
            pixmap = QtGui.QPixmap(path_img).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
        layout.addWidget(self.img_label)

        # Contenedor derecho para el input y botones
        right_layout = QVBoxLayout()
        
        title = QLabel("AUTHENTICATION REQUIRED")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff7f00; letter-spacing: 2px;")
        right_layout.addWidget(title)
        
        label_text = QLabel("Enter Neural Link Admin Password (SUDO):")
        label_text.setStyleSheet("font-size: 11px; color: #ffffff;")
        right_layout.addWidget(label_text)

        # Campo de contraseña con botón de visibilidad
        pass_container = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("background-color: #000; color: #ff7f00; border: 1px solid #ff7f00; padding: 8px; border-radius: 4px;")
        self.password_input.setPlaceholderText("Password...")
        
        self.btn_toggle = QPushButton("👁")
        self.btn_toggle.setFixedSize(35, 33)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet("background: rgba(255,127,0,0.1); border: 1px solid #ff7f00; color: #ff7f00; font-size: 16px;")
        self.btn_toggle.clicked.connect(self.toggle_password_visibility)
        
        pass_container.addWidget(self.password_input)
        pass_container.addWidget(self.btn_toggle)
        right_layout.addLayout(pass_container)

        # Botones de acción (Cancel / Authorize)
        btns = QHBoxLayout()
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_ok = QPushButton("AUTHORIZE")
        self.btn_ok.setObjectName("ActionBtn")
        self.btn_ok.setStyleSheet("border: 1px solid #ff7f00; color: #ff7f00; background: rgba(255,127,0,0.05);")
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Agregar interactividad sonora
        self.btn_ok.installEventFilter(self)
        self.btn_cancel.installEventFilter(self)
        self.btn_ok.clicked.connect(self._play_click)
        self.btn_cancel.clicked.connect(self._play_click)
        
        self.password_input.returnPressed.connect(self.accept)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        right_layout.addLayout(btns)
        
        layout.addLayout(right_layout)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            if self.parent_sao and hasattr(self.parent_sao, 'snd_hover') and self.parent_sao.snd_hover:
                self.parent_sao.snd_hover.stop()
                self.parent_sao.snd_hover.play()
        return super().eventFilter(obj, event)

    def _play_click(self):
        if self.parent_sao and hasattr(self.parent_sao, 'snd_click') and self.parent_sao.snd_click:
            self.parent_sao.snd_click.stop()
            self.parent_sao.snd_click.play()

    def toggle_password_visibility(self):
        if self.btn_toggle.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle.setText("👁")

    def textValue(self):
        return self.password_input.text()

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
        self.btn_exit = QPushButton("SALIR")
        self.btn_cancel = QPushButton("CANCELAR")
        
        self.btn_stop_exit.clicked.connect(lambda: self.done(1))
        self.btn_exit.clicked.connect(lambda: self.done(2))
        self.btn_cancel.clicked.connect(lambda: self.done(0))
        self.btn_stop_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.btn_stop_exit)
        layout.addWidget(self.btn_exit)
        layout.addWidget(self.btn_cancel)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

from sao_tasks.about_dialog import AboutDialog

class Kirito(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAO FORGE DIRECTORY - ARCH ADMIN")
        self.setFixedSize(1100, 800)
        self.favoritos = [] # Inicialización inmediata para evitar errores de atributo
        self.idioma = "ES"
        
        # Centrar la ventana en la pantalla disponible
        qr = self.frameGeometry()
        qr.moveCenter(QtGui.QGuiApplication.primaryScreen().availableGeometry().center())
        self.move(qr.topLeft())

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.sudo_password = None
        # En Arch Linux el default es /srv/http, en el resto /var/www/html.
        self.dir_proyectos = "/srv/http" if os.path.exists("/etc/arch-release") else "/var/www/html"
        self.version_php_actual = "..."
        self.service_status_dots = {}
        self.git_repo_url = "git@github.com:Slashdog29/SAO-Server.git"
        self.ruta_config = os.path.expanduser("~/.sao-server-config.json")
        
        # Credenciales internas para pruebas de conexión
        self.db_user = "root"
        self.db_pass = ""

        self.critical_deps = ["php", "apache", "mariadb", "php-apache", "php-gd"]
        self.recommended_deps = ["vte3"]

        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        self.pixmap_cache = {}
        
        self.yui = YuiMonitor()
        self.cargar_ajustes_sao()
        self.init_ui()
        
        self.setStyleSheet(SAO_GLASS_QSS)
        self.yui.log("Neural Link Established. System Metrics: Online.", "#00ffcc")
        
        # Configuración de Audio y reproducción inicial
        self.setup_audio()
        if hasattr(self, 'snd_entrada') and self.snd_entrada:
            self.snd_entrada.play()
            
        self.setup_tray_icon()
        self.update_ui_texts()
            
        # Configurar Terminal Context Menu (Adaptación)
        self.yui.terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.yui.terminal.customContextMenuRequested.connect(self.show_yui_context_menu)
        
        # Iniciar lógica operativa del panel (Adaptado de GTK)
        QtCore.QTimer.singleShot(100, self._iniciar_logica_panel)

    def update_ui_texts(self):
        """Actualiza todos los textos de la interfaz según el idioma seleccionado"""
        t = TRANSLATIONS[self.idioma]
        self.setWindowTitle(t["title"])
        # Mostrar título base y añadir versión dinámica (controlada por user via VERSION or tag)
        header = t["header_title"]
        try:
            vi = version_info.get_panel_info()
            ver = vi.get("version") or vi.get("commit")
            if ver:
                header = f"{header} — {ver}"
        except Exception:
            pass
        self.title_lbl.setText(header)
        self.lbl_php_unit.setText(t["php_unit"])
        self.lbl_project.setText(t["project"])
        self.btn_open_project.setText(t["open_proj"])
        self.btn_link_start.setText(t["link_start"])
        self.btn_log_out.setText(t["log_out"])
        self.label_tools.setText(t["maintenance"])
        self.btn_show_yui.setText(t["yui_btn"])
        for btn, name in zip(self.tool_btns, t["tools"]):
            btn.setText(name)

        # Actualizar Menú de la Bandeja
        if hasattr(self, 'tray_menu'):
            self.tray_menu.clear()
            
            toggle_act = self.tray_menu.addAction(t["tray_toggle"])
            toggle_act.triggered.connect(self.toggle_visibility)
            
            self.tray_menu.addSeparator()
            
            start_act = self.tray_menu.addAction(t["tray_start"])
            start_act.triggered.connect(self.link_start_init)
            
            stop_act = self.tray_menu.addAction(t["tray_stop"])
            stop_act.triggered.connect(self.log_out_stop)
            
            open_act = self.tray_menu.addAction(t["tray_open"])
            open_act.triggered.connect(self.open_localhost)
            
            self.tray_menu.addSeparator()
            
            exit_act = self.tray_menu.addAction(t["tray_exit"])
            exit_act.triggered.connect(self.close)

    def toggle_language(self):
        self.idioma = "EN" if self.idioma == "ES" else "ES"
        self.update_ui_texts()
        self.guardar_ajustes_sao()
        self.yui.log(f"System: Language toggled to {self.idioma}", "#FFD700")

    def setup_tray_icon(self):
        """Configura el icono de la bandeja del sistema (Adaptación mejorada de GTK)."""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("XDG_SESSION_TYPE", "").lower()

        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self.yui.log("Tray Alert: Neural Link Tray is OFFLINE.", "#ff4444")
            
            if "gnome" in desktop:
                self.yui.log("GNOME FIX: sudo pacman -S gnome-shell-extension-appindicator", "#00ccff")
            elif "hyprland" in desktop or session == "wayland":
                self.yui.log("Hyprland/Wayland DETECTED: Tray requires 'libdbusmenu-qt6'.", "#00ccff")
                self.yui.log("Command: sudo pacman -S libdbusmenu-qt6 qt6-wayland", "#00ccff")
                self.yui.log("Tip: Ensure 'tray' is active in Waybar and a SNI daemon is running.", "#555")
            elif "kde" in desktop:
                self.yui.log("KDE Plasma: Tray is native. Check 'Status Notifier' settings.", "#00ccff")

            self.yui.log("System Tray Icon: Attempting forced Link Start...", "#00ffcc")
            self.yui.log("Security Note: Running as 'sudo' blocks Tray detection.", "#ff7f00")
            # En Wayland/Hyprland forzamos el intento de inicialización (Best Effort)
            if session != "wayland": return

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        
        # Usar sao.png como icono de bandeja
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sao.png")
        if os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
            self.tray_icon.setIcon(icon)
        else:
            icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
            self.tray_icon.setIcon(icon)
            
        self.tray_menu = QMenu(self)
        self.tray_menu.setObjectName("TrayMenu")
        self.tray_menu.setStyleSheet(SAO_GLASS_QSS)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("SAO Server Panel - Neural Link")
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        self.yui.log("System Tray Icon: Active (Forced SNI).", "#00ffcc")

    def on_tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def setup_audio(self):
        """Inicializa los efectos de sonido del sistema SAO"""
        def init_player(filename, loop=False, volume=0.5):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", filename)
            if not os.path.exists(path):
                return None
            
            player = QMediaPlayer(self)
            audio_output = QAudioOutput(self)
            audio_output.setVolume(volume)
            player.setAudioOutput(audio_output)
            player.setSource(QUrl.fromLocalFile(path))
            if loop:
                player.setLoops(QMediaPlayer.Loops.Infinite.value)
            return player

        self.snd_entrada = init_player("entrada.mp3", loop=False)
        self.snd_start = init_player("start.mp3")
        self.snd_death = init_player("death.mp3")
        self.snd_hover = init_player("hover.mp3", volume=0.2)
        self.snd_click = init_player("click.mp3", volume=0.4)

    def request_sudo_password(self):
        """Muestra el diálogo SAO para obtener privilegios de administrador"""
        # Prevenir SIGSEGV: No permitir la creación de diálogos fuera del hilo principal
        if QtCore.QThread.currentThread() != QtWidgets.QApplication.instance().thread():
            return False
            
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

    @QtCore.pyqtSlot()
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
        # El texto base del encabezado proviene de las traducciones; la versión se añade dinámicamente
        self.title_lbl = QLabel(TRANSLATIONS[self.idioma]["header_title"])
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 900; letter-spacing: 4px; color: #00ffcc;")
        
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(35, 35)
        self.conectar_cursor_mano(self.btn_menu)
        self.btn_menu.clicked.connect(self.show_options_menu)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(35, 35)
        self.btn_close.setObjectName("LogOut")
        self.btn_close.clicked.connect(self.close)
        self.conectar_cursor_mano(self.btn_close)

        title_row.addWidget(self.title_lbl)
        title_row.addStretch()
        title_row.addWidget(self.btn_menu)
        title_row.addWidget(self.btn_close)

        # Accesos directos rápidos
        nav_row = QHBoxLayout()
        self.btn_php_folder = QPushButton("⚙️ CONFIG PHP"); self.btn_php_folder.setObjectName("FolderBtn")
        self.btn_localhost = QPushButton("🌐 LOCALHOST ROOT"); self.btn_localhost.setObjectName("FolderBtn")
        self.btn_web_localhost = QPushButton("🌐 LOCALHOST WEB"); self.btn_web_localhost.setObjectName("ProjectBtn")
        self.conectar_cursor_mano(self.btn_php_folder)
        self.conectar_cursor_mano(self.btn_localhost)
        self.conectar_cursor_mano(self.btn_web_localhost)
        self.btn_php_folder.clicked.connect(self.open_php_config)
        self.btn_localhost.clicked.connect(self.open_localhost)
        self.btn_web_localhost.clicked.connect(self.open_web_localhost)
        
        nav_row.addWidget(self.btn_php_folder)
        nav_row.addWidget(self.btn_localhost)
        nav_row.addWidget(self.btn_web_localhost)
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
        self.project_sel.currentTextChanged.connect(self.actualizar_icono_favorito)

        self.btn_fav = QPushButton("☆")
        self.btn_fav.setFixedSize(40, 35)
        self.btn_fav.setStyleSheet("font-size: 18px; color: #FFD700; background: rgba(255,215,0,0.05);")
        self.btn_fav.clicked.connect(self.al_alternar_favorito)
        self.conectar_cursor_mano(self.btn_fav)

        self.btn_open_project = QPushButton("🚀 OPEN PROJECT"); self.btn_open_project.setObjectName("ProjectBtn")
        self.btn_open_project.clicked.connect(self.open_selected_project)
        self.conectar_cursor_mano(self.btn_open_project)
        
        sel_row = QHBoxLayout()
        self.lbl_php_unit = QLabel("PHP UNIT:")
        self.lbl_project = QLabel("PROJECT:")
        sel_row.addWidget(self.lbl_php_unit); sel_row.addWidget(self.php_sel, 1)
        sel_row.addWidget(self.lbl_project); sel_row.addWidget(self.project_sel, 2)
        sel_row.addWidget(self.btn_fav)
        sel_row.addWidget(self.btn_open_project)
        inv_layout.addLayout(sel_row)
        main_layout.addWidget(inv_frame)

        # --- 3. SERVICES & SYSTEM TOOLS ---
        mid_layout = QHBoxLayout()
        
        # Panel de Servicios
        serv_panel = QVBoxLayout()
        serv_panel.addWidget(self.create_service_row("Kirito Engine (Apache)", "httpd"))
        serv_panel.addWidget(self.create_service_row("Asuna Core (MariaDB)", "mariadb"))
        
        btn_row = QHBoxLayout()
        self.btn_link_start = QPushButton("⚡ LINK START"); self.btn_link_start.setObjectName("LinkStart")
        self.btn_log_out = QPushButton("🛑 LOG OUT"); self.btn_log_out.setObjectName("LogOut")
        self.btn_link_start.setFixedHeight(45); self.btn_log_out.setFixedHeight(45)
        self.btn_link_start.clicked.connect(self.link_start_init)
        self.btn_log_out.clicked.connect(self.log_out_stop)
        self.conectar_cursor_mano(self.btn_link_start)
        self.conectar_cursor_mano(self.btn_log_out)
        
        btn_row.addWidget(self.btn_link_start)
        btn_row.addWidget(self.btn_log_out)
        serv_panel.addLayout(btn_row)
        mid_layout.addLayout(serv_panel, 60)

        # Panel de Herramientas (Grid)
        tools_frame = QFrame()
        tools_frame.setObjectName("GlassCard")
        t_grid = QGridLayout(tools_frame)
        t_grid.setSpacing(10)
        
        self.label_tools = QLabel("SYSTEM MAINTENANCE"); self.label_tools.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_tools.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        t_grid.addWidget(self.label_tools, 0, 0, 1, 2)

        # Implementación de botones solicitados
        tools = [
            (self.al_sanear_apache),
            (self.al_optimizar_ram),
            (self.al_cambiar_php),
            (self.al_abrir_mailpit),
            (self.al_vaciar_logs),
            (self.al_abrir_ajustes),
            (self.hide_yui_monitor)
        ]

        self.tool_btns = []
        for i, func in enumerate(tools):
            btn = QPushButton()
            btn.setFixedSize(120, 35)
            btn.clicked.connect(func)
            self.conectar_cursor_mano(btn)
            t_grid.addWidget(btn, (i // 2) + 1, i % 2)
            self.tool_btns.append(btn)

        mid_layout.addWidget(tools_frame, 40)
        main_layout.addLayout(mid_layout)

        # Botón para restaurar terminal cuando está oculta
        self.btn_show_yui = QPushButton("📄 ACTIVAR MONITOR DE LOGS (YUI TERMINAL)")
        self.btn_show_yui.setObjectName("ProjectBtn")
        self.btn_show_yui.setFixedHeight(40)
        self.conectar_cursor_mano(self.btn_show_yui)
        self.btn_show_yui.clicked.connect(self.show_yui_monitor)
        self.btn_show_yui.hide()
        main_layout.addWidget(self.btn_show_yui)

        main_layout.addWidget(self.yui)
        
    # --- LÓGICA DE FAVORITOS Y CONFIGURACIÓN ---
    def cargar_ajustes_sao(self):
        """Carga la configuración persistente (Favoritos y Carpeta)"""
        if os.path.exists(self.ruta_config):
            try:
                with open(self.ruta_config, "r") as f:
                    datos = json.load(f)
                    self.dir_proyectos = datos.get("project_dir", self.dir_proyectos)
                    self.favoritos = datos.get("favorites", [])
                    self.idioma = datos.get("language", "ES")
            except:
                pass

    def guardar_ajustes_sao(self):
        """Guarda la configuración persistente"""
        try:
            datos = {
                "project_dir": self.dir_proyectos,
                "favorites": self.favoritos,
                "language": self.idioma
            }
            with open(self.ruta_config, "w") as f:
                json.dump(datos, f)
        except:
            pass

    def al_alternar_favorito(self):
        """Añade o quita el proyecto actual de la lista de favoritos"""
        proyecto = self.project_sel.currentText()
        if not proyecto or proyecto in ["No projects detected", "Localhost root missing"]: return
        
        if proyecto in self.favoritos:
            self.favoritos.remove(proyecto)
            self.yui.log(f"Project '{proyecto}' removed from favorites.", "#ff7f00")
        else:
            self.favoritos.append(proyecto)
            self.yui.log(f"Project '{proyecto}' added to favorites! ★", "#FFD700")
        
        self.guardar_ajustes_sao()
        self.actualizar_icono_favorito()
        self.refresh_projects()
        self.project_sel.setCurrentText(proyecto)

    def actualizar_icono_favorito(self):
        """Cambia el icono de la estrella según si el proyecto es favorito o no"""
        proyecto = self.project_sel.currentText()
        if proyecto in self.favoritos:
            self.btn_fav.setText("★")
        else:
            self.btn_fav.setText("☆")

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
            res = subprocess.run(["php", "-r", "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;"], capture_output=True, text=True)
            self.version_php_actual = res.stdout.strip()
            self.yui.log(f"Active Binary detected: PHP {self.version_php_actual}", "#00ffcc")
        except:
            self.version_php_actual = "N/A"
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
        """Escanea el directorio raíz usando os.scandir para máxima velocidad"""
        path = self.dir_proyectos
        if os.path.exists(path):
            try:
                # os.scandir es mucho más rápido que os.listdir + os.path.isdir
                with os.scandir(path) as it:
                    projects = [entry.name for entry in it if entry.is_dir()]
                
                self.project_sel.clear()
                if projects:
                    projects.sort(key=lambda x: (0 if x in self.favoritos else 1, x.lower()))
                    self.project_sel.addItems(projects)
                    self.actualizar_icono_favorito()
                    self.yui.log(f"Neural Index: {len(projects)} projects scanned.")
                else:
                    self.project_sel.addItem("No projects detected")
            except Exception as e:
                self.project_sel.clear()
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
        self.conectar_cursor_mano(btn_start)
        self.conectar_cursor_mano(btn_stop)
        
        l.addWidget(btn_start)
        l.addWidget(btn_stop)
        return f

    def setup_localhost_index(self):
        """Genera automáticamente el dashboard profesional de SAO (index, style, js)"""
        path = self.dir_proyectos
        if not os.path.exists(path):
            # Intentar crear la carpeta raíz si no existe
            res = self.run_cmd(["mkdir", "-p", path], True)
            if not res or res.returncode != 0:
                self.yui.log(f"Error: No se pudo crear la carpeta raíz {path}", "#ff4444")
                return

        if not self.sudo_password and not self.request_sudo_password():
            return

        index_php = r"""<?php
/**
 * SAO ForgeStack Explorer - Improved Edition
 * Autonomous recursive navigation with project detection + launch capabilities
 * Version: 2.0 (Neon Glassmorphism + Smart Routing)
 */

// 1. CONFIGURACIÓN Y SEGURIDAD
$baseDir = realpath(__DIR__);
$queryDir = isset($_GET['dir']) ? $_GET['dir'] : '';

// Limpiar ruta: eliminar intentos de directory traversal
$cleanPath = preg_replace('/\.\.|\\\\/', '', $queryDir);
$currentFullPath = realpath($baseDir . DIRECTORY_SEPARATOR . $cleanPath);

// Validar que no salimos del directorio raíz permitido
if (!$currentFullPath || strpos($currentFullPath, $baseDir) !== 0) {
    $currentFullPath = $baseDir;
    $cleanPath = '';
}

// 2. OBTENER ELEMENTOS DEL DIRECTORIO ACTUAL
$ignored = ['.', '..', '.git', 'node_modules', 'vendor', '.env', '.idea', '.DS_Store', 'thumbs.db'];
$items = @scandir($currentFullPath);
if ($items === false) { $items = []; }
$items = array_diff($items, $ignored);

// 3. CLASIFICAR CARPETAS (y contar elementos internos)
$folders = [];
foreach ($items as $item) {
    $fullPath = $currentFullPath . DIRECTORY_SEPARATOR . $item;
    if (is_dir($fullPath)) {
        $isProject = false;
        $identifiers = ['index.php', 'index.html', 'index.htm', 'composer.json', 'package.json'];
        foreach ($identifiers as $id) {
            if (file_exists($fullPath . DIRECTORY_SEPARATOR . $id)) {
                $isProject = true;
                break;
            }
        }
        $subItems = @scandir($fullPath);
        $subCount = $subItems ? count(array_diff($subItems, $ignored)) : 0;
        $folders[] = [
            'name'     => $item,
            'relPath'  => trim($cleanPath . '/' . $item, '/'),
            'type'     => $isProject ? 'project' : 'container',
            'subCount' => $subCount
        ];
    }
}
usort($folders, function($a, $b) { return strcasecmp($a['name'], $b['name']); });

// 4. BREADCRUMBS
$breadcrumbs = array_filter(explode('/', $cleanPath));

// 5. URL BASE PARA LANZAR PROYECTOS
$scriptName = $_SERVER['SCRIPT_NAME'] ?? 'index.php';
$baseWebPath = rtrim(dirname($scriptName), '/') . '/';
if ($baseWebPath === '//') $baseWebPath = '/';
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAO ForgeStack | <?php echo $cleanPath ? '/' . htmlspecialchars($cleanPath) : 'ROOT'; ?></title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="crt-overlay"></div>
<div id="loading-screen">
    <h1 class="loading-text">LINK START</h1>
    <div class="progress-container"><div class="loading-bar" id="bar"></div></div>
</div>
<div class="main-interface">
    <header class="status-bar">
        <div class="breadcrumb">
            <a href="index.php">◢ ROOT</a>
            <?php 
            $buildPath = '';
            foreach($breadcrumbs as $crumb): 
                $buildPath .= ($buildPath ? '/' : '') . $crumb;
            ?>
                <span>/</span><a href="index.php?dir=<?php echo urlencode($buildPath); ?>"><?php echo htmlspecialchars(strtoupper($crumb)); ?></a>
            <?php endforeach; ?>
        </div>
        <div class="system-tag">
            ⚡ FORGE // <span style="color:var(--neon-cyan)"><?php echo count($folders); ?> NODES</span>
        </div>
    </header>
    <div class="search-bar">
        <input type="text" id="filterInput" placeholder="[ FILTER NODES ]" autocomplete="off">
    </div>
    <main class="dashboard">
        <div class="project-grid" id="projectGrid">
            <?php if ($cleanPath !== ''): ?>
                <a href="index.php?dir=<?php echo urlencode(dirname($cleanPath) == '.' ? '' : dirname($cleanPath)); ?>" class="project-card back-btn">
                    <div class="project-name">⬆ RETURN TO UPPER LEVEL</div>
                </a>
            <?php endif; ?>
            <?php foreach($folders as $folder): 
                $isProject = ($folder['type'] === 'project');
                $exploreUrl = 'index.php?dir=' . urlencode($folder['relPath']);
                $launchUrl = $baseWebPath . $folder['relPath'] . '/';
                $badgeText = $isProject ? '⚔️ DEPLOYABLE' : '📂 DIRECTORY';
            ?>
                <div class="project-card type-<?php echo $folder['type']; ?>" data-name="<?php echo htmlspecialchars(strtolower($folder['name'])); ?>">
                    <div class="card-header">
                        <div class="icon"><?php echo $isProject ? '⚡' : '🗀'; ?></div>
                        <div class="project-info">
                            <div class="project-name"><?php echo htmlspecialchars($folder['name']); ?></div>
                            <span class="badge"><?php echo $badgeText; ?></span>
                            <div class="subinfo">📦 <?php echo $folder['subCount']; ?> elementos</div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <a href="<?php echo $exploreUrl; ?>" class="btn-explore">🔍 EXPLORE</a>
                        <?php if ($isProject): ?>
                            <a href="<?php echo $launchUrl; ?>" target="_blank" class="btn-launch">▶ LAUNCH</a>
                        <?php endif; ?>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </main>
    <footer>SAO ForgeStack Explorer v2 | <?php echo date('Y-m-d H:i:s'); ?></footer>
</div>
<script src="script.js"></script>
</body>
</html>"""

        style_css = r""":root {
  --neon-cyan: #00ffcc;
  --neon-pink: #ff00aa;
  --bg-color: #05070a;
  --glass-bg: rgba(0, 255, 204, 0.05);
  --card-border: rgba(0, 255, 204, 0.3);
}
* { box-sizing: border-box; }
body {
  background: var(--bg-color);
  color: #cfcfcf;
  font-family: 'Courier New', monospace;
  margin: 0;
  overflow-x: hidden;
}
.crt-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
              linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
  background-size: 100% 4px, 3px 100%;
  pointer-events: none;
  z-index: 9999;
}
.main-interface { padding: 30px 40px; opacity: 0; animation: fadeIn 0.6s forwards 0.4s; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
header.status-bar { border-bottom: 2px solid var(--neon-cyan); padding-bottom: 12px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: baseline; }
.breadcrumb a { color: var(--neon-cyan); text-decoration: none; text-transform: uppercase; }
.breadcrumb span { margin: 0 8px; color: #555; }
.system-tag { font-size: 13px; background: rgba(0,255,204,0.1); padding: 6px 12px; border-radius: 20px; }
.search-bar { margin-bottom: 25px; display: flex; justify-content: flex-end; }
#filterInput { background: rgba(0,0,0,0.6); border: 1px solid var(--neon-cyan); padding: 10px 18px; color: var(--neon-cyan); font-family: monospace; outline: none; width: 280px; }
.project-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 22px; }
.project-card {
  position: relative;
  border: 1px solid var(--card-border);
  padding: 20px;
  transition: 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
  background: var(--glass-bg);
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: #fff;
}
.project-card:hover { transform: translateY(-4px); border-color: var(--neon-cyan); box-shadow: 0 8px 25px rgba(0, 255, 204, 0.15); }
.project-card.type-project { border-left: 3px solid var(--neon-cyan); }
.card-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
.icon { font-size: 38px; color: var(--neon-cyan); }
.project-name { font-size: 1.1rem; font-weight: bold; margin-bottom: 6px; }
.badge { font-size: 9px; padding: 2px 8px; border: 1px solid var(--neon-cyan); color: var(--neon-cyan); text-transform: uppercase; background: rgba(0,0,0,0.5); }
.subinfo { font-size: 11px; color: #88aaff; }
.card-actions { margin-top: 18px; display: flex; gap: 12px; border-top: 1px dashed rgba(0,255,204,0.2); padding-top: 14px; }
.btn-explore, .btn-launch { font-size: 12px; text-decoration: none; padding: 5px 12px; transition: 0.2s; font-family: monospace; font-weight: bold; }
.btn-explore { border: 1px solid var(--neon-cyan); color: var(--neon-cyan); }
.btn-launch { background: rgba(0,255,204,0.15); border: 1px solid #00ccaa; color: #ccffff; }
.btn-explore:hover, .btn-launch:hover { background: var(--neon-cyan); color: #000; }
.back-btn { grid-column: 1 / -1; text-align: center; border-style: dashed; }
footer { margin-top: 50px; text-align: center; font-size: 11px; color: #667788; }
#loading-screen { position: fixed; inset: 0; background: var(--bg-color); z-index: 10000; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: opacity 0.5s ease; }
.loading-text { font-size: 42px; letter-spacing: 12px; color: var(--neon-cyan); text-shadow: 0 0 12px var(--neon-cyan); }
.progress-container { width: 320px; height: 2px; background: rgba(255,255,255,0.2); margin-top: 20px; overflow: hidden; }
.loading-bar { width: 0%; height: 100%; background: var(--neon-cyan); }"""

        script_js = r"""window.addEventListener("load", () => {
    const bar = document.getElementById('bar');
    const loadingScreen = document.getElementById('loading-screen');
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 100) {
            clearInterval(interval);
            if (loadingScreen) {
                loadingScreen.style.opacity = '0';
                setTimeout(() => { if (loadingScreen.parentNode) loadingScreen.remove(); }, 500);
            }
            return;
        }
        width += Math.random() * 8 + 2;
        if (width > 100) width = 100;
        if (bar) bar.style.width = width + '%';
    }, 35);

    const filterInput = document.getElementById('filterInput');
    const cards = document.querySelectorAll('.project-card');

    function filterNodes() {
        const term = filterInput.value.trim().toLowerCase();
        cards.forEach(card => {
            if (card.classList.contains('back-btn')) { card.style.display = ''; return; }
            const nameAttr = card.getAttribute('data-name');
            if (nameAttr && nameAttr.includes(term)) { card.style.display = ''; } 
            else { card.style.display = 'none'; }
        });
    }
    if (filterInput) filterInput.addEventListener('input', filterNodes);
});"""

        files = {
            "index.php": index_php,
            "style.css": style_css,
            "script.js": script_js
        }

        for filename, content in files.items():
            full_path = os.path.join(path, filename)
            
            # Codificar en base64 para evitar que el shell interprete los símbolos $ de PHP
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            cmd = f"echo '{content_b64}' | base64 -d | tee '{full_path}' > /dev/null"
            
            self.run_cmd(["sh", "-c", cmd], use_sudo=True)
            # Asegurar que el archivo sea legible por el servidor inmediatamente
            self.run_cmd(["chmod", "644", full_path], True)

        self.yui.log(f"Neural Link: Dashboard files deployed to {path}", "#00ffcc")
        self.fix_permissions(path)

    def configure_apache_for_path(self, path):
        """Genera dinámicamente la configuración de Apache para una ruta específica."""
        if not os.path.exists(path):
            self.yui.log(f"Error: Path {path} does not exist.", "#ff4444")
            return False
        
        path = os.path.abspath(path).rstrip('/')
        conf_file = "/etc/httpd/conf/extra/sao-server-projects.conf"
        conf_content = f"""# Autogenerated by SAO-Server
<Directory "{path}">
    DirectoryIndex index.php index.html index.htm
    Options +Indexes +FollowSymLinks +MultiViews
    AllowOverride All
    Require all granted
    
    AddType application/x-httpd-php .php
    <FilesMatch \\.php$>
        SetHandler application/x-httpd-php
    </FilesMatch>
</Directory>
"""
        temp_file = "/tmp/sao-projects.conf"
        try:
            with open(temp_file, "w") as f:
                f.write(conf_content)
            
            # Mover a la configuración de Apache
            self.run_cmd(["mv", temp_file, conf_file], use_sudo=True)
            
            # Asegurar que el archivo principal incluya esta configuración al principio de los extras
            httpd_conf = "/etc/httpd/conf/httpd.conf"
            include_line = f"Include {conf_file}"
            # Usamos sed para insertar el Include antes de otros VirtualHosts si es posible
            check_cmd = f"grep -q '{include_line}' {httpd_conf} || sed -i '1i {include_line}' {httpd_conf}"
            self.run_cmd(["sh", "-c", check_cmd], use_sudo=True)
            
            self.yui.log(f"Apache config generated for {path}", "#00ffcc")
            return True
        except Exception as e:
            self.yui.log(f"Config Generation Failed: {e}", "#ff4444")
            return False

    def fix_permissions(self, path):
        """Repara el árbol de permisos desde ROOT hasta el destino para evitar Error 403."""
        if not os.path.exists(path): return False
        path = os.path.abspath(path)
        
        # 1. Traversal Path (Rápido): Asegurar acceso de búsqueda en padres
        self.yui.log("Fixing Traversal Path (Aincrad Protocol)...", "#ff7f00")
        cmd_traversal = f'p="{path}"; while [ "$p" != "/" ] && [ "$p" != "." ]; do chmod a+x "$p"; p=$(dirname "$p") 2>/dev/null || break; done'
        self.run_cmd(["sh", "-c", cmd_traversal], use_sudo=True)
        
        # 2. Operaciones Recursivas (Pesadas): Optimizadas para una sola pasada lógica
        user = getpass.getuser()
        self.yui.log(f"Optimizing tree permissions for {user}:http...", "#00ccff")
        self.run_cmd(["chown", "-R", f"{user}:http", path], use_sudo=True)
        # u=rwX: Directorios (7) y Archivos (6). g/o=rX: Directorios (5) y Archivos (4).
        self.run_cmd(["chmod", "-R", "u=rwX,g=rX,o=rX", path], use_sudo=True)
        
        return True

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
        # Efectos de sonido de inicio
        if hasattr(self, 'snd_start') and self.snd_start:
            self.snd_start.play()
        if hasattr(self, 'snd_entrada') and self.snd_entrada:
            self.snd_entrada.stop()

        # Lanzar la lógica pesada en un hilo separado para no congelar la UI
        self._lanzar_hilo(self._tarea_iniciar_entorno_bg)

    def _tarea_iniciar_entorno_bg(self):
        """Lógica operativa de inicio ejecutada en segundo plano."""
        # 1. Configuración avanzada de Apache (MPM Prefork para PHP)
        if os.path.exists("/etc/httpd/conf/httpd.conf"):
            self.yui.log("Configuring Apache Modules (MPM Prefork)...", "#555")
            enable_php = (
                "sed -i 's/^LoadModule mpm_event_module/#LoadModule mpm_event_module/' /etc/httpd/conf/httpd.conf; "
                "sed -i 's/^#LoadModule mpm_prefork_module/LoadModule mpm_prefork_module/' /etc/httpd/conf/httpd.conf; "
                "sed -i 's/^#LoadModule speling_module/LoadModule speling_module/' /etc/httpd/conf/httpd.conf; "
                r"grep -q 'DirectoryIndex index.php' /etc/httpd/conf/httpd.conf || sed -i '/<IfModule dir_module>/a \    DirectoryIndex index.php index.html' /etc/httpd/conf/httpd.conf; "
                r"grep -q 'php_module' /etc/httpd/conf/httpd.conf || echo -e '\n# SAO PHP CONFIG\nLoadModule php_module modules/libphp.so\nInclude conf/extra/php_module.conf' >> /etc/httpd/conf/httpd.conf"
            )
            self.run_cmd(["sh", "-c", enable_php], use_sudo=True)

        # 2. Inicialización de MariaDB (Si el directorio está vacío)
        check_db = self.run_cmd(["test", "-d", "/var/lib/mysql/mysql"], use_sudo=True)
        if check_db and check_db.returncode != 0:
            self.yui.log("Initializing MariaDB Data Directory...", "#ff7f00")
            self.run_cmd(["mariadb-install-db", "--user=mysql", "--basedir=/usr", "--datadir=/var/lib/mysql"], use_sudo=True)

        # 3. Reinicio de servicios
        self.yui.log("Restarting Core Units: Apache & MariaDB...", "#00ccff")
        self.run_cmd(["systemctl", "restart", "httpd", "mariadb"], use_sudo=True)

        # 4. SQL Fix para phpmyadmin (Evita errores de permisos comunes)
        sql_fix = "CREATE USER IF NOT EXISTS 'phpmyadmin'@'localhost' IDENTIFIED BY ''; " \
                  "GRANT ALL PRIVILEGES ON phpmyadmin.* TO 'phpmyadmin'@'localhost'; FLUSH PRIVILEGES;"
        self.run_cmd(["mariadb", "-e", sql_fix], use_sudo=True)

        # 5. Despliegue de Dashboard y Permisos
        self.setup_localhost_index()
        
        # 6. Iniciar Mailpit si no está corriendo (Silent)
        try:
            check_mail = subprocess.run(["pgrep", "mailpit"], capture_output=True)
            if check_mail.returncode != 0:
                self.yui.log("Starting Mailpit Service...", "#555")
                subprocess.Popen(["mailpit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

        self.yui.log("LINK START COMPLETE. Welcome to Aincrad.", "#00ffcc")
        # Abrir navegador tras el éxito
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://localhost"))

    def al_sanear_apache(self):
        """Inicia el proceso de saneamiento de Apache."""
        self.yui.log("REPAIR: Iniciando secuencia de saneamiento de Apache...", "#ff7f00")
        if hasattr(self, 'snd_click') and self.snd_click:
            self.snd_click.play()
        self._lanzar_hilo(self.sanear_apache_bg)

    def sanear_apache_bg(self):
        """Valida sintaxis y aplica correcciones administrativas en segundo plano."""
        # 1. Verificar integridad de sintaxis usando apachectl
        res = self.run_cmd(["apachectl", "-t"], use_sudo=True)
        
        if res and res.stderr and "Syntax error" in res.stderr:
            error_msg = res.stderr.strip()
            self.yui.log("CRITICAL: Error de sintaxis detectado en la configuración.", "#ff4444")
            self.yui.log(error_msg, "#ff8888")
            
            # Extraer archivo y línea del error para apertura automática
            # Ejemplo: AH00526: Syntax error on line 54 of /etc/httpd/conf/httpd.conf:
            match = re.search(r"on line (\d+) of ([^:]+):", error_msg)
            if match:
                line_num = match.group(1)
                config_file = match.group(2)
                self.yui.log(f"REPAIR: Localizado en línea {line_num}. Abriendo archivo...", "#00ccff")
                subprocess.run(["xdg-open", config_file])

            self.yui.log("Intentando resetear estados de fallo y reiniciar...", "#555")
            self.run_cmd(["systemctl", "reset-failed", "httpd"], use_sudo=True)
            self.run_cmd(["systemctl", "restart", "httpd"], use_sudo=True)
        else:
            self.yui.log("Apache Syntax: OK.", "#00ffcc")
            # Aplicar corrección de privilegios para phpMyAdmin (Fix SQL)
            sql_fix = "CREATE USER IF NOT EXISTS 'phpmyadmin'@'localhost' IDENTIFIED BY ''; " \
                      "GRANT ALL PRIVILEGES ON phpmyadmin.* TO 'phpmyadmin'@'localhost'; FLUSH PRIVILEGES;"
            self.run_cmd(["mariadb", "-e", sql_fix], use_sudo=True)
            self.yui.log("Secuencia de saneamiento completada con éxito.", "#00ffcc")
            self.poll_services_status()

    def al_optimizar_ram(self):
        """Libera cachés del sistema para optimizar memoria."""
        if not self.get_sudo_auth(): return
        self.yui.log("MEMORY: Iniciando purga de cachés del sistema...", "#ff7f00")
        self._lanzar_hilo(self._tarea_optimizar_ram_bg)

    def _tarea_optimizar_ram_bg(self):
        res = self.run_cmd(["sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], use_sudo=True)
        if res and res.returncode == 0:
            self.yui.log("MEMORY: Optimización completada con éxito.", "#00ffcc")
            gc.collect()
            # Refrescar métricas visuales inmediatamente tras optimizar
            QtCore.QTimer.singleShot(0, self.refresh_real_stats)
        else:
            self.yui.log("MEMORY: Fallo al liberar cachés (Sudo requerido).", "#ff4444")

    def al_abrir_mailpit(self):
        """Abre la interfaz web de Mailpit."""
        self.yui.log("EMAIL: Accediendo a Mailpit (Panel de Correo)...", "#00ccff")
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://localhost:8025"))

    def al_vaciar_logs(self):
        """Limpia el archivo de logs de Apache."""
        if not self.get_sudo_auth(): return
        self.yui.log("SYSTEM: Vaciando registros de errores de Apache...", "#ff7f00")
        self._lanzar_hilo(self._tarea_vaciar_logs_bg)

    def _tarea_vaciar_logs_bg(self):
        res = self.run_cmd(["sh", "-c", "truncate -s 0 /var/log/httpd/error_log"], use_sudo=True)
        if res and res.returncode == 0:
            self.yui.log("SYSTEM: Logs de Apache reiniciados.", "#00ffcc")
        else:
            self.yui.log("SYSTEM: Error al vaciar logs.", "#ff4444")

    def al_cambiar_php(self):
        """Diálogo interactivo para cambiar la versión de PHP en Arch."""
        rutas = ["/usr/bin/php*", "/usr/local/bin/php*"]
        candidatos = []
        for r in rutas: candidatos.extend(glob.glob(r))
        
        versiones = []
        for c in candidatos:
            nombre = os.path.basename(c)
            if re.match(r"^php[0-9\.]*$", nombre) and nombre not in ["php-config", "phpize", "phpdbg", "php-cgi"] and os.access(c, os.X_OK):
                versiones.append(nombre)
        
        versiones = sorted(list(set(versiones)))
        if not versiones:
            self.yui.log("PHP: No se detectaron binarios alternativos en /usr/bin/", "#ff4444")
            return

        if not self.get_sudo_auth(): return
        ver, ok = QInputDialog.getItem(self, "PHP UNIT SELECTOR", "Seleccione motor PHP:", versiones, 0, False)
        if ok and ver:
            self.yui.log(f"PHP: Redirigiendo enlace binario a {ver}...", "#ff7f00")
            self._lanzar_hilo(self._tarea_cambiar_php_bg, (ver,))

    def _tarea_cambiar_php_bg(self, seleccionado):
        cmd = f"ln -sf /usr/bin/{seleccionado} /usr/bin/php; systemctl restart httpd"
        res = self.run_cmd(["sh", "-c", cmd], use_sudo=True)
        if res and res.returncode == 0:
            self._detectar_version_php()
            self.yui.log(f"PHP: Sistema vinculado a {seleccionado} correctamente.", "#00ffcc")
        else:
            self.yui.log("PHP: Error al actualizar enlace. Revise privilegios.", "#ff4444")

    def al_abrir_ajustes(self):
        """Configura la carpeta raíz de proyectos y actualiza Apache."""
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Raíz (LOCALHOST)", self.dir_proyectos)
        
        if new_dir and new_dir != self.dir_proyectos:
            new_dir = os.path.normpath(new_dir)
            # Alerta de seguridad para rutas críticas
            criticas = [os.path.expanduser("~"), "/", "/etc", "/usr", "/var"]
            if new_dir in criticas:
                reply = QtWidgets.QMessageBox.warning(self, "SEGURIDAD CRÍTICA", 
                    f"Has seleccionado una ruta sensible ({new_dir}).\nEsto expondrá archivos del sistema en Apache.\n\n¿Continuar?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if reply == QtWidgets.QMessageBox.StandardButton.No: return

            self.dir_proyectos = new_dir
            self.yui.log(f"SYSTEM: Raíz actualizada a {new_dir}", "#00ccff")
            self.get_sudo_auth() # Asegurar sudo antes de reconfigurar Apache
            self.guardar_ajustes_sao() # Guardar permanentemente de inmediato
            self.refresh_projects()
            self._lanzar_hilo(self.update_apache_config)

    def _mostrar_popup_db_faltante(self, db_name):
        """Detecta bases de datos faltantes en los logs y ofrece crearlas."""
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("DATABASE ERROR")
        msg.setText(f"Base de datos '{db_name}' no encontrada.")
        msg.setInformativeText(f"¿Deseas que el sistema cree '{db_name}' automáticamente?")
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg.setStyleSheet(SAO_GLASS_QSS)
        
        if msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            self._lanzar_hilo(self._tarea_crear_db_rapida, (db_name,))

    def _tarea_crear_db_rapida(self, nombre_db):
        self.yui.log(f"DB: Generando base de datos '{nombre_db}'...", "#ff7f00")
        res = self.run_cmd(["mariadb", "-e", f"CREATE DATABASE IF NOT EXISTS `{nombre_db}`;"], use_sudo=True)
        if res and res.returncode == 0:
            self.yui.log(f"DB: '{nombre_db}' creada con éxito.", "#00ffcc")
        else:
            self.yui.log(f"DB: Error al crear '{nombre_db}'.", "#ff4444")

    def log_out_stop(self):
        self.yui.log("LOG OUT: Terminating Units...", "#ff7f00")
        if hasattr(self, 'snd_death') and self.snd_death:
            self.snd_death.play()
        self.manage_service("httpd", "stop")
        self.manage_service("mariadb", "stop")

    def sync_repository(self):
        """Wrapper que usa `sao_tasks.update_task.run_update` para actualizar.
        Ejecuta `scripts/update.sh` si está disponible, o fallback a git pull.
        """
        self.yui.log("SYNC: Running update task...", "#00ffcc")
        repo_path = os.path.dirname(os.path.abspath(__file__))
        res = update_task.run_update(repo_path=repo_path, logger=getattr(self.yui, 'log', None))

        # Compatible con subprocess.CompletedProcess y otros retornos
        code = getattr(res, 'returncode', 0) if res is not None else 0
        if code == 0:
            self.yui.log("System updated to latest version.", "#00ffcc")
        else:
            self.yui.log("Update failed. Check logs and connection.", "#ff4444")

    def repair_panel(self):
        """Wrapper que delega la reparación en `sao_tasks.repair_task.repair_panel`.
        Mantiene la interfaz `self.yui.log` para registrar progreso.
        """
        self.yui.log("REPAIR: Initiating integrity recovery...", "#ff7f00")
        repo_path = os.path.dirname(os.path.abspath(__file__))
        res = repair_task.repair_panel(repo_path=repo_path, logger=getattr(self.yui, 'log', None), run_cmd=self.run_cmd)
        code = getattr(res, 'returncode', 0) if res is not None else 0
        if code == 0:
            self.yui.log("REPAIR COMPLETE: Integrity restored.", "#00ffcc")
        else:
            self.yui.log("REPAIR FAILED: System manual intervention required.", "#ff4444")

    def save_git_token_dialog(self):
        """Muestra un diálogo para ingresar y guardar el token de GitHub de forma segura."""
        t = TRANSLATIONS[self.idioma]
        prompt = "Introduce tu Personal Access Token de GitHub (se guardará en ~/.sao_server_token):"
        token, ok = QInputDialog.getText(self, t.get("opt_save_token", "Save Token"), prompt, QLineEdit.EchoMode.Password)
        if not ok:
            self.yui.log("Token not saved (cancelled).", "#ffbb33")
            return
        token = token.strip()
        if not token:
            self.yui.log("Empty token — not saved.", "#ffbb33")
            return
        res = auth_task.save_token(token)
        if res:
            self.yui.log("Token saved to ~/.sao_server_token (mode 600).", "#00ffcc")
        else:
            self.yui.log("Failed to save token.", "#ff4444")

    def hide_yui_monitor(self):
        """Detiene el monitoreo visual y restaura el botón inicial (Adaptación)"""
        self.yui.hide()
        self.btn_show_yui.show()
        self.yui.log("System Alert: Yui Terminal minimized to background.", "#ff7f00")

    def show_yui_monitor(self):
        """Restaura la terminal de logs Yui"""
        self.btn_show_yui.hide()
        self.yui.show()
        self.yui.log("System Alert: Yui Terminal link restored.", "#00ffcc")

    def show_yui_context_menu(self, pos):
        """Muestra menú personalizado en la terminal embebida (Adaptación)"""
        menu = self.yui.terminal.createStandardContextMenu()
        menu.addSeparator()
        
        hide_act = menu.addAction("❌ Ocultar Monitor")
        hide_act.triggered.connect(self.hide_yui_monitor)
        
        menu.setStyleSheet(SAO_GLASS_QSS)
        menu.exec(self.yui.terminal.mapToGlobal(pos))

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
        path = self.dir_proyectos
        
        if not os.path.exists(path):
            self.yui.log(f"Localhost path {path} not found. Creating...", "#ff7f00")
            res = self.run_cmd(["mkdir", "-p", path], True)
            if not res or res.returncode != 0:
                self.yui.log("Failed to create directory.", "#ff4444")
                return
        
        # Reparar permisos en segundo plano para no congelar la UI al abrir carpetas pesadas
        self._lanzar_hilo(self.fix_permissions, (path,))
        self.yui.log(f"Syncing path permissions & opening: {path}", "#00ccff")
        subprocess.run(["xdg-open", path])

    def open_web_localhost(self):
        """Abre la web del localhost en el navegador"""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://localhost/"))

    def update_apache_config(self):
        """Actualiza la configuración de Apache para forzar errores en pantalla y desarrollo"""
        self.yui.log("Neural Link: Sincronizando VirtualHost de Apache...", "#ff7f00")
        path = self.dir_proyectos.rstrip('/')
        
        conf_content = (f"<VirtualHost *:80>\n"
                        f"    ServerAdmin webmaster@localhost\n"
                        f"    ServerName localhost\n"
                        f"    ServerAlias 127.0.0.1\n"
                        f"    DocumentRoot \"{path}\"\n"
                        f"    DirectoryIndex index.php index.html index.htm\n"
                        f"    <Directory \"{path}\">\n"
                        f"        Options +Indexes +FollowSymLinks +MultiViews\n"
                        f"        AllowOverride All\n"
                        f"        Require all granted\n"
                        f"        # Ignorar mayúsculas/minúsculas\n"
                        f"        CheckSpelling On\n"
                        f"        CheckCaseOnly On\n"
                        f"\n"
                        f"        # Forzar errores en pantalla (Modo Desarrollo)\n"
                        f"        AddType application/x-httpd-php .php\n"
                        f"        php_admin_flag display_errors On\n"
                        f"        php_admin_flag display_startup_errors On\n"
                        f"        php_admin_value error_reporting 32767\n"
                        f"        php_flag html_errors On\n"
                        f"    </Directory>\n"
                        f"\n"
                        f"    # Garantizar que Apache reconozca y procese PHP\n"
                        f"    <FilesMatch \\.php$>\n"
                        f"        SetHandler application/x-httpd-php\n"
                        f"    </FilesMatch>\n"
                        f"\n"
                        f"    ErrorLog /var/log/httpd/error_log\n"
                        f"    CustomLog /var/log/httpd/access_log combined\n"
                        f"</VirtualHost>")
        
        archivo_tmp = "/tmp/sao-apache.conf"
        try:
            with open(archivo_tmp, "w") as f:
                f.write(conf_content)
            
            cmd = (f"mkdir -p /etc/httpd/conf/extra/; "
                   f"mv {archivo_tmp} /etc/httpd/conf/extra/000-default.conf; "
                   f"grep -q 'Include conf/extra/000-default.conf' /etc/httpd/conf/httpd.conf || echo 'Include conf/extra/000-default.conf' >> /etc/httpd/conf/httpd.conf")
            
            self.run_cmd(["sh", "-c", cmd], True)
        except Exception as e:
            self.yui.log(f"Error al escribir config de Apache: {e}", "#ff4444")

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
        """Abre el proyecto seleccionado en el navegador"""
        project = self.project_sel.currentText()
        # Filtramos los mensajes de marcador de posición que inserta refresh_projects
        if project and project not in ["No projects detected", "Localhost root missing", ""]:
            # 1. Abrir en el navegador web (URL local)
            url = f"http://localhost/{project}/"
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
            self.yui.log(f"Neural Link: Project '{project}' deployed to view.", "#00ffcc")
        else:
            self.yui.log("Please select a valid project from the index.", "#ff7f00")

    def refresh_real_stats(self):
        """Métricas de sistema optimizadas para no bloquear el hilo principal"""
        try:
            # interval=None hace que psutil sea no bloqueante (retorna valor desde la última llamada)
            cpu = psutil.cpu_percent(interval=None)
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

    def _iniciar_logica_panel(self):
        """Punto de entrada de la lógica operativa del panel (Adaptado para PyQt6)."""
        if not self.sudo_password:
            self.request_sudo_password()
        
        # Lanzar tareas pesadas en segundo plano para evitar congelamiento inicial
        self._lanzar_hilo(self._warmup_system_bg)
        self._lanzar_hilo(self.refresh_projects)

        # Temporizador de estado (3s para métricas, 5s para servicios)
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.refresh_real_stats)
        self.stats_timer.timeout.connect(self.poll_services_status)
        self.stats_timer.start(5000)
        self.refresh_real_stats()

        # Verificación de actualizaciones en segundo plano
        QTimer.singleShot(5000, lambda: self._lanzar_hilo(self._verificar_actualizaciones_bg))
        
        gc.collect()
        return False

    def _warmup_system_bg(self):
        """Hilo de calentamiento para detectar versiones y dependencias sin bloquear la UI"""
        self._detectar_version_php()
        # Usar InvokeMethod para disparar el diálogo de dependencias en el hilo principal si es necesario
        QtCore.QMetaObject.invokeMethod(self, "check_environment_dependencies", Qt.ConnectionType.QueuedConnection)

    def poll_services_status(self):
        """Inicia la verificación de servicios en un hilo secundario"""
        self._lanzar_hilo(self._poll_services_worker)

    def _poll_services_worker(self):
        """Hilo trabajador que consulta systemd"""
        status_results = {}
        for srv in self.service_status_dots.keys():
            res = subprocess.run(["systemctl", "is-active", srv], capture_output=True, text=True)
            status_results[srv] = "#00ffcc" if res.stdout.strip() == "active" else "#ff4444"
        
        # Retornar resultados al hilo principal para actualizar la UI
        QtCore.QMetaObject.invokeMethod(self, "_update_status_dots_ui", 
                                      Qt.ConnectionType.QueuedConnection,
                                      QtCore.Q_ARG(dict, status_results))

    @QtCore.pyqtSlot(dict)
    def _update_status_dots_ui(self, results):
        """Actualiza los indicadores visuales (Solo hilo principal)"""
        for srv, color in results.items():
            if srv in self.service_status_dots:
                self.service_status_dots[srv].setStyleSheet(
                    f"background-color: {color}; border-radius: 6px; border: 1px solid white;"
                )

    @QtCore.pyqtSlot(str)
    def _update_php_selector_ui(self, text):
        """Actualiza el selector de PHP de forma segura (Solo hilo principal)"""
        self.php_sel.clear()
        self.php_sel.addItem(text)

    def _obtener_pixmap(self, ruta, w, h):
        """Retorna un QPixmap escalado desde caché para ahorrar RAM (Adaptado de GTK)."""
        cache_key = (ruta, w, h)
        if cache_key not in self.pixmap_cache:
            try:
                pixmap = QtGui.QPixmap(ruta)
                if not pixmap.isNull():
                    self.pixmap_cache[cache_key] = pixmap.scaled(
                        w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    return None
            except:
                return None
        return self.pixmap_cache.get(cache_key)

    def _detectar_version_php(self):
        """Detecta la versión de PHP actual mediante el binario del sistema."""
        try:
            res = subprocess.run(["php", "-r", "echo PHP_VERSION;"], capture_output=True, text=True)
            self.version_php_actual = res.stdout.strip()
        except:
            self.version_php_actual = "N/A"

        # Sincronizar con la UI de forma segura
        text = f"PHP Unit: {self.version_php_actual}" if self.version_php_actual != "N/A" else "PHP: NOT DETECTED"
        QtCore.QMetaObject.invokeMethod(self, "_update_php_selector_ui", 
                                      Qt.ConnectionType.QueuedConnection, 
                                      QtCore.Q_ARG(str, text))
        self.yui.log(f"PHP Engine: {self.version_php_actual} detected.", "#00ccff")

    def conectar_cursor_mano(self, widget):
        """Añade interactividad: cursor de mano, sonido de hover y sonido de click."""
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.installEventFilter(self)
        if isinstance(widget, QPushButton):
            widget.clicked.connect(self._play_click_sound)

    def eventFilter(self, obj, event):
        """Gestiona sonidos de hover para elementos interactivos."""
        if event.type() == QtCore.QEvent.Type.Enter:
            if hasattr(self, 'snd_hover') and self.snd_hover:
                self.snd_hover.stop()
                self.snd_hover.play()
        return super().eventFilter(obj, event)

    def _play_click_sound(self):
        """Reproduce el sonido de confirmación de SAO."""
        if hasattr(self, 'snd_click') and self.snd_click:
            self.snd_click.stop()
            self.snd_click.play()

    def _lanzar_hilo(self, funcion, args=()):
        """Ejecuta tareas en segundo plano para no congelar la UI."""
        threading.Thread(target=funcion, args=args, daemon=True).start()

    def _verificar_actualizaciones_bg(self):
        """Verifica actualizaciones de paquetes en segundo plano."""
        # Sincronización silenciosa de pacman
        self.run_cmd(["pacman", "-Sy"], use_sudo=True, capture=True)
        res = subprocess.run(["pacman", "-Qu"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            self.yui.log("System Alert: New updates detected in repositories.", "#ff7f00")

    def add_to_system_menu(self):
        """Crea un archivo .desktop para integrar el panel en el menú de aplicaciones de Linux"""
        try:
            script_path = os.path.abspath(__file__)
            desktop_dir = os.path.expanduser("~/.local/share/applications/")
            icon_src = os.path.join(os.path.dirname(script_path), "assets", "icon.png")
            icon_theme_dir = os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps/")
            
            # Asegurar que los directorios existen
            os.makedirs(desktop_dir, exist_ok=True)
            os.makedirs(icon_theme_dir, exist_ok=True)
            
            if os.path.exists(icon_src):
                icon_dest = os.path.join(icon_theme_dir, "sao-server.png")
                if not os.path.exists(icon_dest) or os.path.getmtime(icon_src) != os.path.getmtime(icon_dest):
                    shutil.copy2(icon_src, icon_dest)
                icon_entry = "sao-server"
            else:
                icon_entry = icon_src
            
            file_path = os.path.join(desktop_dir, "sao-server.desktop")
            content = f"""[Desktop Entry]
Name=SAO Server Panel
Exec=python3 {script_path}
Icon={icon_entry}
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

    def remove_from_system_menu(self):
        desktop_path = os.path.expanduser("~/.local/share/applications/sao-server.desktop")
        if os.path.exists(desktop_path):
            os.remove(desktop_path)
            self.yui.log("Acceso directo eliminado del menú.", "#ff4444")
        else:
            self.yui.log("No se encontró acceso directo para eliminar.", "#ff7f00")

    def show_about_modal(self):
        """Llamada a la modal de información del sistema"""
        AboutDialog(self).exec()

    def show_options_menu(self):
        t = TRANSLATIONS[self.idioma]
        menu = QMenu(self)
        # Aplicamos un estilo específico al menú para que sea coherente con el panel
        menu.setStyleSheet("""
            QMenu { 
                background-color: rgba(20, 20, 30, 0.95); 
                border: 1px solid #00ffcc; 
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item { 
                padding: 8px 25px; 
                color: #ffffff; 
                border-radius: 4px; 
            }
            QMenu::item:selected { 
                background-color: rgba(0, 255, 204, 0.2); 
                color: #00ffcc; 
            }
            QMenu::separator { 
                height: 1px; 
                background: rgba(255, 255, 255, 0.1); 
                margin: 5px 0; 
            }
        """)
        
        # Acciones mejoradas con lógica de "Añadir/Quitar"
        root_act = menu.addAction(t["opt_root"])
        app_menu_act = menu.addAction(t["opt_add"])
        rm_menu_act = menu.addAction(t["opt_rm"])
        php_act = menu.addAction(t["opt_php"])
        hide_act = menu.addAction(t["opt_hide"])
        sync_act = menu.addAction(t["opt_sync"])
        update_act = menu.addAction(t["opt_update_panel"])
        save_token_act = menu.addAction(t["opt_save_token"])
        repair_act = menu.addAction(t["opt_repair_panel"])
        clear_act = menu.addAction(t["opt_clear"])
        lang_act = menu.addAction(t["lang_menu"])
        menu.addSeparator()
        about_act = menu.addAction(t["opt_about"])
        
        # Ejecutar menú
        action = menu.exec(self.btn_menu.mapToGlobal(QtCore.QPoint(0, self.btn_menu.height())))
        
        # Lógica de acciones
        if action == root_act: self.open_localhost()
        elif action == app_menu_act: self.add_to_system_menu()
        elif action == rm_menu_act: self.remove_from_system_menu() # Nueva función
        elif action == php_act: self.open_php_config()
        elif action == hide_act: self.hide()
        elif action == sync_act: self.sync_web_folder_action()
        elif action == update_act: self.sync_repository()
        elif action == save_token_act: self.save_git_token_dialog()
        elif action == repair_act: self.repair_panel()
        elif action == clear_act: self.yui.terminal.clear()
        elif action == lang_act: self.toggle_language()
        elif action == about_act: self.show_about_modal() # Llamada a la nueva modal mejorada

    def sync_web_folder_action(self):
        """Acción de alto nivel para sincronizar configuración y permisos."""
        if not self.get_sudo_auth(): return
        self.yui.log("SYNC: Starting background web synchronization...", "#00ccff")
        self._lanzar_hilo(self._tarea_sync_web_bg)

    def _tarea_sync_web_bg(self):
        """Tarea en segundo plano para evitar congelamiento durante la sincronización total"""
        target_path = self.dir_proyectos
        self.setup_localhost_index()
        
        conf_ok = self.configure_apache_for_path(target_path)
        perm_ok = self.fix_permissions(target_path)
        self.update_apache_config()
        
        if conf_ok and perm_ok:
            self.run_cmd(["systemctl", "restart", "httpd"], use_sudo=True)
            self.yui.log("SYNC COMPLETE: Apache is now serving the new root.", "#00ffcc")
        else:
            self.yui.log("SYNC ERROR: Process failed.", "#ff4444")

    def closeEvent(self, event):
        diag = CloseSelectionDialog(self)
        result = diag.exec()
        
        if result == 1: # Detener y Salir
            self.guardar_ajustes_sao()
            self.log_out_stop()
            event.accept()
        elif result == 2: # Solo Salir
            self.guardar_ajustes_sao()
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
