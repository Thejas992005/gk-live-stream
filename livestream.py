import subprocess
import numpy as np
import os
import sys
import time
import logging
import threading
import queue
from question_generator import generate_question
from stream_creator import generate_question_frames, WIDTH, HEIGHT, FPS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY")

def find_ffmpeg():
    """Find ffmpeg binary in common locations."""
    locations = [
        "ffmpeg",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/nix/var/nix/profiles/default/bin/ffmpeg",
    ]
    # Also search nix store
    try:
        result = subprocess.run(["which", "ffmpeg"],
                               capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            log.info(f"Found ffmpeg at: {path}")
            return path
    except:
        pass

    # Search nix store
    try:
        result = subprocess.run(
            ["find", "/nix/store", "-name", "ffmpeg", "-type", "f"],
            capture_output=True, text=True, timeout=10
        )
        paths = [p for p in result.stdout.strip().split('\n') if p and 'bin/ffmpeg' in p]
        if paths:
            log.info(f"Found ffmpeg in nix store: {paths[0]}")
            return paths[0]
    except:
        pass

    # Install ffmpeg via pip as fallback
    log.info("Installing ffmpeg-python...")
    subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"], check=True)
    import imageio_ffmpeg
    path = imageio_ffmpeg.get_ffmpeg_exe()
    log.info(f"Using imageio ffmpeg: {path}")
    return path

def get_ffmpeg_process(ffmpeg_path):
    """Start FFmpeg process that streams to YouTube Live."""
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

    cmd = [
        ffmpeg_path,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vcodec", "libx264",
        "-preset", "veryfast",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),
        "-acodec", "aac",
        "-ar", "44100",
        "-b:a", "128k",
        "-f", "flv",
        rtmp_url
    ]

    log.info(f"🎥 Starting FFmpeg stream to YouTube...")
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)

def preload_next_question(q_queue):
    """Background thread to preload next question."""
    while True:
        try:
            if q_queue.qsize() < 2:
                log.info("⏳ Pre-loading next question...")
                qdata = generate_question()
                frames = generate_question_frames(
                    qdata,
                    question_secs=5,
                    countdown_secs=5,
                    answer_secs=3,
                    transition_secs=2
                )
                q_queue.put((qdata, frames))
                log.info(f"✅ Pre-loaded: {qdata['question'][:50]}...")
            time.sleep(1)
        except Exception as e:
            log.error(f"Pre-load error: {e}")
            time.sleep(5)

def stream_forever():
    if not STREAM_KEY:
        log.error("❌ YOUTUBE_STREAM_KEY not set!")
        sys.exit(1)

    log.info("=" * 55)
    log.info("🔴 GK LIVE QUIZ STREAM STARTING!")
    log.info("=" * 55)

    # Find ffmpeg
    ffmpeg_path = find_ffmpeg()
    log.info(f"✅ Using ffmpeg: {ffmpeg_path}")

    # Queue to hold preloaded questions
    q_queue = queue.Queue(maxsize=3)

    # Start background preloader
    preloader = threading.Thread(target=preload_next_question,
                                 args=(q_queue,), daemon=True)
    preloader.start()

    # Wait for first question
    log.info("⏳ Loading first question...")
    while q_queue.empty():
        time.sleep(1)

    ffmpeg = get_ffmpeg_process(ffmpeg_path)
    question_num = 1

    try:
        while True:
            log.info(f"📺 Streaming question #{question_num}...")
            qdata, frames = q_queue.get(timeout=30)
            log.info(f"❓ {qdata['question'][:60]}...")

            for frame in frames:
                try:
                    ffmpeg.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    log.warning("FFmpeg pipe broken — restarting...")
                    ffmpeg = get_ffmpeg_process(ffmpeg_path)
                    ffmpeg.stdin.write(frame.tobytes())

            question_num += 1
            log.info(f"✅ Question #{question_num-1} streamed!")

    except KeyboardInterrupt:
        log.info("🛑 Stream stopped.")
    except Exception as e:
        log.error(f"Stream error: {e}")
    finally:
        if ffmpeg and ffmpeg.stdin:
            ffmpeg.stdin.close()
        if ffmpeg:
            ffmpeg.wait()

if __name__ == "__main__":
    stream_forever()
