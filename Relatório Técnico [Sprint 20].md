# Relatório Técnico [Sprint 20]

---

**Equipe:** SIVIRA — Pesquisa Operacional
**Sprint:** 20
**Período:** 03/11/25 — 16/11/25
**Responsável Técnico:** Jardel Rodrigues
**Data de Emissão:** 16/11/25
**Repositório:** https://github.com/jardel-ifce/sivira-src_equip

---

## 1. Progressos da Sprint

### 1.1 Resumo Executivo

A Sprint 20 foi concluída com **100% das atividades planejadas entregues**. O foco principal foi a implementação do **Sistema de Recuperação de Estado via Parsing de Logs de Equipamentos**, permitindo que o sistema restaure automaticamente o estado dos equipamentos a partir de arquivos de log previamente gerados.

### 1.2 Atividades Concluídas

#### Objetivo 01: Sistema de Recuperação de Estado via Parsing de Logs

**Descrição:** Desenvolvimento de infraestrutura completa para recuperação automática do estado de equipamentos através da leitura e interpretação de arquivos de log.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 1 | Implementar DetectorLogs | Concluído | Detecção automática de arquivos de log no sistema de arquivos |
| 2 | Desenvolver validador estrutural de logs | Concluído | Validação do formato e integridade dos arquivos |
| 3 | Criar DTOs imutáveis | Concluído | OcupacaoDTO, EstadoEquipamentoDTO, RelatorioRecuperacaoDTO |
| 4 | Implementar ParserBase abstrato | Concluído | Classe base para todos os parsers especializados |
| 5 | Desenvolver 17 parsers especializados | Concluído | Um parser para cada tipo de equipamento |

**Como foi atingido:**

O objetivo foi alcançado através da criação de uma arquitetura em camadas para processamento de logs. Primeiro, implementamos o `DetectorLogs`, responsável por varrer o sistema de arquivos e identificar automaticamente os arquivos de log gerados pelo sistema de produção. Em seguida, desenvolvemos um validador estrutural que verifica se cada arquivo possui o formato esperado (cabeçalho, corpo e rodapé) antes de prosseguir com o parsing.

Para garantir a integridade dos dados durante a transferência entre camadas, criamos três DTOs (Data Transfer Objects) imutáveis: `OcupacaoDTO` para representar uma ocupação individual, `EstadoEquipamentoDTO` para o estado completo de um equipamento, e `RelatorioRecuperacaoDTO` para consolidar os resultados do processo.

A classe abstrata `ParserBase` foi implementada definindo a interface comum que todos os parsers devem seguir, incluindo métodos para extração de timestamps, identificação de equipamentos e parsing de ocupações. Por fim, desenvolvemos 17 parsers especializados — um para cada tipo de equipamento do sistema (fornos, batedeiras, masseiras, fogões, fritadeiras, balanças, bancadas, câmaras refrigeradas, freezers, armários de fermentação, divisoras, modeladoras de pães, modeladoras de salgados, embaladoras, misturadoras e hot mix) — cada um conhecendo as particularidades do formato de log do seu respectivo equipamento.

---

#### Objetivo 02: Restauração Automática de Objetos de Equipamentos em Memória

**Descrição:** Implementação da camada de restauração que aplica os estados extraídos dos logs nos objetos de equipamentos em memória.

| # | Tarefa | Status | Observações |
|---|--------|--------|-------------|
| 6 | Implementar RestauradorBase abstrato | Concluído | Classe base com padrão Strategy |
| 7 | Criar 17 restauradores especializados | Concluído | Um restaurador para cada tipo de equipamento |
| 8 | Desenvolver ValidadorOcupacoes | Concluído | Validação de ocupações temporais |
| 9 | Implementar ValidadorConsistencia | Concluído | Verificação de consistência entre estados |
| 10 | Criar RecuperadorEstado | Concluído | Orquestrador central do pipeline de recuperação |

**Como foi atingido:**

O objetivo foi alcançado através da implementação de uma camada de restauração que traduz os dados extraídos dos logs em estados reais dos objetos de equipamentos em memória. Utilizamos o padrão Strategy para criar a classe abstrata `RestauradorBase`, que define o contrato para aplicação de estados em equipamentos. Foram desenvolvidos 17 restauradores especializados, cada um responsável por restaurar um tipo específico de equipamento. Cada restaurador conhece a estrutura interna do seu equipamento e sabe como aplicar corretamente as ocupações extraídas, respeitando as regras de negócio específicas (capacidade, temperaturas, velocidades, etc.). Para garantir a qualidade dos dados antes da restauração, implementamos duas camadas de validação: o `ValidadorOcupacoes` verifica se as ocupações temporais são válidas (sem sobreposições, dentro dos limites de capacidade), enquanto o `ValidadorConsistencia` assegura que os estados a serem aplicados são coerentes com o estado atual do sistema (equipamentos existentes, funcionários válidos, etc.). Por fim, criamos o `RecuperadorEstado` como orquestrador central do pipeline. Esta classe coordena todo o fluxo de recuperação: detecta os logs disponíveis, aciona os parsers apropriados, valida os dados extraídos e aplica os estados através dos restauradores. O resultado é um processo automatizado e robusto que permite restaurar o estado completo do sistema de produção a partir dos logs.

