# 📋 Módulo de Recuperação de Estado de Equipamentos

## 📌 Visão Geral

Sistema completo e modular para recuperar o estado de ocupação de equipamentos a partir de logs detalhados. Implementado em `/utils/recuperacao/`.

## 🎯 Objetivo

Após uma queda do sistema, permitir a recuperação completa do estado de todos os equipamentos, restaurando suas ocupações a partir dos logs salvos em `/logs/equipamentos_detalhados/`.

## ✅ Status Atual

### Implementado (100% funcional):
- ✅ Estrutura completa de diretórios
- ✅ DTOs (Modelos de dados)
- ✅ Classes base (ParserBase, RestauradorBase)
- ✅ DetectorLogs (detecta e valida logs)
- ✅ RecuperadorEstado (orquestrador principal)
- ✅ Validadores (ocupações e consistência)
- ✅ **Parser de Bancada** (totalmente implementado e testado)
- ✅ **Restaurador de Bancada** (totalmente implementado)
- ✅ Stubs para todos os 16 tipos de equipamentos
- ✅ Script de teste básico

### Testado:
- ✅ Parsing de Bancadas: **22 ocupações recuperadas** com sucesso
- ✅ Detecção de logs
- ✅ Validação de estrutura
- ✅ Extração de metadados

### Pendente:
- ⏳ Implementar parsers específicos para os 15 tipos restantes
- ⏳ Implementar restauradores específicos para os 15 tipos restantes
- ⏳ Testar restauração com aplicação em objetos
- ⏳ Integrar ao menu principal

---

## 📁 Estrutura de Arquivos

```
utils/recuperacao/
├── __init__.py                          # Exporta classes principais
├── recuperador_estado.py                # Orquestrador principal
├── detector_logs.py                     # Detecta e valida logs
│
├── modelos/                             # DTOs
│   ├── __init__.py
│   ├── ocupacao_dto.py                  # Dados de uma ocupação
│   ├── estado_equipamento_dto.py        # Estado de um equipamento
│   └── relatorio_recuperacao_dto.py     # Relatório completo
│
├── parsers/                             # Parsers por tipo (16 tipos)
│   ├── __init__.py
│   ├── parser_base.py                   # Classe base abstrata ✅
│   ├── parser_bancada.py                # Bancada ✅ IMPLEMENTADO
│   ├── parser_camara_refrigerada.py     # Câmara Refrigerada (stub)
│   ├── parser_freezer.py                # Freezer (stub)
│   ├── parser_fogao.py                  # Fogão (stub)
│   ├── parser_balanca.py                # Balança (stub)
│   ├── parser_masseira.py               # Masseira (stub)
│   ├── parser_batedeira.py              # Batedeiras (stub)
│   ├── parser_hotmix.py                 # HotMix (stub)
│   ├── parser_fritadeira.py             # Fritadeira (stub)
│   ├── parser_armario.py                # Armários (stub)
│   ├── parser_divisora.py               # Divisora (stub)
│   ├── parser_modeladora.py             # Modeladora (stub)
│   ├── parser_embaladora.py             # Embaladora (stub)
│   └── parser_forno.py                  # Forno (stub)
│
├── restauradores/                       # Restauradores por tipo (16 tipos)
│   ├── __init__.py
│   ├── restaurador_base.py              # Classe base abstrata ✅
│   ├── restaurador_bancada.py           # Bancada ✅ IMPLEMENTADO
│   ├── restaurador_camara_refrigerada.py # Câmara Refrigerada (stub)
│   ├── restaurador_freezer.py           # Freezer (stub)
│   ├── restaurador_fogao.py             # Fogão (stub)
│   ├── restaurador_balanca.py           # Balança (stub)
│   ├── restaurador_masseira.py          # Masseira (stub)
│   ├── restaurador_batedeira.py         # Batedeiras (stub)
│   ├── restaurador_hotmix.py            # HotMix (stub)
│   ├── restaurador_fritadeira.py        # Fritadeira (stub)
│   ├── restaurador_armario.py           # Armários (stub)
│   ├── restaurador_divisora.py          # Divisora (stub)
│   ├── restaurador_modeladora.py        # Modeladora (stub)
│   ├── restaurador_embaladora.py        # Embaladora (stub)
│   └── restaurador_forno.py             # Forno (stub)
│
└── validadores/                         # Validadores
    ├── __init__.py
    ├── validador_ocupacoes.py           # Valida ocupações ✅
    └── validador_consistencia.py        # Verifica consistência ✅
```

---

## 🔧 Componentes Principais

