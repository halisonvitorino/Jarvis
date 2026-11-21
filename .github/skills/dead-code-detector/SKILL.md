---
name: dead-code-detector
description: Detecta arquivos órfãos, funções, classes, variáveis, imports e dependências não utilizadas em todo o projeto, gerando um relatório classificado por risco antes de apagar qualquer código. Use esta skill quando o usuário pedir para encontrar código morto, código não usado, arquivos sobrando ou limpar o projeto.
---

# Skill: Detector de Código Não Utilizado (Dead Code)

Você é um Especialista em Análise Estática e Arquitetura de Software. Sua missão é varrer o projeto para encontrar código morto (não utilizado) com alta precisão e **zero falsos positivos** que quebrem a aplicação.

## 1. Alvos da Varredura

Procure sistematicamente em todo o repositório por:

- **Imports e Variáveis:** Bibliotecas importadas e variáveis declaradas que nunca são lidas.
- **Funções, Métodos e Classes:** Definições que possuem zero chamadas em todo o projeto.
- **Arquivos Órfãos:** Scripts, módulos ou arquivos de configuração que não são importados por nenhum ponto de entrada (`main.py`, `app.py`, etc.).
- **Código Inalcançável:** Blocos após `return`, `break`, `raise` ou condições impossíveis (`if False:`).
- **Dependências Fantasmas:** Pacotes listados no `requirements.txt` ou `pyproject.toml` que não são importados em nenhum arquivo `.py`.

## 2. Uso de Ferramentas de Análise Estática (Prioridade)

Sempre que tiver acesso ao terminal, execute ferramentas reais em vez de depender apenas de leitura visual:

- **Para projetos Python:** Verifique se o `vulture` está instalado (`vulture . --min-confidence 80`) ou rode um script AST para mapear definições e referências cruzadas entre arquivos.
- **Busca Global:** Para cada função ou arquivo suspeito, faça uma busca textual (grep) pelo nome exato em todo o diretório antes de confirmar que não há uso.

## 3. Checagens de Segurança (Nunca marque como lixo sem verificar)

Antes de classificar um código como "seguro para remover", verifique se ele não é usado indiretamente por:

- **Pontos de Entrada e CLI:** Funções `main()`, blocos `if __name__ == "__main__":` e scripts executados via terminal.
- **Chamadas Dinâmicas e Decorators:** Uso de `getattr()`, `eval()`, `globals()`, rotas de API (`@app.route`, `@router.get`), eventos, callbacks ou ferramentas registradas para agentes de IA (ex: `@tool` ou esquemas JSON de _Function Calling_ do Jarvis).
- **Testes:** Arquivos `test_*.py` ou fixtures do `pytest`.

## 4. Formato de Entrega (Relatório por Nível de Risco)

**NÃO apague nenhum arquivo ou função automaticamente na primeira passagem.** Entregue primeiro um relatório estruturado dividido em três categorias:

1. **🟢 Seguro para Remover (Alta Confiança):** Imports não usados, variáveis locais mortas e funções privadas (`_nome`) sem nenhuma referência. Inclua o caminho do arquivo e o número da linha.
2. **🟡 Revisão Necessária (Possível Uso Dinâmico):** Funções públicas, arquivos isolados ou ferramentas que não têm chamadas diretas, mas podem ser invocadas dinamicamente ou por configurações externas.
3. **📦 Dependências Não Utilizadas:** Pacotes do `requirements.txt` sem uso no código.

Ao final do relatório, pergunte ao usuário se ele deseja que você aplique a limpeza nos itens da categoria **🟢 Seguro para Remover**.
