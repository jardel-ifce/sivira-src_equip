# Módulos de Interface do Otimizador v2.0

**Data:** 14 de Novembro de 2025
**Objetivo:** Facilitar uso e integração do Otimizador v2.0

---

## 1. Motivação

O otimizador v2.0 foi criado com sucesso, mas havia problemas de incompatibilidade entre interfaces dos componentes existentes:

- `ConversorPedidos` não tinha método esperado
- `GerenciadorPedidos` tinha assinatura diferente
- `ExtratorDadosPedidos` interface não documentada

**Solução:** Criar camada de adaptação e interfaces de alto nível para uso simplificado.

---

## 2. Módulos Criados

### 2.1 AdaptadorDados

**Arquivo:** [otimizador_v2/adaptador_dados.py](../otimizador_v2/adaptador_dados.py)

**Responsabilidade:** Adaptar diferentes fontes de dados para formato esperado pelo otimizador.

**Classes:**

1. **`AdaptadorDados`**
   - `carregar_pedidos_do_csv(csv_path)` → Lista de PedidoDeProducao
   - `extrair_dados_de_pedidos(pedidos)` → Lista de DadosPedido
   - `pipeline_completo_csv(csv_path)` → (pedidos, dados)

2. **`FabricaAdaptador`**
   - `criar_com_almoxarifado_padrao()` → AdaptadorDados
   - `criar_com_configurador(configurador)` → AdaptadorDados

**Fluxo:**

```
CSV → PedidoDeProducao → DadosPedido → Otimizador
  ↑         ↑                ↑
  └─────────┴────────────────┘
      AdaptadorDados
```

**Exemplo:**

```python
from otimizador_v2 import FabricaAdaptador

adaptador = FabricaAdaptador.criar_com_almoxarifado_padrao()
pedidos, dados = adaptador.pipeline_completo_csv('exemplo_pedidos.csv')
```

---

### 2.2 ExecutorV2

**Arquivo:** [otimizador_v2/executor_v2.py](../otimizador_v2/executor_v2.py)

**Responsabilidade:** Interface de alto nível que orquestra todo o processo de otimização.

**Classe Principal: `ExecutorV2`**

**Métodos:**

1. **`inicializar(limpar_logs=True)`**
   - Configura ConfiguradorAmbiente
   - Cria AdaptadorDados
   - Cria OtimizadorIntegradoV2
   - Retorna: bool (sucesso)

2. **`otimizar_csv(csv_path, timeout, resolucao, limitar_pedidos)`**
   - Carrega pedidos do CSV
   - Executa otimização completa
   - Retorna: SolucaoPLCompleta

3. **`otimizar_pedidos(pedidos, timeout, resolucao)`**
   - Otimiza lista de PedidoDeProducao já criados
   - Retorna: SolucaoPLCompleta

4. **`imprimir_resumo_solucao(solucao, pedidos)`**
   - Mostra resumo detalhado da solução
   - Lista pedidos executados e não executados
   - Exibe estatísticas do modelo

5. **`comparar_com_baseline(solucao, total_pedidos)`**
   - Compara v2 com v1 (Sequencial e PL Original)
   - Análise de melhoria

**Função de Conveniência:**

```python
def executar_otimizacao_rapida(csv_path, timeout, limitar)
```

**Exemplo Simples:**

```python
from otimizador_v2 import ExecutorV2

executor = ExecutorV2()
executor.inicializar()
solucao = executor.otimizar_csv('exemplo_pedidos.csv')
executor.imprimir_resumo_solucao(solucao, pedidos)
```

**Exemplo Ultra-Rápido:**

```python
from otimizador_v2 import executar_otimizacao_rapida

solucao = executar_otimizacao_rapida('exemplo_pedidos.csv')
```

---

### 2.3 Atualização do `__init__.py`

**Arquivo:** [otimizador_v2/__init__.py](../otimizador_v2/__init__.py)

**Mudanças:**

- Exporta todas as interfaces públicas
- Documentação de uso rápido e avançado
- Organização por categorias (Modelo, Otimizador, Adaptadores, Executor)

**Imports Disponíveis:**

```python
# Uso rápido
from otimizador_v2 import executar_otimizacao_rapida

# Executor
from otimizador_v2 import ExecutorV2

# Adaptadores
from otimizador_v2 import AdaptadorDados, FabricaAdaptador

# Modelo PL
from otimizador_v2 import ModeloPLCompleto, SolucaoPLCompleta

# Otimizador integrado
from otimizador_v2 import OtimizadorIntegradoV2
```

---

## 3. Scripts de Teste e Exemplos

### 3.1 Teste Simplificado

**Arquivo:** [testar_v2_simplificado.py](../testar_v2_simplificado.py)

**Funcionalidade:**

- Teste 1: 2 pedidos (validação rápida)
- Teste 2: 13 pedidos (comparação completa)
- Resumo automático
- Comparação com baseline

**Uso:**

```bash
python testar_v2_simplificado.py
```

**Saída Esperada:**

```
# TESTE 1: 2 PEDIDOS
✅ TESTE 1 PASSOU (2/2 pedidos atendidos)

# TESTE 2: 13 PEDIDOS COMPLETOS
📊 Comparação: v2 vs v1
🎯 Análise: v2 superou PL v1

# RESUMO FINAL
✅ Teste 1: PASSOU
📊 Teste 2: X/13 pedidos (Y%)
```

---

### 3.2 Exemplos de Uso

