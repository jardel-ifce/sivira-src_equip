# Documentação do Sistema SIVIRA

**Sistema:** SIVIRA - Sistema Inteligente para Visualização e Replanejamento de Atividades
**Última Atualização:** 14 de Novembro de 2025

---

## 📚 Índice de Documentos

### 1. Análise Comparativa (Baseline - v1)

📄 **[DISSERTACAO_COMPLETA.md](DISSERTACAO_COMPLETA.md)**

Análise acadêmica completa comparando métodos Sequencial vs PL v1:
- Taxa de sucesso: 84,6% vs 30,8%
- Identificação de 3 deficiências críticas no PL
- Exemplos práticos de falhas
- Conclusões e recomendações técnicas

**Status:** ✅ Análise Completa

---

### 2. Otimizador v2.0 - Desenvolvimento

📄 **[OTIMIZADOR_V2_CRIADO.md](OTIMIZADOR_V2_CRIADO.md)**

Documentação do desenvolvimento do otimizador v2:
- Correção das 3 deficiências identificadas
- Arquitetura do modelo PL completo
- Expectativas de melhoria (3 cenários)
- Status de implementação

**Status:** ✅ Implementado - 🟡 Testes Pendentes

📄 **[MODULOS_INTERFACE_V2_CRIADOS.md](MODULOS_INTERFACE_V2_CRIADOS.md)**

Módulos de interface para uso simplificado do v2:
- AdaptadorDados: Adaptação entre formatos
- ExecutorV2: Interface de alto nível
- Exemplos de uso (4 padrões)
- 7 novos arquivos (~1.118 linhas)

**Status:** ✅ Interfaces Criadas

📄 **[INTEGRACAO_MENU_V2.md](INTEGRACAO_MENU_V2.md)**

Integração do otimizador v2 ao menu principal:
- Nova opção: 9️⃣ Executar Ordem Atual (OTIMIZADO PL v2)
- Método: `executar_otimizado_v2()`
- Fluxo completo de execução
- Tratamento de erros

**Status:** ✅ Integração Completa

---

### 3. Documentação Técnica do Módulo

📄 **[../otimizador_v2/README.md](../otimizador_v2/README.md)**

Manual técnico completo do otimizador v2:
- Guia de uso (3 níveis de abstração)
- API completa de todas as classes
- Detalhes de implementação (solver, variáveis, restrições)
- Troubleshooting e limitações
- Performance esperada

**Status:** ✅ Documentação Completa

---

## 🎯 Resultados Comparativos

### Baseline (v1) - 13 Pedidos

| Métrica | Sequencial | PL Original |
|---------|------------|-------------|
| Taxa de Sucesso | **84,6%** (11/13) | 30,8% (4/13) |
| Pedidos gap=0 atendidos | 83,3% (5/6) | **0%** (0/6) |
| Makespan | 1.753 min | 383 min* |
| Tempo Execução | 0,42s | 0,51s |

_*Incomparável (workloads diferentes: 11 vs 4 pedidos)_

**Conclusão v1:** Método Sequencial 2,75× mais eficaz que PL devido a deficiências de modelagem.

---

### Otimizador v2 (Expectativas)

| Cenário | Taxa Esperada | Pedidos gap=0 | Tempo |
|---------|---------------|---------------|-------|
| Otimista | 80-100% (10-13/13) | 100% (6/6) | <10s |
| Realista | 60-80% (8-10/13) | 80-100% (5-6/6) | 10-60s |
| Conservador | 40-60% (5-8/13) | 50-80% (3-5/6) | 60-600s |

**Meta:** Igualar ou superar método Sequencial (≥84,6%)

---

## 📁 Estrutura de Arquivos

```
docs/
├── README.md                               ← Este arquivo
├── DISSERTACAO_COMPLETA.md                 ← Análise comparativa v1
├── OTIMIZADOR_V2_CRIADO.md                 ← Desenvolvimento v2
├── MODULOS_INTERFACE_V2_CRIADOS.md         ← Interfaces v2
├── VERIFICACAO_ATIVIDADES.md               ← Validação de dados
├── NOTA_TECNICA_MAKESPAN.md                ← Explicação makespan
├── ANALISE_SEQUENCIAL_VS_PL.md             ← Análise técnica
└── DIAGRAMA_COMPARATIVO_METODOS.txt        ← Diagramas ASCII

otimizador_v2/
├── README.md                               ← Manual técnico v2
├── __init__.py                             ← Interfaces públicas
├── modelo_pl_completo.py                   ← Modelo PL corrigido (490 linhas)
├── otimizador_integrado_v2.py              ← Integração (187 linhas)
├── adaptador_dados.py                      ← Adaptação de dados (175 linhas)
└── executor_v2.py                          ← Interface alto nível (255 linhas)

Scripts de Teste:
├── testar_v2_simplificado.py               ← Teste simplificado
├── exemplo_uso_v2.py                       ← 4 exemplos de uso
└── teste_final_otimizador_v2.py            ← Teste completo (pendente correção)
```

---

## 🚀 Quick Start - Otimizador v2

### Uso Ultra-Rápido (1 linha)

```python
from otimizador_v2 import executar_otimizacao_rapida

solucao = executar_otimizacao_rapida('data/csv/exemplo_pedidos.csv')
print(f"Pedidos atendidos: {solucao.pedidos_atendidos}")
```

### Uso Simples com Controle

```python
from otimizador_v2 import ExecutorV2

executor = ExecutorV2()
executor.inicializar()

solucao = executor.otimizar_csv('data/csv/exemplo_pedidos.csv')
executor.imprimir_resumo_solucao(solucao, pedidos)
executor.comparar_com_baseline(solucao, 13)
```

