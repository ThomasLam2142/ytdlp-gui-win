from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QMovie, QPixmap, QColor
import sys
import os
from yt_dlp import YoutubeDL
import imageio_ffmpeg

class FetchFormatsThread(QThread):
    formats_ready = Signal(dict)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        ydl_opts = {}
        video_formats = {}
        audio_formats = {}
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                for fmt in info.get('formats', []):
                    vcodec = fmt.get('vcodec', 'none')
                    acodec = fmt.get('acodec', 'none')
                    width = fmt.get('width')
                    height = fmt.get('height')
                    ext = fmt.get('ext')
                    format_id = fmt.get('format_id')
                    abr = fmt.get('abr')
                    # Video formats (with or without audio)
                    if vcodec != 'none' and width and height and ext and format_id:
                        res = f"{width}x{height}"
                        key = (res, ext)
                        if key not in video_formats:
                            video_formats[key] = format_id
                    # Audio only formats
                    elif vcodec == 'none' and acodec != 'none' and ext and format_id:
                        desc = f"{ext}"
                        if abr:
                            desc += f" {abr}kbps"
                        if desc not in audio_formats:
                            audio_formats[desc] = format_id
        except Exception as e:
            pass
        self.formats_ready.emit({'video': video_formats, 'audio': audio_formats})

class DownloadThread(QThread):
    finished = Signal()

    def __init__(self, url, format_id):
        super().__init__()
        self.url = url
        self.format_id = format_id

    def run(self):
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': self.format_id,
            'ffmpeg_location': ffmpeg_path
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        self.finished.emit()

