import os
from datetime import datetime
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from sao_tasks import version_info


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 300)
        self.setObjectName("DependencyDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("SAO-SERVER - SYSTEM INFO")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffcc; letter-spacing: 2px;")

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet("background: transparent; color: #ff4444; font-size: 16px; border: none;")
        btn_close.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_close)
        layout.addLayout(header)

        layout.addSpacing(20)

        creator_row = QHBoxLayout()

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setStyleSheet("border: 2px solid #00ffcc; border-radius: 30px; background: rgba(0,0,0,0.3);")
        self.avatar_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.on_avatar_loaded)
        self.manager.get(QNetworkRequest(QtCore.QUrl("https://github.com/Slashdog29.png")))

        info_vbox = QVBoxLayout()
        creator_label = QLabel("CREATOR: <span style='color: #00ffcc; font-weight: bold;'>Slashdog29</span>")
        creator_label.setStyleSheet("font-size: 14px;")
        link_label = QLabel("<a href='https://github.com/Slashdog29/SAO-Server' style='color: #00ffcc; text-decoration: none;'>github.com/Slashdog29/SAO-Server</a>")
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("font-size: 11px;")

        try:
            vi = version_info.get_panel_info()
            ver_txt = f"Version: {vi.get('version','n/a')} | {vi.get('branch','')}@{vi.get('commit','') or 'n/a'}"
            ver_label = QLabel(ver_txt)
            ver_label.setStyleSheet("font-size: 11px; color: #00ffcc;")
            info_vbox.addWidget(ver_label)
        except Exception:
            pass

        info_vbox.addWidget(creator_label)
        info_vbox.addWidget(link_label)

        creator_row.addWidget(self.avatar_label)
        creator_row.addLayout(info_vbox)
        creator_row.addStretch()
        layout.addLayout(creator_row)

        layout.addSpacing(30)

        lang_label = QLabel("COMPOSITION ANALYSIS:")
        lang_label.setStyleSheet("font-size: 9px; color: #555; font-weight: bold;")
        layout.addWidget(lang_label)

        lang_bar = QHBoxLayout()
        lang_bar.setSpacing(2)

        segments = self.calculate_repo_languages()
        if not segments:
            segments = [("#3776ab", 100, "Python")]

        for color, weight, name in segments:
            seg = QFrame()
            seg.setFixedHeight(8)
            seg.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
            lang_bar.addWidget(seg, int(weight))

        layout.addLayout(lang_bar)

        legend_layout = QHBoxLayout()
        for color, _, name in segments:
            item = QLabel(f"<span style='color: {color};'>●</span> {name}")
            item.setStyleSheet("font-size: 9px; color: #bbb;")
            legend_layout.addWidget(item)
        layout.addLayout(legend_layout)
        layout.addStretch()

    def calculate_repo_languages(self):
        extensions_map = {
            '.py': ('#3776ab', 'Python'),
            '.qss': ('#007acc', 'CSS/QSS'),
            '.css': ('#007acc', 'CSS/QSS'),
            '.sh': ('#ffcc00', 'Shell'),
            '.cpp': ('#41cd52', 'Qt/C++'),
            '.h': ('#41cd52', 'Qt/C++'),
            '.md': ('#555555', 'Markdown')
        }

        stats = {}
        total_project_size = 0
        root_path = os.path.dirname(os.path.abspath(__file__))

        for root, dirs, files in os.walk(root_path):
            if '.git' in dirs: dirs.remove('.git')
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions_map:
                    color, name = extensions_map[ext]
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                    except Exception:
                        size = 0
                    if name not in stats: stats[name] = [color, 0]
                    stats[name][1] += size
                    total_project_size += size

        if total_project_size == 0: return []

        dynamic_segments = []
        for name, (color, size) in stats.items():
            percentage = (size / total_project_size) * 100
            dynamic_segments.append((color, percentage, name))
        return sorted(dynamic_segments, key=lambda x: x[1], reverse=True)

    def on_avatar_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                size = 60
                rounded_pixmap = QtGui.QPixmap(size, size)
                rounded_pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
                path = QtGui.QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, size, size, pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding, QtCore.Qt.TransformationMode.SmoothTransformation))
                painter.end()
                self.avatar_label.setPixmap(rounded_pixmap)
        reply.deleteLater()
