#!/bin/bash
cd "$(dirname "$0")"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Sistema SIVIRA...${NC}"

# Verifica se o venv existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado!${NC}"
    echo -e "${YELLOW}Criando ambiente virtual...${NC}"
    python3 -m venv venv
fi

# Ativa o ambiente virtual
source venv/bin/activate

# Verifica se as dependências estão instaladas
if ! python -c "import ortools" 2>/dev/null; then
    echo -e "${YELLOW}📦 Instalando/atualizando dependências do requirements.txt...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependências instaladas com sucesso!${NC}"
fi

# Executa o menu principal usando o Python do venv explicitamente
python menu/main_menu.py "$@"
