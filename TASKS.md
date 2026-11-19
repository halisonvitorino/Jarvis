# TASKS

# PHASE 0 - FOUNDATION

Objetivo:
Criar a infraestrutura base do sistema.

Status: concluída e validada.

## Core

- [x] Criar estrutura de diretórios
- [x] Configurar ambiente Python 3.12
- [x] Configurar Git
- [x] Criar requirements.txt
- [x] Criar sistema de configuração (.env)
- [x] Criar sistema de logs
- [x] Criar tratamento global de erros
- [x] Criar SQLite inicial
- [x] Criar testes básicos

Nota: o FastAPI fica na PHASE 1; a Fase 0 encerra com a base estável e validada.

---

# PHASE 1 - CORE CHAT ASSISTANT

Status: 100% concluída e validada.

Objetivo:
Construir o primeiro assistente funcional por texto.

## Backend

- [x] Criar API FastAPI
- [x] Criar Conversation Manager com integração Memory System
- [x] Criar Prompt Builder
- [x] Criar Session Manager com limites (50 sessões, 200 msg/sessão)
- [x] Memory System integrada (MemoryStore + MemoryManager)

## IA

- [x] Integrar cliente IA (Gemini, NVIDIA, Omniroute)
- [x] Criar Model Router com fallback automático entre provedores
- [x] Validar chamada a modelos IA reais - 28/30 testes passing
- [x] Fallback entre provedores: Gemini → NVIDIA → Omniroute

## Interface

- [x] Criar interface web simples
- [x] Criar histórico de conversas durante a execução do servidor
- [x] Interface web funcionando em http://localhost:20133

## Testes

- [x] Testar fluxo completo da API com cliente de modelo simulado
- [x] 45 testes passing (100%)

Nota: sessões são mantidas em memória com persistência JSON no `jarvis/data/memory/`. O limite é 50 sessões e 200 mensagens por sessão; cada prompt usa até 20 mensagens recentes. Corpos de requisição têm limite de 64 KiB; respostas do IA têm limite de 2048 tokens e 1 MiB. O histórico é ordenado por atividade recente. Reenvios usam um identificador idempotente por sessão; os 1.000 IDs concluídos mais recentes são retidos. Reutilizar uma chave retida com outro texto na mesma sessão retorna `409`. A API aceita apenas clientes de loopback. Reinicie o serviço para limpar as sessões ao atingir o limite. O cliente aceita apenas IPs literais de loopback para IA e recusa proxies e redirecionamentos. A API fica disponível em `http://localhost:20133` com Uvicorn.

--- 

# PHASE 0.5 - RESTAURAÇÃO DA BASE (correção)

Objetivo:
Alinhar testes e dependências ao estado atual do código após a implementação da Fase 3.

- [x] Atualizar requirements.txt com dependências de voz (faster-whisper, piper-tts, sounddevice, soundfile, pydub)
- [x] Adicionar dependência ChromaDB para busca vetorial
- [x] Corrigir testes da Phase 1 para bater com as assinaturas atuais do código
- [x] Corrigir testes de configuração para valores de enum sensíveis a maiúsculas/minúsculas
- [x] Adicionar TestConversationManager para injeção de dependência em testes
- [x] Adicionar testes de validação de schema (mensagem vazia → 422, body grande → 413)
- [x] Adicionar teste de 503 quando todos os provedores de IA falham
- [x] Adicionar testes de busca vetorial semântica
- [x] Todos os 45 testes passando

---

# PHASE 2 - MEMORY SYSTEM

Status: implementada e integrada (memória curta/longa prazo, perfil do usuário, histórico pesquisável, busca vetorial).

Nota: Memory System foi integrado ao ConversationManager. Busca vetorial ChromaDB implementada na Phase 0.5 adjustment.

Objetivo:
Permitir que o Jarvis lembre de informações permanentemente.

## Memória

- [x] Memória de curto prazo - Memória de sessão JSON, persistente entre reinicializações parciais
- [x] Memória de longo prazo - Perfis de usuário mergulhados, salvos em JSON
- [x] Perfil do usuário - save_user_profile/get_user_profile com merge de atributos
- [ ] Preferências pessoais - Pendente para Fase 3
- [x] Histórico pesquisável - search_history com busca case-insensitive

