"""Teste do chat do J.A.R.V.I.S"""
from jarvis.brain.conversation_manager import ConversationManager

cm = ConversationManager()
session = cm.create_session("Teste")
print("Sessão criada:", session.id)

result = cm.chat(session.id, "Olá JARVIS")
print("Model:", result["model"])
response = result["response"]
print("Resposta:", response[:100] if response else "N/A")

# Segunda mensagem para testar contexto
result2 = cm.chat(session.id, "Como vai?")
print("Model 2:", result2["model"])
print("Resposta 2:", result2["response"][:100] if result2["response"] else "N/A")