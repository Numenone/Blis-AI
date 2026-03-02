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

Este projeto foi desenvolvido utilizando o agente autônomo **Antigravity** (Google DeepMind). A IA atuou como um parceiro de pair programming de nível sênior, realizando:

1.  **Refatoração para Async**: Conversão de todo o grafo para execução assíncrona para permitir streaming real de tokens.
2.  **Checkpointer Customizado**: Desenvolvimento de um adaptador Redis para contornar limitações de provedores de nuvem que não suportam RediSearch.
3.  **Frontend Robusto**: Implementação de leitura de stream com buffer de linha para evitar que mensagens cheguem "quebradas" ao usuário.
4.  **Otimização de Performance**: Diagnóstico e correção de gargalos causados pela re-inicialização constante de modelos de embeddings.

---

**Desenvolvido como parte do Teste Técnico para a Blis AI.** 🌍✈️🚀