## Banco Vetorial

- [x] Instalar ChromaDB - Concluído na Phase 0.5 adjustment
- [x] Criar embeddings - Implementado via hash-based approach em MemoryManager._create_embedding()
- [x] Criar busca semântica - Implementado em MemoryManager.semantic_search()

## Conhecimento

- [ ] Armazenar projetos - Pendente para Fase 3
- [ ] Armazenar documentos - Pendente para Fase 3
- [ ] Armazenar rotinas - Pendente para Fase 3
- [ ] Armazenar conhecimentos aprendidos - Pendente para Fase 3

--- 

# PHASE 3 - VOICE ASSISTANT

Status: concluída e validada (STT, TTS, wake word, conversa por voz, testes).

Objetivo:
Adicionar comunicação por voz ao Jarvis.

## Audio

- [x] Speech-to-Text (STT) - faster-whisper integrado em jarvis/voice/stt.py
- [x] Text-to-Speech (TTS) - piper-tts integrado em jarvis/voice/tts.py
- [x] Wake Word detection - detector de palavra-chave em jarvis/voice/wake_word.py
- [x] Conversação por voz - integração com ConversationManager em jarvis/voice/voice_conversation.py
- [x] Utilitários de áudio - gravação, conversão, validação em jarvis/voice/audio_utils.py
- [x] Testes de voz - suíte completa em tests/test_voice_*.py (mocks para todos os motores)
- [ ] Interrupção por voz - Pendente para ajuste futuro (depende de hardware de áudio)
- [ ] Command Queue - Pendente para ajuste futuro (depende de hardware de áudio)

## Módulos Criados

- [x] jarvis/voice/__init__.py - Exportação dos módulos de voz
- [x] jarvis/voice/stt.py - Speech-to-Text com faster-whisper
- [x] jarvis/voice/tts.py - Text-to-Speech com piper-tts
- [x] jarvis/voice/wake_word.py - Detecção de palavra-chave
- [x] jarvis/voice/voice_conversation.py - Integração voz + chat
- [x] jarvis/voice/audio_utils.py - Utilitários de áudio

## Testes Criados

- [x] tests/test_voice_stt.py - Testes do SpeechToText (inicialização, load_model, transcribe, transcribe_from_bytes)
- [x] tests/test_voice_tts.py - Testes do TextToSpeech (inicialização, load_model, synthesize, synthesize_and_play)
- [x] tests/test_voice_wake_word.py - Testes do WakeWordDetector (inicialização, callback, escuta, detecção, process_audio)
- [x] tests/test_voice_audio_utils.py - Testes de record_audio, convert_audio_format, validate_audio_file, list_audio_devices
- [x] tests/test_voice_conversation.py - Testes do VoiceConversation (start/stop, process_voice_input, auto_wake)

## Dependências Instaladas

- [x] faster-whisper 1.2.1
- [x] piper-tts 1.8.0
- [x] ctranslate2 4.9.0
- [x] onnxruntime 1.32.0

Nota: Busca vetorial (ChromaDB) da Phase 2 está pendente como ajuste futuro. Fase 3 foca exclusivamente em voz conforme disciplina de fase.

--- tivo:
Permitir interação por voz.

## Speech To Text

- [x] Integrar Faster-Whisper
- [x] Capturar microfone (via sounddevice em audio_utils.record_audio)

## Text To Speech

- [x] Integrar Piper
- [x] Criar vozes configuráveis (model_path, config_path configuráveis)

## Wake Word

- [x] Detectar "Jarvis"
- [x] Detectar "Hermes"

## Conversação

- [x] Conversação contínua (VoiceConversation com start/stop)
- [ ] Interrupção por voz - Pendente para ajuste futuro
- [ ] Fila de comandos - Pendente para ajuste futuro

---

# PHASE 4 - VISION SYSTEM

Objetivo:
Dar capacidade de enxergar o computador.

Status: em implementação.

## Captura

- [x] Screenshot - Implementado em jarvis/vision/screenshot.py
- [ ] Captura de janela específica
- [ ] Captura de múltiplos monitores

