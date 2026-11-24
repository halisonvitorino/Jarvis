# JARVIS — Plano de Auditoria Corretiva, Estabilização e Conclusão da Fase 3

## 1. CONTEXTO E OBJETIVO

Estamos desenvolvendo o JARVIS, um assistente pessoal baseado em IA, com arquitetura modular, capacidade de interação por texto e voz, memória persistente, processamento local e integração com provedores externos de inteligência artificial.

Antes de implementar novas funcionalidades, precisamos realizar uma **auditoria técnica corretiva, seguida de um ciclo estruturado de correções, integração e testes**.

Uma análise técnica anterior identificou que o projeto possui uma boa estrutura inicial, mas alguns componentes estão implementados apenas parcialmente, apresentam inconsistências ou ainda não estão efetivamente integrados.

O objetivo desta etapa é:

1. Auditar o código atual e confirmar os problemas identificados.
2. Identificar problemas adicionais relacionados ao escopo definido neste documento.
3. Transformar cada problema confirmado em tarefas pequenas, independentes e priorizadas.
4. Definir critérios de aceite objetivos para cada tarefa.
5. Distribuir as tarefas entre os agentes de IA especializados.
6. Executar as correções de maneira incremental.
7. Validar cada correção por meio de testes automatizados.
8. Entregar uma aplicação funcional, estável e integrada antes de iniciar novas funcionalidades.

**Não queremos reconstruir o projeto do zero. Queremos aproveitar o que já foi desenvolvido, corrigir suas deficiências e concluir adequadamente as funcionalidades previstas.**

---

# 2. ESCOPO DESTA INTERVENÇÃO

A intervenção está limitada aos seguintes problemas e áreas:

### 2.1 Memória aparentemente não conectada ao cérebro

Problemas identificados anteriormente:

- O `ConversationManager` importa `MemoryManager`, mas aparentemente não o utiliza efetivamente no fluxo principal de conversação.
- A memória não parece participar adequadamente da construção do contexto enviado ao modelo.
- Os mecanismos de armazenamento e recuperação precisam ser validados.
- A busca semântica utiliza uma implementação baseada em hash, que não representa embeddings semânticos reais.
- A busca pode retornar identificadores em vez do conteúdo das memórias.
- O VectorStore apresenta possíveis problemas de implementação, incluindo a utilização de `Path` sem importação explícita.

Objetivo:

Fazer com que a memória seja parte efetiva do cérebro do JARVIS, permitindo armazenar, recuperar e utilizar informações relevantes durante as conversas.

### 2.2 Limitações na memória das conversas

Investigar e corrigir:

- Persistência das conversas após reinicialização.
- Recuperação do histórico de sessões.
- Isolamento de memória entre sessões.
- Memória de curto e longo prazo.
- Recuperação contextual de informações anteriores.
- Limites de contexto enviados aos modelos.
- Estratégias de resumo e compactação do histórico.
- Prevenção de duplicidade de memórias.
- Consistência entre banco de dados, sessões e memória vetorial.

Objetivo:

Garantir continuidade das conversas, preservação de informações importantes e recuperação contextual confiável.

### 2.3 Voz implementada, mas ainda não integrada à interface

Investigar os componentes existentes:

- STT com Faster-Whisper.
- TTS com Piper.
- Voice Conversation.
- Wake Word.
- Processamento de áudio.

O objetivo não é simplesmente verificar se os módulos funcionam individualmente.

É necessário validar o fluxo completo:

**Microfone → STT → Conversation Manager → Modelo de IA → TTS → Reprodução de áudio na interface.**

A interface deve apresentar os estados correspondentes ao processamento de voz.

### 2.4 API ainda precisa evoluir

Investigar:

- Estrutura atual dos endpoints.
- Integração com ConversationManager.
- Gerenciamento de sessões.
- Comunicação em tempo real.
- WebSocket.
- Tratamento de erros.
- Validação de entradas.
- Controle de conexões.
- Streaming de respostas, quando aplicável.
- Comunicação entre backend e frontend.
- Compatibilidade entre `api.py` e `api_fixed.py`.

Objetivo:

Estabelecer uma API consistente, segura e preparada para suportar a interface definitiva.

### 2.5 Problemas de qualidade e manutenção

Investigar:

- Código duplicado.
- Dependências ausentes ou incompatíveis.
- Imports incorretos.
- Configurações inconsistentes.
- Código não utilizado.
- Exceções mal tratadas.
- Problemas de tipagem.
- Responsabilidades misturadas.
- Acoplamento excessivo.
- Ausência de testes.
- Testes desatualizados.
- Documentação incompatível com o código atual.
- Inconsistências entre README, PROGRESS, TASKS, ROADMAP e planos de teste.

Não realizar refatorações cosméticas sem justificativa técnica.

---

# 3. PLANO DE EXECUÇÃO

A execução deverá seguir obrigatoriamente quatro fases sequenciais.

## FASE A — CORREÇÃO E ESTABILIZAÇÃO

**Objetivo:** estabelecer uma base confiável antes de evoluir a arquitetura.

### A1. Auditoria de configuração

- Verificar `pyproject.toml`.
- Verificar `requirements.txt`.
- Verificar `.env` e `config.py`.
- Identificar configurações duplicadas ou conflitantes.
- Validar caminhos relativos e absolutos.
- Padronizar versões de Python e dependências.
- Verificar configurações de desenvolvimento e produção.

Critérios de aceite:

- Dependências declaradas de maneira consistente.
- Ambiente instalável seguindo documentação.
- Configurações centralizadas.
- Nenhuma variável obrigatória ausente sem validação clara.
- Aplicação inicializa sem erros.

### A2. Correção do VectorStore

- Revisar integralmente `vector_store.py`.
- Corrigir imports e referências.
- Validar inicialização do ChromaDB.
- Garantir persistência física dos dados.
- Validar criação e recuperação de coleções.
- Validar inserção, atualização e exclusão.
- Validar isolamento entre usuários ou sessões, conforme o modelo adotado.
- Eliminar embeddings artificiais baseados em hash.
- Implementar embeddings reais, utilizando um modelo adequado à arquitetura.

Critérios de aceite:

- VectorStore inicializa corretamente.
- Dados continuam disponíveis após reiniciar o backend.
- Embeddings são gerados por um modelo real.
- Consultas retornam conteúdo relevante, não somente IDs.
- Testes de persistência e recuperação passam.

### A3. Integração efetiva da memória

Revisar:

- `conversation_manager.py`
- `memory_manager.py`
- `vector_store.py`
- `session_manager.py`
- `prompt_builder.py`

Implementar o fluxo:

1. Receber mensagem do usuário.
2. Identificar a sessão.
3. Recuperar informações relevantes da memória.
4. Recuperar o histórico necessário.
5. Construir o contexto.
6. Enviar contexto e mensagem ao modelo.
7. Receber resposta.
8. Persistir a interação.
9. Extrair e armazenar informações relevantes quando apropriado.

A memória não deve armazenar indiscriminadamente cada frase como uma memória permanente. Deve existir uma estratégia de relevância, atualização e recuperação.

Critérios de aceite:

- O cérebro consulta a memória antes de responder.
- Informações relevantes de conversas anteriores são recuperadas.
- Novas interações são persistidas.
- Informações permanecem disponíveis após reinicialização.
- Uma sessão não acessa indevidamente a memória privada de outra.
- Testes comprovam recuperação contextual.

### A4. Persistência e gerenciamento de conversas

- Revisar o armazenamento de sessões.
- Eliminar dependência exclusiva de memória RAM.
- Persistir sessões e mensagens.
- Recuperar sessões após reinicialização.
- Definir limites de histórico e contexto.
- Implementar estratégia de compactação quando necessário.
- Revisar consistência dos limites documentados e implementados.

Critérios de aceite:

- Histórico sobrevive à reinicialização.
- Sessões podem ser recuperadas.
- Mensagens mantêm sua ordem.
- Não ocorre mistura de sessões.
- Limites de contexto são respeitados.

### A5. Alinhamento de dependências e CI

- Corrigir incompatibilidade entre a versão Python do projeto e a versão utilizada no GitHub Actions.
- Padronizar a instalação das dependências.
- Revisar scripts de execução.
- Configurar execução de testes Python.
- Configurar execução de testes Playwright.
- Garantir que falhas nos testes interrompam o pipeline.

Critérios de aceite:

- CI utiliza a versão de Python compatível com o projeto.
- Dependências são instaladas corretamente.
- Testes backend são executados.
- Testes frontend são executados.
- Pipeline apresenta resultados reais e reproduzíveis.

### A6. Consolidação dos testes

Organizar os testes em categorias:

