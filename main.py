import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import requests
from playwright.sync_api import sync_playwright

MEGABYTE = 1024 * 1024
TIMEOUT = 1000
STREAM_RE = re.compile(r"s(\d+)q(\d+)\.mp4")
AUDIO_STREAM = 0
LEFT_STREAM = 1
RIGHT_STREAM = 2
AUDIO_FILE_NAME = "audio"
VIDEO_FILE_NAME = "video"
OUT_FILE_EXT = ".mp4"
AUDIO_FILTER = (
    "highpass=f=100,dynaudnorm=f=250:g=15:p=0.9:m=10,loudnorm=I=-16:TP=-1.5:LRA=7"
)


def get_stream_urls(page, url, streams):
    mp4_urls = {}

    # accumulate stream URLs from requests
    def handle_request(request):
        if not ("content.echo360.net.au" in request.url and ".mp4" in request.url):
            return
        path = urlsplit(request.url).path
        if path in mp4_urls:
            return
        re = STREAM_RE.search(path)
        s = int(re.group(1))
        if s in streams and s not in mp4_urls:
            mp4_urls[s] = request.url

    # open URL in chromium, play videos and collect request mp4 urls
    page.on("request", handle_request)
    page.goto(url)
    page.locator("video").first.evaluate("v => v.play()")

    while not all(stream in mp4_urls for stream in streams):
        page.wait_for_timeout(TIMEOUT)

    return mp4_urls


def download_content(url, out_file):
    # request the content
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # stream each chunk to file
    with open(out_file, "wb") as file:
        for chunk in response.iter_content(chunk_size=MEGABYTE):
            if chunk:
                file.write(chunk)


def normalise_audio(audio_file):
    path = Path(audio_file)
    tmp_path = path.with_name(f"tmp_{path.name}")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-stats",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(path),
                "-vn",
                "-af",
                AUDIO_FILTER,
                "-ar",
                "48000",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                str(tmp_path),
            ],
            check=True,
        )

        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)


def merge_audio_into_video(audio_file, video_file):
    audio_path = Path(audio_file)
    video_path = Path(video_file)
    tmp_path = video_path.with_name(f"tmp_{video_path.name}")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-stats",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(audio_path),
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(tmp_path),
            ],
            check=True,
        )

        os.replace(tmp_path, video_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    if len(sys.argv) != 2:
        print("Usage: echo360_normalise URL")
        return

    url = sys.argv[1]
    stream_urls = None

    # get stream URLs
    print("Getting stream URLs...")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            stream_urls = get_stream_urls(page, url, [AUDIO_STREAM, LEFT_STREAM])
        except Exception as e:
            print("Failed to get stream URLs:", e)
            return
        finally:
            browser.close()

    audio_file = None
    video_files = []

    # download video/audio streams
    print("Downloading streams...")
    try:
        for stream, stream_url in stream_urls.items():
            is_audio = stream == AUDIO_STREAM

            out_file_name = (
                AUDIO_FILE_NAME if is_audio else VIDEO_FILE_NAME + str(stream)
            )
            out_file = out_file_name + OUT_FILE_EXT

            download_content(stream_url, out_file)

            if is_audio:
                audio_file = out_file
                print("Audio stream downloaded to", out_file)
            else:
                video_files.append(out_file)
                print("Video stream downloaded to", out_file)
    except Exception as e:
        print("Failed to download stream:", e)
        return

    if not audio_file:
        return

    # normalise audio and merge with video files
    try:
        print("Normalising audio...")
        normalise_audio(audio_file)

        print("Merging audio with video files...")
        for video_file in video_files:
            merge_audio_into_video(audio_file, video_file)

        Path(audio_file).unlink(missing_ok=True)
    except Exception as e:
        print("Failed to merge and normalise audio:", e)


if __name__ == "__main__":
    main()
