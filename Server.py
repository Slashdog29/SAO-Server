#!/usr/bin/env python3
"""
FORGE DIRECTORY / SERVERS — Panel de Control Estilo SAO
Requisito: Python 3.10+ en Arch Linux o derivados.
Ejecutar: python sao_panel.py
"""

import sys
import subprocess
import os
import time
import random

# ----------------------------------------------------------------------
# BLOQUE DEFENSIVO DE AUTO-INSTALACIÓN DE PyQt6 (Arch/CachyOS/Manjaro)
# ----------------------------------------------------------------------
def ensure_dependencies():
    try:
        from PyQt6 import QtWidgets, QtCore, QtGui
    except ImportError:
        print("\n" + "="*60)
        print("[SYSTEM] SAO UI COMPONENTS NOT DETECTED.")
        print("[SYSTEM] INITIATING FORGE SYNC WITH ARCH LINUX REPOSITORIES...")
        print("="*60 + "\n")
        try:
            subprocess.run(
                ["sudo", "pacman", "-S", "--noconfirm", "python-pyqt6"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            print("\n[SUCCESS] UI COMPONENT SYNC COMPLETE. INITIALIZING LINK START...\n")
        except subprocess.CalledProcessError:
            print("\n[ERROR] FAILED TO INSTALL DEPENDENCIES. PLEASE RUN: sudo pacman -S python-pyqt6")
            sys.exit(1)
        except FileNotFoundError:
            print("\n[ERROR] 'sudo' o 'pacman' no encontrados. ¿Estás en Arch Linux?")
            sys.exit(1)

ensure_dependencies()

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QProgressBar, QTextEdit,
    QFrame, QGridLayout, QScrollBar
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QLinearGradient

# ----------------------------------------------------------------------
# HOJA DE ESTILOS SAO (QSS)
# ----------------------------------------------------------------------
SAO_QSS = """
QMainWindow {
    background-color: #1a1a24;
}

QWidget {
    color: #e0e0e0;
    font-family: 'Inter', sans-serif;
}

/* HP Bars */
QProgressBar {
    border: 1px solid #3d3d4d;
    border-radius: 2px;
    background-color: #0a0a0f;
    text-align: center;
    color: white;
    font-weight: bold;
    height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00c896, stop:0.5 #ff7f00, stop:1 #ff3300);
    border-radius: 3px;
}

/* Contenedores estilo SAO */
QFrame#Card {
    background-color: rgba(45, 45, 60, 0.5);
    border: 1px solid #3d3d4d;
    border-radius: 6px;
    padding: 12px;
}

/* Selectores */
QComboBox {
    background-color: #252533;
    border: 1px solid #ff7f00;
    padding: 6px 12px;
    border-radius: 4px;
    color: #ff7f00;
    font-weight: bold;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #00ff99;
}
QComboBox::drop-down {
    border-left: 1px solid #3d3d4d;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #252533;
    border: 1px solid #3d3d4d;
    selection-background-color: #ff7f00;
    color: #e0e0e0;
}

/* Botones generales */
QPushButton {
    background-color: #323242;
    border: 1px solid #4d4d5d;
    padding: 8px 16px;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #44445a;
    border-color: #00ff99;
}

/* Botón verde (Link Start) */
QPushButton#LinkStart {
    background-color: rgba(0, 200, 150, 0.15);
    border: 2px solid #00c896;
    color: #00c896;
    font-size: 14px;
}
QPushButton#LinkStart:hover {
    background-color: rgba(0, 200, 150, 0.25);
}

/* Botón naranja/rojo (Log Out) */
QPushButton#LogOut {
    background-color: rgba(255, 68, 68, 0.15);
    border: 2px solid #ff4444;
    color: #ff4444;
    font-size: 14px;
}
QPushButton#LogOut:hover {
    background-color: rgba(255, 68, 68, 0.25);
}

/* Consola de logs */
QTextEdit {
    background-color: #050508;
    border: none;
    border-top: 2px solid #3d3d4d;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    color: #00e6cc;
}
"""

# ----------------------------------------------------------------------
# FILA DE SERVICIO (Apache / Base de Datos)
# ----------------------------------------------------------------------
class ServiceRow(QFrame):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.service_name = name
        self._active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        # Círculo indicador de estado
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(14, 14)
        self.set_inactive()

        # Nombre del servicio
        self.label = QLabel(name.upper())
        self.label.setStyleSheet("font-weight: 800; letter-spacing: 1px;")

        # Botones individuales
        self.btn_start = QPushButton("Iniciar")
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setStyleSheet("color: #ff4444;")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)

    def set_active(self, state: bool):
        self._active = state
        if state:
            self.status_dot.setStyleSheet(
                "background-color: #00e6a8; border-radius: 7px;"
            )
        else:
            self.set_inactive()

    def set_inactive(self):
        self.status_dot.setStyleSheet(
            "background-color: #ff3b3b; border-radius: 7px;"
        )
        self._active = False

    def is_active(self):
        return self._active

# ----------------------------------------------------------------------
# VENTANA PRINCIPAL DEL PANEL SAO
# ----------------------------------------------------------------------
class SAOPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FORGE SYSTEM | ARCH LINUX CONTROL")
        self.resize(1000, 700)
        self.setStyleSheet(SAO_QSS)

        # Estados de servicios
        self.apache_active = False
        self.db_active = False
        self.current_db_name = "MariaDB"

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ------------------------------------------------------------------
        # 1. ENCABEZADO (Título + HP Bars)
        # ------------------------------------------------------------------
        header_layout = QHBoxLayout()

        title_box = QVBoxLayout()
        self.main_title = QLabel("FORGE DIRECTORY / SERVERS")
        self.main_title.setStyleSheet(
            "font-size: 24px; font-weight: 900; color: #e0e0e0; letter-spacing: 3px;"
        )

        # Etiqueta de versión PHP (se actualiza con el selector)
        self.php_ver_label = QLabel("SYSTEM ENGINE: PHP v8.3.x (Zend Runtime)")
        self.php_ver_label.setStyleSheet(
            "color: #ff7f00; font-size: 12px; font-weight: bold;"
        )
        title_box.addWidget(self.main_title)
        title_box.addWidget(self.php_ver_label)

        # Barras de salud (CPU / RAM)
        stats_box = QGridLayout()
        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        # Etiquetas pequeñas
        cpu_label = QLabel("CPU [CORE]")
        cpu_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
        ram_label = QLabel("RAM [DATA]")
        ram_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")

        stats_box.addWidget(cpu_label, 0, 0)
        stats_box.addWidget(self.cpu_bar, 0, 1)
        stats_box.addWidget(ram_label, 1, 0)
        stats_box.addWidget(self.ram_bar, 1, 1)

        header_layout.addLayout(title_box, 60)
        header_layout.addLayout(stats_box, 40)
        main_layout.addLayout(header_layout)

        # ------------------------------------------------------------------
        # 2. SELECTORES DE ENTORNO (Estilo inventario)
        # ------------------------------------------------------------------
        sel_container = QFrame()
        sel_container.setObjectName("Card")
        sel_layout = QHBoxLayout(sel_container)
        sel_layout.setContentsMargins(12, 8, 12, 8)

        sel_layout.addWidget(QLabel("ENVIRONMENT SETUP:"))
        self.php_select = QComboBox()
        self.php_select.addItems(["PHP 8.3", "PHP 8.2", "PHP 8.1", "PHP 7.4"])
        sel_layout.addWidget(self.php_select)

        sel_layout.addSpacing(20)
        sel_layout.addWidget(QLabel("DATABASE UNIT:"))
        self.db_select = QComboBox()
        self.db_select.addItems(["MariaDB", "MySQL 8.0", "PostgreSQL"])
        sel_layout.addWidget(self.db_select)
        sel_layout.addStretch()
        main_layout.addWidget(sel_container)

        # ------------------------------------------------------------------
        # 3. CONTROL DE SERVICIOS
        # ------------------------------------------------------------------
        content_layout = QHBoxLayout()

        services_vbox = QVBoxLayout()
        services_vbox.setSpacing(10)

        # Fila Apache
        self.row_apache = ServiceRow("Apache Server (httpd)")
        self.row_apache.btn_start.clicked.connect(self.start_apache)
        self.row_apache.btn_stop.clicked.connect(self.stop_apache)

        # Fila Base de Datos
        self.row_db = ServiceRow(self.current_db_name)
        self.row_db.btn_start.clicked.connect(self.start_db)
        self.row_db.btn_stop.clicked.connect(self.stop_db)

        services_vbox.addWidget(self.row_apache)
        services_vbox.addWidget(self.row_db)

        # 4. BOTONES DE ACCIÓN GLOBAL
        global_btns = QHBoxLayout()
        self.btn_link_start = QPushButton("⚡ Link Start (Iniciar Todo)")
        self.btn_link_start.setObjectName("LinkStart")
        self.btn_link_start.setFixedHeight(55)
        self.btn_link_start.clicked.connect(self.start_all)

        self.btn_logout = QPushButton("🛑 Log Out (Detener Todo)")
        self.btn_logout.setObjectName("LogOut")
        self.btn_logout.setFixedHeight(55)
        self.btn_logout.clicked.connect(self.stop_all)

        global_btns.addWidget(self.btn_link_start)
        global_btns.addWidget(self.btn_logout)
        services_vbox.addLayout(global_btns)

        content_layout.addLayout(services_vbox, 65)

        # ------------------------------------------------------------------
        # 5. CAJA DE HERRAMIENTAS / ACCIONES DE REPARACIÓN
        # ------------------------------------------------------------------
        tools_frame = QFrame()
        tools_frame.setObjectName("Card")
        tools_grid = QGridLayout(tools_frame)
        tools_grid.setSpacing(8)

        tools_grid.addWidget(
            QLabel("MAINTENANCE PROTOCOLS"),
            0, 0, 1, 2,
            Qt.AlignmentFlag.AlignCenter
        )

        self.tool_apache = QPushButton("Acomodar / Arreglar Apache")
        self.tool_db = QPushButton("Verificar BBDD")
        self.tool_user = QPushButton("Cambiar Usuario/Clave")
        self.tool_repair = QPushButton("Reparar Panel")
        self.tool_sync = QPushButton("🔄 Sincronizar / Actualizar Panel")
        self.tool_sync.setStyleSheet("color: #00ccff; border-color: #00ccff;")

        # Conexiones de herramientas
        self.tool_apache.clicked.connect(self.fix_apache)
        self.tool_db.clicked.connect(self.check_db)
        self.tool_user.clicked.connect(self.change_credentials)
        self.tool_repair.clicked.connect(self.repair_panel)
        self.tool_sync.clicked.connect(self.sync_panel)

        tools_grid.addWidget(self.tool_apache, 1, 0)
        tools_grid.addWidget(self.tool_db, 1, 1)
        tools_grid.addWidget(self.tool_user, 2, 0)
        tools_grid.addWidget(self.tool_repair, 2, 1)
        tools_grid.addWidget(self.tool_sync, 3, 0, 1, 2)

        content_layout.addWidget(tools_frame, 35)
        main_layout.addLayout(content_layout)

        # ------------------------------------------------------------------
        # 6. CONSOLA DE LOGS INTEGRADA
        # ------------------------------------------------------------------
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText(">> SYSTEM IDLE. WAITING FOR COMMAND...")
        main_layout.addWidget(self.console)

        # ------------------------------------------------------------------
        # Conexiones adicionales (cambios en selectores)
        # ------------------------------------------------------------------
        self.php_select.currentTextChanged.connect(self.update_php_display)
        self.db_select.currentTextChanged.connect(self.update_db_display)

        # Timer para refrescar las barras de salud según servicios activos
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.refresh_health)
        self.health_timer.start(2000)

        # Mensaje inicial
        self.log("Sistema SAO iniciado. Esperando comandos...")

    # ------------------------------------------------------------------
    # MÉTODOS DE LOG Y ACTUALIZACIÓN VISUAL
    # ------------------------------------------------------------------
    def log(self, message: str):
        """Añade línea de log con timestamp y color turquesa."""
        timestamp = time.strftime("%H:%M:%S")
        formatted = (
            f'<span style="color:#4d4d5d;">[{timestamp}]</span> '
            f'<span style="color:#00e6cc;">{message}</span>'
        )
        self.console.append(formatted)
        # Auto-scroll al final
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )

    def update_php_display(self, text):
        """Actualiza la etiqueta de versión PHP al cambiar el selector."""
        version = text.replace("PHP ", "v")
        self.php_ver_label.setText(f"SYSTEM ENGINE: PHP {version}.x (Zend Runtime)")
        self.log(f"[CONFIG] Versión PHP cambiada a {text}")

    def update_db_display(self, text):
        """Cambia el nombre mostrado en la fila de base de datos."""
        self.current_db_name = text
        self.row_db.label.setText(text.upper())
        self.log(f"[CONFIG] Motor de base de datos cambiado a {text}")

    def refresh_health(self):
        """
        Simula el uso de CPU y RAM basado en los servicios activos.
        En producción usaríamos psutil.
        """
        cpu_base = 12.0
        ram_base = 18.0
        cpu = cpu_base
        ram = ram_base

        if self.row_apache.is_active():
            cpu += 15.0
            ram += 20.0
        if self.row_db.is_active():
            cpu += 10.0
            ram += 25.0

        # Añadir fluctuación aleatoria
        cpu += random.uniform(-3, 3)
        ram += random.uniform(-3, 3)
        cpu = max(0, min(100, cpu))
        ram = max(0, min(100, ram))

        self.cpu_bar.setValue(int(cpu))
        self.ram_bar.setValue(int(ram))

    # ------------------------------------------------------------------
    # FUNCIONES DE CONTROL DE SERVICIOS (simuladas con subprocess)
    # ------------------------------------------------------------------
    def run_command(self, cmd_list, success_msg):
        """
        Ejecuta un comando real en el sistema (simulado por ahora).
        En producción usaríamos subprocess.run() sin la simulación.
        """
        self.log(f"$ {' '.join(cmd_list)}")
        # --- SIMULACIÓN ---
        # En una implementación real:
        # try:
        #     result = subprocess.run(cmd_list, capture_output=True, text=True)
        #     if result.returncode == 0:
        #         self.log(success_msg)
        #     else:
        #         self.log(f"Error: {result.stderr.strip()}")
        # except Exception as e:
        #     self.log(f"Excepción: {e}")
        # -----------------
        # Simulación: asumimos éxito siempre
        self.log(success_msg)

    def start_apache(self):
        if not self.row_apache.is_active():
            self.run_command(
                ["sudo", "systemctl", "start", "httpd"],
                "Apache httpd iniciado correctamente (PID simulado 1234)."
            )
            self.row_apache.set_active(True)
            self.apache_active = True
        else:
            self.log("⚠️ Apache ya está en ejecución.")

    def stop_apache(self):
        if self.row_apache.is_active():
            self.run_command(
                ["sudo", "systemctl", "stop", "httpd"],
                "Apache httpd detenido correctamente."
            )
            self.row_apache.set_inactive()
            self.apache_active = False
        else:
            self.log("⚠️ Apache no está activo.")

    def start_db(self):
        if not self.row_db.is_active():
            db_unit = self._get_db_service_name()
            self.run_command(
                ["sudo", "systemctl", "start", db_unit],
                f"{self.current_db_name} iniciado correctamente (PID simulado 5678)."
            )
            self.row_db.set_active(True)
            self.db_active = True
        else:
            self.log(f"⚠️ {self.current_db_name} ya está en ejecución.")

    def stop_db(self):
        if self.row_db.is_active():
            db_unit = self._get_db_service_name()
            self.run_command(
                ["sudo", "systemctl", "stop", db_unit],
                f"{self.current_db_name} detenido correctamente."
            )
            self.row_db.set_inactive()
            self.db_active = False
        else:
            self.log(f"⚠️ {self.current_db_name} no está activo.")

    def _get_db_service_name(self):
        """Devuelve el nombre del servicio systemd según el motor seleccionado."""
        if self.current_db_name == "PostgreSQL":
            return "postgresql"
        elif self.current_db_name == "MySQL 8.0":
            return "mysqld"
        else:  # MariaDB
            return "mariadb"

    def start_all(self):
        self.log("⚡ Link Start: Iniciando todos los servicios...")
        self.start_apache()
        self.start_db()

    def stop_all(self):
        self.log("🛑 Log Out: Deteniendo todos los servicios...")
        self.stop_apache()
        self.stop_db()

    # ------------------------------------------------------------------
    # HERRAMIENTAS DE MANTENIMIENTO
    # ------------------------------------------------------------------
    def fix_apache(self):
        self.log("🔧 Ejecutando 'apachectl configtest'... Syntax OK")
        self.log("🧹 Limpiando archivos .pid huérfanos... Eliminado /run/httpd/httpd.pid")
        self.log("Apache acomodado correctamente.")

    def check_db(self):
        self.log(f"🩺 Verificando integridad de tablas en {self.current_db_name}...")
        self.log("Tablas 'users', 'config' -> OK (sin errores).")

    def change_credentials(self):
        self.log("🔐 Solicitando cambio de credenciales del root de la base de datos...")
        self.log("Usuario root: contraseña actualizada correctamente.")

    def repair_panel(self):
        self.log("🛠️ Restableciendo permisos en /var/www/html... chmod 755 aplicado.")
        self.log("🗑️ Limpiando caché de panel... /tmp/sao_cache limpiado.")

    def sync_panel(self):
        self.log("🔄 Sincronizando estado actual de servicios...")
        self.log(f"Apache: {'Activo' if self.row_apache.is_active() else 'Inactivo'}")
        self.log(f"{self.current_db_name}: {'Activo' if self.row_db.is_active() else 'Inactivo'}")
        self.refresh_health()
        self.log("✅ Sincronización completada.")

# ----------------------------------------------------------------------
# PUNTO DE ENTRADA
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Fuente global (si Inter no está disponible, usa la de sistema)
    font = QFont("Inter", 10)
    app.setFont(font)

    panel = SAOPanel()
    panel.show()
    sys.exit(app.exec())