- Unitários.
- Integração.
- API.
- Memória.
- Sessões.
- IA e Model Router.
- Voz.
- Interface.
- End-to-end.

Critérios de aceite:

- Cada componente crítico possui testes.
- Testes não dependem de serviços externos sem necessidade.
- Mocks são utilizados adequadamente.
- Cenários críticos possuem cobertura automatizada.
- Não existem testes documentados como aprovados sem execução real.

---

## FASE B — CÉREBRO LOCAL E MODEL ROUTER

**Objetivo:** consolidar o cérebro do JARVIS, garantindo seleção de modelos, gerenciamento de contexto e disponibilidade dos provedores.

### B1. Provedor principal

Adotar a seguinte estratégia:

- Gemini como provedor principal.
- OmniRouter como alternativa.
- Ollama como alternativa para execução de modelos locais.

Importante: não confundir o cliente OmniRouter existente com um cliente Ollama local. São integrações distintas e devem possuir implementações e configurações próprias.

### B2. Model Router desacoplado

Revisar a arquitetura do Model Router.

O ConversationManager não deve depender diretamente de implementações específicas de provedores.

Criar ou aperfeiçoar uma abstração comum para os provedores, permitindo:

- Seleção dinâmica de modelos.
- Troca de provedor.
- Configuração independente.
- Fallback automático.
- Tratamento padronizado de respostas.
- Tratamento padronizado de erros.
- Timeouts.
- Retry controlado.
- Logs de disponibilidade.

### B3. Gerenciamento de contexto e memória

Integrar definitivamente:

- Histórico de conversas.
- Memória persistente.
- Memórias relevantes recuperadas.
- Instruções de sistema.
- Limites de tokens.
- Resumos de conversas longas.

O contexto deverá ser construído de maneira independente do provedor utilizado.

### B4. Tratamento de indisponibilidade

Implementar estratégias para:

- Falha de conexão.
- Timeout.
- Limite de requisições.
- Erros de autenticação.
- Provedor indisponível.
- Modelo inexistente.
- Respostas inválidas.
- Falhas de fallback.

Critérios de aceite da Fase B:

- Gemini funciona como provedor principal.
- OmniRouter pode assumir quando necessário.
- Ollama pode ser utilizado como alternativa local.
- A troca de provedor não exige alterações no ConversationManager.
- Falhas são tratadas sem derrubar a aplicação.
- O contexto e a memória funcionam independentemente do provedor.
- Testes automatizados validam os cenários de fallback.

---

## FASE C — INTERFACE DEFINITIVA

**Objetivo:** integrar o frontend definitivo ao backend Python, preservando a identidade visual e a esfera 3D já desenvolvida.

Frontend de referência:

https://github.com/halisonvitorino/echo-orbit-visual-companion

Não reconstruir a esfera 3D do zero.

Aproveitar a implementação existente em React, TypeScript e Three.js.

### C1. Integração do frontend

Analisar o frontend atual e integrá-lo ao backend JARVIS.

Manter:

- React.
- TypeScript.
- Three.js.
- Esfera 3D.
- Animações.
- Análise de áudio.
- Identidade visual existente.

Adaptar a interface para consumir a API real do JARVIS.

Eliminar gradualmente os dados simulados quando os respectivos recursos reais estiverem integrados.

### C2. Comunicação em tempo real

Implementar WebSocket entre frontend e backend.

Definir um protocolo de comunicação documentado e versionado.

O protocolo deverá contemplar:

- Estado do assistente.
- Mensagens do usuário.
- Respostas do modelo.
- Streaming de respostas.
- Eventos de voz.
- Transcrições.
- Dados de áudio.
- Erros.
- Reconexão.

Manter compatibilidade com os estados já previstos no frontend:

- `idle`
- `listening`
- `thinking`
- `speaking`

Ajustar o protocolo caso a implementação atual exija outros eventos.

### C3. Interface de conversação

Implementar ou integrar:

- Chat.
- Histórico.
- Identificação de sessão.
- Exibição de mensagens.
- Indicador de processamento.
- Streaming de respostas.
- Transcrição.
- Tratamento visual de erros.
- Reconexão automática.
- Estado da conexão com o backend.

### C4. Esfera 3D e estados do assistente

A esfera deverá refletir o estado real do JARVIS.

Exemplos:

- Idle: aguardando interação.
- Listening: capturando áudio.
- Thinking: processando solicitação.
- Speaking: reproduzindo resposta.

