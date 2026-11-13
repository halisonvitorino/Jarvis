# PROGRESS

Registro do estado atual do projeto, decisões tomadas e próximos passos.
Leia junto com PRD.md, PROJECT_CONTEXT.md, ARCHITECTURE.md, ROADMAP.md, AI_RULES.md e TASKS.md para entender o projeto e seu status antes de qualquer decisão.

---

# Fase atual

PHASE 1 - CORE CHAT ASSISTANT: implementação pronta; validação com IA real pendente - (Omniroute disponivel em http://localhost:20128/v1).

---

# Concluído

- Estrutura de diretórios modular (`jarvis/` com `core/`, `database/` e placeholders para fases futuras)
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`
- `.env.example` e `.gitignore`
- Repositório git local inicializado (sem commits)
- Configuração: `jarvis/core/config.py`
- Logs: `jarvis/core/logger.py`
- Tratamento global de erros: `jarvis/core/errors.py`
- SQLite + migrações: `jarvis/database/connection.py`, `migrator.py`, `events.py`, `migrations/0001_initial.sql`
- Inicialização: `jarvis/core/bootstrap.py`, `jarvis/__main__.py`
- Testes: `tests/` (config, logger, errors, database, bootstrap)
- `README.md`
- Validação executada em ambiente Python 3.12 com `python -m pytest -q` e `python -m jarvis`

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
- Turnos serializados por sessão; mensagens são salvas apenas após resposta do modelo. Reenvios com o mesmo identificador são idempotentes na sessão entre os 1.000 IDs retidos; chave retida reutilizada com outro texto retorna conflito.
- Execução local via Uvicorn; o bootstrap roda na inicialização da API.

## Limites e validação pendente

- Sessões e mensagens existem apenas na memória do processo. Reiniciar o servidor apaga o histórico.
- A API e o fallback foram testados com respostas controladas.
- A interface foi aberta no navegador em desktop e em 375 px; o viewport móvel não teve rolagem horizontal e manteve o histórico acessível.
- Botões do histórico mantêm largura legível no celular; respostas novas usam uma região de anúncio acessível.
- Com IA indisponível, a interface manteve o texto para nova tentativa e não exibiu nem salvou um turno incompleto.
- Respostas novas são anunciadas por uma região acessível; histórico carregado não é anunciado em massa.
- O código de memória em `jarvis/memory/` é um protótipo antecipado. Ele não está integrado ao chat e não conclui a Phase 2.

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
   Resultado: **25 passed in 1.04s**.
2. Smoke test do bootstrap confirmada:
   ```powershell
   python -m jarvis
   ```
   Resultado: inicialização concluída com sucesso e registro de startup no banco.
3. Escopo mantido: **FastAPI permanece na PHASE 1**. A base da fase 0 foi concluída sem incluir API web, e o roadmap já considera a API como parte do primeiro assistente funcional.

---

# Próximo passo

Iniciar a IA, confirmar modelos disponíveis e validar o fluxo completo de chat. Só então marcar a Phase 1 como concluída e iniciar a Phase 2.
