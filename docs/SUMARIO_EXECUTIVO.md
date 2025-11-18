# Sumário Executivo: Análise Comparativa de Métodos de Agendamento

**Sistema:** SIVIRA (Sistema Inteligente para Visualização e Replanejamento de Atividades)
**Data:** 14 de Novembro de 2025

---

## Pergunta Central

**Por que um algoritmo guloso simples (backward scheduling sequencial) alcançou 84,6% de taxa de sucesso enquanto um otimizador baseado em Programação Linear falhou em 69,2% dos casos, apesar de encontrar soluções matematicamente "ótimas"?**

---

## Contexto

Análise experimental comparando dois métodos de agendamento de produção em ambiente industrial de panificação e confeitaria:
- **Dataset:** 13 pedidos reais com deadlines em 31/12/2024
- **Complexidade:** 130+ atividades, 6 pedidos com restrições temporais rígidas (gap zero)
- **Recursos limitados:** Fritadeira única, 3 fornos, 7 bancadas, 4 fermentadores

---

## Resultados Experimentais

| Métrica | Sequencial (Guloso) | PL (OR-Tools) | Interpretação |
|---------|---------------------|---------------|---------------|
| **Pedidos Executados** | **11/13 (84,6%)** | **4/13 (30,8%)** | PL falhou em entregar 69% |
| **Pedidos Falhados** | 2 | 9 | PL teve 7 falhas a mais |
| **Makespan** | 1.753 min | 383 min | ❌ Incomparável* |
| **Tempo de Execução** | 0,42s | 0,51s | PL 21% mais lento |

*O makespan menor do PL é **enganoso**: reflete apenas executar menos trabalho (4 vs 11 pedidos), não maior eficiência. O makespan maior do sequencial é **esperado** ao processar 2,75× mais pedidos com sucesso.

---

## Descoberta Principal

O método PL encontrou solução declarada "OPTIMAL" pelo solver OR-Tools, mas **69% dos pedidos falharam durante execução** por violação de restrições que **não foram modeladas matematicamente**.

**Não é paradoxo real:** A solução é "ótima" apenas para o modelo incompleto. Como o modelo omite restrições críticas, a "otimalidade" é irrelevante para o problema real. O makespan menor do PL (383 min vs 1.753 min) reflete simplesmente executar menos pedidos (4 vs 11), não maior eficiência.

---

## Três Deficiências Críticas do Modelo PL

### 1. Restrições de Tempo Máximo de Espera NÃO Modeladas

**Problema:** 6 de 13 pedidos possuem `tempo_maximo_de_espera = 0` (atividades sucessivas devem ser imediatamente contíguas, sem gaps).

**Código:**
- ✅ Dados extraídos: `extrator_dados_pedidos.py` (linhas 388-396)
- ❌ NUNCA modelados: `modelo_pl_otimizador.py` (linhas 40-120)

**Resultado:** PL criou gaps de 30-44 minutos onde o máximo permitido era 0.

**Exemplo Real (Pedido 7 - Coxinha):**
```
Atividade 10691 terminou:  31/12 06:03
Atividade 10692 iniciou:   31/12 06:47
Gap criado:                44 minutos
Máximo permitido:          0 minutos ❌
```

**Taxa de falha:** 100% dos pedidos críticos (6/6) falharam no PL

---

### 2. Equipamentos NÃO Modelados como Recursos Limitados

**Problema:** Modelo PL não garante exclusão mútua de equipamentos.

**Código:**
- ✅ Equipamentos extraídos: `extrator_dados_pedidos.py` (linhas 144-173)
- ❌ NUNCA modelados: `modelo_pl_otimizador.py` (sem restrições de capacidade)

**Resultado:** PL "agenda" múltiplas atividades para mesmo equipamento simultaneamente. Conflitos descobertos apenas na execução.

**Exemplo:** Fritadeira única compartilhada entre 4+ atividades sem proteção matemática.

---

### 3. Orçamento de Restrições Insuficiente

**Problema:** Limite arbitrário de 1.000 restrições.

**Código:** `modelo_pl_otimizador.py` (linha 66)
```python
MAX_CONSTRAINTS = 1000  # ❌ Limite fixo
```

**Impacto:**
- Conflitos potenciais: C(130,2) = **8.385**
- Restrições modeladas: **1.000**
- **Cobertura: 11,9%** (88% dos conflitos desprotegidos!)

