"""Teste direto do chat J.A.R.V.I.S usando Gemini Client"""
import os
import sys
import json
import urllib.request
import urllib.error

# Usar a chave Gemini do .env
GEMINI_KEY = "AQ.Ab8RN6I6Cqck3XtgclKSfD5JqogEpMb_TZWG6gZFCp5WVnhu8w"

# URL do Gemini API
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"

print("=" * 60)
print("Teste Direto do Gemini API")
print("=" * 60)

# Payload para o Gemini
payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Olá JARVIS, como vai?"}]
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

try:
    req = urllib.request.Request(GEMINI_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
        # Extrair texto da resposta do Gemini
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            print("✅ Sucesso! Resposta do Gemini:")
            print(f"   {text.strip()[:100]}")
        except (KeyError, IndexError):
            # Tentar estrutura alternativa
            text = result.get("text", "Sem texto")
            print(f"✅ Resposta (estrutura alternativa): {text.strip()[:100]}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")[:200]
    print(f"❌ Erro HTTP {e.code}: {body}")
except Exception as e:
    print(f"❌ Erro: {type(e).__name__}: {str(e)[:200]}")

print()
print("=" * 60)
print("Teste 2: Pergunta sobre tempo/tempo")
print("=" * 60)

payload2 = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Qual é a capital do Brasil?"}]
        }
    ]
}

try:
    req = urllib.request.Request(GEMINI_URL, data=json.dumps(payload2).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"✅ Sucesso! Resposta: {text.strip()}")
        except (KeyError, IndexError):
            text = result.get("text", "Sem texto")
            print(f"✅ Resposta: {text.strip()}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8")[:200]
    print(f"❌ Erro HTTP {e.code}: {body}")
except Exception as e:
    print(f"❌ Erro: {type(e).__name__}: {str(e)[:200]}")