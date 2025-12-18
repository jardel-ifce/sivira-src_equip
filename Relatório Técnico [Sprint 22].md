# Relatório Técnico [Sprint 22]

---

**Equipe:** SIVIRA — Pesquisa Operacional
**Sprint:** 22
**Período:** 02/12/25 — 16/12/25
**Responsável Técnico:** Jardel Rodrigues
**Data de Emissão:** 16/12/25
**Repositório:** https://github.com/jardel-ifce/sivira-src_equip

---

## 1. Progressos da Sprint

### 1.1 Resumo Executivo

A Sprint 22 foi concluída com **100% das atividades planejadas entregues**. O foco principal foi a **correção e aprimoramento do sistema de alocação de funcionários**, alcançando uma taxa de sucesso de 100% na alocação dos 13 pedidos de teste através de carregamento dinâmico, dimensionamento adequado da escala e tratamento de conflitos de folga.

### 1.2 Atividades Concluídas

#### Objetivo 01: Refatoração do GestorFuncionarios para Carregamento Dinâmico

**Descrição:** Modificar o `GestorFuncionarios` para carregar funcionários dinamicamente via arquivo JSON, eliminando a dependência de listas hardcoded no código.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 1 | Diagnosticar falhas de alocação nos logs de funcionários | Concluído | Identificação de 8 falhas em 13 pedidos |
| 2 | Identificar limitações do carregamento estático atual | Concluído | Lista hardcoded de apenas 9 funcionários |
| 3 | Integrar `GestorFuncionarios` com `FabricaFuncionarios` | Concluído | Padrão Singleton preservado |
| 4 | Substituir importações hardcoded por carregamento dinâmico | Concluído | Remoção de `funcionario_1` a `funcionario_9` |
| 5 | Validar que o singleton mantém consistência após refatoração | Concluído | Ocupações preservadas entre instâncias |

**Como foi atingido:**

O diagnóstico inicial revelou que o `GestorFuncionarios` utilizava importações estáticas de apenas 9 funcionários (`funcionario_1` a `funcionario_9`), limitando severamente a capacidade de alocação. A refatoração substituiu essas importações pela integração com `FabricaFuncionarios`, que carrega funcionários dinamicamente do arquivo `funcionarios.json`. O padrão Singleton foi mantido em ambas as classes, garantindo que os mesmos objetos Funcionario sejam compartilhados em toda a aplicação e que as ocupações sejam preservadas corretamente entre diferentes pontos do código.

---

#### Objetivo 02: Dimensionamento e Expansão da Escala de Funcionários

**Descrição:** Expandir a escala de funcionários para atender a demanda simultânea de múltiplos pedidos, garantindo disponibilidade de todos os tipos profissionais necessários.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 6 | Analisar demanda por tipo de funcionário nos 13 pedidos de teste | Concluído | Mapeamento completo por profissão |
| 7 | Mapear picos de demanda simultânea por profissão | Concluído | Identificação de gargalos em Confeiteiros e Cozinheiros |
| 8 | Expandir escala de funcionários conforme necessidade identificada | Concluído | De 9 para 34 funcionários |
| 9 | Distribuir funcionários por tipo profissional | Concluído | 6 tipos cobertos com redundância |
| 10 | Criar backup da escala original para referência | Concluído | Arquivo escala_antiga_funcionarios.json criado |

**Como foi atingido:**

A análise de demanda identificou que os 13 pedidos de teste requeriam simultaneamente múltiplos profissionais do mesmo tipo, especialmente Confeiteiros e Cozinheiros. A escala foi expandida de 9 para 34 funcionários, distribuídos conforme a demanda: 3 Padeiros, 3 Auxiliares de Padeiro, 8 Confeiteiros, 8 Auxiliares de Confeiteiro, 6 Cozinheiros, 4 Almoxarifes e 2 Auxiliares Polivalentes. O arquivo original foi preservado em `escala_antiga_funcionarios.json` para referência e possível rollback.

---

#### Objetivo 03: Tratamento de Conflitos de Folga por Dia da Semana

