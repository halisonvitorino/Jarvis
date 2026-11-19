import os
import sys

print("="*50)
print("TESTE MANUAL - Voice Assistant Structure")
print("="*50)

print("\n[INFO] Pastas:")
voice_dir = 'jarvis/voice'
data_voice = 'data/voice'
print(f"  voice module: {voice_dir}")
print(f"  data/voice: {data_voice}")

try:
    modules = [f.replace('.py', '') for f in os.listdir(voice_dir) if f.endswith('.py') and not f.startswith('__')]
    print(f"  modules: {', '.join(modules)}")
except Exception as e:
    print(f"  erro ao listar: {e}")

print("\n[TST] Testando STT...")
try:
    from jarvis.voice.stt import SpeechToText, STTError
    stt = SpeechToText(model_size='tiny')
    stt.load_model()
    print("  ✅ STT: OK")
except Exception as e:
    print(f"  ⚠️  STT: {type(e).__name__}")

print("\n[TST] Testando TTS with downloaded models...")
try:
    from jarvis.voice.tts import TextToSpeech, TTSError
    # Use the downloaded model files
    model_path = 'data/voice/models/pt_BR-jeff-medium.onnx'
    config_path = 'data/voice/models/pt_BR-jeff-medium.onnx.json'
    
    if os.path.exists(model_path) and os.path.exists(config_path):
        tts = TextToSpeech(
            model_path=model_path,
            config_path=config_path,
            output_dir=data_voice
        )
        try:
            tts.load_model()
            print("  ✅ TTS: Modelo carregado com sucesso!")
        except TTSError:
            print("  ⚠️  TTS: Erro ao carregar modelo (compatibilidade)")
    else:
        print(f"  ⚠️  Arquivos do modelo não encontrados em {data_voice}/models/")
        print(f"  ONNX exists: {os.path.exists(model_path)}")
        print(f"  JSON exists: {os.path.exists(config_path)}")
except Exception as e:
    print(f"  ⚠️  TTS: {type(e).__name__}")

print("\n[TST] Testando outros módulos...")
try:
    from jarvis.voice.wake_word import WakeWordDetector
    from jarvis.voice.audio_utils import record_audio, validate_audio_file
    print("  ✅ WakeWord + Audio: import OK")
except Exception as e:
    print(f"  ⚠️: {type(e).__name__}")

print("\n[TST] Testando VoiceConversation...")
try:
    from jarvis.voice.voice_conversation import VoiceConversation
    from jarvis.brain.conversation_manager import ConversationManager
    manager = ConversationManager()
    vc = VoiceConversation(conversation_manager=manager, auto_wake=False)
    print("  ✅ VoiceConversation: OK")
except Exception as e:
    print(f"  ⚠️: {type(e).__name__}")

print("\n" + "="*50)
print("TESTE CONCLUÍDO")
print("="*50)

print("\nNotes:")
print("  - STT usa faster-whisper (modelo 'tiny' offline)")
print("  - TTS: Modelos piper baixados em data/voice/models/")
print("  - Módulos Python carregam corretamente")
print("  - VoiceConversation usa injeção de dependência")