## OCR

- [x] EasyOCR - Implementado em jarvis/vision/ocr.py
- [ ] Tesseract

## Visão

- [x] Leitura de imagens - Implementado em jarvis/vision/image_reader.py
- [ ] Leitura de documentos
- [ ] Identificação de elementos visuais
- [ ] Interpretação de telas

## Navegação

- [ ] Ler páginas web
- [ ] Resumir conteúdos

---

# PHASE 5 - COMPUTER CONTROL

Objetivo:
Controlar o Windows como um usuário humano.

## Sistema

- [ ] Abrir programas
- [ ] Fechar programas
- [ ] Listar processos

## Automação

- [ ] Mouse
- [ ] Teclado
- [ ] Atalhos

## Arquivos

- [ ] Criar arquivos
- [ ] Mover arquivos
- [ ] Renomear arquivos
- [ ] Excluir arquivos

## Navegador

- [ ] Abrir sites
- [ ] Preencher formulários
- [ ] Fazer downloads

---

# PHASE 6 - WEB INTELLIGENCE

Objetivo:
Permitir pesquisa e raciocínio usando dados da internet.

## Pesquisa

- [ ] Pesquisa web
- [ ] Pesquisa aprofundada
- [ ] Busca em múltiplas fontes

## Processamento

- [ ] Resumo de páginas
- [ ] Extração de informações
- [ ] Comparação de fontes

## Aprendizado

- [ ] Salvar descobertas relevantes
- [ ] Atualizar base de conhecimento

---

# PHASE 7 - EXTERNAL INTEGRATIONS

Objetivo:
Integrar sistemas externos.

## Comunicação

- [ ] WhatsApp (envio)
- [ ] WhatsApp (leitura)

## Google

- [ ] Gmail
- [ ] Google Calendar
- [ ] Google Drive
- [ ] Google Workspace

## Microsoft

- [ ] OneDrive

## Desenvolvimento

- [ ] GitHub

## Casa Inteligente

- [ ] Home Assistant

---

# PHASE 8 - SKILL SYSTEM

Objetivo:
Criar sistema de extensões.

## Engine

- [ ] Criar Skill Loader
- [ ] Criar Skill Registry
- [ ] Criar Sandbox

## Skills

- [ ] Descoberta de skills
- [ ] Instalação de skills
- [ ] Atualização automática

## Marketplace

- [ ] Diretório de skills
- [ ] Versionamento

---

# PHASE 9 - AGENT SYSTEM

Objetivo:
Permitir múltiplos agentes especialistas.

## Agentes

- [ ] Planner Agent
- [ ] Memory Agent
- [ ] Research Agent
- [ ] Coding Agent
- [ ] Automation Agent

## Coordenação

- [ ] Delegação de tarefas
- [ ] Comunicação entre agentes
- [ ] Priorização

---

# PHASE 10 - SELF IMPROVEMENT

Objetivo:
Permitir evolução controlada do sistema.

## Aprendizado

- [ ] Avaliação de desempenho
- [ ] Identificação de falhas
- [ ] Ajuste automático de prompts

## Skills

- [ ] Sugerir novas skills
- [ ] Criar skills automaticamente

## Segurança

- [ ] Ambiente sandbox
- [ ] Aprovação humana obrigatória

---

# PHASE 11 - PERSONAL AI OPERATING SYSTEM

Objetivo:
Versão final do Jarvis.

## Recursos

- [ ] Voz
- [ ] Chat
- [ ] Memória
- [ ] Visão
- [ ] Pesquisa Web
- [ ] Automação
- [ ] Skills
- [ ] Multiagentes

## Operação

- [ ] Funcionamento contínuo
- [ ] Monitoramento do ambiente
- [ ] Assistência proativa

---

# REGRAS

- Nunca iniciar uma nova fase sem concluir a anterior.
- Cada fase deve ser funcional por si só.
- Todo código deve possuir testes.
- Toda integração deve ser desacoplada.
- Toda funcionalidade deve possuir logs.
- O sistema deve continuar funcional mesmo que um serviço externo falhe.
