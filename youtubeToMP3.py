import sys
import os
import re
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QRadioButton, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont
import qdarkstyle


class DownloadThread(QThread):
    progress_changed = pyqtSignal(int)
    finished = pyqtSignal()
    status_changed = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            self.status_changed.emit(line.strip())
            match = re.search(r'(\d{1,3}\.\d)%', line)
            if match:
                progress = float(match.group(1))
                self.progress_changed.emit(int(progress))

        process.wait()
        self.finished.emit()


class YouTubeDownloaderUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube MP3/MP4 Downloader")
        self.setGeometry(100, 100, 400, 350)
        self.initUI()

    def initUI(self):
        font = QFont("Segoe UI", 10)

        url_label = QLabel("YouTube URL:")
        url_label.setFont(font)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/...")
        self.url_input.setFont(font)

        format_group = QGroupBox("Format")
        self.mp3_radio = QRadioButton("MP3")
        self.mp4_radio = QRadioButton("MP4")
        self.mp4_radio.setChecked(True)

        format_layout = QHBoxLayout()
        format_layout.addWidget(self.mp3_radio)
        format_layout.addWidget(self.mp4_radio)
        format_group.setLayout(format_layout)

        quality_label = QLabel("MP4 Kalitesi:")
        quality_label.setFont(font)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Best", "1080p", "720p", "480p", "144p"])
        self.quality_combo.setFont(font)

        self.mp3_radio.toggled.connect(self.toggle_quality_selection)

        location_label = QLabel("Kaydetme Konumu:")
        location_label.setFont(font)

        self.location_input = QLineEdit()
        self.location_input.setFont(font)
        self.location_input.setPlaceholderText("Bir klasör seçin...")

        browse_button = QPushButton("Gözat")
        browse_button.setFont(font)
        browse_button.clicked.connect(self.browse_folder)

        location_layout = QHBoxLayout()
        location_layout.addWidget(self.location_input)
        location_layout.addWidget(browse_button)

        download_button = QPushButton("İndir")
        download_button.setFont(font)
        download_button.clicked.connect(self.download)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Durum: Hazır")
        self.status_label.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(format_group)
        layout.addWidget(quality_label)
        layout.addWidget(self.quality_combo)
        layout.addWidget(location_label)
        layout.addLayout(location_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(download_button)

        self.setLayout(layout)

    def toggle_quality_selection(self):
        self.quality_combo.setEnabled(self.mp4_radio.isChecked())

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç", "")
        if folder:
            self.location_input.setText(folder)

    def download(self):
        url = self.url_input.text()
        format_selected = "mp3" if self.mp3_radio.isChecked() else "mp4"
        quality = self.quality_combo.currentText()
        download_path = self.location_input.text()

        if not url.strip():
            QMessageBox.warning(self, "Hata", "Lütfen bir YouTube URL'si girin.")
            return

        if not download_path:
            QMessageBox.warning(self, "Hata", "Lütfen bir kaydetme konumu seçin.")
            return

        if format_selected == "mp3":
            cmd = f'yt-dlp -P "{download_path}" -x --audio-format mp3 "{url}"'
        elif format_selected == "mp4":
            if quality == "Best":
                cmd = f'yt-dlp -P "{download_path}" "{url}"'
            else:
                resolution = quality.replace("p", "")
                cmd = f'yt-dlp -P "{download_path}" -S res:{resolution} "{url}"'

        self.progress_bar.setValue(0)
        self.status_label.setText("İndirme başlatılıyor...")

        self.download_thread = DownloadThread(cmd)
        self.download_thread.progress_changed.connect(self.progress_bar.setValue)
        self.download_thread.status_changed.connect(lambda text: self.status_label.setText(f"Durum: {text}"))
        self.download_thread.finished.connect(lambda: QMessageBox.information(self, "Bitti", "İndirme tamamlandı."))
        self.download_thread.finished.connect(lambda: self.status_label.setText("Durum: Tamamlandı"))
        self.download_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())  # Dark tema
    window = YouTubeDownloaderUI()
    window.show()
    sys.exit(app.exec_())