Ver documentação completa em: **[otimizador_v2/README.md](../otimizador_v2/README.md)**

---

## 🔍 Deficiências Corrigidas no v2

| # | Deficiência Identificada no PL v1 | Correção Implementada no v2 |
|---|-----------------------------------|----------------------------|
| **1** | `tempo_maximo_de_espera` não modelado<br>→ 100% falha em pedidos com gap=0 (6/6) | ✅ Validação via filtro de janelas<br>Backward scheduling garante gap=0 |
| **2** | Equipamentos não modelados como recursos<br>→ Conflitos descobertos tarde demais | ✅ Conflitos temporais explícitos<br>Verificação de sobreposição completa |
| **3** | Orçamento de 1.000 restrições<br>→ 88% das restrições não protegidas | ✅ SEM LIMITE arbitrário<br>Algoritmo O(n²) modela TODAS |

**Resultado Esperado:** Taxa de sucesso significativamente superior aos 30,8% do PL v1.

---

## 📊 Roadmap do Projeto

### Concluído ✅

- [x] Análise comparativa baseline (v1)
- [x] Identificação de 3 deficiências críticas
- [x] Implementação do modelo PL completo (v2)
- [x] Criação de interfaces simplificadas
- [x] Documentação técnica completa
- [x] Exemplos de uso e testes
- [x] **Integração ao menu principal** (Opção 9)

### Em Andamento 🟡

- [ ] **Testes em produção com menu** ← Próximo passo
- [ ] Validação de correções implementadas
- [ ] Medição de performance real

### Planejado 📅

- [ ] Relatório comparativo final (v1 vs v2)
- [ ] Análise de casos especiais (gap=0, conflitos)
- [ ] Integração ao menu principal do sistema
- [ ] Otimizações de performance (v3)

---

## 🎓 Publicações Acadêmicas

### Dissertação Principal

**[DISSERTACAO_COMPLETA.md](DISSERTACAO_COMPLETA.md)**

Texto dissertativo acadêmico analisando:
- Problema de Job Shop Scheduling (JSSP)
- Implementação de dois métodos (Sequencial e PL)
- Comparação empírica com 13 pedidos reais
- Análise crítica de deficiências
- Conclusões sobre completude vs sofisticação

**Contribuição:** Demonstra que completude da modelagem é mais crítica que sofisticação algorítmica em ambientes reais.

---

## 📖 Referências de Código

### Método Sequencial (v1)
- **Implementação:** [services/gestores/producao/executor_pedidos.py](../services/gestores/producao/executor_pedidos.py) (linhas 48-166)
- **Características:** Backward scheduling, pool dinâmico, ordenação topológica

### Método PL Original (v1 - com deficiências)
- **Modelo:** [otimizador/modelo_pl_otimizador.py](../otimizador/modelo_pl_otimizador.py) (linhas 40-120)
- **Deficiência Principal:** Linha 66 - `MAX_CONSTRAINTS = 1000`
- **Extrator:** [otimizador/extrator_dados_pedidos.py](../otimizador/extrator_dados_pedidos.py) (linhas 388-396)

### Método PL Completo (v2 - corrigido)
- **Modelo:** [otimizador_v2/modelo_pl_completo.py](../otimizador_v2/modelo_pl_completo.py)
- **Executor:** [otimizador_v2/executor_v2.py](../otimizador_v2/executor_v2.py)
- **Adaptador:** [otimizador_v2/adaptador_dados.py](../otimizador_v2/adaptador_dados.py)

### Dataset
- **CSV:** [data/csv/exemplo_pedidos.csv](../data/csv/exemplo_pedidos.csv) - 13 pedidos
- **Métricas v1:** [data/metricas_comparacao.json](../data/metricas_comparacao.json)

---

## 🔬 Metodologia de Teste

### Conjunto de Teste Padrão

**13 pedidos** do arquivo `exemplo_pedidos.csv`:
- 5 pedidos com deadline 07:00
- 8 pedidos com deadline 08:00
- 6 pedidos com `tempo_maximo_de_espera = 0` (crítico)

### Métricas Avaliadas

1. **Taxa de Sucesso:** Percentual de pedidos atendidos
2. **Pedidos gap=0:** Atendimento de pedidos com restrição crítica
3. **Makespan:** Duração total da produção (quando comparável)
4. **Tempo de Execução:** Duração do cálculo de agendamento

### Critérios de Validação

- ✅ **Sucesso:** Pedido agendado dentro do deadline
- ❌ **Falha:** Pedido não agendado ou fora do deadline
- ⚠️ **Gap zero:** Atividades sucessoras devem ser contíguas (sem intervalo)

---

## 💡 Principais Aprendizados

1. **Completude > Sofisticação:** Modelo simples e completo supera modelo sofisticado mas incompleto

2. **Restrições Implícitas:** Backward scheduling e pool dinâmico satisfazem restrições por construção

3. **Orçamentos Arbitrários:** Limitar restrições por "budget" prejudica completude sem ganho real de performance

4. **Gap Zero:** Restrição crítica em produção industrial - deve ser modelada explicitamente

5. **Validação Prática:** Testes com dados reais revelam deficiências que análise teórica não captura

---

## 📞 Suporte e Contribuições

### Reportar Problemas

- Criar issue no repositório
- Incluir logs relevantes
- Descrever comportamento esperado vs observado

### Contribuir

1. Fork do repositório
2. Criar branch para feature/correção
3. Implementar mudanças com testes
4. Criar pull request com descrição detalhada

---

## 📄 Licença

Este projeto faz parte do sistema SIVIRA.

---

**Autor:** Claude (Anthropic)
**Versão da Documentação:** 2.0
**Status:** Documentação Completa ✅ | Testes Pendentes 🟡
