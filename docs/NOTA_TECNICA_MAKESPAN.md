# Nota Técnica: Por Que o Makespan Não É Métrica Válida Nesta Comparação

**Data:** 14 de Novembro de 2025
**Questão:** Por que o makespan maior no sequencial não indica ineficiência?

---

## Resumo

O makespan do método sequencial (1.753 minutos) é **4,58× maior** que o do método PL (383 minutos). Esta diferença **NÃO indica** que o PL é mais eficiente. Pelo contrário, o makespan maior do sequencial é **esperado e desejável**, pois reflete processar **2,75× mais pedidos com sucesso**.

---

## O Erro de Interpretação

### ❌ Interpretação INCORRETA
"PL tem makespan 78% menor → PL é mais eficiente"

### ✅ Interpretação CORRETA
"PL tem makespan 78% menor → PL executou 64% menos trabalho (4 vs 11 pedidos)"

---

## Análise Matemática

### Métricas Brutas
```
Sequencial: 1.753 minutos | 11 pedidos | ~107 atividades
PL:         383 minutos   | 4 pedidos  | ~42 atividades

Razão de makespan:    1.753 / 383 = 4,58×
Razão de trabalho:    107 / 42 = 2,55×
```

### Makespan Normalizado por Pedido

**Métrica correta:** Makespan médio por pedido executado

```
Sequencial: 1.753 min / 11 pedidos = 159,4 min/pedido
PL:         383 min / 4 pedidos    = 95,8 min/pedido
```

**Interpretação:** PL parece 40% mais eficiente **por pedido**, MAS:
- Executou apenas os 4 pedidos mais simples (seleção do solver)
- Pedidos complexos (com restrições de gap zero) TODOS falharam
- Comparação injusta: pedidos fáceis vs pedidos diversos

---

## Por Que o Makespan é Maior no Sequencial?

### Explicação Intuitiva

Imagine dois trabalhadores:
- **Trabalhador A (Sequencial):** Completa 11 tarefas em 29 horas
- **Trabalhador B (PL):** Completa 4 tarefas em 6,4 horas

**Questão:** Quem é mais produtivo?

**Resposta óbvia:** Trabalhador A!
- Entregou 2,75× mais trabalho
- Tempo maior é consequência natural de fazer mais

**O mesmo vale para os métodos de agendamento.**

---

## Por Que Comparar Makespan é Inválido?

### Condição para Comparação Válida

Makespan só é comparável quando:
```
✅ Mesma quantidade de pedidos executados
✅ Mesma complexidade de pedidos
✅ Mesmos recursos disponíveis
✅ Mesmo período de análise
```

### Situação Real

```
❌ Quantidades diferentes: 11 vs 4 pedidos
❌ Complexidades diferentes: PL rejeitou todos os críticos
✅ Recursos iguais: Sim
✅ Período igual: Sim

Conclusão: Makespan NÃO É COMPARÁVEL
```

---

## Métricas Válidas para Esta Comparação

### 1. Taxa de Atendimento (Primary Metric)

```
Sequencial: 11/13 = 84,6%  ✅ SUPERIOR
PL:         4/13 = 30,8%   ❌ INFERIOR
```

**Interpretação:** Sequencial entrega 2,75× mais pedidos.

---

### 2. Robustez a Restrições Críticas

```
Pedidos com tempo_maximo_de_espera = 0:

Sequencial: 5/6 executados (83,3%)  ✅
PL:         0/6 executados (0%)     ❌
```

**Interpretação:** PL falha sistematicamente em pedidos complexos.

---

### 3. Tempo Computacional

```
Sequencial: 0,42s
PL:         0,51s (+21%)
```

**Interpretação:** PL mais lento para entregar menos.

---

### 4. Makespan Normalizado (com ressalvas)

```
Sequencial: 159,4 min/pedido (média com pedidos diversos)
PL:         95,8 min/pedido  (média com pedidos selecionados)
```

**Ressalva:** PL só executou pedidos "fáceis" (sem gap zero), então comparação é enviesada.

---

## Cenário Hipotético: E Se Ambos Executassem 11 Pedidos?