### 1. **RecuperadorEstado** (Orquestrador)
- Coordena todo o processo de recuperação
- Identifica tipo de cada equipamento
- Seleciona parser e restaurador apropriados
- Valida recuperação
- Gera relatório completo

**Uso:**
```python
from utils.recuperacao import RecuperadorEstado

recuperador = RecuperadorEstado()
relatorio = recuperador.recuperar_de_log("logs/equipamentos_detalhados/log.log")

if relatorio.sucesso:
    print(f"✅ {relatorio.total_ocupacoes_recuperadas} ocupações recuperadas")
```

### 2. **DetectorLogs**
- Detecta logs disponíveis
- Extrai metadados (ordem, pedidos, data)
- Valida estrutura dos logs
- Ordena por data

**Uso:**
```python
from utils.recuperacao import DetectorLogs

detector = DetectorLogs()
logs = detector.detectar_logs()

for log in logs:
    print(f"Log: {log['nome']}")
    print(f"  Ordem: {log['ordem']}")
    print(f"  Pedidos: {log['pedidos']}")
```

### 3. **DTOs (Data Transfer Objects)**

#### OcupacaoDTO
Representa uma ocupação extraída do log:
- IDs (ordem, pedido, atividade, item)
- Horários (início, fim)
- Detalhes específicos do tipo (fração, boca, nível, etc.)

#### EstadoEquipamentoDTO
Estado de um equipamento:
- Nome e tipo
- Lista de ocupações
- Status de restauração
- Erros encontrados

#### RelatorioRecuperacaoDTO
Relatório completo:
- Lista de estados de equipamentos
- Estatísticas gerais
- Erros e mensagens
- Status de sucesso

### 4. **Parsers**

Classe base `ParserBase` fornece:
- Métodos regex para extração (IDs, horários, quantidades)
- Conversão de horários para datetime
- Validações básicas

Cada parser específico implementa:
- Método `parse(log_content, nome_equipamento) -> List[OcupacaoDTO]`
- Extração de detalhes específicos do tipo

**Exemplo - ParserBancada (implementado):**
```python
class ParserBancada(ParserBase):
    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        # Extrai frações e ocupações
        # Retorna lista de OcupacaoDTO com detalhes {"fracao_numero": X}
```

### 5. **Restauradores**

Classe base `RestauradorBase` fornece:
- Validações de tipo e índices
- Conversão de DTOs para tuplas
- Gerenciamento de erros
- Backup/restauração

Cada restaurador específico implementa:
- Método `restaurar(ocupacoes, equipamento) -> bool`
- Aplicação das ocupações na estrutura interna do equipamento

**Exemplo - RestauradorBancada (implementado):**
```python
class RestauradorBancada(RestauradorBase):
    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Bancada) -> bool:
        # Para cada ocupação:
        #   - Obter número da fração
        #   - Adicionar em equipamento.fracoes_ocupacoes[fracao_index]
```

### 6. **Validadores**

#### ValidadorOcupacoes
- Valida IDs e horários
- Detecta sobreposições temporais
- Verifica ordem cronológica
- Valida durações

#### ValidadorConsistencia
- Verifica duplicatas
- Valida cobertura de tipos
- Gera estatísticas
- Verifica consistência geral

---

## 🧪 Testes

### Teste Básico
```bash
python3 testar_recuperacao_basico.py
```

**Resultado atual:**
```
✅ PASSOU: Detector de Logs
✅ PASSOU: Parsing sem Restauração

Resultado: 2/2 testes passaram
🎉 Todos os testes passaram!

📊 Estatísticas:
   • Total de equipamentos: 41
   • Equipamentos com ocupações: 3 (Bancadas)
   • Total de ocupações recuperadas: 22
```

---

## 📊 Mapeamento de Tipos

O sistema suporta 16 tipos de equipamentos:

| Tipo | Parser | Restaurador | Status |
|------|--------|-------------|--------|
| Bancada | ✅ Implementado | ✅ Implementado | **Testado** |
| CamaraRefrigerada | Stub | Stub | Pendente |
| Freezer | Stub | Stub | Pendente |
| Fogao | Stub | Stub | Pendente |
| BalancaDigital | Stub | Stub | Pendente |
| Masseira | Stub | Stub | Pendente |
| BatedeiraIndustrial | Stub | Stub | Pendente |
| BatedeiraPlanetaria | Stub | Stub | Pendente |
| HotMix | Stub | Stub | Pendente |
| Fritadeira | Stub | Stub | Pendente |
| ArmarioEsqueleto | Stub | Stub | Pendente |
| ArmarioFermentador | Stub | Stub | Pendente |
| DivisoraDeMassas | Stub | Stub | Pendente |
| ModeladoraDePaes | Stub | Stub | Pendente |
| ModeladoraDeSalgados | Stub | Stub | Pendente |
| Embaladora | Stub | Stub | Pendente |
| Forno | Stub | Stub | Pendente |