Os dados de áudio deverão alimentar a visualização, quando disponíveis.

Critérios de aceite da Fase C:

- Frontend conecta ao backend real.
- WebSocket funciona de maneira estável.
- Chat envia e recebe mensagens.
- Histórico é recuperado corretamente.
- Estados são atualizados em tempo real.
- Esfera reage aos estados reais do assistente.
- Reconexão funciona após interrupção.
- Interface não depende de simulação para suas funcionalidades principais.

---

## FASE D — VOZ E VISÃO INTEGRADAS

**Objetivo:** transformar os módulos de voz e visão existentes em fluxos funcionais, integrados ao cérebro e à interface.

### D1. Microfone e STT

Integrar o microfone do usuário à interface.

Fluxo esperado:

Microfone → Captura de áudio → Backend → Faster-Whisper → Texto reconhecido → ConversationManager.

Implementar:

- Solicitação de permissão do microfone.
- Início e encerramento da captura.
- Envio de áudio.
- Tratamento de falhas.
- Exibição da transcrição.
- Controle do estado de escuta.

### D2. TTS no frontend

Integrar o Piper TTS ao fluxo de conversação.

Fluxo esperado:

Modelo de IA → Resposta textual → Piper TTS → Áudio → Frontend → Reprodução.

A reprodução deverá ocorrer no navegador do usuário, e não apenas no computador onde o backend está executando.

Implementar:

- Recebimento do áudio.
- Reprodução.
- Controle de estado.
- Tratamento de erros.
- Interrupção da reprodução, quando necessário.

### D3. Wake Word

Revisar a implementação existente.

Diferenciar reconhecimento de texto transcrito de uma verdadeira detecção contínua de palavra de ativação.

Implementar uma solução apropriada para:

- Escuta em segundo plano.
- Detecção da palavra de ativação.
- Ativação do assistente.
- Controle de falso acionamento.
- Ativação e desativação pelo usuário.

### D4. Captura de tela

Integrar o módulo de captura de tela.

Permitir que o JARVIS obtenha uma captura autorizada da tela do usuário.

Implementar:

- Captura.
- Processamento.
- Envio ao componente de visão.
- Tratamento de permissões.
- Tratamento de erros.

### D5. Interpretação visual por IA

Integrar a captura de tela a um modelo multimodal compatível.

Fluxo esperado:

Captura de tela → Processamento da imagem → Modelo multimodal → Interpretação → Resposta do JARVIS.

O sistema deve conseguir responder a perguntas sobre o conteúdo visual recebido.

Critérios de aceite da Fase D:

- Microfone funciona pela interface.
- STT converte áudio em texto.
- Texto é enviado ao cérebro.
- Respostas são convertidas em áudio.
- Áudio é reproduzido no frontend.
- Wake Word possui detecção funcional.
- Captura de tela funciona.
- Modelo multimodal interpreta imagens capturadas.
- Os fluxos possuem testes de integração.

---

# 4. METODOLOGIA OBRIGATÓRIA DE TRABALHO DOS AGENTES

Não iniciar implementações imediatamente.

O primeiro trabalho deverá ser uma auditoria corretiva detalhada.

### Etapa 1 — Inspeção

Os agentes deverão analisar o código real da branch `developer`.

Não assumir que os problemas descritos anteriormente continuam existindo. Confirmar cada problema no código atual.

Não confiar exclusivamente na documentação.

Verificar também:

- Implementação real.
- Imports.
- Chamadas entre módulos.
- Dependências.
- Testes existentes.
- Configurações.
- Fluxos de execução.
- Logs e exceções.

### Etapa 2 — Diagnóstico

Para cada problema encontrado, registrar:

1. Identificador.
2. Fase relacionada.
3. Arquivo e localização.
4. Descrição do problema.
5. Evidência técnica.
6. Causa raiz.
7. Impacto.
8. Prioridade.
9. Solução recomendada.
10. Dependências.
11. Critérios de aceite.
12. Testes necessários.

Não criar tarefas baseadas apenas em suposições.

Classificar os achados como:

- Confirmado.
- Parcialmente confirmado.
- Não reproduzido.
- Já corrigido.
- Novo problema identificado.

### Etapa 3 — Decomposição em tarefas

Transformar cada problema confirmado em tarefas pequenas.

Cada tarefa deverá:

- Ter um único objetivo principal.
- Ser executável por um agente especializado.
- Ter escopo delimitado.
- Evitar alterações desnecessárias.
- Possuir critérios de aceite verificáveis.
- Possuir testes associados.
- Informar arquivos que podem ser modificados.
- Identificar dependências de outras tarefas.

Evitar tarefas genéricas como:

"Melhorar a memória."

Preferir:

"Corrigir a recuperação de conteúdo no método semantic_search do MemoryManager, garantindo que a consulta retorne o conteúdo das memórias encontradas."

### Etapa 4 — Priorização

Utilizar a seguinte classificação:

- **P0 — Crítico:** impede inicialização, compromete dados, segurança ou funcionamento central.
- **P1 — Alto:** impede a conclusão de uma fase ou quebra integração essencial.
- **P2 — Médio:** limita qualidade, manutenção ou confiabilidade.
- **P3 — Baixo:** melhoria não bloqueante.

As tarefas também devem respeitar dependências técnicas.

Não iniciar uma tarefa se suas dependências ainda não estiverem concluídas.

### Etapa 5 — Distribuição entre agentes

Distribuir as tarefas conforme especialização:

**Agente Backend/Python**

- FastAPI.
- ConversationManager.
- Model Router.
- Integração de provedores.
- Configurações.
- Tratamento de erros.

**Agente Memory/Database**

- MemoryManager.
- VectorStore.
- ChromaDB.
- Embeddings.
- Persistência.
- Recuperação contextual.

**Agente Frontend**

- React.
- TypeScript.
- Three.js.
- Interface.
- Chat.
- Estados.
- WebSocket.

**Agente Voice/Vision**

- Faster-Whisper.
- Piper.
- Microfone.
- Wake Word.
- Captura de tela.
- Modelos multimodais.

**Agente QA/Testes**

- Testes unitários.
- Testes de integração.
- Playwright.
- API.
- Regressão.
- CI/CD.
- Validação dos critérios de aceite.

**Agente Revisor/Arquiteto**

- Revisar soluções.
- Identificar conflitos.
- Verificar arquitetura.
- Aprovar integrações.
- Validar qualidade.
- Impedir alterações fora do escopo.

O agente principal deverá coordenar a execução e manter uma única visão do progresso.

### Etapa 6 — Implementação incremental

Executar uma tarefa por vez ou em paralelo somente quando não houver dependências ou conflitos entre arquivos.

Para cada tarefa:

1. Ler o código envolvido.
2. Entender o comportamento atual.
3. Implementar a menor correção possível.
4. Criar ou atualizar os testes.
5. Executar os testes.
6. Revisar o resultado.
7. Registrar arquivos alterados.
8. Atualizar a documentação.
9. Marcar a tarefa como concluída somente após validação.

Não declarar uma tarefa concluída apenas porque o código foi escrito.

### Etapa 7 — Validação de fase

Ao finalizar cada fase:

- Executar a suíte de testes correspondente.
- Executar testes de regressão.
- Verificar integração com os componentes anteriores.
- Conferir logs.
- Conferir documentação.
- Registrar resultados reais.
- Apresentar problemas remanescentes.

A fase seguinte só poderá começar depois da aprovação da fase anterior.

---

# 5. REGRAS E RESTRIÇÕES

As seguintes regras são obrigatórias:

1. Não reconstruir o projeto do zero.
2. Não remover componentes funcionais sem justificativa técnica.
3. Não implementar funcionalidades fora das quatro fases definidas.
4. Não adicionar integrações como Gmail, Google Calendar, WhatsApp ou controle geral do Windows nesta intervenção.
5. Não substituir tecnologias existentes sem apresentar justificativa técnica.
6. Não criar abstrações desnecessárias.
7. Não duplicar funcionalidades já implementadas.
8. Não criar arquivos alternativos sem necessidade.
9. Não ocultar falhas de testes.
10. Não utilizar mocks para declarar que uma integração real está concluída.
11. Não marcar funcionalidades como concluídas apenas porque seus módulos existem.
12. Não modificar a esfera 3D sem necessidade comprovada.
13. Preservar a compatibilidade entre frontend e backend.
14. Preservar dados existentes antes de alterações em estruturas de armazenamento.
15. Não expor chaves de API, tokens ou credenciais nos logs.
16. Solicitar aprovação antes de alterações destrutivas ou migrações irreversíveis.
17. Manter as alterações rastreáveis por commits pequenos e descritivos, quando o fluxo de trabalho permitir.