class MyWidget(QWidget):    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Youtube Downloader')
        self.resize(800, 900)

        main_layout = QVBoxLayout()
        main_layout.addStretch(1)

        # Add logo at the top
        logo_label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "assets", "logo.png")
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaledToHeight(300, Qt.SmoothTransformation)  
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignHCenter)
        main_layout.addWidget(logo_label)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignHCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        main_layout.addWidget(self.status_label)

        # Resolution, video format, and audio format dropdowns
        self.resolution_combo = QComboBox()
        self.resolution_combo.setEnabled(False)
        self.video_format_combo = QComboBox()
        self.video_format_combo.setEnabled(False)
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.setEnabled(False)
        main_layout.addWidget(QLabel("Resolution:"))
        main_layout.addWidget(self.resolution_combo)
        main_layout.addWidget(QLabel("Video Format:"))
        main_layout.addWidget(self.video_format_combo)
        main_layout.addWidget(QLabel("Audio Format:"))
        main_layout.addWidget(self.audio_format_combo)

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignHCenter)

        self.label = QLabel("Enter URL Below")
        self.input = QLineEdit()
        self.input.setFixedWidth(600)
        self.input.textChanged.connect(self.on_url_changed)

        self.check_button = QPushButton("Check Formats")
        self.check_button.clicked.connect(self.on_check_formats)
        self.download_button = QPushButton("Download")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.on_download)

        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignHCenter)
        spinner_size = 48
        self.spinner.setFixedSize(spinner_size, spinner_size)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spinner_path = os.path.join(script_dir, "assets", "spinner.gif")
        self.movie = QMovie(spinner_path)
        self.movie.setScaledSize(QSize(spinner_size, spinner_size))
        self.spinner.setMovie(self.movie)
        # Transparent placeholder pixmap
        transparent_pixmap = QPixmap(spinner_size, spinner_size)
        transparent_pixmap.fill(QColor(0, 0, 0, 0))
        self.transparent_spinner = transparent_pixmap
        self.spinner.setPixmap(self.transparent_spinner)
        self.spinner.setVisible(True)

        center_layout.addWidget(self.label, alignment=Qt.AlignHCenter)
        center_layout.addWidget(self.input, alignment=Qt.AlignHCenter)
        center_layout.addWidget(self.check_button, alignment=Qt.AlignHCenter)
        center_layout.addWidget(self.download_button, alignment=Qt.AlignHCenter)
        center_layout.addWidget(self.spinner, alignment=Qt.AlignHCenter)

        main_layout.addLayout(center_layout)
        main_layout.addStretch(1)

        self.setLayout(main_layout)

        self.video_formats = {}
        self.audio_formats = {}
        self.checked_url = None
        self.resolution_combo.currentIndexChanged.connect(self.on_resolution_selected)
        self.video_format_combo.currentIndexChanged.connect(self.on_video_format_selected)
        self.audio_format_combo.currentIndexChanged.connect(self.on_audio_format_selected)

    def on_url_changed(self):
        self.resolution_combo.clear()
        self.resolution_combo.setEnabled(False)
        self.video_format_combo.clear()
        self.video_format_combo.setEnabled(False)
        self.audio_format_combo.clear()
        self.audio_format_combo.setEnabled(False)
        self.download_button.setEnabled(False)
        self.checked_url = None
        self.status_label.setText("")

    def on_check_formats(self):
        url = self.input.text()
        if url:
            self.status_label.setText("Checking formats...")
            self.check_button.setEnabled(False)
            self.show_spinner()
            self.resolution_combo.clear()
            self.resolution_combo.setEnabled(False)
            self.video_format_combo.clear()
            self.video_format_combo.setEnabled(False)
            self.audio_format_combo.clear()
            self.audio_format_combo.setEnabled(False)
            self.download_button.setEnabled(False)
            self.fetch_thread = FetchFormatsThread(url)
            self.fetch_thread.formats_ready.connect(self.populate_format_dropdowns)
            self.fetch_thread.start()

    def populate_format_dropdowns(self, formats):
        self.hide_spinner()
        self.check_button.setEnabled(True)
        self.checked_url = self.input.text() if formats['video'] or formats['audio'] else None
        self.video_formats = formats['video']
        self.audio_formats = formats['audio']
        if self.video_formats:
            resolutions = sorted({k[0] for k in self.video_formats.keys()}, key=lambda x: int(x.split('x')[1]), reverse=True)
            self.resolution_combo.clear()
            self.resolution_combo.addItems(resolutions)
            self.resolution_combo.setEnabled(True)
        if self.audio_formats:
            self.audio_format_combo.clear()
            self.audio_format_combo.addItems(list(self.audio_formats.keys()))
            self.audio_format_combo.setEnabled(True)
        self.status_label.setText("Select resolution, video format, and audio format, then click Download.")
        self.update_download_button_state()

    def on_resolution_selected(self):
        # Populate video format combo based on selected resolution
        res = self.resolution_combo.currentText()
        video_exts = [k[1] for k in self.video_formats.keys() if k[0] == res]
        self.video_format_combo.clear()
        self.video_format_combo.addItems(video_exts)
        self.video_format_combo.setEnabled(bool(video_exts))
        self.update_download_button_state()

    def on_video_format_selected(self):
        self.update_download_button_state()

    def on_audio_format_selected(self):
        self.update_download_button_state()

    def update_download_button_state(self):
        res = self.resolution_combo.currentText()
        v_ext = self.video_format_combo.currentText()
        a_fmt = self.audio_format_combo.currentText()
        valid = bool(self.checked_url and res and v_ext and a_fmt)
        self.download_button.setEnabled(valid)

    def on_download(self):
        res = self.resolution_combo.currentText()
        v_ext = self.video_format_combo.currentText()
        a_fmt = self.audio_format_combo.currentText()
        video_key = (res, v_ext)
        audio_key = a_fmt
        video_format_id = self.video_formats.get(video_key)
        audio_format_id = self.audio_formats.get(audio_key)
        url = self.checked_url
        if video_format_id and audio_format_id and url:
            self.status_label.setText("Downloading...")
            self.download_button.setEnabled(False)
            self.show_spinner()
            self.thread = DownloadThread(url, f"{video_format_id}+{audio_format_id}")
            self.thread.finished.connect(self.on_download_finished)
            self.thread.start()

    def on_download_finished(self):
        self.download_button.setEnabled(True)
        self.hide_spinner()
        self.status_label.setText("Download Complete!")

    def show_spinner(self):
        self.spinner.setMovie(self.movie)
        self.movie.start()
        self.spinner.setVisible(True)

    def hide_spinner(self):
        self.movie.stop()
        self.spinner.setPixmap(self.transparent_spinner)
        self.spinner.setVisible(True)

app = QApplication(sys.argv)

dark_stylesheet = """
QWidget {
    background-color: #232629;
    color: #F0F0F0;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2b2b2b;
    color: #F0F0F0;
    border: 1px solid #444;
    font-size: 18pt;
}
QPushButton {
    background-color: #444;
    color: #F0F0F0;
    border: 1px solid #666;
    padding: 5px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #555;
}
QLabel {
    color: #F0F0F0;
    font-size: 20pt;
}
QProgressBar {
    background-color: #2b2b2b;
    color: #F0F0F0;
    border: 1px solid #444;
}
QComboBox {
    font-size: 18pt;
    background-color: #2b2b2b;
    color: #F0F0F0;
    border: 1px solid #444;
}
"""
app.setStyleSheet(dark_stylesheet)

window = MyWidget()
window.show()
sys.exit(app.exec())
