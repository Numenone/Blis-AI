# 🌍 Blis AI - Assistente Inteligente de Viagens

Seja bem-vindo ao projeto **Blis AI**, um ecossistema de agentes inteligentes projetado para transformar a experiência de planejamento de viagens. Este sistema utiliza uma arquitetura multi-agente avançada para fornecer respostas precisas, seguras e em tempo real.

---

## 🏗️ Arquitetura do Sistema

O projeto foi construído utilizando **FastAPI** e **LangGraph**, seguindo um fluxo de orquestração inteligente:

1.  **Orchestrator (O Maestro)**: Recebe a mensagem do usuário e decide o fluxo ideal. Se for uma dúvida de política interna, consulta a FAQ. Se for algo em tempo real (voos, clima), aciona a busca web.
2.  **FAQ Agent (RAG)**: Especialista em políticas de bagagem e documentação. Utiliza **RAG (Retrieval-Augmented Generation)** com uma base de dados vetorial (**ChromaDB**) para garantir que as informações sejam oficiais e precisas.
3.  **Search Agent (Web Search)**: Integrado com a API **Tavily**, este agente busca na internet dados atualizados sobre preços, conexões e condições climáticas.
4.  **Guardian Protocol**: Uma camada de segurança robusta aplicada nos prompts de todos os agentes para evitar *prompt injection* e garantir que a IA se mantenha estritamente no domínio de viagens.
5.  **OpenRouter Integration**: O projeto utiliza o **OpenRouter** como gateway unificado para acessar modelos de linguagem de ponta (como GPT-4o e Claude), garantindo flexibilidade e facilidade de troca de modelos.

---

## 🚀 Funcionalidades Principais

*   **⚙️ Escolha Dinâmica de IA**: Interface para trocar o gateway (OpenRouter, OpenAI, Local), o modelo e a chave de API sem reiniciar o servidor.
*   **💬 Painel de Atendimento (`/painel`)**: Interface moderna inspirada no WhatsApp, com suporte completo a **Markdown**, links clicáveis e uma animação de digitação humana com cursor interativo.
*   **⚡ Streaming de Respostas (SSE)**: As respostas são geradas caractere por caractere, reduzindo a latência percebida e tornando a interação mais dinâmica.
*   **🔒 Segurança de Elite**: Autenticação via `X-API-Key` e proteção contra vazamento de dados internos de código ou arquivos.
*   **💾 Persistência com Redis Stack**: Histórico de chat persistente utilizando o checkpointer nativo do LangGraph com [Redis Stack](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/) (Necessário para persistência de sessões com RediSearch). (Possui fallback automático para memória RAM caso o Redis não esteja disponível).
*   **🐳 Dockerizado**: Pronto para rodar em containers com builds otimizados e healthchecks de serviços.

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
2.  Configure o arquivo `.env` com suas chaves (veja `.env.example`).
3.  Inicie o servidor:
```bash
uvicorn app.main:app --reload
```

---

## 📖 Documentação da API

*   **Swagger UI (`/docs`)**: Documentação interativa de todos os endpoints. Use o token de autorização `blis_secret_token_123` para testar.
*   **Chat Endpoint (`POST /chat`)**: Recebe `session_id` e `message`. Suporta streaming via cabeçalho `Accept: text/event-stream`.
*   **Painel de Chat (`/painel`)**: Acesso visual para interagir com a IA diretamente pelo navegador.

---

## ⚙️ Configuração Dinâmica (LLM Tooling)

Este projeto permite que você teste diferentes modelos e provedores em tempo real através da UI ou da API:

1.  **No Painel (`/painel`)**: Clique no ícone de **engrenagem** no topo. Você poderá inserir o endpoint do seu provedor (ex: `https://api.openai.com/v1` ou localmente via Ollama), o nome do modelo e sua chave pessoal.
2.  **No Swagger (`/docs`)**: O endpoint `POST /chat` agora aceita os campos opcionais:
    *   `llm_model`: O ID do modelo (ex: `anthropic/claude-3.5-sonnet`).
    *   `llm_gateway`: A URL base do provedor.
    *   `llm_api_key`: Sua chave de API privada para aquele provedor.

---

## 🤖 Como usei IA no desenvolvimento (Requisito Obrigatório)

Para a construção deste projeto, utilizei a ferramenta de codificação agente **Antigravity** (desenvolvida pela Google DeepMind), operando em modo proativo para orquestrar o ciclo de vida do software.

### **Ferramentas e MCPs Utilizados:**
*   **Framework**: Antigravity Agent.
*   **Capacidades (Tools/MCPs)**:
    *   `Filesystem`: Gestão completa da estrutura de arquivos e refatoração de módulos.
    *   `Shell/Terminal`: Execução de comandos para testes de ambiente, migrações e validação do Docker.
    *   `Search/Browser`: Pesquisa de documentação técnica para integração do `langgraph-checkpoint-redis`.

### **Exemplos Reais de Apoio da IA:**
1.  **Depuração de Streaming (SSE)**: A IA identificou que metadados internos do roteador estavam "vazando" para o chat e implementou um filtro inteligente no backend.
2.  **Desenvolvimento da UI**: A lógica de animação do cursor (*caret*) que segue o texto Markdown em tempo real foi gerada e iterada pela IA para garantir que funcionasse mesmo em listas complexas.
3.  **Segurança (Prompt Hardening)**: A IA sugeriu a implementação do **Guardian Protocol** usando tags XML, o que bloqueou tentativas de *prompt injection* que pedia receitas de bolo ou acesso ao código-fonte.

### **O que funcionou e intervenções manuais:**
O uso de IA foi extremamente eficiente na prototipagem da interface e na estruturação do grafo do LangGraph. No entanto, houve a necessidade de **intervenção manual** no refinamento da velocidade da animação de digitação para garantir um "feeling" mais humano e no ajuste final da ordem das camadas do Docker para otimizar o cache de build.

---

**Desenvolvido como parte do Teste Técnico para a Blis AI.** 🌍✈️🚀