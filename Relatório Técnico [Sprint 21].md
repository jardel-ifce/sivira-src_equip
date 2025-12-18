# Relatório Técnico [Sprint 21]

---

**Equipe:** SIVIRA — Pesquisa Operacional
**Sprint:** 21
**Período:** 17/11/25 — 02/12/25
**Responsável Técnico:** Jardel Rodrigues
**Data de Emissão:** 02/12/25
**Repositório:** https://github.com/jardel-ifce/sivira-src_equip

---

## 1. Progressos da Sprint

### 1.1 Resumo Executivo

A Sprint 21 foi concluída com **100% das atividades planejadas entregues**. O foco principal foi a implementação do **Otimizador v2** baseado em Programação Linear, incluindo sistema de detecção de modo de operação, motor de otimização MIP, calculador de horários determinísticos e executor unificado.

### 1.2 Atividades Concluídas

#### Objetivo 01: Sistema de Detecção de Modo de Operação

**Descrição:** Criação de um sistema inteligente que analisa os pedidos e detecta automaticamente qual modo de operação deve ser utilizado.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 1 | Analisar campo `tempo_maximo_espera` das atividades | Concluído | Identificação automática de restrições temporais |
| 2 | Classificar pedidos em modo Determinístico ou Flexível | Concluído | Baseado na presença de deadlines fixos |
| 3 | Implementar estatísticas de distribuição dos modos | Concluído | Relatório detalhado por pedido |

**Como foi atingido:**

O objetivo foi alcançado através da análise automática do campo `tempo_maximo_espera` presente em cada atividade dos pedidos. O sistema classifica pedidos como **Determinístico** quando possuem horários fixos obrigatórios (tempo_maximo_espera = 0) ou **Flexível** quando permitem múltiplas configurações de janelas temporais. A detecção ocorre em tempo inferior a 1 segundo para conjuntos de até 50 pedidos, conforme critério de sucesso estabelecido.

---

#### Objetivo 02: Motor de Otimização por Programação Linear

**Descrição:** Implementação do núcleo do otimizador utilizando técnicas de Programação Linear Inteira Mista (MIP).

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 4 | Definir variáveis de decisão para janelas temporais | Concluído | Modelagem binária de seleção |
| 5 | Modelar restrições de capacidade de equipamentos | Concluído | Respeita limites de cada equipamento |
| 6 | Modelar restrições de tempo máximo de espera | Concluído | Gaps entre atividades controlados |
| 7 | Implementar função objetivo (maximizar pedidos) | Concluído | Priorização por FIP e criticidade |
| 8 | Integrar solver OR-Tools SCIP | Concluído | Resolução otimizada do modelo MIP |

**Como foi atingido:**

O motor de otimização foi implementado utilizando a biblioteca OR-Tools com o solver SCIP. As variáveis de decisão binária representam a seleção de janelas temporais para cada atividade. As restrições modelam a capacidade dos equipamentos (evitando sobreposição de ocupações), o tempo máximo de espera entre atividades dependentes e a consistência temporal do fluxo de produção. A função objetivo maximiza o número de pedidos atendidos, ponderando pela prioridade (FIP) dos funcionários e criticidade das atividades. O tempo de resolução ficou abaixo de 10 minutos para os cenários de teste.

---

#### Objetivo 03: Calculador de Horários Determinísticos

**Descrição:** Desenvolvimento do módulo de cálculo de horários exatos utilizando backward scheduling.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 9 | Implementar backward scheduling a partir do deadline | Concluído | Propagação reversa de horários |
| 10 | Calcular horário de término da última atividade PRODUTO | Concluído | Âncora para cálculo reverso |
| 11 | Propagar horários respeitando dependências | Concluído | Tratamento de subprodutos |
| 12 | Garantir gaps zero quando especificado | Concluído | Atividades contíguas sem espera |

**Como foi atingido:**

