Segue uma versão mais estruturada e objetiva do seu prompt:

---

# Contexto

Atualmente trabalho em uma squad enxuta composta por:

- 1 Product Manager
- 1 Tech Lead
- 2 Engenheiros de Software Backend Pleno

Nossa missão é aumentar o nível de automação do ciclo de desenvolvimento de software, reduzindo atividades manuais e melhorando a consistência dos processos.

Hoje, a etapa de refinamento já utiliza um fluxo baseado em orquestração de agentes de IA para apoiar a análise, decomposição e especificação de demandas.

Na fase de implementação, adotamos a abordagem **SDD (Spec-Driven Development)**, utilizando especificações como principal fonte de verdade para orientar o desenvolvimento.

Referência:

- [How I Finally Sorted My Claude Code Memory](https://www.youngleaders.tech/p/how-i-finally-sorted-my-claude-code-memory?utm_source=chatgpt.com)

# Objetivo

Quero projetar uma arquitetura de agentes, skills, rotinas e mecanismos de memória que permitam ao Claude Code:

1. Manter contexto persistente entre diferentes sessões de desenvolvimento.
2. Compartilhar conhecimento entre múltiplos repositórios pertencentes ao mesmo produto ou domínio de negócio.
3. Aprender continuamente a partir de decisões arquiteturais, ADRs, refinamentos, incidentes e implementações anteriores.
4. Reduzir a necessidade de reexplicar regras de negócio, padrões arquiteturais e convenções técnicas a cada nova sessão.
5. Aumentar a qualidade das sugestões de código e das análises realizadas pelos agentes.

# Cenário Desejado

Gostaria que a solução fosse capaz de armazenar e recuperar informações como:

## Conhecimento de Negócio

- Glossário de domínio
- Regras de negócio
- Fluxos críticos
- Eventos de domínio
- Integrações externas

## Conhecimento Técnico

- Arquitetura dos sistemas
- ADRs (Architecture Decision Records)
- Padrões adotados
- Convenções de código
- Estratégias de observabilidade
- Decisões de infraestrutura

## Conhecimento Operacional

- Incidentes passados
- Postmortems
- Problemas recorrentes
- Runbooks
- Lições aprendidas

## Conhecimento de Desenvolvimento

- Features implementadas
- Bugs corrigidos
- Refatorações realizadas
- Especificações históricas
- Relação entre specs e código produzido

# O que estou buscando

Gostaria de receber sugestões sobre:

1. Arquiteturas de memória para Claude Code.
2. Estratégias de compartilhamento de contexto entre repositórios.
3. Estruturas de knowledge base que funcionem bem com SDD.
4. Agentes especializados que poderiam compor esse ecossistema.
5. Ferramentas open source ou comerciais para:
   - Memória persistente
   - RAG
   - Knowledge Graph
   - Vector Database
   - ADR Management
   - Context Engineering

6. Boas práticas para evitar degradação de contexto e acúmulo de conhecimento obsoleto.
7. Estratégias para versionar memória e conhecimento organizacional da mesma forma que versionamos código.

# Pergunta

Se você estivesse desenhando uma plataforma de engenharia aumentada por IA para uma squad pequena utilizando Claude Code e SDD, como estruturaria os agentes, a memória de longo prazo, os mecanismos de recuperação de contexto e o compartilhamento de conhecimento entre múltiplos repositórios e múltiplos produtos ao longo do tempo?

---

Esse formato tende a produzir respostas muito mais profundas e arquiteturalmente relevantes de modelos como Claude, GPT e Gemini.
