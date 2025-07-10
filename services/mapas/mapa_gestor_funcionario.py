from services.gestor_funcionario import GestorFuncionario
from factory.fabrica_funcionarios import (
    funcionario_1,
    funcionario_2,
    funcionario_3,
    funcionario_4,
    funcionario_5
)

FUNCIONARIOS_DISPONIVEIS = [
    funcionario_1,
    funcionario_2,
    funcionario_3,
    funcionario_4,
    funcionario_5
]

def carregar_funcionarios():
    return FUNCIONARIOS_DISPONIVEIS

FUNCIONARIOS = carregar_funcionarios()
GESTOR_FUNCIONARIO = GestorFuncionario(FUNCIONARIOS)

MAPA_GESTOR_FUNCIONARIO = {
    "GLOBAL": GESTOR_FUNCIONARIO
}

def gestor_funcionario_global():
    return MAPA_GESTOR_FUNCIONARIO["GLOBAL"]
