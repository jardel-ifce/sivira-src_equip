# Documentação: Análise Comparativa de Métodos de Agendamento

**Sistema:** SIVIRA - Sistema Inteligente para Visualização e Replanejamento de Atividades
**Data:** 14 de Novembro de 2025
**Autor:** Claude (Anthropic)

---

## 📚 Índice de Documentos

Esta pasta contém uma análise completa comparando dois métodos de agendamento de produção: **Sequencial (Guloso)** vs **Programação Linear (PL)**.

### 🎯 Documentos Principais

#### 1. [SUMARIO_EXECUTIVO.md](SUMARIO_EXECUTIVO.md)
**Para:** Gestores, tomadores de decisão
**Tamanho:** ~3 páginas
**Conteúdo:**
- Descoberta principal em 1 parágrafo
- Tabela de resultados experimentais
- 3 deficiências críticas do PL
- Recomendações práticas (curto/médio/longo prazo)
- **Leia primeiro** se precisar de resposta rápida

---

#### 2. [DISSERTACAO_METODOS_AGENDAMENTO.md](DISSERTACAO_METODOS_AGENDAMENTO.md)
**Para:** Pesquisadores, desenvolvedores, acadêmicos
**Tamanho:** ~12 páginas
**Formato:** Texto dissertativo estruturado
**Conteúdo:**
- Introdução ao problema JSSP
- Metodologia experimental detalhada
- Análise de causa raiz com evidências de código
- Discussão sobre complexidade computacional
- Implicações para sistemas de produção reais
- Caminhos para correção do PL
- Referências bibliográficas e de código

**Estilo:** Argumentação acadêmica fluida, mínimo de tabelas, máximo de explicações

---

#### 3. [ANALISE_SEQUENCIAL_VS_PL.md](ANALISE_SEQUENCIAL_VS_PL.md)
**Para:** Engenheiros de software, arquitetos de sistema
**Tamanho:** ~18 páginas
**Formato:** Análise técnica estruturada
**Conteúdo:**
- Estrutura dos pedidos e alocação de equipamentos
- Impedimentos identificados (com exemplos de código)
- Comparação arquitetural detalhada
- Análise de dados experimentais
- Evidências de superioridade do método sequencial
- Recomendações técnicas com código

**Estilo:** Técnico, com muitas tabelas, diagramas e trechos de código

---

#### 4. [DIAGRAMA_COMPARATIVO_METODOS.txt](DIAGRAMA_COMPARATIVO_METODOS.txt)
**Para:** Todos os públicos (visual)
**Tamanho:** ~400 linhas
**Formato:** Diagramas ASCII
**Conteúdo:**
- Fluxograma do método sequencial (passo a passo)
- Fluxograma do método PL (5 fases)
- Comparação lado a lado (visual)
- Exemplo concreto: Pedido 7 (Coxinha) com falha detalhada
- Tabelas comparativas

**Estilo:** Visual, diagramático, fácil de entender

---

#### 5. [VERIFICACAO_ATIVIDADES.md](VERIFICACAO_ATIVIDADES.md)
**Para:** Auditores, revisores de qualidade
**Tamanho:** ~8 páginas
**Formato:** Relatório de verificação
**Conteúdo:**
- Validação de todos os produtos mencionados (IDs 1069, 1074, 1004, 1005)
- Verificação de atividades linha por linha
- Confirmação de restrições `tempo_maximo_de_espera`
- Comparação de logs reais vs análise
- Correções documentadas
- Estatísticas de validação (100% aprovado)

**Estilo:** Checklist, evidências, status ✅/❌

---

#### 6. [NOTA_TECNICA_MAKESPAN.md](NOTA_TECNICA_MAKESPAN.md) ⭐ **IMPORTANTE**
**Para:** Todos (esclarece confusão comum)
**Tamanho:** ~4 páginas
**Formato:** Nota técnica explicativa
**Conteúdo:**
- Por que makespan maior do sequencial é **esperado**, não problemático
- Por que comparar makespan é **inválido** (cargas diferentes)
- Makespan normalizado por pedido
- Métricas válidas para comparação
- Analogia da maratona (didático)

**Estilo:** Didático, esclarecedor, com exemplos práticos

**⚠️ Leia se:** Você achou que "PL tem makespan 78% menor = PL é melhor"

---

## 📊 Hierarquia Recomendada de Leitura

### 🔴 Nível 1: Visão Geral (5 minutos)
➡️ **Comece aqui:** [SUMARIO_EXECUTIVO.md](SUMARIO_EXECUTIVO.md)
- Entenda o problema em 1 parágrafo
- Veja os resultados principais
- Saiba as 3 deficiências críticas

### 🟡 Nível 2: Compreensão Profunda (30 minutos)
➡️ **Continue com:** [DISSERTACAO_METODOS_AGENDAMENTO.md](DISSERTACAO_METODOS_AGENDAMENTO.md)
- Entenda a metodologia
- Compreenda as causas raiz
- Veja as implicações práticas

### 🟢 Nível 3: Detalhes Técnicos (1-2 horas)
➡️ **Aprofunde-se:**
1. [ANALISE_SEQUENCIAL_VS_PL.md](ANALISE_SEQUENCIAL_VS_PL.md) - Código e arquitetura
2. [DIAGRAMA_COMPARATIVO_METODOS.txt](DIAGRAMA_COMPARATIVO_METODOS.txt) - Visualização
3. [VERIFICACAO_ATIVIDADES.md](VERIFICACAO_ATIVIDADES.md) - Validação

---

## 🎯 Principais Descobertas

### Resultado Experimental

| Métrica | Sequencial | PL | Interpretação |
|---------|------------|-----|---------------|
| **Taxa de Sucesso** | **84,6%** | 30,8% | PL falhou em 69% |
| Pedidos Executados | 11/13 | 4/13 | -7 pedidos |
| Makespan | 1.753 min | 383 min | ❌ Incomparável* |

