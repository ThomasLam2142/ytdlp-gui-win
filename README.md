# ytdlp-gui-win

A simple Windows GUI for downloading YouTube videos and audio using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features
- Select video resolution, video format, and audio format separately
- Combines video and audio streams using FFmpeg
- Progress spinner and status messages
- Modern dark-themed interface

## Requirements
- Python 3.11+
- Windows (tested)

## Setup
1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Run the setup script:
    ```
    powershell -ExecutionPolicy Bypass -File setup.ps1
    ```
   This will install dependencies and launch the app.

Or, if you want to install dependencies manually:
```sh
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python gui.py
```

## Usage
1. Enter a YouTube video URL.
2. Click **Check Formats**.
3. Select your desired resolution, video format, and audio format.
4. Click **Download** to save the combined file.

## Dependencies
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [PySide6](https://pypi.org/project/PySide6/)
- [imageio[ffmpeg]](https://pypi.org/project/imageio-ffmpeg/)

FFmpeg is downloaded automatically via `imageio[ffmpeg]`.

## Notes
- The app uses FFmpeg to combine video and audio streams.
- Make sure you comply with YouTube's Terms of Service.

## License
MIT License