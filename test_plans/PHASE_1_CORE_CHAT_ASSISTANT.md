# Plano de Testes — PHASE 1: CORE CHAT ASSISTANT

> Projeto: J.A.R.V.I.S. (Just A Rather Very Intelligent System)
> Escopo: Phase 1 — Core Chat Assistant (texto)
> URL base: `http://127.0.0.1:8001`
> Ferramenta: Playwright (Chromium) + API HTTP
> Formato: BDD / Gherkin

---

## 1. Escopo da Fase 1

Conforme `ROADMAP.md`, a Phase 1 entrega o primeiro Jarvis funcional por texto:

| Entregável | Descrição |
|---|---|
| Interface de chat | UI web para conversar com o Jarvis |
| Histórico de conversa | Lista de sessões recentes + mensagens |
| Integração com IA | Cliente de IA com fallback entre provedores |
| Router de modelos | Seleção de modelo primário/fallback |
| Gerenciamento de contexto | Histórico limitado por janela de contexto |
| FastAPI inicial | API REST para sessões e chat |

**Resultado esperado:** Usuário conversa com Jarvis via texto.

---

## 2. Critérios de Aceite

| ID | Critério | Como validar |
|---|---|---|
| AC-01 | Criar nova conversa | UI: botão "+ Nova conversa" cria sessão e limpa o chat |
| AC-02 | Enviar mensagem e receber resposta | UI: mensagem do usuário + resposta do Jarvis aparecem no chat |
| AC-03 | Histórico de conversas | UI: sessões aparecem na lista "RECENTES" e podem ser reabertas |
| AC-04 | Título automático | Primeira mensagem define o título da sessão |
| AC-05 | Contexto da conversa | Múltiplas mensagens mantêm contexto na mesma sessão |
| AC-06 | Validação de entrada | Mensagem vazia não é enviada (UI e API 422) |
| AC-07 | Sessão inexistente | API retorna 404 |
| AC-08 | Limite de corpo | API retorna 413 para corpo > 64 KiB |
| AC-09 | Idempotência | Mesmo `request_id` + mesma mensagem = 200; + mensagem diferente = 409 |
| AC-10 | Indisponibilidade de IA | API retorna 503 quando todos os provedores falham |
| AC-11 | Limite de sessões | API retorna 429 ao exceder 50 sessões |
| AC-12 | Segurança | Headers CSP, X-Frame-Options, X-Content-Type-Options presentes |
| AC-13 | Responsividade | Sem rolagem horizontal em 375px; composer utilizável |
| AC-14 | Acessibilidade | ARIA labels, regiões de status/politemess, foco por teclado |

---

## 3. Cenários de Teste (Gherkin)

### 3.1 Interface de Chat (Frontend)

#### CT-01 — Carregar a aplicação
```gherkin
Dado que o servidor está em execução em http://127.0.0.1:8001
Quando o usuário acessa a página inicial
Então o título da página deve ser "J.A.R.V.I.S. | Conversas"
E a sidebar "Conversas" deve estar visível
E o campo "Sua mensagem" deve estar visível
E o botão "Enviar mensagem" deve estar visível
E o estado inicial deve mostrar "Como posso ajudar?"
```

#### CT-02 — Criar nova conversa
```gherkin
Dado que o usuário está na página inicial
Quando clica no botão "+ Nova conversa"
Então uma nova sessão deve ser criada
E o título da conversa deve ser "Nova conversa"
E o status deve mostrar "Conversa aberta"
E o estado vazio "Como posso ajudar?" deve aparecer
```

#### CT-03 — Enviar mensagem e receber resposta (Happy Path)
```gherkin
Dado que o usuário tem uma conversa aberta
Quando digita "Olá, Jarvis! Tudo bem?" no campo de mensagem
E clica em "Enviar mensagem"
Então a mensagem do usuário deve aparecer no chat
E o Jarvis deve responder
E o status deve mostrar "Resposta recebida. Modelo: <modelo>"
E o título da conversa deve mudar para "Olá, Jarvis! Tudo bem?"
```

#### CT-04 — Múltiplas mensagens mantêm contexto
```gherkin
Dado que o usuário já enviou uma mensagem e recebeu resposta
Quando envia uma segunda mensagem "Qual é o sentido da vida?"
Então ambas as mensagens devem aparecer no histórico do chat
E o Jarvis deve responder considerando o contexto
```

#### CT-05 — Navegar pelo histórico
```gherkin
Dado que existem conversas no histórico "RECENTES"
Quando o usuário clica em uma conversa anterior
Então as mensagens daquela conversa devem ser carregadas
E o título da conversa deve corresponder
E o status deve mostrar "Conversa aberta"
```

#### CT-06 — Validação de campo vazio (UI)
```gherkin
Dado que o usuário tem uma conversa aberta
Quando o campo de mensagem está vazio
E clica em "Enviar mensagem"
Então nenhuma mensagem deve ser adicionada ao chat
E o campo deve permanecer utilizável
```

