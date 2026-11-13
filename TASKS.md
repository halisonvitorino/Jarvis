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

Status: implementação pronta; validação com IA real pendente.

Objetivo:
Construir o primeiro assistente funcional por texto.

## Backend

- [x] Criar API FastAPI
- [x] Criar Conversation Manager
- [x] Criar Prompt Manager
- [x] Criar Session Manager

## IA

- [x] Integrar cliente IA
- [x] Criar Model Router
- [x] Criar fallback de modelos
- [ ] Validar chamada a modelos IA reais

## Interface

- [x] Criar interface web simples
- [x] Criar histórico de conversas durante a execução do servidor

## Testes

- [x] Testar fluxo completo da API com cliente de modelo simulado

Nota: sessões são mantidas em memória e terminam quando o servidor reinicia. O limite é 50 sessões e 200 mensagens por sessão; cada prompt usa até 20 mensagens recentes. Corpos de requisição têm limite de 64 KiB; respostas do IA têm limite de 2048 tokens e 1 MiB. O histórico é ordenado por atividade recente. Reenvios usam um identificador idempotente por sessão; os 1.000 IDs concluídos mais recentes são retidos. Reutilizar uma chave retida com outro texto na mesma sessão retorna `409`. A API aceita apenas clientes de loopback. Reinicie o serviço para limpar as sessões ao atingir o limite. O cliente aceita apenas IPs literais de loopback para IA e recusa proxies e redirecionamentos. A API fica disponível em `http://localhost:20128/v1` com Uvicorn.

---

# PHASE 2 - MEMORY SYSTEM

Status: aguardando conclusão da Phase 1.

Nota: existe um protótipo em `jarvis/memory/` com testes para memória curta, perfil e busca textual. Ele foi criado antes da conclusão da Phase 1 e ainda não está integrado ao chat. Não considerar a Phase 2 concluída nem ampliar seu escopo até validar a Phase 1.

Objetivo:
Permitir que o Jarvis lembre de informações permanentemente.

## Memória

- [ ] Memória de curto prazo
- [ ] Memória de longo prazo
- [ ] Perfil do usuário
- [ ] Preferências pessoais
- [ ] Histórico pesquisável

## Banco Vetorial

- [ ] Instalar ChromaDB
- [ ] Criar embeddings
- [ ] Criar busca semântica

## Conhecimento

- [ ] Armazenar projetos
- [ ] Armazenar documentos
- [ ] Armazenar rotinas
- [ ] Armazenar conhecimentos aprendidos

---

# PHASE 3 - VOICE ASSISTANT

Objetivo:
Permitir interação por voz.

## Speech To Text

- [ ] Integrar Faster-Whisper
- [ ] Capturar microfone

## Text To Speech

- [ ] Integrar Piper
- [ ] Criar vozes configuráveis

## Wake Word

- [ ] Detectar "Jarvis"
- [ ] Detectar "Hermes"

## Conversação

- [ ] Conversação contínua
- [ ] Interrupção por voz
- [ ] Fila de comandos

---

# PHASE 4 - VISION SYSTEM

Objetivo:
Dar capacidade de enxergar o computador.

## Captura

- [ ] Screenshot
- [ ] Captura de janela específica
- [ ] Captura de múltiplos monitores

## OCR

- [ ] EasyOCR
- [ ] Tesseract

## Visão

- [ ] Leitura de imagens
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
