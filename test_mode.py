"""Teste do modo voice/text na API"""
import json
from fastapi.testclient import TestClient
from jarvis.ui.api import create_app

app = create_app()
client = TestClient(app)

# Testar modo texto (padrão) - enviar mode no body
r = client.post("/api/chat", json={"session_id": "test", "message": "Olá", "mode": "text"})
print("Modo text no body:", r.status_code)
if r.status_code == 200:
    print("  Resposta:", r.json())

# Testar modo voice - enviar mode no body
r = client.post("/api/chat", json={"session_id": "test", "message": "Olá", "mode": "voice"})
print("Modo voice no body:", r.status_code)
if r.status_code == 200:
    print("  Resposta:", r.json())