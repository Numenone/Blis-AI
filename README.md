# 🌍 Blis AI - Seu Assistente Inteligente de Viagens

Seja bem-vindo ao **Blis AI**, um projeto desenvolvido com o objetivo de reimaginar como planejamos nossas aventuras pelo mundo. Mais do que um simples chatbot, o Blis AI é um ecossistema de agentes especializados que trabalham em harmonia para garantir que cada detalhe da sua viagem seja planejado com precisão, segurança e informação em tempo real.

---

## �️ Por dentro da Inteligência

A arquitetura do Blis AI foi construída sobre bases sólidas: **FastAPI** para uma comunicação ágil e **LangGraph** para orquestrar o raciocínio dos nossos agentes:

1.  **Orchestrator (O Maestro)**: Ele é o primeiro a ouvir sua mensagem. Sua função é entender exatamente o que você precisa e decidir se deve chamar o especialista em documentos ou o mestre das buscas na web.
2.  **FAQ Agent (RAG)**: Imagine um consultor que leu todos os manuais de política de viagem da Blis. Ele utiliza **RAG (Retrieval-Augmented Generation)** para buscar respostas diretamente nos arquivos que você alimenta.
3.  **Search Agent (Web Search)**: Para informações que mudam a cada segundo (clima, preço de passagens, horários), ele consulta a web em tempo real via **Tavily**.
4.  **Guardian Protocol**: Nossa camada de proteção que garante que a conversa foque no que importa: viagens. Ele bloqueia tentativas de desviar o assunto ou comandos maliciosos.

---

## 🚀 O que torna o Blis AI especial?

### 💬 Painel de Atendimento (UI/UX)
Desenvolvemos uma interface inspirada na fluidez do WhatsApp. O foco aqui foi a **humanização**:
*   **Feedback em Tempo Real**: Assim que você envia uma mensagem, o sistema avisa que está "Buscando informações...", eliminando a ansiedade da espera.
*   **Typing Inteligente**: O cursor de digitação (`caret`) só aparece quando a IA realmente começa a falar, criando uma experiência de chat natural e profissional.
*   **Markdown Completo**: Respostas organizadas com negritos, listas e links clicáveis para facilitar a leitura.

### 📁 Gestão de Conhecimento (RAGs)
Você tem o controle total sobre o que a IA sabe. Através do **Painel de Documentos**, você pode:
*   **Alimentar a IA**: Faça upload de PDFs, arquivos Markdown ou planilhas Excel (`.xlsx`, `.xls`).
*   **Gerenciar**: Liste todos os documentos ativos e remova conteúdos antigos com um clique, garantindo que a IA nunca traga informações defasadas.

### � Histórico com Persistência (History)
Nada se perde. Graças ao nosso adaptador customizado para **Redis Standard**, suas conversas são salvas e permanecem acessíveis mesmo se você fechar o navegador ou atualizar a página. O Thread ID garante que cada conversa seja única e contínua.

### 🛠️ Playground Swagger
Para os desenvolvedores, o `/docs` (Swagger) oferece um ambiente completo para testar cada endpoint, desde o streaming de chat até a listagem de documentos, tudo protegido por autenticação.

---

## 🤖 Como usei IA no desenvolvimento (Requisito Obrigatório)

Este projeto não foi apenas "escrito", ele foi **orquestrado** em uma parceria profunda entre humano e inteligência artificial.

### **Minha Ferramenta de Trabalho**
Utilizei o **Antigravity**, um agente autônomo de codificação de última geração (projeto da Google DeepMind). Diferente de um simples preenchimento automático, o Antigravity atua como um parceiro de pair programming que entende o contexto global do projeto.

É possível trocar o modelo da LLM e o Gateway direto pelo painel ou pelo endpoint, on-live!

*   **Modelo**: GPT-4o-mini (da OpenAI).
*   **Gateway**: OpenRouter (escolhido pela versatilidade e estabilidade).

### **Os Superpoderes da IA (MCPs)**
Para que a IA pudesse me ajudar de verdade, configurei o **Model Context Protocol (MCP)** com capacidades específicas:
*   **MCP de Filesystem**: Essencial para a IA "enxergar" e manipular toda a estrutura de pastas e arquivos. Foi ela quem criou a arquitetura modular do projeto do zero.
*   **MCP de Terminal/Shell**: A IA não apenas sugeria comandos; ela os executava para subir o servidor Uvicorn, realizar diagnósticos de rede (resolvendo conflitos de porta 8000/8005) e gerenciar commits no Git.
*   **MCP de Busca (Tavily)**: Usado pela IA para consultar documentações atualizadas da LangChain e FastAPI, garantindo que não usássemos métodos depreciados.
*   **MCP de Knowledge Discovery**: Permitiu que a IA analisasse padrões de design complexos e sugerisse a melhor forma de implementar o checkpointer do Redis.

### **Casos Reais de Apoio**
1.  **Refatoração SSE**: Inicialmente, as mensagens chegavam "travadas". A IA analisou os logs de eventos e reescreveu todo o fluxo de streaming para ser 100% assíncrono, permitindo que cada caractere aparecesse na tela assim que gerado.
2.  **Resiliência do Redis**: Quando percebemos que o servidor não tinha o módulo `RediSearch`, a IA projetou um adaptador customizado usando apenas comandos básicos do Redis, garantindo que o chat funcionasse em qualquer infraestrutura.
3.  **Debug de UI**: A IA identificou um erro silêncio de JavaScript que impedia o envio de mensagens após o reset da sessão e aplicou uma correção preventiva ("defensive programming") em todo o frontend.

### **O Toque Humano (O que precisei ajustar)**
Nem tudo foi automático. A supervisão humana foi vital em:
*   **Tom de Voz**: Tive que calibrar o `GUARDIAN_PROTOCOL`. A IA estava sendo "estrita demais", bloqueando perguntas simples sobre o clima. Eu ajustei as instruções para que ela fosse mais prestativa sem perder a segurança.
*   **UX Design**: Decidi manualmente por esconder o cursor piscante enquanto a mensagem de "Buscando..." estava ativa, uma decisão estética que a IA implementou sob minha orientação para deixar o visual mais limpo.
*   **Hierarquia de Dados**: Organizei manualmente a estrutura de pastas do ChromaDB para garantir backups consistentes.

---

**Desenvolvido como parte do Teste Técnico para a Blis AI.** 🌍✈️🚀
