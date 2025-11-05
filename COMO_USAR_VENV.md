# 🐍 Como Usar o Ambiente Virtual (venv) - SIVIRA

## 🚀 Execução Rápida (Recomendado)

Para executar o sistema, simplesmente use:

```bash
./run.sh
```

O script `run.sh` faz automaticamente:
- ✅ Verifica se o venv existe (cria se não existir)
- ✅ Ativa o ambiente virtual
- ✅ Verifica se OR-Tools está instalado
- ✅ Instala dependências automaticamente se necessário
- ✅ Executa o sistema usando o Python correto

---

## 🔧 Ativação Manual do Ambiente Virtual

Se você precisar ativar o ambiente virtual manualmente para desenvolvimento ou testes:

### Opção 1: Script Automático (Recomendado)

```bash
source activate_venv.sh
```

Este script:
- Ativa o venv
- Verifica e instala dependências se necessário
- Mostra informações do ambiente

### Opção 2: Ativação Manual Tradicional

```bash
source venv/bin/activate
```

Para desativar:
```bash
deactivate
```

---

## 📦 Gerenciamento de Dependências

### Instalar/Atualizar Dependências

Com o venv ativado:

```bash
pip install -r requirements.txt
```

### Verificar se OR-Tools está instalado

```bash
python -c "from ortools.linear_solver import pywraplp; print('✅ OR-Tools OK!')"
```

### Listar pacotes instalados

```bash
pip list
```

### Adicionar nova dependência

1. Instale o pacote:
```bash
pip install nome-do-pacote
```

2. Atualize o requirements.txt:
```bash
pip freeze > requirements.txt
```

---

## 🐛 Solução de Problemas

### Problema: "OR-Tools não encontrado"

**Causa**: O Python do sistema está sendo usado ao invés do Python do venv.

**Solução**: Use sempre o `./run.sh` para executar o sistema.

### Problema: Python 3.14 detectado mas venv usa 3.12

**Causa**: OR-Tools ainda não suporta Python 3.14. O venv foi criado com Python 3.12 para compatibilidade.

**O que fazer**:
- ✅ Use `./run.sh` - funciona automaticamente
- ✅ Ou use `source venv/bin/activate` e depois `python menu/main_menu.py` (sem o 3)
- ❌ NÃO use `python3` diretamente pois pode pegar a versão 3.14 do sistema

**Verificar qual Python está ativo**:
```bash
python --version  # Deve mostrar 3.12.x (do venv)
which python      # Deve mostrar caminho do venv
```

### Problema: "ModuleNotFoundError"

**Solução**: Reinstale as dependências:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: venv corrompido

**Solução**: Recrie o ambiente virtual:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 Estrutura do Projeto

```
src_equip/
├── run.sh                  # Script principal (USE ESTE!)
├── activate_venv.sh        # Ativação manual do venv
├── requirements.txt        # Dependências do projeto
├── venv/                   # Ambiente virtual (não commitar!)
│   ├── bin/
│   │   ├── python         # Python do venv
│   │   ├── pip            # pip do venv
│   │   └── activate       # Script de ativação
│   └── lib/               # Bibliotecas instaladas
└── menu/
    └── main_menu.py       # Menu principal do sistema
```

---

## ✅ Checklist Rápido

- [ ] Usar `./run.sh` para executar o sistema
- [ ] Nunca commitar a pasta `venv/`
- [ ] Sempre usar `source activate_venv.sh` para desenvolvimento manual
- [ ] Atualizar `requirements.txt` quando adicionar novos pacotes
- [ ] Verificar se OR-Tools está disponível antes de executar código que use PL

---

## 🎯 Resumo

| Ação | Comando |
|------|---------|
| Executar sistema | `./run.sh` |
| Ativar venv (dev) | `source activate_venv.sh` |
| Desativar venv | `deactivate` |
| Instalar deps | `pip install -r requirements.txt` |
| Verificar OR-Tools | `python -c "import ortools"` |
| Recriar venv | `rm -rf venv && python3 -m venv venv` |

---

**💡 Dica**: O `run.sh` já cuida de tudo automaticamente. Use-o sempre!
