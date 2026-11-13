"""Teste do ModelRouter com configurações"""
from jarvis.core.config import get_settings
from jarvis.brain.model_router import ModelRouter

s = get_settings()
print("Configurações carregadas:")
print("  default_provider:", s.default_provider)
print("  gemini_api_key:", repr(s.gemini_api_key[:10]) + "...")

r = ModelRouter()
print("\nModelRouter criado sem argumentos:")
print("  default_provider:", r.default_provider)
print("  default_model:", r.default_model)