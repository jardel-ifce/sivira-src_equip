# SIVIRA - System Information

## 📋 Configurações do Sistema

### 🐍 Python Environment
- **Versão**: Python 3.12.9
- **Virtual Environment**: `/venv/` (configurado)
- **Executável**: `/usr/local/Cellar/python@3.12/3.12.9/`

### 🏗️ Arquitetura do Projeto
```
src_equip/
├── models/           # Modelos de dados (equipamentos, atividades)
├── services/         # Lógica de negócio e gestores
├── factory/          # Padrão Factory para instanciação
├── utils/            # Utilitários e helpers
├── enums/            # Enumerações e constantes
├── parser/           # Processamento de arquivos JSON
├── menu/             # Interface de usuário
├── otimizador/       # Algoritmos de otimização (PL)
└── data/             # Dados do sistema (JSON)
```

### 🔧 Componentes Principais

#### **Services (Lógica de Negócio)**
- `gestor_producao/` - Coordenação da produção
- `gestores_equipamentos/` - Gestão individual de equipamentos
- `gestor_almoxarifado/` - Controle de estoque
- `otimizador/` - Algoritmos de otimização

#### **Models (Entidades)**
- `equipamentos/` - Classes de equipamentos industriais
- `atividades/` - Pedidos e atividades de produção
- `funcionarios/` - Recursos humanos

#### **Utils (Utilitários)**
- `logs/` - Sistema de logging avançado
- `time/` - Manipulação temporal
- `producao/` - Cálculos de produção

### 🚀 Funcionalidades

#### **Sistema de Produção**
- **Execução Sequencial**: Algoritmo tradicional otimizado
- **Execução Otimizada**: Programação Linear (OR-Tools)
- **Sistema de Ordens**: Agrupamento e controle de sessões
- **Liberação de Equipamentos**: Sistema modular automatizado

#### **Equipamentos Suportados**
- Masseiras, Batedeiras, HotMix
- Fornos, Fogões, Fritadeiras
- Bancadas, Armários, Câmaras Refrigeradas
- Divisoras, Modeladoras, Embaladoras

#### **Otimização**
- **OR-Tools**: Programação Linear para otimização
- **Algoritmo Genético**: Scheduling avançado
- **Análise de Dependências**: Resolução automática

### 📊 Sistema de Logs
- **Estrutura**: logs/{equipamentos,funcionarios,erros,execucoes}/
- **Formatação**: Timestamp + Ordem/Pedido + Detalhes
- **Limpeza**: Automática na inicialização
- **Rastreamento**: Completo por ordem/pedido

### 🔗 Git Configuration
- **Repository**: https://github.com/jardel-ifce/sivira-src_equip.git
- **Branch**: main
- **Remote**: origin

### 🛠️ Comandos Úteis

#### **Ativação do Ambiente**
```bash
source venv/bin/activate
```

#### **Execução do Sistema**
```bash
python menu/main_menu.py
```

#### **Instalação de Dependências**
```bash
pip install -r requirements.txt
```

#### **Limpeza Manual**
```bash
python regenerar_logs_limpos.py
```

### ⚙️ Variáveis de Configuração

#### **Otimizador PL**
- **Resolução Temporal**: 30 minutos (padrão)
- **Timeout**: 300 segundos (padrão)
- **Solver**: OR-Tools (SCIP/CBC)

#### **Sistema de Ordens**
- **Incremento Automático**: Após execução
- **Salvamento**: Automático em data/pedidos/
- **Formato**: JSON estruturado

### 🔒 Segurança
- **Virtual Environment**: Isolamento de dependências
- **Logs Estruturados**: Rastreamento completo
- **Rollback**: Sistema de reversão implementado

### 📈 Performance
- **Programação Linear**: Otimização matemática
- **Cache**: Reutilização de cálculos
- **Paralelização**: Processamento concorrente

---

*Documentação gerada pelo Claude Doctor - Sistema de Saúde Automatizado*
*Última atualização: 2025-01-26*