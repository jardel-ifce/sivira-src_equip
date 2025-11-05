#!/bin/bash
# Script para ativar o ambiente virtual do SIVIRA
# Uso: source activate_venv.sh

cd "$(dirname "$0")"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 SIVIRA - Ativando Ambiente Virtual${NC}"
echo "================================================"

# Verifica se o venv existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado!${NC}"
    echo -e "${YELLOW}Criando ambiente virtual...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado!${NC}"
fi

# Ativa o ambiente virtual
source venv/bin/activate

# Verifica se OR-Tools está instalado
if ! python -c "import ortools" 2>/dev/null; then
    echo -e "${YELLOW}📦 OR-Tools não encontrado. Instalando dependências...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependências instaladas!${NC}"
else
    echo -e "${GREEN}✅ OR-Tools disponível!${NC}"
fi

echo ""
echo -e "${BLUE}Python:${NC} $(which python)"
echo -e "${BLUE}Versão:${NC} $(python --version)"
echo ""
echo -e "${GREEN}🎉 Ambiente virtual ativado com sucesso!${NC}"
echo -e "${YELLOW}💡 Para desativar, execute: deactivate${NC}"
echo ""