#### CT-07 — Responsividade mobile (375px)
```gherkin
Dado que o usuário está em um viewport de 375x667
Quando a página é carregada
Então não deve haver rolagem horizontal
E o campo de mensagem e botão devem estar acessíveis
E o histórico deve permanecer acessível
```

#### CT-08 — Acessibilidade
```gherkin
Dado que o usuário está na página inicial
Quando a página é carregada
Então a sidebar deve ter aria-label "Conversas"
E o campo de mensagem deve ter label associado
E o status deve usar role="status"
E elementos interativos devem ser focáveis por teclado
```

---

### 3.2 API Backend (Integração)

#### CT-09 — Criar sessão via API
```gherkin
Dado que a API está disponível
Quando POST /api/sessions com {"title": "Teste"}
Então deve retornar 200
E o body deve conter session_id e title
```

#### CT-10 — Listar sessões
```gherkin
Dado que existe pelo menos uma sessão
Quando GET /api/sessions
Então deve retornar 200
E a lista deve conter a sessão criada
```

#### CT-11 — Buscar sessão existente
```gherkin
Dado que existe uma sessão com id válido
Quando GET /api/sessions/{id}
Então deve retornar 200
E o body deve conter mensagens e metadados
```

#### CT-12 — Buscar sessão inexistente (404)
```gherkin
Quando GET /api/sessions/id-inexistente
Então deve retornar 404
```

#### CT-13 — Enviar mensagem via API
```gherkin
Dado que existe uma sessão válida
Quando POST /api/chat com {"session_id": "...", "message": "Olá"}
Então deve retornar 200
E o body deve conter response, model e session_id
```

#### CT-14 — Mensagem vazia rejeitada (422)
```gherkin
Dado que existe uma sessão válida
Quando POST /api/chat com {"session_id": "...", "message": ""}
Então deve retornar 422
```

#### CT-15 — Título vazio rejeitado (422)
```gherkin
Quando POST /api/sessions com {"title": ""}
Então deve retornar 422
```

#### CT-16 — Corpo acima do limite (413)
```gherkin
Quando POST /api/chat com mensagem de 64KiB + 1 byte
Então deve retornar 413
```

#### CT-17 — Idempotência: conflito (409)
```gherkin
Dado que uma mensagem foi enviada com request_id "X"
Quando POST /api/chat com mesmo request_id "X" mas mensagem diferente
Então deve retornar 409
```

#### CT-18 — Idempotência: reenvio idêntico (200)
```gherkin
Dado que uma mensagem foi enviada com request_id "X"
Quando POST /api/chat com mesmo request_id "X" e mesma mensagem
Então deve retornar 200
E deve retornar a resposta em cache
```

#### CT-19 — Indisponibilidade de IA (503)
```gherkin
Dado que todos os provedores de IA estão indisponíveis
Quando POST /api/chat com mensagem válida
Então deve retornar 503
```

#### CT-20 — Limite de sessões (429)
```gherkin
Dado que já existem 50 sessões
Quando POST /api/sessions
Então deve retornar 429
```

#### CT-21 — Headers de segurança
```gherkin
Quando GET /
Então a resposta deve conter Content-Security-Policy
E X-Frame-Options: DENY
E X-Content-Type-Options: nosniff
```

---

## 4. Dados de Teste

| Caso | Dado | Valor |
|---|---|---|
| CT-03 | Mensagem válida | "Olá, Jarvis! Tudo bem?" |
| CT-04 | Segunda mensagem | "Qual é o sentido da vida?" |
| CT-09 | Título de sessão | "Teste automatizado" |
| CT-14 | Mensagem vazia | `""` |
| CT-15 | Título vazio | `""` |
| CT-16 | Corpo grande | 65537 bytes |
| CT-17/18 | request_id | UUID fixo por execução |

---

## 5. Estratégia de Automação

- **Framework:** Playwright Test (Chromium)
- **Localização:** `tests/chat_assistant-tests/`
- **Configuração:** `playwright.config.ts` (baseURL `http://127.0.0.1:8001`, webServer automático)
- **Seletores:** priorizar `role`, `aria-label`, `id` e `data-*` (estáveis)
- **Esperas:** `expect()` com auto-wait; aguardar status "Resposta recebida" após envio
- **Isolamento:** cada teste cria sua própria sessão; sem dependência de estado anterior
- **CI:** Chromium headless, 1 worker

---

## 6. Riscos e Observações

| Risco | Mitigação |
|---|---|
| Dependência de IA externa (latência/indisponibilidade) | Testes E2E podem usar mock/stub; cenários de API validam fallback |
| Título da sessão muda após primeira mensagem | Seletores de título devem usar `h1#conversation-title` |
| Estado assíncrono (envio em andamento) | Aguardar `status` conter "Resposta recebida" |
| Favicon 404 no console | Ruído conhecido, não é falha funcional |