### Estimativa Conservadora

Assumindo que o PL conseguisse corrigir as deficiências e executar os 11 mesmos pedidos:

```
Makespan PL projetado = 95,8 min/pedido × 11 pedidos = 1.053 min

Comparação:
  Sequencial: 1.753 min (11 pedidos)
  PL corrigido: ~1.053 min (11 pedidos) ← 40% melhor

Speedup projetado: 1,66×
```

**Mas:** Esta é a MELHOR projeção possível, assumindo que:
- PL modela TODAS as restrições corretamente
- Não há overhead adicional de restrições
- Solver encontra solução ótima em tempo razoável
- Pedidos complexos não degradam a eficiência

**Realidade:** Ao adicionar restrições omitidas (equipamentos, gaps, 88% de conflitos), o modelo PL cresce exponencialmente e pode:
- Não encontrar solução ótima no timeout
- Ter performance pior que sequencial
- Ainda falhar em casos extremos

---

## O Que o Makespan Realmente Revela?

### Sobre o Método Sequencial

**Makespan de 1.753 minutos indica:**
- ✅ Processou grande volume de trabalho (11 pedidos)
- ✅ Respeitou todas as restrições (gaps, equipamentos, precedências)
- ✅ Utilizou período de 29,2 horas (30/12 02:47 → 31/12 08:00)
- ⚠️ Não explorou otimização global (apenas gulosa)

### Sobre o Método PL

**Makespan de 383 minutos indica:**
- ⚠️ Processou volume reduzido (4 pedidos)
- ❌ NÃO respeitou restrições (9 pedidos falharam)
- ✅ Utilizou período de 6,4 horas (31/12 01:37 → 31/12 08:00)
- ✅ Solver encontrou "ótimo" (para modelo incompleto)

---

## Analogia: Corrida de Maratona

Imagine uma corrida onde:
- **Corredor A (Sequencial):** Completa 42 km em 4 horas
- **Corredor B (PL):** Completa 15 km em 1,5 horas, depois para

**Questão:** Quem venceu a maratona?

**Resposta:** Corredor A, obviamente!

**Mas alguém poderia argumentar incorretamente:**
"Corredor B é mais rápido: 10 km/h vs 10,5 km/h"

**Problema com esse argumento:**
- Corredor B não completou a prova
- Ritmo inicial não garante completar a distância
- O objetivo é **terminar a maratona**, não ter melhor pace parcial

**No agendamento:**
- **Objetivo:** Executar TODOS os 13 pedidos
- **Sequencial:** Completou 11 (84,6%)
- **PL:** Completou 4 (30,8%)
- **Vencedor:** Sequencial

---

## Conclusão

### Makespan NÃO É Métrica Adequada

Porque:
1. Quantidades de trabalho diferentes (11 vs 4)
2. Complexidades diferentes (PL rejeitou todos os críticos)
3. Taxa de falha drasticamente diferente (15% vs 69%)

### Métricas Adequadas

1. **Taxa de atendimento:** 84,6% vs 30,8% → Sequencial vence
2. **Robustez:** 83,3% vs 0% em críticos → Sequencial vence
3. **Tempo computacional:** 0,42s vs 0,51s → Sequencial vence

### Resposta à Questão Original

**"O makespan maior na execução sequencial é esperado, uma vez que um número maior de pedidos é executado, não é?"**

**Resposta:** **SIM, absolutamente!**

O makespan maior é não apenas esperado, mas **desejável**, pois indica que o sistema:
- ✅ Processou mais trabalho
- ✅ Atendeu mais demanda
- ✅ Entregou mais valor

O makespan menor do PL é **enganoso** porque:
- ❌ Reflete apenas fazer menos trabalho
- ❌ Não indica eficiência, mas falha em entregar
- ❌ Não é comparável com cargas diferentes

---

**Lição aprendida:** Em comparações de sistemas de produção, **taxa de atendimento** (throughput) é mais importante que **makespan absoluto** quando as cargas de trabalho diferem.

---

**Elaborado por:** Claude (Anthropic)
**Sistema:** SIVIRA
**Data:** 14 de Novembro de 2025
