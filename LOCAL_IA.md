Atue como um Engenheiro de Software Sênior especialista em Python e integração de LLMs locais.

Preciso migrar o cérebro do meu assistente "Jarvis" de uma API em nuvem para rodar 100% localmente no meu computador usando o **Ollama** com um modelo **Llama** (como o `qwen3:4b` ou `llama3.1:4b`).

Analise a estrutura atual do meu projeto e faça as seguintes alterações:

1. **Substituição do Cliente de API:**
   - Localize onde o projeto faz chamadas para o provedor de IA atual (nuvem) e substitua a conexão para apontar para o servidor local do Ollama: `http://localhost:11434/v1` (usando o SDK padrão compatível com OpenAI ou a biblioteca oficial `ollama`).
   - Defina uma chave de API fictícia (ex: `api_key="ollama"`), removendo a obrigatoriedade de chaves reais da nuvem para que o app não trave caso o `.env` não tenha chaves externas.

2. **Configuração do Modelo Llama:**
   - Configure o modelo padrão como `qwen3:4b` (ou permita configurá-lo facilmente via variável `OLLAMA_MODEL` no `.env`).
   - Garanta que a estrutura de `messages` (system prompt, histórico e user prompt) e eventuais chamadas de ferramentas/funções (`tools` / `function calling`) continuem funcionando corretamente com o padrão do Ollama.

3. **Tratamento de Erros e Instruções:**
   - Adicione um tratamento de erro amigável caso o serviço do Ollama não esteja rodando em segundo plano no momento em que eu iniciar o Jarvis (ex: avisando no terminal para abrir o Ollama ou rodar `ollama run llama3.2`).
   - Atualize o `requirements.txt` se alguma nova biblioteca for necessária.

Por favor, examine os arquivos do meu projeto primeiro, me explique brevemente quais arquivos serão modificados e aplique as mudanças no código.