**Descrição:** Ajustar as regras de folga dos funcionários para evitar indisponibilidade em massa no dia de alocação, considerando que o sistema agenda 5 dias à frente.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 11 | Identificar o dia da semana resultante da alocação | Concluído | 31/12/2024 é terça-feira (TERÇA) |
| 12 | Mapear funcionários com folga no dia crítico de alocação | Concluído | Múltiplos funcionários com folga em TERÇA |
| 13 | Redistribuir folgas para outros dias da semana | Concluído | Folgas movidas para outros dias |
| 14 | Garantir cobertura mínima de funcionários para cada dia | Concluído | Distribuição equilibrada |
| 15 | Validar alocação completa de todos os pedidos após ajustes | Concluído | 13/13 pedidos alocados com sucesso |

**Como foi atingido:**

O sistema de alocação agenda atividades 5 dias à frente da data atual. Com a data base de 26/12/2024, a alocação ocorre em 31/12/2024, que é uma terça-feira. Funcionários com regra de folga `DIA_FIXO_SEMANA: TERÇA` ficavam indisponíveis nesta data, causando falhas de alocação. A correção redistribuiu as folgas de TERÇA para outros dias da semana (DOMINGO, SEGUNDA, QUARTA, QUINTA, SEXTA, SÁBADO), garantindo cobertura completa no dia crítico. O resultado foi a alocação bem-sucedida de 100% dos pedidos (13/13).

---

### 1.3 Métricas da Sprint

| Métrica | Valor |
|---------|-------|
| Tarefas planejadas | 15 |
| Tarefas concluídas | 15 |
| Taxa de conclusão | 100% |
| Objetivos entregues | 3/3 |
| Pedidos alocados com sucesso | 13/13 (100%) |
| Taxa de sucesso anterior | 5/13 (38%) |
| Melhoria na taxa de alocação | +62 pontos percentuais |
| Funcionários na escala | 34 |

---

## 2. Planos para a Próxima Sprint

### 2.1 Visão Geral

A definir.

### 2.2 Objetivos Técnicos

A definir.

---

## 3. Problemas e Impedimentos

### 3.1 Problemas Identificados

| Problema | Impacto | Resolução |
|----------|---------|-----------|
| GestorFuncionarios com lista hardcoded | Bloqueante | Refatorado para carregamento dinâmico via JSON |
| Escala insuficiente de funcionários | Bloqueante | Expandida de 9 para 34 funcionários |
| Conflito de folgas em TERÇA | Bloqueante | Folgas redistribuídas para outros dias |

### 3.2 Impedimentos Resolvidos

Todos os impedimentos identificados foram resolvidos durante a sprint, não havendo pendências para a próxima iteração.

---

## 4. Considerações Finais

### 4.1 Pontos Positivos

A integração entre FabricaFuncionarios e GestorFuncionarios via padrão Singleton garante que os mesmos objetos Funcionario sejam utilizados em toda a aplicação, preservando ocupações e evitando inconsistências.

O carregamento dinâmico via JSON elimina a necessidade de alterações no código para adicionar ou remover funcionários, permitindo ajustes na escala através de simples edição do arquivo de configuração.

A análise de demanda por tipo profissional permitiu dimensionar corretamente a escala, identificando gargalos em Confeiteiros e Cozinheiros que causavam falhas de alocação.

A redistribuição de folgas considerando o dia resultante da alocação (+5 dias) eliminou conflitos de indisponibilidade em massa, garantindo cobertura completa no dia crítico.

### 4.2 Lições Aprendidas

Listas hardcoded de entidades dinâmicas como funcionários devem ser substituídas por carregamento de arquivos de configuração, facilitando manutenção e evitando recompilação.

O dimensionamento de recursos deve considerar o pico de demanda simultânea, não apenas o volume total de atividades, para evitar gargalos durante a execução.

O sistema de alocação com agendamento futuro requer atenção especial ao dia da semana resultante, pois regras de folga podem causar indisponibilidade inesperada.

A criação de backups antes de alterações significativas em arquivos de configuração permite rollback seguro em caso de problemas.

### 4.3 Arquivos Modificados

| Arquivo | Tipo de Alteração |
|---------|-------------------|
| `data/funcionarios/funcionarios.json` | Expandido de 9 para 34 funcionários |
| `data/funcionarios/escala_antiga_funcionarios.json` | Criado como backup da escala original |
| `services/gestores/funcionarios/gestor_funcionarios.py` | Refatorado para carregamento dinâmico |

---

**Aprovado por:** Jardel Rodrigues
**Data:** 16/12/25