**Importante sobre autonomia:** os agentes possuem autonomia para inspecionar, diagnosticar, propor e implementar correções dentro do escopo autorizado. Ações destrutivas, alterações irreversíveis de dados ou mudanças de arquitetura que extrapolem este documento exigem aprovação.

---

# 6. ENTREGÁVEIS OBRIGATÓRIOS

Antes de começar a implementação, apresentar:

### Entregável 1 — Relatório de auditoria

Documento com todos os problemas confirmados, evidências, causas e impactos.

### Entregável 2 — Backlog técnico

Lista de tarefas pequenas, priorizadas e organizadas por fase.

Cada tarefa deverá seguir este modelo:

**ID:** JARVIS-A-001  
**Título:** Corrigir inicialização do VectorStore.  
**Prioridade:** P0.  
**Fase:** A.  
**Problema:** Descrição objetiva.  
**Causa raiz:** Evidência técnica.  
**Arquivos envolvidos:** Lista de arquivos.  
**Solução proposta:** Alteração necessária.  
**Dependências:** IDs de outras tarefas, se existirem.  
**Agente responsável:** Especialidade.  
**Critérios de aceite:**

- [ ] VectorStore inicializa sem erro.
- [ ] Persistência funciona.
- [ ] Dados podem ser recuperados após reinicialização.
- [ ] Testes automatizados passam.

**Testes:** Descrição dos testes necessários.  
**Definição de pronto:** Critérios que determinam a conclusão.

### Entregável 3 — Mapa de dependências

Apresentar a ordem recomendada de execução, identificando quais tarefas podem ser realizadas em paralelo.

### Entregável 4 — Plano de execução

Apresentar a sequência de implementação, os agentes responsáveis e os pontos de validação.

### Entregável 5 — Relatório de conclusão

Ao final de cada fase, apresentar:

- Tarefas concluídas.
- Arquivos modificados.
- Testes executados.
- Resultados reais dos testes.
- Problemas encontrados durante a implementação.
- Débitos técnicos restantes.
- Tarefas pendentes.
- Situação da fase.

---

# 7. DEFINIÇÃO GLOBAL DE SUCESSO

Esta intervenção será considerada concluída quando:

- A memória estiver efetivamente integrada ao cérebro.
- As conversas possuírem persistência confiável.
- O VectorStore estiver funcional e utilizando embeddings reais.
- O Model Router estiver desacoplado dos provedores.
- Gemini, OmniRouter e Ollama estiverem integrados conforme seus respectivos papéis.
- A API estiver estável e preparada para comunicação em tempo real.
- O frontend React/Three.js estiver integrado ao backend.
- A esfera 3D refletir os estados reais do assistente.
- Chat, histórico e comunicação em tempo real funcionarem.
- Voz e visão estiverem integradas aos respectivos fluxos.
- Os testes críticos estiverem automatizados e aprovados.
- O CI estiver alinhado com as dependências e versões do projeto.
- A documentação refletir fielmente a implementação existente.

---

# 8. PRIMEIRA ORDEM DE EXECUÇÃO

**Neste primeiro momento, NÃO implemente nenhuma alteração no código.**

Execute somente a auditoria corretiva.

Sua primeira resposta deverá conter:

1. Diagnóstico atualizado da branch `developer`.
2. Confirmação ou contestação dos problemas anteriormente identificados.
3. Novos problemas encontrados dentro do escopo deste documento.
4. Backlog completo, dividido entre Fases A, B, C e D.
5. Priorização P0, P1, P2 e P3.
6. Critérios de aceite para cada tarefa.
7. Identificação dos agentes mais adequados para cada tarefa.
8. Mapa de dependências.
9. Ordem recomendada de execução.
10. Riscos técnicos e possíveis impactos sobre o código existente.

Não comece a implementação até apresentar esse diagnóstico e o backlog para revisão.

Após a aprovação do backlog, inicie a Fase A e avance sequencialmente.

**DIRETRIZ FINAL:**

Nosso objetivo não é adicionar mais funcionalidades rapidamente. É transformar o que já foi desenvolvido em uma aplicação consistente, funcional, testável e bem integrada.

Priorize qualidade, integração real, persistência, confiabilidade e manutenção.

Não confunda código existente com funcionalidade concluída. Toda funcionalidade deverá ser validada por meio de seu fluxo real de execução e testes reproduzíveis.