O calculador de horários determinísticos parte do prazo final (deadline) de cada pedido e calcula retroativamente os horários de cada atividade. O algoritmo identifica a última atividade do tipo PRODUTO, define seu horário de término como o deadline, e propaga os horários para as atividades anteriores respeitando as durações e dependências. Para subprodutos, o sistema considera as relações de precedência e garante que os gaps entre atividades sejam zero quando `tempo_maximo_espera = 0`. O resultado são cronogramas precisos que respeitam todas as restrições temporais do sistema.

---

#### Objetivo 04: Executor Unificado e Integração

**Descrição:** Criação do orquestrador principal e integração com o sistema existente.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 13 | Coordenar fluxo em 4 fases | Concluído | Detecção → Cálculo → Otimização → Execução |
| 14 | Manter compatibilidade com menu atual | Concluído | Interface transparente |
| 15 | Gerar relatórios consolidados | Concluído | Logs detalhados por fase |
| 16 | Permitir comparação com método anterior | Concluído | Métricas comparativas disponíveis |

**Como foi atingido:**

O executor unificado foi implementado como orquestrador central do pipeline de otimização. O fluxo segue 4 fases distintas: (1) **Detecção** - análise dos pedidos e classificação do modo de operação; (2) **Cálculo** - determinação dos horários via backward scheduling; (3) **Otimização** - resolução do modelo MIP para encontrar a melhor alocação; (4) **Execução** - aplicação da solução nos equipamentos e funcionários. A integração com o menu de produção existente foi realizada de forma transparente, mantendo a interface de usuário inalterada. Os logs detalhados de cada fase são gerados automaticamente em `logs/equipamentos/` e `logs/funcionarios/`.

---

### 1.3 Métricas da Sprint

| Métrica | Valor |
|---------|-------|
| Tarefas planejadas | 16 |
| Tarefas concluídas | 16 |
| Taxa de conclusão | 100% |
| Objetivos entregues | 4/4 |

---

## 2. Planos para a Próxima Sprint

### 2.1 Visão Geral

A Sprint 22 terá foco na **correção e aprimoramento do sistema de alocação de funcionários**, garantindo que todos os pedidos sejam executados com sucesso através de carregamento dinâmico, dimensionamento adequado da escala e tratamento de conflitos de folga.

### 2.2 Objetivos Técnicos

#### Objetivo 01: Refatoração do GestorFuncionarios para Carregamento Dinâmico

**Descrição:** Modificar o `GestorFuncionarios` para carregar funcionários dinamicamente via arquivo JSON, eliminando a dependência de listas hardcoded no código.

**Escopo:**
- Diagnosticar falhas de alocação nos logs de funcionários
- Identificar limitações do carregamento estático atual
- Integrar `GestorFuncionarios` com `FabricaFuncionarios`
- Substituir importações hardcoded (`funcionario_1` a `funcionario_9`) por carregamento dinâmico
- Validar que o singleton mantém consistência após refatoração

**Critérios de Sucesso:**
- Zero importações hardcoded de funcionários no `GestorFuncionarios`
- Funcionários carregados automaticamente do arquivo `funcionarios.json`
- Logs de inicialização confirmando quantidade de funcionários carregados

---

#### Objetivo 02: Dimensionamento e Expansão da Escala de Funcionários

**Descrição:** Expandir a escala de funcionários para atender a demanda simultânea de múltiplos pedidos, garantindo disponibilidade de todos os tipos profissionais necessários.

**Escopo:**
- Analisar demanda por tipo de funcionário nos 13 pedidos de teste
- Mapear picos de demanda simultânea por profissão
- Expandir escala de funcionários conforme necessidade identificada
- Distribuir funcionários por tipo: Padeiros, Auxiliares de Padeiro, Confeiteiros, Auxiliares de Confeiteiro, Cozinheiros, Almoxarifes
- Criar backup da escala original para referência

