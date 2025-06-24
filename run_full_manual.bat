@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
color 0A
cls

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🎙️  WHISPER + SLIDES EXTRACTOR — by Павел
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:: 1) Входной файл (перетаскивание)
set "INPUT_FILE=%~1"
if "%INPUT_FILE%"=="" (
  echo ❌ Ошибка: файл не передан!
  pause
  exit /b
)
if not exist "%INPUT_FILE%" (
  echo ❌ Ошибка: файл не найден!
  pause
  exit /b
)

:: 2) Пути к Python и основным папкам
set "PYTHON_EXE=C:\Users\TUF\whisper-env\Scripts\python.exe"
for %%F in ("%INPUT_FILE%") do set "FILENAME=%%~nF"
set "RESULT_DIR=D:\Work\%FILENAME%_result"
set "CUT_DIR=%RESULT_DIR%\CUT"

mkdir "%RESULT_DIR%" 2>nul
mkdir "%CUT_DIR%"    2>nul

echo 📁  Файл:       %INPUT_FILE%
echo 📦  Результаты:  %RESULT_DIR%
echo 🧩  Чанки:       %CUT_DIR%

:: 3) Выбор модели
echo.
echo 📦  Выберите модель Whisper:
echo   [Enter] — large-v3 (по умолчанию)
echo   [1]     — medium
set /p MODEL_CHOICE="Ваш выбор: "
if "%MODEL_CHOICE%"=="1" (
  set "MODEL=medium"
) else (
  set "MODEL=large-v3"
)
set "LANGUAGE=ru"

:: 4) Проверка GPU
echo.
"%PYTHON_EXE%" -c "import torch; print('🧠 GPU: доступен ✅' if torch.cuda.is_available() else '🧠 GPU: ❌ НЕ доступен — CPU')"

:: 5) Создание или пере-создание чанков
echo.
echo ✂️  Сплит видео на чанки по речи (макс. 10 мин)…
if exist "%CUT_DIR%\*.mp4" (
  echo ⚠️  В CUT уже есть mp4-файлы.
  echo   [Enter] — оставить
  echo   [1]     — удалить и создать заново
  set /p RE="Ваш выбор: "
  if "%RE%"=="1" (
    del /q "%CUT_DIR%\*.mp4"
  )
)
"%PYTHON_EXE%" split_video_by_voice.py "%INPUT_FILE%" "%CUT_DIR%"
if errorlevel 1 (
  echo ❌ Ошибка при сплите!
  pause
  exit /b
)

:: 6) Транскрипция чанков
echo.
echo 🎧  Транскрибировать чанки?
echo   [Enter] — Да
echo   [0]     — Нет
set /p DO_T="Ваш выбор: "
if not "%DO_T%"=="0" (
  for %%C in ("%CUT_DIR%\*.mp4") do (
    echo.
    echo 🔄  Транскрибируем: %%~nxC

    set "CHUNK_NAME=%%~nC"
    set "CHUNK_DIR=%RESULT_DIR%\!CHUNK_NAME!"
    mkdir "!CHUNK_DIR!" 2>nul

    "%PYTHON_EXE%" whisper_transcribe.py "%%C" "%MODEL%" "%LANGUAGE%" "!CHUNK_DIR!"
    if errorlevel 1 (
      echo ❌ Ошибка транскрибации %%~nxC!
      pause
      exit /b
    )
  )
) else (
  echo ⏭️  Пропускаем транскрибацию.
)

:: 7) Извлечение слайдов для каждого чанка
echo.
echo 🖼️  Извлечь слайды из каждого чанка?
echo   [Enter] — Да
echo   [0]     — Нет
set /p DO_S="Ваш выбор: "
if not "%DO_S%"=="0" (
  echo.
  echo 📊  Задайте общие параметры:
  set /p TH="➤ Threshold [по умолч. 10.0]: "
  set /p MS="➤ MinSceneSec [по умолч. 5.0]: "
  if "%TH%"=="" set TH=10.0
  if "%MS%"=="" set MS=5.0

  for %%C in ("%CUT_DIR%\*.mp4") do (
    echo.
    echo 🖼️  Слайды для: %%~nxC

    set "CHUNK_NAME=%%~nC"
    set "SLIDE_DIR=%RESULT_DIR%\!CHUNK_NAME!_slides"
    mkdir "!SLIDE_DIR!" 2>nul

    "%PYTHON_EXE%" extract_slides.py "%%C" %TH% %MS% "!SLIDE_DIR!"
    if errorlevel 1 (
      echo ❌ Ошибка извлечения слайдов для %%~nxC!
      pause
      exit /b
    )
  )
) else (
  echo ⏭️  Пропускаем слайды.
)

:: 8) Финал
echo.
echo 🟢  Все задачи выполнены!
echo   ├─ Чанки:        %CUT_DIR%
echo   ├─ Транскрипты:  %RESULT_DIR%\*_chunk_XXX\*.txt/.srt/.text.txt
echo   └─ Слайды:       %RESULT_DIR%\*_chunk_XXX_slides\*.jpg
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pause
