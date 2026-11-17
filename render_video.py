from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "index.html"
FRAMES_DIR = ROOT / "frames"
OUTPUT_FILE = ROOT / "repo_intro.mp4"
FPS = 30
DURATION_SECONDS = 6


async def capture_animation() -> None:
    if not HTML_FILE.exists():
        raise FileNotFoundError(f"Missing animation file: {HTML_FILE}")

    FRAMES_DIR.mkdir(exist_ok=True)
    for existing in FRAMES_DIR.iterdir():
        if existing.is_file():
            existing.unlink()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        await page.goto(HTML_FILE.as_uri(), wait_until="networkidle")
        await page.wait_for_timeout(6500)

        for frame_index in range(FPS * DURATION_SECONDS):
            file_name = FRAMES_DIR / f"{frame_index:04d}.png"
            await page.screenshot(path=str(file_name), full_page=False)
            await page.wait_for_timeout(int(1000 / FPS))

        await browser.close()


def build_video() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not installed. Install it and rerun this script.")

    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUTPUT_FILE),
    ]
    subprocess.run(cmd, check=True)


async def main() -> None:
    await capture_animation()
    build_video()
    print(f"Video exported to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
