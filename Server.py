import sys
import subprocess
import os
import time
from datetime import datetime

# --- BLOQUE DE AUTO-INSTALACIÓN (PACMAN NATIVO PARA ARCH) ---
def ensure_dependencies():
    try:
        import psutil
        from PyQt6 import QtWidgets, QtCore, QtGui
    except ImportError:
        print("\n[SYSTEM] INITIATING NEURAL LINK SYNC...")
        try:
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "python-pyqt6", "python-psutil"], check=True)
            print("[SUCCESS] Sync Complete. Restarting Script...\n")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"[ERROR] Sync Failed: {e}")
            sys.exit(1)

ensure_dependencies()

import psutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QProgressBar, QTextEdit, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

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

class Kirito(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAO FORGE DIRECTORY")
        self.resize(1100, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)
        
        self.yui = YuiMonitor()
        self.init_ui()
        
        # Iniciar monitoreo de métricas reales
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.refresh_real_stats)
        self.stats_timer.start(1000)
        
        # Cargar versiones de PHP instaladas
        self.detect_php_versions()
        
        self.setStyleSheet(SAO_GLASS_QSS)
        self.yui.log("Neural Link Established. System Metrics: Online.")

    def init_ui(self):
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(35, 35, 35, 35)
        main_layout.setSpacing(20)

        # --- 1. ENCABEZADO (Métricas y Carpeta) ---
        header = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title = QLabel("SAO DIRECTORY v0.2/ SERVERS")
        title.setStyleSheet("font-size: 24px; font-weight: 900; letter-spacing: 5px;")

        self.btn_php_folder = QPushButton("📂 Abrir PHP*")
        self.btn_php_folder.setObjectName("FolderBtn")
        self.btn_php_folder.clicked.connect(self.open_php_dir)

        title_vbox.addWidget(title)
        title_vbox.addWidget(self.btn_php_folder)

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
        inv_layout = QHBoxLayout(inv_frame)

        self.php_sel = QComboBox()
        self.db_sel = QComboBox()
        self.db_sel.addItems(["MySQL 8.0", "PostgreSQL", "MariaDB"])
        
        inv_layout.addWidget(QLabel("INSTALLED PHP:"))
        inv_layout.addWidget(self.php_sel)
        inv_layout.addSpacing(40)
        inv_layout.addWidget(QLabel("DB ENGINE:"))
        inv_layout.addWidget(self.db_sel)
        inv_layout.addStretch()
        main_layout.addWidget(inv_frame)

        # --- 3. SERVICIOS Y ACCIONES GLOBALES ---
        mid_layout = QHBoxLayout()
        serv_vbox = QVBoxLayout()
        self.row_kirito = self.create_service_row("Kirito Unit (Apache/httpd)")
        self.row_asuna = self.create_service_row("Asuna Unit (Database)")
        
        global_btns = QHBoxLayout()
        self.btn_link_start = QPushButton("⚡ LINK START")
        self.btn_link_start.setObjectName("LinkStart")
        self.btn_link_start.setFixedHeight(50)
        self.btn_link_start.clicked.connect(lambda: self.yui.log("LINK START: Global initialization active.", "#00ffcc"))
        
        self.btn_log_out = QPushButton("🛑 LOG OUT")
        self.btn_log_out.setObjectName("LogOut")
        self.btn_log_out.setFixedHeight(50)
        self.btn_log_out.clicked.connect(lambda: self.yui.log("LOG OUT: Global termination active.", "#ff7f00"))
        
        global_btns.addWidget(self.btn_link_start)
        global_btns.addWidget(self.btn_log_out)

        serv_vbox.addWidget(self.row_kirito)
        serv_vbox.addWidget(self.row_asuna)
        serv_vbox.addLayout(global_btns)
        mid_layout.addLayout(serv_vbox, 65)

        tools_frame = QFrame()
        tools_frame.setObjectName("GlassCard")
        t_grid = QGridLayout(tools_frame)
        t_list = ["Fix Apache", "Verify DB", "Root Pass", "Repair Panel", "🔄 Sync"]
        for i, name in enumerate(t_list):
            btn = QPushButton(name)
            t_grid.addWidget(btn, i // 2, i % 2)

        mid_layout.addWidget(tools_frame, 35)
        main_layout.addLayout(mid_layout)

        # --- 4. TERMINAL YUI ---
        main_layout.addWidget(self.yui)

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

    def create_service_row(self, name):
        f = QFrame(); f.setObjectName("GlassCard")
        l = QHBoxLayout(f)
        dot = QLabel(); dot.setFixedSize(12, 12)
        dot.setStyleSheet("background-color: #ff4444; border-radius: 6px;")
        l.addWidget(dot)
        l.addWidget(QLabel(name.upper()))
        l.addStretch()
        l.addWidget(QPushButton("START"))
        l.addWidget(QPushButton("STOP"))
        return f

    def open_php_dir(self):
        # Abre el directorio de la versión seleccionada o /etc general
        selected = self.php_sel.currentText().lower().replace(" ", "").replace(".", "").replace("(systemdefault)", "")
        path = f"/etc/{selected}" if selected.startswith("php") else "/etc/php"
        
        if not os.path.exists(path): path = "/etc/" # Fallback

        self.yui.log(f"Accessing folder: {path}", "#ff7f00")
        subprocess.run(["xdg-open", path])

    def refresh_real_stats(self):
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Inter", 10))
    kirito_ui = Kirito()
    kirito_ui.show()
    sys.exit(app.exec())