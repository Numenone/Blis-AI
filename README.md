# 🌍 Blis AI - Assistente Inteligente de Viagens

Seja bem-vindo ao projeto **Blis AI**, um ecossistema de agentes inteligentes projetado para transformar a experiência de planejamento de viagens. Este sistema utiliza uma arquitetura multi-agente avançada para fornecer respostas precisas, seguras e em tempo real.

---

## 🏗️ Arquitetura do Sistema

O projeto foi construído utilizando **FastAPI** e **LangGraph**, seguindo um fluxo de orquestração inteligente:

1.  **Orchestrator (O Maestro)**: Analisa a intenção do usuário e roteia para o especialista adequado.
2.  **FAQ Agent (RAG)**: Especialista em políticas e documentação. Utiliza **RAG (Retrieval-Augmented Generation)** com **ChromaDB** ou **Supabase**.
3.  **Search Agent (Web Search)**: Integrado com **Tavily**, busca dados em tempo real (clima, voos, roteiros).
4.  **Guardian Protocol**: Camada de blindagem de prompt para manter a IA estritamente no domínio de viagens.
5.  **Standard Redis Checkpointer**: Implementação personalizada (`AsyncStandardRedisSaver`) que garante persistência de sessão em **qualquer servidor Redis padrão**, sem depender de módulos extras como RediSearch.

---

## 🚀 Funcionalidades Principais

*   **⚡ Latência Otimizada**: Utiliza cache de componentes (`app.state`) para Embeddings e VectorStores, eliminando o atraso de inicialização em cada mensagem.
*   **🔵 Feedback Instantâneo**: Envio imediato de payload SSE ("Buscando informações...") para reduzir a latência percebida pelo usuário.
*   **💬 Painel de Atendimento Moderno**: Interface inspirada no WhatsApp com suporte a Markdown, animações suaves e persistência de sessão.
*   **💾 Persistência Robusta**: Histórico de chat salvo no Redis, mantendo o contexto mesmo após reinicializações do servidor ou F5 na página.
*   **🔒 Segurança Total**: Filtros contra vazamento de código, caminhos de sistema e *prompt injections*.
*   **⚙️ Configuração Dinâmica**: Troca de modelos (GPT-4, Claude), chaves de API e Gateways em tempo real pelo painel de configurações.

---

## 🛠️ Como Executar o Projeto

### 📦 Via Docker (Recomendado)
Certifique-se de que o **Docker Desktop** esteja rodando e execute:
```bash
docker compose up --build
```
A API estará disponível em `http://localhost:8000`.

### 🐍 Nativamente (Desenvolvimento)
1.  Instale as dependências: `pip install -e .`
2.  Configure o arquivo `.env` (veja `.env.example`).
3.  Inicie o servidor (utilize a porta 8005 para evitar conflitos comuns):
```bash
uvicorn app.main:app --port 8005 --reload
```

---

## 📖 Documentação da API

*   **Swagger UI (`/docs`)**: Documentação interativa. Use a API Key padrão: `blis_secret_token_123`.
*   **Chat History (`GET /api/history/{session_id}`)**: Recupera o histórico limpo da sessão (apenas mensagens Human/AI).
*   **Chat Endpoint (`POST /chat`)**: Suporta streaming SSE para respostas em tempo real.

---

## 🤖 Como usei IA no desenvolvimento (Requisito Obrigatório)

Este projeto foi construído utilizando um fluxo de **Pair Programming de Próxima Geração**, aproveitando as capacidades do agente autônomo **Antigravity** (Google DeepMind). A maturidade no uso de ferramentas de IA foi um pilar central para atingir a robustez técnica do produto final.

### **Ferramentas Utilizadas**
- **Orquestrador**: Antigravity Agent (Google DeepMind).
- **Modelo de Linguagem**: OpenAI GPT-4o-mini (via gateway OpenRouter).

### **MCPs (Model Context Protocol) e Capacidades Configuradas**
A IA operou com acesso a ferramentas avançadas que permitiram uma compreensão profunda do projeto:
- **`Filesystem`**: Utilizado para gerenciar a estrutura de diretórios, criar módulos do zero e realizar refatorações em larga escala (ex: conversão de síncrono para assíncrono em múltiplos arquivos).
- **`Shell/Terminal`**: Execução proativa de comandos `uvicorn`, `git`, `redis-cli` e diagnósticos de rede (`netstat`) para resolver conflitos de porta e validar o estado do servidor em tempo real.
- **`Knowledge Discovery`**: Acesso a base de conhecimento sobre padrões de projeto LangGraph, o que permitiu a implementação do `AsyncStandardRedisSaver` quando o checkpointer nativo falhou em ambientes padrão.
- **`Web Browser/Search`**: Utilizado para consultar a documentação de última hora da LangChain e Tavily, garantindo o uso de APIs atualizadas.

### **Exemplos Reais de Apoio da IA**
1.  **Debug de Streaming SSE**: A IA analisou logs de rede e identificou que o `orchestrator` estava enviando eventos de "raciocínio interno" para o stream. Ela projetou e implementou um filtro de metadados (`metadata.get("langgraph_node")`) para limpar a interface do usuário.
2.  **Refatoração Arquitetural**: Ao notar que o streaming não funcionava "token-a-token", a IA propôs e executou a transformação de todos os nodos do grafo em funções `async`, injetando corretamente o `RunnableConfig` para permitir a propagação de eventos.
3.  **Otimização de Latência (Gargalo de Embeddings)**: Através da análise de tempos de resposta, a IA identificou que recriar o `OpenAIEmbeddings` em cada requisição custava ~1.5s. Ela sugeriu e implementou o cache no `app.state` do FastAPI (lifespan).
4.  **Resiliência de Persistência**: Quando o Redis local falhou por falta do módulo RediSearch, a IA escreveu um adaptador customizado usando comandos `HSET/SCAN` puros, garantindo que o projeto funcionasse em qualquer infraestrutura.

### **Intervenções e Lógica Humana vs. IA**
- **O que funcionou bem**: A geração de boilerplates, lógica de persistência e a interface visual inspirada no WhatsApp foram quase 100% conduzidas pela IA sob minha supervisão.
- **Correções Manuais e Decisões de Design**:
    - **Refinamento de Tom**: Ajustei manualmente o `GUARDIAN_PROTOCOL` para ser mais amigável e permitir temas específicos (clima/tempo) que a IA estava bloqueando por excesso de zelo.
    - **UX de Latência**: Tomei a decisão de design de enviar uma mensagem imediata "Buscando informações..." via SSE, uma técnica de *optimistic UI* que a IA implementou seguindo minha orientação para melhorar a percepção de velocidade.
    - **Ordem de Docker**: Ajustei a ordem das camadas do `Dockerfile` manualmente para garantir que mudanças no `README.md` não invalidassem o cache de instalação de dependências Python.

---

**Desenvolvido como parte do Teste Técnico para a Blis AI.** 🌍✈️🚀
