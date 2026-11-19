 """
 Script de teste do TTS com download do modelo Piper.
 """
 import piper

 print("Teste TTS - J.A.R.V.I.S")
 print("=" * 40)

 # Baixa e carrega o modelo brasileiro
 print("Baixando modelo pt_BR-Cicero-Cristiano...")
 voz = piper.PiperVoice.load("pt_BR-Cicero-Cristiano")
 print("Modelo carregado com sucesso!")

 # Sintetiza um texto
 print("\nSintetizando audio...")
 voz.synthesize("Olá, eu sou o J.A.R.V.I.S. Este é um teste de voz.")
 print("Teste TTS OK!")