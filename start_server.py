"""Start J.A.R.V.I.S server in background"""
import subprocess
import sys
import time

# Start uvicorn process
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "jarvis.core:app", "--host", "127.0.0.1", "--port", "8001"],
    cwd="C:\\Users\\halis\\Desenvolvimento\\Jarvis",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
time.sleep(3)

# Test if server is up
import requests
try:
    resp = requests.get("http://127.0.0.1:8001/api/sessions", timeout=5)
    if resp.status_code == 200:
        print("✅ Servidor J.A.R.V.I.S iniciado com sucesso na porta 8001")
    else:
        print(f"⚠️ Servidor respondendo com status: {resp.status_code}")
except Exception as e:
    print(f"❌ Erro ao conectar ao servidor: {e}")
    print("O servidor pode levar alguns segundos para iniciar completamente.")
    # Kill the process if we can't connect
    proc.terminate()
    sys.exit(1)

# Keep the process running - store PID for later termination
import os
print(f"🆔 PID do servidor: {proc.pid}")
print("💡 Para encerrar: taskkill /PID {pid} /F".format(pid=proc.pid))