# AI DEVELOPMENT RULES

Antes de gerar qualquer código :

1. Ler PROJECT_CONTEXT.md
2. Ler PRD.md
3. Ler ARCHITECTURE.md
4. Ler TASKS.md
5. Ler PROGRESS.md
6. Ler ROADMAP.md

---

# Critical Rules

Nunca gerar soluções monolíticas.

Sempre separar em módulos.

Exemplo:

jarvis/

├── brain/
├── memory/
├── voice/
├── vision/
├── agents/
├── skills/
├── automation/
├── integrations/
└── ui/

---

# Phase Discipline

A IA deve trabalhar exclusivamente na fase atual.

É proibido implementar componentes de fases futuras.

Exemplo:

Durante PHASE 1:

✅ Chat
✅ Contexto
✅ IA

❌ Voz
❌ OCR
❌ Mouse
❌ Agentes
❌ Skills

A evolução do sistema deve seguir estritamente a ordem definida em ROADMAP.md.

Toda funcionalidade deve:

- Ser testável
- Ser substituível
- Possuir logs
- Possuir tratamento de erros

---

Nunca remover funcionalidades existentes sem justificativa.

---

Sempre propor:

- melhorias
- refatorações
- otimizações

quando identificar oportunidades.
