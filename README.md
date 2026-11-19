# J.A.R.V.I.S

Just A Rather Very Intelligent System - assistente pessoal local para Windows.

Estado atual: **Phase 1 - Core Chat Assistant**, em validação local. A interface de chat, a API, as sessões, o roteamento e o cliente IA estão implementados. A validação com um serviço e modelos IA reais ainda está pendente. Voz, visão, automação e agentes não estão implementados. Veja [ROADMAP.md](ROADMAP.md) e [TASKS.md](TASKS.md).

## Requisitos

- Windows 10/11
- Python 3.12+
- Git

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

## Execução

```powershell
python -m uvicorn jarvis.ui.api:app --host 127.0.0.1 --port 8000
```

As sessões e mensagens ficam na memória do processo. Elas não são mantidas após o reinício do servidor. O serviço aceita até 50 sessões e mantém até 200 mensagens por sessão; o modelo recebe até 20 mensagens recentes como contexto. O corpo de cada solicitação tem limite de 64 KiB, e a resposta do Ollama tem limite de 2048 tokens e 1 MiB. Reinicie o serviço para limpar as sessões quando atingir o limite. A persistência de longo prazo pertence à Phase 2.

Se uma resposta não chegar, o texto permanece no campo. A interface reutiliza o identificador do envio ao tentar de novo, para não duplicar um turno já processado na mesma sessão. A API mantém os 1.000 identificadores concluídos mais recentes na memória; chaves mais antigas podem ser processadas novamente. Novas respostas também são anunciadas a leitores de tela.

## Testes

```powershell
pytest
```

## Configuração

Todas as variáveis usam o prefixo `JARVIS_` e podem vir do ambiente ou do arquivo `.env` (variáveis de ambiente têm prioridade). Caminhos relativos são resolvidos a partir da raiz do projeto.

| Variável                  | Padrão           | Descrição                                       |
| ------------------------- | ---------------- | ----------------------------------------------- |
| `JARVIS_APP_NAME`         | `JARVIS`         | Nome exibido nos logs                           |
| `JARVIS_ENVIRONMENT`      | `dev`            | `dev` ou `prod`                                 |
| `JARVIS_LOG_LEVEL`        | `INFO`           | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `JARVIS_LOG_DIR`          | `logs`           | Diretório dos logs                              |
| `JARVIS_LOG_MAX_BYTES`    | `5242880`        | Tamanho máximo do arquivo antes da rotação      |
| `JARVIS_LOG_BACKUP_COUNT` | `5`              | Quantidade de arquivos rotacionados mantidos    |
| `JARVIS_DATA_DIR`         | `data`           | Diretório de dados                              |
| `JARVIS_DATABASE_PATH`    | `data/jarvis.db` | Arquivo SQLite                                  |

## Estrutura

```text
jarvis/
├── core/          config.py, logger.py, errors.py, bootstrap.py
├── database/      connection.py, migrator.py, events.py, migrations/
├── brain/         ConversationManager, PromptBuilder, SessionManager, ModelRouter
├── memory/        (Phase 2)
├── voice/         (Phase 3)
├── vision/        (Phase 4)
├── automation/    (Phase 5)
├── integrations/  OllamaClient (Phase 1)
├── skills/        (Phase 8)
├── agents/        (Phase 9)
└── ui/            API FastAPI e interface web (Phase 1)
tests/             testes pytest
```

Ordem de inicialização (`jarvis/core/bootstrap.py`): configuração, logs, handler global de exceções, migrações do banco, registro do evento de startup.

## Banco de dados e migrações

As migrações ficam em `jarvis/database/migrations/` com o nome `NNNN_descricao.sql` (ex.: `0002_conversations.sql`). Cada uma roda em sua própria transação e é registrada em `schema_migrations`; migrações já aplicadas são ignoradas. Não use `BEGIN`/`COMMIT` dentro dos arquivos, o executor já delimita a transação.

## Logs

Os logs vão para o console e para `logs/jarvis.log` (rotativo). Em código, use:

```python
from jarvis.core.logger import get_logger

logger = get_logger("meu_modulo")  # -> "jarvis.meu_modulo"
```

Exceções não tratadas (inclusive em threads) são registradas como `CRITICAL` com traceback.
