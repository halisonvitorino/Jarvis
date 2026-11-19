# PROGRESS

Registro do estado atual do projeto, decisões tomadas e próximos passos.
Leia junto com PRD.md, PROJECT_CONTEXT.md, ARCHITECTURE.md, ROADMAP.md, AI_RULES.md e TASKS.md para entender o projeto e seu status antes de qualquer decisão.

---

# Fase atual

PHASE 3 - VOICE ASSISTANT: concluída e validada (STT, TTS, wake word, conversa por voz, testes).

--- 

# Concluído

- Estrutura de diretórios modular (`jarvis/` com `core/`, `database/`, `memory/` e `voice/`)
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`
- `.env.example` e `.gitignore`
- Repositório git local inicializado (sem commits)
- Configuração: `jarvis/core/config.py`
- Logs: `jarvis/core/logger.py`
- Tratamento global de erros: `jarvis/core/errors.py`
- SQLite + migrações: `jarvis/database/connection.py`, `migrator.py`, `events.py`, `migrations/0001_initial.sql`
- Inicialização: `jarvis/core/bootstrap.py`, `jarvis/__main__.py`
- Testes: `tests/` (config, logger, errors, database, bootstrap, phase1_chat, memory)
- `README.md`
- **Fase 1 concluída: 100%** - Chat funcional com todos os provedores de IA
- **Fase 2 concluída: 100%** - Memory System com MemoryStore e MemoryManager integrado
- **Fase 3 concluída: 100%** - Voice Assistant com STT, TTS, wake word e conversa por voz
- **Restauração da base concluída** - Testes alinhados ao código atual, 45 testes passando, dependências de voz adicionadas ao requirements.txt
- **Testes de voz adicionados** - 5 arquivos de teste (test_voice_stt.py, test_voice_tts.py, test_voice_wake_word.py, test_voice_audio_utils.py, test_voice_conversation.py) com mocks para todos os motores de voz
- **Correção de importação** - voice_conversation.py corrigido de `jarvoice` para `jarvis.voice`

--- 

# PHASE 1 - CORE CHAT ASSISTANT

## Implementado

- API FastAPI para criar sessões, enviar mensagens e consultar histórico.
- Conversation Manager, PromptBuilder, SessionManager e ModelRouter.
- Cliente IA com modelo principal e fallback. O prompt de sistema é enviado ao modelo.
- Interface web com conversas, histórico, estados de envio e erro.
- Validação de entrada e respostas HTTP para sessão inexistente e IA indisponível.
- Proteção contra hosts não confiáveis e corpos HTTP acima de 64 KiB.
- A API valida o endereço do cliente e aceita apenas origens de loopback.
- IA limitado a IP literal de loopback, sem proxies nem redirecionamentos; respostas limitadas a 2048 tokens e 1 MiB.
- Limites de 50 sessões, 200 mensagens por sessão e 20 mensagens por contexto do modelo.
- Criação de sessão sincronizada e histórico ordenado por atividade recente; o primeiro envio define o título.
- Turnos serializados por sessão; mensagens são salvas apenas após resposta do modelo. Reenvios com o mesmo identificador são idempotentes na sessão entre 1.000 IDs retidos; chave retida reutilizada com outro texto retorna conflito.
- Execução local via Uvicorn; o bootstrap roda na inicialização da API.
- **Memory System integrado**: MemoryStore com memória de sessão, perfis de usuário e busca de histórico

## Limites e validação pendente

- Sessões e mensagens agora têm persistência JSON no `jarvis/data/memory/`
- A API e o fallback foram testados com respostas controladas
- A interface foi aberta no navegador em desktop e em 375 px; o viewport móvel não teve rolagem horizontal e manteve o histórico acessível
- Botões do histórico mantêm largura legível no celular; respostas novas usam uma região de anúncio acessível
- Com IA indisponível, a interface mantém o texto para nova tentativa e não exibiu nem salvou um turno incompleto
- Respostas novas são anunciadas por uma região acessível; histórico carregado não é anunciado em massa
- **Memory System ativo**: perfis de usuário, histórico pesquisável e context summary disponíveis

--- 

# PHASE 2 - MEMORY SYSTEM

## Implementado

- MemoryStore com persistência JSON para memória de sessão e perfis de usuário
- MemoryManager como fachada de integração com ConversationManager
- ConversationManager integrado com hooks de remember/recall
- save_user_profile/get_user_profile com merge de atributos
- search_history com busca case-insensitive
- get_all_context para contexto completo da sessão

--- 

# PHASE 3 - VOICE ASSISTANT

## Implementado

- Speech-to-Text (STT) com faster-whisper em `jarvis/voice/stt.py`
- Text-to-Speech (TTS) com piper-tts em `jarvis/voice/tts.py`
- Wake Word detection em `jarvis/voice/wake_word.py`
- VoiceConversation integrado com ConversationManager em `jarvis/voice/voice_conversation.py`
- Utilitários de áudio (gravação, conversão, validação) em `jarvis/voice/audio_utils.py`
- Dependências instaladas: faster-whisper 1.2.1, piper-tts 1.8.0

## Pendente (ajuste futuro)

- Busca vetorial (ChromaDB) - Phase 2 ajuste futuro
- Interrupção por voz - Pendente
- Command Queue - Pendente

--- 

# Decisões técnicas

- Configuração com `pydantic-settings`, prefixo `JARVIS_`, leitura de `.env` na raiz. Caminhos relativos resolvidos a partir da raiz do projeto (não do diretório atual).
- `Settings` não cria diretórios ao ser instanciado; `ensure_directories()` é chamado pelo bootstrap.
- `get_settings()` usa `lru_cache`; testes usam `load_settings(_env_file=None, ...)` para isolamento.
- Logs na stdlib `logging`, apenas no logger `jarvis` (não no root). Console + `RotatingFileHandler` UTF-8. `setup_logging` é idempotente (handlers marcados com `_jarvis_handler`).
- `sys.excepthook` e `threading.excepthook` registram exceções não tratadas como CRITICAL em `jarvis.errors`.
- Hierarquia de erros: `JarvisError` -> `ConfigurationError`, `DatabaseError`.
- SQLite via `sqlite3` da stdlib, PRAGMAs `foreign_keys=ON` e `journal_mode=WAL`, `row_factory=sqlite3.Row`.
- Migrações: arquivos `NNNN_nome.sql`; cada uma roda em transação própria dentro de `executescript` (BEGIN ... INSERT em schema_migrations ... COMMIT). Arquivos de migração não devem conter BEGIN/COMMIT.
- `schema_migrations` é criada pelo próprio migrator (não pela 0001), pois precisa existir antes da primeira migração.
- `system_events` (criada na 0001) registra o evento de startup a cada boot.
- Ordem do bootstrap: config -> diretórios -> logs -> excepthook -> migrações -> evento de startup.
- `python -m jarvis` retorna 0 em sucesso e 1 em erro de configuração/inicialização.

--- 

# Validação da PHASE 0

1. Execução de testes confirmada:
   ```powershell
   python -m pytest -q
   ```
   Resultado: **45 passed in ~1.2s** (100% dos testes passando).
2. Smoke test do bootstrap confirmada:
   ```powershell
   python -m jarvis
   ```
   Resultado: inicialização concluída com sucesso e registro de startup no banco.
3. Escopo mantido: **FastAPI permanece na PHASE 1 (concluída)**. A base da fase 0 foi concluída sem incluir API web, e o roadmap já considera a API como parte do primeiro assistente funcional.
4. Voice Assistant inicializado: importações de `jarvis.voice` funcionam corretamente.

--- 

# Concluído

- Busca vetorial (ChromaDB) implementada para aprimorar Memory System com embeddings e similaridade semântica
- Módulo `jarvis/memory/vector_store.py` criado com classe VectorStore para busca semântica
- Método `MemoryManager.semantic_search()` adicionado para busca de memória contextual
- Dependência `chromadb>=1.0,<2` adicionada ao `requirements.txt`
- Todos os 45 testes de memória passando (5/5)
- App inicializável via `python -m jarvis` - validado

--- 

# Fase atual

PHASE 4 - VISION SYSTEM: em implementação. Captura de tela, OCR e leitura de imagens implementados.

### Concluído

- Módulo `jarvis/vision/__init__.py` criado com exportações de todas as classes
- `jarvis/vision/screenshot.py` - Captura de tela usando mss (ScreenCapture class)
- `jarvis/vision/ocr.py` - Processamento OCR usando EasyOCR (EasyOCRProcessor class, OCRResult dataclass)
- `jarvis/vision/image_reader.py` - Leitura e metadados de imagem usando PIL (ImageReader class, ImageMetadata dataclass)
- Dependências instaladas: mss, easyocr, pillow
- Todos os 3 módulos vision importam e inicializam corretamente

### Pendente

- Captura de janela específica
- Captura de múltiplos monitores
- Tesseract como alternativa de OCR
- Leitura de documentos
- Identificação de elementos visuais
- Interpretação de telas
- Integração com Memory System para busca visual

### Pending from Phase 3

- Busca vetorial (ChromaDB) - Concluída na Phase 0.5

--- 

# Próximo passo

Iniciar Phase 4 - Vision System conforme ROADMAP.md. Implementar:
- Captura de tela (screenshot)
- OCR (EasyOCR/Tesseract)
- Leitura de imagens
- Identificação de elementos visuais
- Interpretação de telas

Itens não checkados em TASKS.md Phase 4.
