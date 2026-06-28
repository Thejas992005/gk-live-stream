import subprocess
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
    handlers=[logging.StreamHandler(sys.stdout)]
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
    for loc in locations:
        try:
            res = subprocess.run([loc, "-version"], capture_output=True, text=True)
            if res.returncode == 0:
                log.info(f"Found ffmpeg at: {loc}")
                return loc
        except Exception:
            pass

    # Search via which
    try:
        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            log.info(f"Found ffmpeg via which at: {path}")
            return path
    except Exception:
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
    except Exception:
        pass

    # Install ffmpeg via pip fallback
    log.info("Installing ffmpeg-python fallback...")
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
        "-i", "anullsrc=r=44100:cl=stereo",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vcodec", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-minrate", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-nal-hrd", "cbr",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),
        "-acodec", "aac",
        "-ar", "44100",
        "-b:a", "128k",
        "-f", "flv",
        rtmp_url
    ]

    log.info("🎥 Starting FFmpeg stream to YouTube...")
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=10**7
    )

def preload_next_question(q_queue):
    """Background thread to preload question metadata (ultra low memory)."""
    while True:
        try:
            if q_queue.qsize() < 3:
                log.info("⏳ Pre-loading next question...")
                qdata = generate_question()
                q_queue.put(qdata)
                log.info(f"✅ Pre-loaded: {qdata['question'][:50]}...")
            time.sleep(1)
        except Exception as e:
            log.error(f"Pre-load error: {e}")
            time.sleep(5)

def log_ffmpeg_stderr(ffmpeg_proc):
    """Reads and logs stderr output from dead FFmpeg process."""
    if ffmpeg_proc and ffmpeg_proc.stderr:
        try:
            err = ffmpeg_proc.stderr.read().decode("utf-8", errors="replace")
            if err:
                log.error(f"FFmpeg Error output (last 1000 chars):\n{err[-1000:]}")
        except Exception as e:
            log.error(f"Failed to read FFmpeg stderr: {e}")

def stream_forever():
    if not STREAM_KEY:
        log.error("❌ YOUTUBE_STREAM_KEY environment variable is not set!")
        log.error("Please add YOUTUBE_STREAM_KEY in your Railway deployment variable settings.")
        sys.exit(1)

    log.info("=" * 55)
    log.info("🔴 GK LIVE QUIZ STREAM STARTING!")
    log.info("=" * 55)

    ffmpeg_path = find_ffmpeg()
    log.info(f"✅ Using ffmpeg: {ffmpeg_path}")

    q_queue = queue.Queue(maxsize=5)
    preloader = threading.Thread(target=preload_next_question, args=(q_queue,), daemon=True)
    preloader.start()

    log.info("⏳ Loading first question...")
    while q_queue.empty():
        time.sleep(1)

    ffmpeg = None
    question_num = 1
    frame_duration = 1.0 / FPS

    while True:
        if ffmpeg is None or ffmpeg.poll() is not None:
            if ffmpeg is not None:
                log.error(f"❌ FFmpeg process exited with code {ffmpeg.poll()}.")
                log_ffmpeg_stderr(ffmpeg)
                log.info("Sleeping 5 seconds before restarting FFmpeg to avoid log rate-limiting...")
                time.sleep(5)

            ffmpeg = get_ffmpeg_process(ffmpeg_path)

        log.info(f"📺 Streaming question #{question_num}...")
        try:
            qdata = q_queue.get(timeout=30)
        except queue.Empty:
            log.warning("Queue empty, waiting for questions...")
            time.sleep(2)
            continue

        log.info(f"❓ {qdata['question'][:60]}...")

        pipe_broken = False
        frame_gen = generate_question_frames(
            qdata,
            question_secs=12,
            countdown_secs=5,
            answer_secs=5,
            transition_secs=2
        )

        start_time = time.time()
        frame_idx = 0
        for frame_bytes in frame_gen:
            if ffmpeg.poll() is not None:
                log.warning("FFmpeg process died mid-stream.")
                pipe_broken = True
                break
            try:
                ffmpeg.stdin.write(frame_bytes)
                ffmpeg.stdin.flush()
            except (BrokenPipeError, IOError):
                log.warning("FFmpeg pipe broken during frame write.")
                pipe_broken = True
                break

            frame_idx += 1
            target_time = start_time + (frame_idx * frame_duration)
            sleep_time = target_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        if pipe_broken:
            log_ffmpeg_stderr(ffmpeg)
            try:
                if ffmpeg.stdin:
                    ffmpeg.stdin.close()
            except Exception:
                pass
            ffmpeg = None
            log.info("Sleeping 5 seconds before retrying stream loop...")
            time.sleep(5)
            continue

        question_num += 1
        log.info(f"✅ Question #{question_num-1} streamed!")

if __name__ == "__main__":
    try:
        stream_forever()
    except KeyboardInterrupt:
        log.info("🛑 Stream stopped by user.")
    except Exception as e:
        log.error(f"Fatal stream error: {e}")
