# Otimizador v2.0 - Modelo PL Completo

Módulo de otimização corrigido que resolve as três deficiências críticas identificadas no PL v1.

---

## Correções Implementadas

| # | Deficiência v1 | Correção v2 | Arquivo |
|---|----------------|-------------|---------|
| 1 | `tempo_maximo_de_espera` não modelado | Validação via filtro de janelas | [modelo_pl_completo.py](modelo_pl_completo.py#L207-L244) |
| 2 | Equipamentos não modelados | Conflitos temporais explícitos | [modelo_pl_completo.py](modelo_pl_completo.py#L246-L297) |
| 3 | Orçamento de 1.000 restrições | SEM LIMITE (O(n²) completo) | [modelo_pl_completo.py](modelo_pl_completo.py#L299-L355) |

**Resultado Esperado:** Taxa de sucesso superior a 30,8% (PL v1), objetivo de alcançar 84,6% (Sequencial v1).

---

## Arquitetura do Módulo

```
otimizador_v2/
├── __init__.py                     # Exporta interfaces públicas
├── README.md                       # Este arquivo
│
├── modelo_pl_completo.py           # Modelo PL com TODAS as restrições
├── otimizador_integrado_v2.py      # Integração com pipeline de execução
│
├── adaptador_dados.py              # Adaptação de dados entre formatos
└── executor_v2.py                  # Interface de alto nível
```

---

## Uso Rápido

### Opção 1: Ultra-Rápido (1 linha)

```python
from otimizador_v2 import executar_otimizacao_rapida

solucao = executar_otimizacao_rapida('data/csv/exemplo_pedidos.csv')
print(f"Pedidos atendidos: {solucao.pedidos_atendidos}")
```

### Opção 2: Simples com Controle

```python
from otimizador_v2 import ExecutorV2

executor = ExecutorV2()
executor.inicializar()

solucao = executor.otimizar_csv(
    csv_path='data/csv/exemplo_pedidos.csv',
    timeout_segundos=600
)

# Mostrar resultados
pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')
executor.imprimir_resumo_solucao(solucao, pedidos)
executor.comparar_com_baseline(solucao, len(pedidos))
```

### Opção 3: Avançado (Controle Total)

```python
from otimizador_v2 import (
    OtimizadorIntegradoV2,
    AdaptadorDados,
    FabricaAdaptador
)
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente

# 1. Configurar ambiente
configurador = ConfiguradorAmbiente()
configurador.inicializar_ambiente()

# 2. Criar adaptador
adaptador = FabricaAdaptador.criar_com_configurador(configurador)

# 3. Carregar e extrair dados
pedidos, dados = adaptador.pipeline_completo_csv('data/csv/exemplo_pedidos.csv')

# 4. Criar otimizador
otimizador = OtimizadorIntegradoV2(configurador)

# 5. Executar otimização
solucao = otimizador.otimizar(
    pedidos=pedidos,
    timeout_segundos=600,
    resolucao_minutos=60
)

# 6. Analisar resultados
print(f"Status: {solucao.status_solver}")
print(f"Pedidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
print(f"Makespan: {solucao.makespan_minutos} min")
```

---

## Scripts de Teste

### Teste Simplificado
```bash
python testar_v2_simplificado.py
```

Testa com 2 e 13 pedidos, mostra comparação automática com v1.

### Exemplo de Uso
```bash
python exemplo_uso_v2.py
```

Demonstra 4 formas diferentes de uso do módulo.

---

## Classes Principais

### 1. ModeloPLCompleto

Modelo de programação linear completo com todas as restrições.

**Métodos:**
- `resolver(timeout_segundos)` → `SolucaoPLCompleta`

**Estatísticas:**
```python
solucao.estatisticas = {
    'total_variaveis': int,
    'total_restricoes': int,
    'pedidos_totais': int,
    'pedidos_atendidos': int,
    'taxa_atendimento': float,
    'tempo_resolucao': float,
    'makespan_minutos': float,
    'restricoes_por_tipo': {
        'unicidade_pedido': int,
        'tempo_maximo_espera': int,
        'equipamentos_capacidade': int,
        'conflitos_temporais': int
    }
}
```

### 2. ExecutorV2

Interface de alto nível para execução simplificada.

**Métodos:**
- `inicializar()` → `bool`: Configura ambiente completo
- `otimizar_csv(csv_path, timeout, limitar)` → `SolucaoPLCompleta`
- `otimizar_pedidos(pedidos, timeout)` → `SolucaoPLCompleta`
- `imprimir_resumo_solucao(solucao, pedidos)`: Mostra resultados detalhados
- `comparar_com_baseline(solucao, total)`: Compara com v1

### 3. AdaptadorDados

Adaptador entre diferentes formatos de dados.

**Métodos:**
- `carregar_pedidos_do_csv(csv_path)` → `List[PedidoDeProducao]`
- `extrair_dados_de_pedidos(pedidos)` → `List[DadosPedido]`
- `pipeline_completo_csv(csv_path)` → `(pedidos, dados)`

### 4. SolucaoPLCompleta

Resultado da otimização.

**Atributos:**
- `pedidos_atendidos`: int
- `pedidos_selecionados`: Dict[id, janela_index]
- `janelas_selecionadas`: Dict[id, JanelaTemporal]
- `tempo_resolucao`: float
- `status_solver`: str ("OPTIMAL", "FEASIBLE", "INFEASIBLE", ...)
- `objetivo_otimo`: float
- `estatisticas`: Dict
- `makespan_minutos`: float

---

## Comparação v1 vs v2

| Aspecto | PL v1 | PL v2 |
|---------|-------|-------|
| Taxa de sucesso (13 pedidos) | 30,8% (4/13) | **? (a testar)** |
| Pedidos com gap=0 | 0% (0/6) | **? (a testar)** |
| `tempo_maximo_de_espera` | ❌ Não modelado | ✅ Modelado |
| Equipamentos | ❌ Não modelados | ✅ Modelados |
| Restrições de conflito | ⚠️ Incompletas (1.000 limite) | ✅ Completas (sem limite) |
| Complexidade | O(n) restrições | O(n²) restrições |
| Tempo de execução | 0,51s | **? (a testar)** |

---

## Detalhes Técnicos

### Solver
- **Engine:** OR-Tools (SCIP)
- **Tipo:** Mixed Integer Programming (MIP)
- **Timeout:** Configurável (padrão: 600s)

### Variáveis de Decisão
- `x[pedido_id, janela_index]`: Binária, 1 se janela é selecionada

### Restrições

1. **Unicidade por Pedido:**
   ```
   ∑_j x[p,j] ≤ 1  ∀ pedido p
   ```

2. **Tempo Máximo de Espera:**
   - Filtro pré-processamento: janelas inviáveis são removidas
   - Backward scheduling garante gap = 0 quando necessário

3. **Conflitos Temporais:**
   ```
   x[p1,j1] + x[p2,j2] ≤ 1  ∀ (j1, j2) que se sobrepõem
   ```
   **SEM LIMITE** - todas as combinações são verificadas

### Função Objetivo
```
maximize ∑_p ∑_j x[p,j]
```
(Maximizar número de pedidos atendidos)

---

## Performance Esperada

### Cenário Otimista
- Taxa de sucesso: 80-100% (10-13/13)
- Pedidos gap=0: 100% (6/6)
- Tempo: <10s

### Cenário Realista
- Taxa de sucesso: 60-80% (8-10/13)
- Pedidos gap=0: 80-100% (5-6/6)
- Tempo: 10-60s

### Cenário Conservador
- Taxa de sucesso: 40-60% (5-8/13)
- Pedidos gap=0: 50-80% (3-5/6)
- Tempo: 60-600s

---

## Troubleshooting

### Problema: "ImportError: cannot import name..."
**Solução:** Certifique-se que está no diretório correto e `sys.path` inclui `src_equip`

### Problema: "TypeError: ExtratorDadosPedidos..."
**Solução:** Use `AdaptadorDados` ou `ExecutorV2` que encapsulam a lógica corretamente

### Problema: Solver retorna "INFEASIBLE"
**Causas possíveis:**
- Deadline impossível de atingir
- Restrições de tempo_maximo_espera muito rígidas
- Conflitos de equipamentos insolúveis

**Solução:** Aumentar deadline dos pedidos ou reduzir quantidade

### Problema: Tempo de execução muito longo
**Causas possíveis:**
- Muitos pares de janelas com sobreposição
- Complexidade O(n²) do algoritmo de conflitos

**Solução:**
- Reduzir `resolucao_minutos` (diminui granularidade)
- Reduzir `timeout_segundos` (aceita solução sub-ótima)
- Limitar número de pedidos simultâneos

---

## Limitações Conhecidas

1. **Complexidade Quadrática:** Algoritmo de conflitos é O(n²), pode ser lento para muitos pedidos

2. **Equipamentos:** Modelados implicitamente via conflitos temporais, não via restrições de capacidade explícitas

3. **Makespan:** Minimização de makespan é objetivo secundário (primário é maximizar pedidos)

4. **Memória:** Modelos grandes (>50 pedidos) podem consumir muita RAM

---

## Próximas Melhorias (v3.0)

- [ ] Modelagem explícita de capacidade de equipamentos
- [ ] Objetivo multi-critério (pedidos + makespan)
- [ ] Algoritmo de conflitos mais eficiente (sweep line O(n log n))
- [ ] Suporte a prioridades de pedidos
- [ ] Warm start com solução sequencial
- [ ] Paralelização do solver

---

## Referências

- **Análise Original:** [docs/DISSERTACAO_COMPLETA.md](../docs/DISSERTACAO_COMPLETA.md)
- **Deficiências Identificadas:** [docs/OTIMIZADOR_V2_CRIADO.md](../docs/OTIMIZADOR_V2_CRIADO.md)
- **OR-Tools Documentation:** https://developers.google.com/optimization

---

**Versão:** 2.0
**Data:** Novembro 2025
**Status:** ✅ Implementado - 🟡 Testes Pendentes
**Autor:** Claude (Anthropic)
