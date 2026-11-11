# PROGRESS

Registro do estado atual do projeto, decisões tomadas e próximos passos.
Leia junto com PRD.md, PROJECT_CONTEXT.md, ARCHITECTURE.md, ROADMAP.md, AI_RULES.md e TASKS.MD.

---

# Fase atual

PHASE 0 - FOUNDATION: código escrito, **não validado** (nenhum teste executado ainda).

---

# Concluído (escrito)

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

# Pendências da PHASE 0

1. Validar em um ambiente com Python 3.12:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   pytest
   python -m jarvis
   ```
   Corrigir o que falhar antes de seguir para a PHASE 1.
2. "FastAPI inicial": o ROADMAP.md foi atualizado e agora lista FastAPI na PHASE 0, mas o TASKS.MD mantém "Criar API FastAPI" na PHASE 1. Decidir onde fica. Proposta: app mínima (`fastapi` + `uvicorn`) com `GET /health` reutilizando o bootstrap, mais um teste.
3. Marcar os itens da PHASE 0 no TASKS.MD somente após os testes passarem.

---

# Melhorias sugeridas (documentação)

- Arquivos referenciam `TASKS.md`, mas o nome real é `TASKS.MD`. Renomear para evitar problemas em sistemas case-sensitive.
- Alinhar ROADMAP.md e TASKS.MD (item FastAPI).
- ARCHITECTURE.md usa camadas (Interface/Brain/Tool/Skill/Providers/Data) diferentes das pastas de AI_RULES.md. Considerar adicionar `providers/` (Ollama, Omniroute, cloud) na PHASE 1.

---

# Próximo passo

Concluir as pendências da PHASE 0. Só então iniciar a PHASE 1 (Core Chat Assistant).
