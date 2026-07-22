@echo off
cd /d C:\Users\Srushti\Desktop\DevMind

docker compose up -d
timeout /t 10

cd backend
call .venv\Scripts\activate.bat

start "DevMind API" /min cmd /c "uvicorn app.main:app"
timeout /t 15

start "DevMind Celery" /min cmd /c "celery -A app.infrastructure.queue.celery_app worker --loglevel=info --pool=solo"
timeout /t 5

for %%f in ("%USERPROFILE%\.claude\projects\C--Users-Srushti-Desktop-DevMind\*.jsonl") do (
    python ..\connectors\claude-code-connector\upload_session.py "%%f"
)

for /r "%USERPROFILE%\.codex\sessions" %%f in (*.jsonl) do (
    python ..\connectors\codex-connector\upload_session.py "%%f"
)

python ..\connectors\cursor-connector\upload_session.py "%USERPROFILE%\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"

for /d %%d in ("%USERPROFILE%\.gemini\antigravity-ide\brain\*") do (
    if exist "%%d\.system_generated\logs\transcript.jsonl" (
        python ..\connectors\antigravity-connector\upload_session.py "%%d\.system_generated\logs\transcript.jsonl"
    )
)