---

### 1.3 Métricas da Sprint

| Métrica | Valor |
|---------|-------|
| Tarefas planejadas | 10 |
| Tarefas concluídas | 10 |
| Taxa de conclusão | 100% |
| Tipos de equipamentos suportados | 17 |

---

## 2. Planos para a Próxima Sprint

### 2.1 Visão Geral

A Sprint 21 terá foco na implementação do **Otimizador v2**, um novo módulo de otimização baseado em Programação Linear (PL) que substituirá o algoritmo sequencial atual. O objetivo é melhorar significativamente a taxa de sucesso na alocação de pedidos.

### 2.2 Objetivos Técnicos

#### Objetivo 01: Sistema de Detecção de Modo de Operação

**Descrição:** Criar um sistema inteligente que analisa os pedidos e detecta automaticamente qual modo de operação deve ser utilizado.

**Escopo:**
- Analisar o campo `tempo_maximo_espera` de cada atividade dos pedidos
- Classificar pedidos em modo **Determinístico** (horários fixos obrigatórios) ou **Flexível** (múltiplas configurações possíveis)
- Fornecer estatísticas detalhadas sobre a distribuição dos modos

**Critérios de Sucesso:**
- Detecção correta do modo em 100% dos casos
- Tempo de análise inferior a 1 segundo para conjuntos de até 50 pedidos

---

#### Objetivo 02: Motor de Otimização por Programação Linear

**Descrição:** Implementar o núcleo do otimizador utilizando técnicas de Programação Linear Inteira Mista (MIP) para encontrar a melhor alocação possível de pedidos.

**Escopo:**
- Definir variáveis de decisão para seleção de janelas temporais
- Modelar restrições de capacidade de equipamentos
- Modelar restrições de tempo máximo de espera entre atividades
- Implementar função objetivo que maximiza o número de pedidos atendidos
- Integrar solver OR-Tools SCIP para resolução do modelo

**Critérios de Sucesso:**
- Modelo matemático correto e completo
- Resolução em tempo aceitável (< 10 minutos para cenários típicos)
- Taxa de sucesso superior ao método sequencial atual

---

#### Objetivo 03: Calculador de Horários Determinísticos

**Descrição:** Desenvolver módulo que calcula os horários exatos de execução de cada atividade utilizando a técnica de backward scheduling (agendamento reverso).

**Escopo:**
- Partir do prazo final (deadline) do pedido
- Calcular horário de término da última atividade do tipo PRODUTO
- Propagar horários para atividades anteriores respeitando dependências
- Garantir que gaps entre atividades sejam zero quando especificado

**Critérios de Sucesso:**
- Cálculo correto de horários para todos os tipos de atividade
- Tratamento adequado de subprodutos e dependências
- Horários resultantes respeitam todas as restrições temporais

---

#### Objetivo 04: Executor Unificado e Integração

**Descrição:** Criar o orquestrador principal que coordena todas as fases do processo de otimização e integra o novo módulo com o sistema existente.

**Escopo:**
- Coordenar fluxo em 4 fases: Detecção → Cálculo → Otimização → Execução
- Manter compatibilidade com interface do menu atual
- Gerar relatórios consolidados de execução
- Permitir comparação de resultados com método anterior

**Critérios de Sucesso:**
- Integração transparente com sistema existente
- Interface compatível com menu de produção
- Logs detalhados de cada fase do processo

---

## 3. Problemas e Impedimentos

Não foram identificados problemas ou impedimentos durante esta sprint.

---

## 4. Considerações Finais

### 4.1 Pontos Positivos

- **Arquitetura modular:** A separação em parsers e restauradores especializados permitiu desenvolvimento e testes isolados de cada componente
- **Padrões de projeto:** O uso dos padrões Strategy e Factory facilitou a extensibilidade do sistema para novos tipos de equipamentos
- **Interface consistente:** Todos os 17 parsers e restauradores seguem a mesma interface, simplificando a manutenção

### 4.2 Lições Aprendidas

- **DTOs imutáveis:** A utilização de objetos de transferência imutáveis garantiu consistência dos dados durante todo o pipeline de recuperação
- **Validação em camadas:** Implementar validação em múltiplas etapas (estrutural, semântica, consistência) previne erros em cascata e facilita diagnóstico
- **Orquestrador central:** Concentrar a coordenação do fluxo em uma única classe (RecuperadorEstado) simplificou significativamente a manutenção e evolução do sistema

---

**Aprovado por:** Jardel Rodrigues
**Data:** 16/11/25