---

## 🚀 Próximos Passos

### Fase 2: Implementar Parsers Restantes
Para cada tipo de equipamento, seguir o padrão de ParserBancada:
1. Ler formato do log para o tipo
2. Criar regex para extração de dados específicos
3. Gerar OcupacaoDTO com detalhes corretos
4. Testar com log real

**Sugestão de ordem de implementação:**
1. **Câmara Refrigerada / Freezer** (similar, níveis e caixas)
2. **Masseira** (ocupações simples)
3. **Fogão** (bocas com chamas e pressões)
4. **Balança** (pesagens)
5. **Armários** (níveis/andares)
6. Demais tipos

### Fase 3: Implementar Restauradores Restantes
Para cada tipo, seguir o padrão de RestauradorBancada:
1. Identificar estrutura interna do equipamento
2. Converter OcupacaoDTO para tupla no formato correto
3. Adicionar na estrutura apropriada
4. Validar índices e capacidades

### Fase 4: Testes Completos
1. Testar cada parser individualmente
2. Testar cada restaurador individualmente
3. Teste end-to-end com restauração real
4. Validar que objetos restaurados funcionam corretamente

### Fase 5: Integração no Menu
1. Adicionar opção no menu principal
2. Permitir seleção de log
3. Exibir relatório de recuperação
4. Confirmar antes de aplicar restauração

---

## 💡 Padrões de Código

### Criar um Novo Parser

```python
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO

class ParserNovo(ParserBase):
    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        self.limpar_erros()
        ocupacoes = []

        # 1. Iterar sobre linhas
        # 2. Usar métodos herdados: extrair_ids_ocupacao, extrair_horarios, etc.
        # 3. Criar OcupacaoDTO com detalhes específicos
        # 4. Adicionar à lista

        return ocupacoes
```

### Criar um Novo Restaurador

```python
from .restaurador_base import RestauradorBase
from models.equipamentos.novo import Novo

class RestauradorNovo(RestauradorBase):
    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Novo) -> bool:
        self.limpar_erros()

        # 1. Validar tipo
        if not self.validar_tipo_equipamento(equipamento, Novo):
            return False

        # 2. Para cada ocupação:
        #    - Extrair detalhes específicos
        #    - Validar índices
        #    - Adicionar na estrutura interna

        return True
```

---

## 📝 Notas Importantes

1. **Stubs não causam erro**: Parsers/restauradores não implementados retornam lista vazia e adicionam mensagem de erro ao estado do equipamento

2. **Modularidade**: Cada tipo de equipamento tem seu próprio parser e restaurador, facilitando manutenção e testes

3. **Reutilização**: Classe base fornece utilitários comuns, reduzindo duplicação de código

4. **Extensibilidade**: Adicionar novo tipo de equipamento é simples:
   - Criar parser herdando de ParserBase
   - Criar restaurador herdando de RestauradorBase
   - Adicionar aos dicionários em RecuperadorEstado

5. **Validação**: Sistema valida em múltiplas camadas:
   - Parser valida dados extraídos
   - Restaurador valida aplicação
   - Validadores verificam consistência geral

---

## 🎓 Arquitetura

### Fluxo de Recuperação

```
┌─────────────────┐
│  Log Detalhado  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DetectorLogs    │ ──> Valida estrutura
│                 │ ──> Extrai metadados
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ RecuperadorEstado│ ──> Orquestra processo
└────────┬─────────┘
         │
         ├──> Para cada equipamento:
         │    │
         │    ▼
         │    ┌──────────┐     ┌─────────────┐
         │    │  Parser  │────>│ OcupacaoDTO │
         │    └──────────┘     └──────┬──────┘
         │                            │
         │                            ▼
         │    ┌─────────────┐   ┌────────────────────┐
         │    │ Restaurador │<──│ EstadoEquipamentoDTO│
         │    └──────┬──────┘   └────────────────────┘
         │           │
         │           ▼
         │    ┌────────────┐
         │    │ Equipamento│ (objeto)
         │    └────────────┘
         │
         ▼
┌─────────────────┐
│ Validadores     │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ RelatorioRecuperacao│
└─────────────────────┘
```

---

## 👥 Autores

Sistema SIVIRA - Módulo de Recuperação de Estado
Outubro 2025

---

## 📄 Licença

Parte do Sistema SIVIRA
