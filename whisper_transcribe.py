# whisper_transcribe.py
import os
import sys
import whisper
from unidecode import unidecode

# --- Вспомогательная функция: чистое имя без кириллицы/пробелов ---
def sanitize(name: str) -> str:
    name = unidecode(name).replace(' ', '_')
    allowed = "-_.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(c for c in name if c in allowed)

# --- Чтение аргументов ---
#   1) путь к видео/чанку
#   2) размер модели (large-v3 / medium)
#   3) язык (например, ru)
#   4) папка результатов для этого чанка
#   5) смещение в секундах (offset), по умолчанию 0.0
input_file = sys.argv[1]
model_size = sys.argv[2] if len(sys.argv) > 2 else 'large-v3'
language   = sys.argv[3] if len(sys.argv) > 3 else 'ru'
result_dir = sys.argv[4] if len(sys.argv) > 4 else None
offset     = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0

# --- Готовим safe_name и result_dir ---
orig = os.path.splitext(os.path.basename(input_file))[0]
safe = sanitize(orig)
if not result_dir:
    result_dir = os.path.join("D:/Work", f"{safe}_result")
os.makedirs(result_dir, exist_ok=True)

# --- Пути к файлам ---
txt_path  = os.path.join(result_dir, f"{safe}.txt")
srt_path  = os.path.join(result_dir, f"{safe}.srt")
text_path = os.path.join(result_dir, f"{safe}.text.txt")

# --- Функция: спросить о пропуске/пересоздании ---
def ask_skip(path: str) -> bool:
    if os.path.exists(path):
        print(f"⚠️ Файл уже существует: {path}")
        c = input("[Enter] — пропустить, [1] — пересоздать: ").strip()
        return c != '1'
    return False

skip_txt  = ask_skip(txt_path)
skip_srt  = ask_skip(srt_path)
skip_text = ask_skip(text_path)

# Если всё пропускаем — сразу выходим
if skip_txt and skip_srt and skip_text:
    print("⏭️ Всё уже есть, пропускаем транскрипцию.")
    # Для батника:
    print(f"[RETURN] RESULT_DIR={result_dir}")
    print(f"[RETURN] SAFE_NAME={safe}")
    sys.exit(0)

# --- Загрузка модели и транскрипция ---
print("🎷 Загружаем модель:", model_size)
model = whisper.load_model(model_size)
print("🎧 Распознаём:", input_file)
res = model.transcribe(input_file, language=language, verbose=True)
segs = res["segments"]

# --- Сохраняем .txt с таймкодами (с учётом offset) ---
if not skip_txt:
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segs:
            start = seg["start"] + offset
            end   = seg["end"]   + offset
            f.write(f"[{start:.2f} - {end:.2f}] {seg['text'].strip()}\n")
    print("💾 Сохранено:", txt_path)

# --- Сохраняем .srt ---
def fmt_srt(t: float) -> str:
    ms    = int((t - int(t)) * 1000)
    h     = int(t // 3600)
    m     = int((t % 3600) // 60)
    s     = int(t % 60)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

if not skip_srt:
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segs, start=1):
            s = seg["start"] + offset
            e = seg["end"]   + offset
            f.write(f"{i}\n")
            f.write(f"{fmt_srt(s)} --> {fmt_srt(e)}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    print("💾 Сохранено:", srt_path)

# --- Сохраняем .text.txt (абзацы без таймкодов) ---
if not skip_text:
    with open(text_path, "w", encoding="utf-8") as f:
        # простой вариант: разделяем по паузам не более 1.5 сек
        paras, curr, last_end = [], [], None
        for seg in segs:
            if last_end is not None and seg["start"] - last_end > 1.5:
                paras.append(" ".join(curr))
                curr = []
            curr.append(seg["text"].strip())
            last_end = seg["end"]
        if curr:
            paras.append(" ".join(curr))
        f.write("\n\n".join(paras))
    print("💾 Сохранено:", text_path)

# --- Финальные маркеры для батника ---
print(f"[RETURN] RESULT_DIR={result_dir}")
print(f"[RETURN] SAFE_NAME={safe}")
