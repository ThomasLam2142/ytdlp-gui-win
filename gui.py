from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QMovie, QPixmap, QColor
import sys
import os
from yt_dlp import YoutubeDL
import imageio_ffmpeg

class FetchFormatsThread(QThread):
    formats_ready = Signal(dict)
    error = Signal(str)  # Signal for errors

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
            self.error.emit("Could not retrieve video information. Please check the URL.")
            return
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
    """
    Main application window for the YouTube Downloader.
    """
    
    def __init__(self):
        """
        Initialize the main window with its layout and widgets.
        """
        super().__init__()
        # Set window title and size
        self.setWindowTitle('Youtube Downloader')
        self.resize(800, 900)

        # Main vertical layout for the window
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)

        # Add logo at the top of the UI
        logo_label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "assets", "logo.png")
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaledToHeight(300, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignHCenter)
        main_layout.addWidget(logo_label)

        # Status label for messages (e.g., errors, progress)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignHCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        main_layout.addWidget(self.status_label)

        # Create and register dropdowns for resolution, video, and audio formats
        self.dropdowns = {}
        dropdown_info = [
            ("Resolution:", "resolution_combo"),
            ("Video Format:", "video_format_combo"),
            ("Audio Format:", "audio_format_combo")
        ]
        for label, name in dropdown_info:
            combo = QComboBox()
            combo.setEnabled(False)
            combo.setFixedWidth(600)
            setattr(self, name, combo)  # Set as attribute for direct access
            self.dropdowns[name] = combo  # Store in dict for batch operations

        # Centered layout for main interactive controls
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignHCenter)

        def add_centered(layout, widget):
            """
            Helper to add widgets centered in a layout.
            """
            layout.addWidget(widget, alignment=Qt.AlignHCenter)

        # URL input and action buttons
        self.label = QLabel("Enter URL Below")
        self.input = QLineEdit()
        self.input.setFixedWidth(600)
        self.input.textChanged.connect(self.on_url_changed)
        self.check_button = QPushButton("Check Formats")
        self.check_button.clicked.connect(self.on_check_formats)

        # URL validation label (hidden by default, red text)
        self.url_error_label = QLabel("")
        self.url_error_label.setStyleSheet("color: red; font-size: 14px;")
        self.url_error_label.setAlignment(Qt.AlignHCenter)
        self.url_error_label.hide()

        for widget in [self.label, self.input, self.check_button, self.url_error_label]:
            add_centered(center_layout, widget)

        # Dropdowns
        for label, name in dropdown_info:
            center_layout.addWidget(QLabel(label), alignment=Qt.AlignHCenter)
            combo = getattr(self, name)
            add_centered(center_layout, combo)

        self.download_button = QPushButton("Download")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.on_download)
        add_centered(center_layout, self.download_button)

        # Spinner for progress indication
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignHCenter)
        spinner_size = 48
        self.spinner.setFixedSize(spinner_size, spinner_size)
        spinner_path = os.path.join(script_dir, "assets", "spinner.gif")
        self.movie = QMovie(spinner_path)
        self.movie.setScaledSize(QSize(spinner_size, spinner_size))
        self.spinner.setMovie(self.movie)
        # Transparent pixmap for hiding spinner but keeping layout stable
        transparent_pixmap = QPixmap(spinner_size, spinner_size)
        transparent_pixmap.fill(QColor(0, 0, 0, 0))
        self.transparent_spinner = transparent_pixmap
        self.spinner.setPixmap(self.transparent_spinner)
        self.spinner.setVisible(True)
        add_centered(center_layout, self.spinner)

        main_layout.addLayout(center_layout)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

        # Format dictionaries and state variables
        self.video_formats = {}
        self.audio_formats = {}
        self.checked_url = None
        # Connect dropdown change signals to handlers
        self.resolution_combo.currentIndexChanged.connect(self.on_resolution_selected)
        self.video_format_combo.currentIndexChanged.connect(self.on_video_format_selected)
        self.audio_format_combo.currentIndexChanged.connect(self.on_audio_format_selected)

    def update_combo(self, combo, items):
        """
        Helper to update a combo box with new items and enable/disable.
        """
        combo.clear()
        combo.addItems(items)
        combo.setEnabled(bool(items))

    def is_valid_url(self, url):
        """Basic check for a valid YouTube URL."""
        return url.startswith("http") and ("youtube.com" in url or "youtu.be" in url)

    def on_url_changed(self):
        """Reset dropdowns and state when the URL changes. Show error if URL is invalid."""
        url = self.input.text()
        for name in self.dropdowns:
            self.update_combo(self.dropdowns[name], [])
        self.download_button.setEnabled(False)
        self.checked_url = None
        self.status_label.setText("")
        # Show/hide error label
        if url and not self.is_valid_url(url):
            self.url_error_label.setText("Invalid YouTube URL.")
            self.url_error_label.show()
        else:
            self.url_error_label.hide()

    def on_check_formats(self):
        """Check available formats for the entered URL. Show error if invalid."""
        url = self.input.text()
        if not self.is_valid_url(url):
            self.url_error_label.setText("Invalid YouTube URL.")
            self.url_error_label.show()
            return
        self.url_error_label.hide()
        self.status_label.setText("Checking formats...")
        self.check_button.setEnabled(False)
        self.show_spinner()
        for name in self.dropdowns:
            self.update_combo(self.dropdowns[name], [])
        self.download_button.setEnabled(False)
        # Start thread to fetch formats
        self.fetch_thread = FetchFormatsThread(url)
        self.fetch_thread.formats_ready.connect(self.populate_format_dropdowns)
        self.fetch_thread.error.connect(self.on_format_error)
        self.fetch_thread.start()

    def populate_format_dropdowns(self, formats):
        """
        Populate dropdowns with fetched video/audio formats.
        """
        self.hide_spinner()
        self.check_button.setEnabled(True)
        self.checked_url = self.input.text() if formats['video'] or formats['audio'] else None
        self.video_formats = formats['video']
        self.audio_formats = formats['audio']
        # Populate resolution and audio format dropdowns
        if self.video_formats:
            resolutions = sorted({k[0] for k in self.video_formats.keys()}, key=lambda x: int(x.split('x')[1]), reverse=True)
            self.update_combo(self.resolution_combo, resolutions)
        if self.audio_formats:
            self.update_combo(self.audio_format_combo, list(self.audio_formats.keys()))
        self.status_label.setText("Select resolution, video format, and audio format, then click Download.")
        self.update_download_button_state()

    def on_resolution_selected(self):
        """
        Update video format dropdown based on selected resolution.
        """
        res = self.resolution_combo.currentText()
        video_exts = [k[1] for k in self.video_formats.keys() if k[0] == res]
        self.update_combo(self.video_format_combo, video_exts)
        self.update_download_button_state()

    def on_video_format_selected(self):
        """
        Update download button state when video format changes.
        """
        self.update_download_button_state()

    def on_audio_format_selected(self):
        """
        Update download button state when audio format changes.
        """
        self.update_download_button_state()

    def update_download_button_state(self):
        """
        Enable download button only if all selections are valid.
        """
        res = self.resolution_combo.currentText()
        v_ext = self.video_format_combo.currentText()
        a_fmt = self.audio_format_combo.currentText()
        valid = bool(self.checked_url and res and v_ext and a_fmt)
        self.download_button.setEnabled(valid)

    def on_download(self):
        """
        Start the download process for the selected formats.
        """
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
            # Start download thread
            self.thread = DownloadThread(url, f"{video_format_id}+{audio_format_id}")
            self.thread.finished.connect(self.on_download_finished)
            self.thread.start()

    def on_download_finished(self):
        """
        Handle UI updates after download completes.
        """
        self.download_button.setEnabled(True)
        self.hide_spinner()
        self.status_label.setText("Download Complete!")

    def on_format_error(self, message):
        """Show error label if yt-dlp cannot extract info from the URL."""
        self.hide_spinner()
        self.check_button.setEnabled(True)
        self.url_error_label.setText(message)
        self.url_error_label.show()
        self.status_label.setText("")
        for name in self.dropdowns:
            self.update_combo(self.dropdowns[name], [])
        self.download_button.setEnabled(False)

    def show_spinner(self):
        """
        Display the spinner animation.
        """
        self.spinner.setMovie(self.movie)
        self.movie.start()
        self.spinner.setVisible(True)

    def hide_spinner(self):
        """
        Hide the spinner but keep its space in the layout.
        """
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
QPushButton:disabled {
    background-color: #222;
    color: #888;
    border: 1px solid #333;
}
QPushButton:hover:!disabled {
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