*O makespan menor do PL é **enganoso** - reflete apenas executar 64% menos trabalho (4 vs 11 pedidos), não maior eficiência. O makespan maior do sequencial é **esperado e natural** ao processar 2,75× mais pedidos com sucesso. Ver: [NOTA_TECNICA_MAKESPAN.md](NOTA_TECNICA_MAKESPAN.md)

### Três Deficiências Críticas do PL

1. **❌ `tempo_maximo_de_espera` não modelado**
   - 6/13 pedidos têm gap zero obrigatório
   - PL criou gaps de 30-44 minutos
   - Taxa de falha: 100% (6/6 pedidos críticos)

2. **❌ Equipamentos não modelados**
   - Sem restrições de exclusão mútua
   - Conflitos descobertos apenas na execução
   - Fritadeira única alocada a múltiplas atividades

3. **❌ Orçamento de restrições insuficiente**
   - Limite: 1.000 restrições
   - Necessário: 8.385 restrições
   - Cobertura: 11,9% (88% desprotegido)

### Por Que Guloso Funciona

✅ **Satisfação implícita** de restrições por construção:
- Gap zero: backward scheduling contíguo
- Equipamentos: pool dinâmico com mutex
- Precedências: ordenação topológica

---

## 🔍 Localização de Evidências no Código

### Deficiências do PL

```python
# ❌ tempo_maximo_de_espera extraído mas NÃO modelado
otimizador/extrator_dados_pedidos.py:388-396     # ✅ Extrai
otimizador/modelo_pl_otimizador.py:40-120        # ❌ Nunca modela

# ❌ Equipamentos extraídos mas NÃO modelados
otimizador/extrator_dados_pedidos.py:144-173     # ✅ Extrai
otimizador/modelo_pl_otimizador.py:40-120        # ❌ Nunca modela

# ❌ Orçamento de restrições
otimizador/modelo_pl_otimizador.py:66            # MAX_CONSTRAINTS = 1000
```

### Método Sequencial Funcional

```python
services/gestores/producao/executor_pedidos.py:48-166   # Implementação completa
models/atividades/atividade_modular.py:548-918          # Alocação backward
```

---

## 📈 Métricas de Validação

Todos os dados mencionados foram **verificados** contra arquivos de configuração:

```
✅ Produtos verificados:       4/4   (100%)
✅ Atividades verificadas:     16+   (100%)
✅ Equipamentos verificados:   7/7   (100%)
✅ Logs consistentes:          13/13 (100%)
✅ Restrições verificadas:     6/6   (100%)
```

Ver: [VERIFICACAO_ATIVIDADES.md](VERIFICACAO_ATIVIDADES.md)

---

## 💡 Recomendações por Prazo

### ⚡ Curto Prazo (Imediato)
- ✅ Usar método **sequencial** em produção
- ⚠️ Desabilitar PL para pedidos críticos
- ✅ Adicionar validação pós-PL

### 🔧 Médio Prazo (1-3 meses)
- Modelar `tempo_maximo_de_espera`
- Modelar equipamentos como recursos
- Remover orçamento de restrições

### 🎯 Longo Prazo (6+ meses)
- Abordagem híbrida (PL + Sequencial)
- Validação obrigatória
- **Objetivo:** PL ≥80% sucesso

---

## 📚 Referências

### Dataset
- `data/csv/exemplo_pedidos.csv` - 13 pedidos experimentais
- `data/metricas_comparacao.json` - Resultados completos

### Código-Fonte
- `services/gestores/producao/executor_pedidos.py`
- `otimizador/modelo_pl_otimizador.py`
- `otimizador/extrator_dados_pedidos.py`
- `otimizador/otimizador_integrado.py`

### Logs
- `logs/comparacao_sequencial_20251114_090610/`
- `logs/comparacao_otimizado_20251114_090613/`

### Atividades Verificadas
- `data/produtos/atividades/1069_coxinha_de_carne_de_sol.json`
- `data/produtos/atividades/1074_folhado_de_queijos_finos.json`
- `data/produtos/atividades/1004_pao_baguete.json`
- `data/produtos/atividades/1005_pao_tranca_de_queijos_finos.json`

---

## 🤝 Como Usar Esta Documentação

### Para Decisão Rápida
➡️ Leia apenas: [SUMARIO_EXECUTIVO.md](SUMARIO_EXECUTIVO.md)

### Para Implementação
➡️ Leia: [ANALISE_SEQUENCIAL_VS_PL.md](ANALISE_SEQUENCIAL_VS_PL.md) + código-fonte referenciado

### Para Publicação Acadêmica
➡️ Leia: [DISSERTACAO_METODOS_AGENDAMENTO.md](DISSERTACAO_METODOS_AGENDAMENTO.md)

### Para Auditoria/Revisão
➡️ Leia: [VERIFICACAO_ATIVIDADES.md](VERIFICACAO_ATIVIDADES.md)

### Para Explicação Visual
➡️ Leia: [DIAGRAMA_COMPARATIVO_METODOS.txt](DIAGRAMA_COMPARATIVO_METODOS.txt)

---

## 📞 Contato

**Autor:** Claude (Anthropic)
**Sistema:** SIVIRA - Sistema Inteligente para Visualização e Replanejamento de Atividades
**Data:** 14 de Novembro de 2025
**Versão:** 1.0

Para questões técnicas, consulte os arquivos de código referenciados em cada documento.

---

## 📄 Licença

Documentação elaborada para o projeto SIVIRA.
Todos os trechos de código citados pertencem ao sistema SIVIRA.

---

**Última atualização:** 14 de Novembro de 2025
