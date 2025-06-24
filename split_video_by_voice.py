# split_video_by_voice.py
import os
import sys
import subprocess
import tempfile
import shutil
from pydub import AudioSegment
import webrtcvad

# --- Максимальная длительность чанка в секундах (10 минут) ---
MAX_CHUNK_SEC = 10 * 60

def format_hms(sec: float):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02}-{m:02}-{s:02}"

# --- Аргументы ---
input_video = sys.argv[1]
output_dir  = sys.argv[2] if len(sys.argv) > 2 else "chunks"

os.makedirs(output_dir, exist_ok=True)
basename = os.path.splitext(os.path.basename(input_video))[0]

# --- Временная папка для wav ---
temp_dir = tempfile.mkdtemp()
wav_path  = os.path.join(temp_dir, "audio.wav")

# --- Извлекаем моно-аудио 16kHz ---
subprocess.run([
    "ffmpeg", "-y", "-i", input_video,
    "-ac", "1", "-ar", "16000", "-vn", wav_path
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

audio = AudioSegment.from_wav(wav_path)
length_ms = len(audio)

# --- VAD: ищем промежутки речи ---
vad = webrtcvad.Vad(2)  # агрессия 0–3
frame_ms = 30
frame_bytes = int(16000 * 2 * frame_ms / 1000)

speech_segs = []
start_ms = None

for t in range(0, length_ms, frame_ms):
    frame = audio[t:t+frame_ms]._data
    if len(frame) < frame_bytes:
        break
    if vad.is_speech(frame, sample_rate=16000):
        if start_ms is None:
            start_ms = t
    else:
        if start_ms is not None and (t - start_ms) > 500:
            speech_segs.append((start_ms, t))
        start_ms = None

if start_ms is not None:
    speech_segs.append((start_ms, length_ms))

# --- Группируем сегменты в чанки не длиннее MAX_CHUNK_SEC ---
chunks = []
current, cur_len = [], 0
for seg_start, seg_end in speech_segs:
    seg_len = seg_end - seg_start
    if cur_len + seg_len > MAX_CHUNK_SEC * 1000 and current:
        chunks.append(current)
        current, cur_len = [], 0
    current.append((seg_start, seg_end))
    cur_len += seg_len
if current:
    chunks.append(current)

# --- Нарезаем видео исходя из группировок ---
print(f"✂️  {len(chunks)} чанков обнаружено, нарезка…")
for idx, grp in enumerate(chunks, start=1):
    start_sec = grp[0][0] / 1000
    end_sec   = grp[-1][1] / 1000
    dur_sec   = end_sec - start_sec
    stamp     = format_hms(start_sec)
    out_name  = f"{basename}_chunk_{idx:03}_{stamp}.mp4"
    out_path  = os.path.join(output_dir, out_name)

    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-ss", f"{start_sec:.2f}",
        "-t", f"{dur_sec:.2f}",
        "-c", "copy", out_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"[CUT] {out_name}  {start_sec:.2f}s → {start_sec+dur_sec:.2f}s")

# --- Убираем временные файлы ---
shutil.rmtree(temp_dir)
print(f"✅ Чанки сохранены в «{output_dir}»")
