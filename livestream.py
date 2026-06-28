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

def get_ffmpeg_process():
    """Start FFmpeg process that streams to YouTube Live."""
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "pipe:0",           # Read frames from stdin
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",  # Silent audio
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

    # Queue to hold preloaded questions
    q_queue = queue.Queue(maxsize=3)

    # Start background preloader
    preloader = threading.Thread(target=preload_next_question,
                                 args=(q_queue,), daemon=True)
    preloader.start()

    # Wait for first question to be ready
    log.info("⏳ Loading first question...")
    while q_queue.empty():
        time.sleep(1)

    ffmpeg = get_ffmpeg_process()
    question_num = 1

    try:
        while True:
            # Get next question (wait if not ready)
            log.info(f"📺 Streaming question #{question_num}...")
            qdata, frames = q_queue.get(timeout=30)
            log.info(f"❓ Question: {qdata['question'][:60]}...")

            # Stream all frames
            for frame in frames:
                try:
                    ffmpeg.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    log.warning("FFmpeg pipe broken — restarting...")
                    ffmpeg = get_ffmpeg_process()
                    ffmpeg.stdin.write(frame.tobytes())

            question_num += 1
            log.info(f"✅ Question #{question_num-1} streamed!")

    except KeyboardInterrupt:
        log.info("🛑 Stream stopped by user.")
    except Exception as e:
        log.error(f"Stream error: {e}")
    finally:
        if ffmpeg and ffmpeg.stdin:
            ffmpeg.stdin.close()
        if ffmpeg:
            ffmpeg.wait()

if __name__ == "__main__":
    stream_forever()
