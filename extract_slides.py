# extract_slides.py
import os
import sys
import cv2
import subprocess
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

def format_timestamp(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

# --- Чтение аргументов ---
# 1) video_path
# 2) threshold (float)
# 3) min_scene_seconds (float)
# 4) output_dir for slides (optional)
if len(sys.argv) < 4:
    print("Usage: extract_slides.py <video_path> <threshold> <min_scene_seconds> [<output_dir>]")
    sys.exit(1)

video_path        = sys.argv[1]
threshold         = float(sys.argv[2])
min_scene_seconds = float(sys.argv[3])
output_dir        = sys.argv[4] if len(sys.argv) > 4 else None

# --- Проверяем видео ---
if not os.path.exists(video_path):
    print(f"❌ Файл не найден: {video_path}")
    sys.exit(1)

# --- Определяем папку для слайдов ---
if not output_dir:
    base_name  = os.path.splitext(os.path.basename(video_path))[0]
    parent_dir = os.path.dirname(video_path)
    output_dir = os.path.join(parent_dir, f"{base_name}_slides")
os.makedirs(output_dir, exist_ok=True)

# --- Получаем FPS и считаем минимальную длину сцены в кадрах ---
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"❌ Не удалось открыть видео: {video_path}")
    sys.exit(1)

fps            = cap.get(cv2.CAP_PROP_FPS)
min_scene_len  = int(fps * min_scene_seconds)

# --- Очищаем старые слайды ---
existing = [f for f in os.listdir(output_dir) if f.lower().endswith(('.jpg','.png'))]
if existing:
    print(f"🧹 Обнаружены старые слайды ({len(existing)}), удаляем…")
    for fname in existing:
        os.remove(os.path.join(output_dir, fname))

# --- Печать параметров ---
print("📦 Параметры:")
print(f"   ➤ Порог чувствительности: {threshold}")
print(f"   ➤ Мин. длина сцены:      {min_scene_seconds} сек ({min_scene_len} кадров)")
print(f"   ➤ FPS видео:             {fps:.2f}")
print(f"   ➤ Папка для слайдов:     {output_dir}")
print()

# --- Детектирование сцен ---
print("🔍 Детектируем сцены…")
video_manager = VideoManager([video_path])
scene_manager = SceneManager()
scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))
video_manager.set_downscale_factor(1)
video_manager.start()
scene_manager.detect_scenes(frame_source=video_manager)
scene_list = scene_manager.get_scene_list()
total = len(scene_list)
print(f"🖼️ Найдено сцен: {total}")

if total == 0:
    print("⚠️ Сцены не найдены. Завершение.")
    cap.release()
    sys.exit(0)

# --- Сохраняем кадры сцен с прогресс-баром ---
print("\n💾 Извлекаем слайды:")
for i, (start, _) in enumerate(scene_list, start=1):
    # обновляем прогресс
    percent = int(i / total * 100)
    bar = "█" * (percent // 2) + "-" * (50 - percent // 2)
    sys.stdout.write(f"\r[{bar}] {percent:3d}%  ({i}/{total})")
    sys.stdout.flush()

    # захват кадра
    frame_no = start.get_frames()
    time_s   = start.get_seconds()
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    if not ret:
        continue

    # сохраняем
    ts = format_timestamp(time_s).replace(":", "-")
    fname = f"slide_{i:03}_{ts}.jpg"
    path  = os.path.join(output_dir, fname)
    cv2.imwrite(path, frame)

cap.release()

print(f"\n✅ Слайды сохранены: {total} шт.")
print(f"📂 Папка: {output_dir}")

# --- Открытие папки ---
try:
    subprocess.run(['explorer', output_dir], check=False)
except Exception as e:
    print(f"⚠️ Не удалось открыть папку: {e}")