**Critérios de Sucesso:**
- Escala dimensionada para suportar execução simultânea de 13+ pedidos
- Todos os tipos profissionais com redundância adequada
- Arquivo de backup da escala anterior criado

---

#### Objetivo 03: Tratamento de Conflitos de Folga por Dia da Semana

**Descrição:** Ajustar as regras de folga dos funcionários para evitar indisponibilidade em massa no dia de alocação, considerando que o sistema agenda 5 dias à frente.

**Escopo:**
- Identificar o dia da semana resultante da alocação (considerando +5 dias)
- Mapear funcionários com folga no dia crítico de alocação
- Redistribuir folgas para outros dias da semana
- Garantir cobertura mínima de funcionários para cada dia
- Validar alocação completa de todos os pedidos após ajustes

**Critérios de Sucesso:**
- Taxa de alocação de 100% dos pedidos (13/13)
- Nenhum funcionário com folga no dia crítico de alocação
- Distribuição equilibrada de folgas ao longo da semana

---

## 3. Problemas e Impedimentos

### 3.1 Problemas Identificados

| Problema | Impacto | Status |
|----------|---------|--------|
| GestorFuncionarios com lista hardcoded | Bloqueante | Pendente para Sprint 22 |
| Escala insuficiente de funcionários | Bloqueante | Pendente para Sprint 22 |
| Conflito de folgas em dia de alocação | Bloqueante | Pendente para Sprint 22 |

### 3.2 Detalhamento dos Problemas

1. **GestorFuncionarios com lista hardcoded:** O sistema atual importa estaticamente apenas 9 funcionários (`funcionario_1` a `funcionario_9`), limitando a capacidade de alocação.

2. **Escala insuficiente:** A quantidade atual de funcionários é insuficiente para atender a demanda simultânea de 13 pedidos, resultando em falhas de alocação.

3. **Conflito de folgas:** Funcionários com folga no dia resultante da alocação (+5 dias) ficam indisponíveis, causando gaps na cobertura.

---

## 4. Considerações Finais

### 4.1 Pontos Positivos

A análise automática do campo tempo_maximo_espera permite classificar pedidos em menos de 1 segundo, eliminando a necessidade de configuração manual do modo de operação.

A modelagem MIP com variáveis binárias para seleção de janelas temporais garante soluções ótimas respeitando capacidade de equipamentos e restrições de tempo máximo de espera.

O backward scheduling a partir do deadline assegura que todas as atividades sejam programadas de forma a cumprir o prazo final, propagando horários corretamente através das dependências.

O pipeline em 4 fases (Detecção, Cálculo, Otimização, Execução) mantém compatibilidade total com o menu existente sem alterações na interface do usuário.

### 4.2 Lições Aprendidas

A classificação prévia dos pedidos em modo Determinístico ou Flexível permite aplicar estratégias de otimização específicas para cada cenário, aumentando a eficiência do solver.

A integração com OR-Tools SCIP requer definição precisa de restrições de capacidade e tempo para obter soluções viáveis em tempo razoável (menos de 10 minutos para 13 pedidos).

O cálculo reverso de horários exige tratamento especial para subprodutos e atividades com gaps zero, garantindo contiguidade quando tempo_maximo_espera é igual a zero.

A geração automática de logs por fase facilita diagnóstico e auditoria, permitindo identificar rapidamente em qual etapa do pipeline ocorrem falhas.

### 4.3 Arquivos Modificados

| Arquivo | Tipo de Alteração |
|---------|-------------------|
| `otimizador_v2/detector_modo.py` | Novo - Sistema de detecção de modo |
| `otimizador_v2/motor_pl.py` | Novo - Motor de Programação Linear |
| `otimizador_v2/calculador_horarios.py` | Novo - Calculador determinístico |
| `otimizador_v2/executor_unificado.py` | Novo - Orquestrador principal |

---

**Aprovado por:** Jardel Rodrigues
**Data:** 02/12/25