**Resultado:** Últimos pedidos não têm restrições de não-sobreposição → PL pensa que são sempre factíveis.

---

## Por Que o Método Guloso Funciona

**Resposta:** Satisfação **implícita** de restrições por construção, não por modelagem explícita.

### Mecanismo de Sucesso

**1. Gap Zero Garantido**
- Backward scheduling aloca atividades em sequência reversa contígua
- Atividade atual termina exatamente quando sucessora inicia
- Gap = 0 **por construção**, sem verificação necessária

**2. Equipamentos: Pool Dinâmico**
- Mantém conjunto de equipamentos disponíveis em tempo real
- Consulta disponibilidade antes de alocar
- Reserva imediata remove do pool (mutex garantido)
- Nunca cria conflitos

**3. Precedências: Ordenação Topológica**
- Processa atividades da última para primeira
- Sucessoras já alocadas quando antecessora é processada
- Violações de precedência impossíveis

---

## Análise de Complexidade

```
Sequencial: O(n × m × e) = ~3.900 operações   | 0,42s | 84,6% sucesso
PL:         O(k³) = ~1.124.864 operações      | 0,51s | 30,8% sucesso

n=pedidos, m=atividades/pedido, e=equipamentos, k=variáveis
```

**Paradoxo:** Método 290× mais complexo falhou 2,7× mais.

---

## Implicações Práticas

### Para Produção Imediata
✅ **Usar método sequencial** como padrão (robusto, confiável, 84,6% sucesso)

### Para Desenvolvimento de Otimizadores
⚠️ **Completude do modelo > Sofisticação do algoritmo**

Lições aprendidas:
1. Modelagem incompleta torna otimalidade matemática irrelevante
2. Validação pós-otimização é obrigatória (não opcional)
3. Heurísticas construtivas são robustas a restrições difíceis de modelar
4. "Solução ótima" sem factibilidade real = solução inútil

---

## Recomendações

### Curto Prazo (Imediato)
- ✅ Manter método sequencial em produção
- ⚠️ Desabilitar PL para pedidos com `tempo_maximo_de_espera = 0`
- ✅ Adicionar validação pós-PL (verificar factibilidade antes de executar)

### Médio Prazo (Correção do PL)
- 🔧 Adicionar restrições de `tempo_maximo_de_espera` ao modelo
- 🔧 Modelar equipamentos como recursos com capacidade limitada
- 🔧 Remover orçamento de 1.000 restrições (modelar TODAS as necessárias)

### Longo Prazo (Abordagem Híbrida)
- 🎯 Classificar pedidos: "otimizáveis" vs "críticos"
- 🎯 PL para pedidos sem restrições rígidas
- 🎯 Sequencial para pedidos críticos
- 🎯 Validação obrigatória antes de qualquer execução

**Objetivo:** PL deve alcançar **≥80% taxa de sucesso** antes de substituir sequencial.

---

## Conclusão

A superioridade do método guloso não é intrínseca ao algoritmo, mas consequência de **modelagem incompleta no método PL**. Três omissões críticas (tempo máximo de espera, equipamentos, 88% das restrições de conflito) transformaram um otimizador matematicamente sofisticado em gerador de soluções infactíveis.

**Mensagem central:** Em sistemas reais com restrições complexas, um modelo simples e completo supera um modelo sofisticado e incompleto. A elegância matemática não compensa abstrações inadequadas.

**Contribuição:** Evidência empírica de que **completude > sofisticação** em otimização de sistemas produtivos reais.

---

## Documentos Relacionados

1. **[DISSERTACAO_METODOS_AGENDAMENTO.md](DISSERTACAO_METODOS_AGENDAMENTO.md)** - Texto dissertativo completo
2. **[ANALISE_SEQUENCIAL_VS_PL.md](ANALISE_SEQUENCIAL_VS_PL.md)** - Análise técnica detalhada
3. **[DIAGRAMA_COMPARATIVO_METODOS.txt](DIAGRAMA_COMPARATIVO_METODOS.txt)** - Diagramas visuais
4. **[VERIFICACAO_ATIVIDADES.md](VERIFICACAO_ATIVIDADES.md)** - Validação das atividades

---

**Elaborado por:** Claude (Anthropic)
**Sistema:** SIVIRA v2.0
**Data:** 14 de Novembro de 2025