**Arquivo:** [exemplo_uso_v2.py](../exemplo_uso_v2.py)

**4 Exemplos Demonstrados:**

1. **`exemplo_rapido()`** - Uma única linha
2. **`exemplo_simples()`** - Com controle básico
3. **`exemplo_avancado()`** - Com comparação
4. **`exemplo_programatico()`** - Criando pedidos manualmente (sem CSV)

**Uso:**

```bash
python exemplo_uso_v2.py
```

Descomente o exemplo desejado no `main()`.

---

### 3.3 README do Módulo

**Arquivo:** [otimizador_v2/README.md](../otimizador_v2/README.md)

**Conteúdo:**

- Correções implementadas (tabela)
- Arquitetura do módulo
- 3 formas de uso (rápido, simples, avançado)
- Documentação completa de classes
- Comparação v1 vs v2
- Detalhes técnicos (solver, variáveis, restrições)
- Performance esperada (3 cenários)
- Troubleshooting
- Limitações e próximas melhorias
- Referências

---

## 4. Resumo de Arquivos Criados

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `otimizador_v2/adaptador_dados.py` | 175 | Adaptação entre formatos de dados |
| `otimizador_v2/executor_v2.py` | 255 | Interface de alto nível |
| `otimizador_v2/__init__.py` | 58 | Exportação de interfaces públicas |
| `otimizador_v2/README.md` | 380 | Documentação completa do módulo |
| `testar_v2_simplificado.py` | 100 | Script de teste simplificado |
| `exemplo_uso_v2.py` | 150 | 4 exemplos de uso |
| `docs/MODULOS_INTERFACE_V2_CRIADOS.md` | Este arquivo | Documentação dos módulos |

**Total:** ~1.118 linhas de código e documentação

---

## 5. Hierarquia de Abstração

```
Nível 4 (Ultra-Rápido):
    executar_otimizacao_rapida()

Nível 3 (Simples):
    ExecutorV2

Nível 2 (Intermediário):
    OtimizadorIntegradoV2 + AdaptadorDados

Nível 1 (Baixo Nível):
    ModeloPLCompleto + ExtratorDadosPedidos + GeradorJanelasTemporais
```

**Recomendação de Uso:**

- **Iniciantes:** `executar_otimizacao_rapida()` ou `ExecutorV2`
- **Intermediário:** `OtimizadorIntegradoV2` com `AdaptadorDados`
- **Avançado:** `ModeloPLCompleto` diretamente

---

## 6. Compatibilidade

### Resolvido ✅

- ✅ Incompatibilidade com `ConversorPedidos`
- ✅ Incompatibilidade com `GerenciadorPedidos`
- ✅ Interface confusa do `ExtratorDadosPedidos`
- ✅ Falta de exemplo de uso simples
- ✅ Falta de documentação de alto nível

### Interfaces Adaptadas

| Componente Original | Adaptação | Localização |
|---------------------|-----------|-------------|
| `ConversorPedidos` | `AdaptadorDados.carregar_pedidos_do_csv()` | adaptador_dados.py:42 |
| `ExtratorDadosPedidos` | `AdaptadorDados.extrair_dados_de_pedidos()` | adaptador_dados.py:87 |
| Inicialização manual | `ExecutorV2.inicializar()` | executor_v2.py:32 |

---

## 7. Fluxo Completo de Uso

### Via ExecutorV2 (Recomendado)

```python
# 1. Importar
from otimizador_v2 import ExecutorV2

# 2. Criar executor
executor = ExecutorV2()

# 3. Inicializar
executor.inicializar()

# 4. Otimizar
solucao = executor.otimizar_csv('data/csv/exemplo_pedidos.csv')

# 5. Visualizar resultados
pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')
executor.imprimir_resumo_solucao(solucao, pedidos)

# 6. Comparar com v1
executor.comparar_com_baseline(solucao, len(pedidos))
```

### Via Função Rápida

```python
from otimizador_v2 import executar_otimizacao_rapida

solucao = executar_otimizacao_rapida('data/csv/exemplo_pedidos.csv')
print(f"Atendidos: {solucao.pedidos_atendidos}")
```

---

## 8. Próximos Passos

### Imediato

1. ✅ Módulos de interface criados
2. ✅ Documentação completa
3. ✅ Exemplos de uso
4. ⏳ **Executar testes completos**
5. ⏳ Validar resultados vs baseline

### Curto Prazo

- Criar testes unitários para adaptadores
- Adicionar logging estruturado
- Implementar cache de resultados
- Criar visualização gráfica de solução

### Médio Prazo

- Integrar ao menu principal do sistema
- Criar API REST para otimização remota
- Implementar otimizações v3 (ver README)

---

## 9. Conclusão

**Status:** ✅ **MÓDULOS DE INTERFACE COMPLETOS**

Foram criados **7 novos arquivos** (~1.118 linhas) que:

1. **Resolvem** incompatibilidades de interface
2. **Simplificam** drasticamente o uso do otimizador v2
3. **Documentam** completamente o módulo
4. **Fornecem** exemplos práticos de uso
5. **Permitem** teste imediato do sistema

**Próximo Marco:** Executar testes completos e gerar relatório comparativo final.

---

**Autor:** Claude (Anthropic)
**Módulo:** SIVIRA - Sistema Inteligente para Visualização e Replanejamento de Atividades
**Versão:** 2.0
**Fase:** Interfaces Criadas ✅
