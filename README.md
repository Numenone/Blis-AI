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
*   **🔵 Feedback Instantâneo**: Streaming SSE inteligente que exibe "Buscando informações..." imediatamente enquanto o modelo processa a consulta.
*   **💬 Painel de Atendimento Moderno**: Interface inspirada no WhatsApp com suporte a Markdown, animações suaves e persistência de sessão.
    *   **Persistência em Redis**: Histórico de chat que sobrevive a recarregamentos de página.
    *   **Caret Sincronizado**: Cursor de digitação inteligente que só aparece quando o conteúdo real começa a fluir.
*   **📁 Ingestão e Gestão de Documentos (RAG Full)**: 
    *   Upload de arquivos `.pdf`, `.md`, `.xlsx` e `.xls`.
    *   **Painel de Gestão**: Interface para listar e excluir documentos do conhecimento da IA em tempo real.
*   **🛡️ Robustez e Segurança**: 
    *   Protocolo UNBREAKABLE de proteção contra Injeção de Prompt.
    *   **UI Fail-Safe**: Tratamento de erros e validações no frontend para garantir que o chat nunca pare de responder.
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
3.  Inicie o servidor:
```bash
uvicorn app.main:app --port 8000 --reload
```

---

## 📖 Documentação da API

*   **Swagger (`/docs`)**: Documentação interativa para teste de endpoints.
*   **Gestão (`/api/documents`)**: Endpoints `GET` para listar e `DELETE` para remover fontes do RAG.
*   **Histórico (`/api/history/{id}`)**: Recupera o contexto da conversa persistido no Redis.

---

## 🤖 Como usei IA no desenvolvimento (Requisito Obrigatório)

Este projeto foi construído utilizando um fluxo de **Desenvolvimento Orientado a Agentes AI**, aproveitando as capacidades do agente autônomo **Antigravity** (Google DeepMind).

### **Destaques da Colaboração IA**
1.  **Arquitetura Redis Customizada**: A IA projetou e implementou o `AsyncStandardRedisSaver` do zero para garantir persistência sem depender de módulos Redis corporativos caros.
2.  **Sistema de Gestão RAG**: A IA criou toda a esteira de deleção de documentos, localizando chunks no ChromaDB baseados em metadados de arquivo para permitir uma limpeza seletiva do conhecimento.
3.  **UX de Streaming**: Implementação de um sistema de fila (`typingQueue`) no frontend para garantir que o Markdown seja renderizado suavemente enquanto os tokens chegam, mantendo o scroll sempre no lugar correto.
4.  **Resiliência de UI**: Após detectar falhas silenciosas de script, a IA implementou um sistema de *defensive programming* no frontend, garantindo que mesmo falhas de rede não travem a interface do usuário.
5.  **Caret Inteligente**: Lógica customizada para sincronizar o cursor de digitação (`caret`) apenas com o fluxo real de dados, ocultando-o durante estados de carregamento.

---

**Desenvolvido como parte do Teste Técnico para a Blis AI.** 🌍✈️🚀
