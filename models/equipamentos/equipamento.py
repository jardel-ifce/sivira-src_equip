from datetime import datetime
from typing import List, Tuple, Any
from utils.logs.logger_factory import setup_logger

# 🔧 Logger específico para a classe Equipamento
logger = setup_logger('Equipamento')

class Equipamento:
    """
    ⚙️ Superclasse base para qualquer equipamento.
    Responsável pela gestão de identidade, setor, tipo, ocupação temporal e status.
    As subclasses são responsáveis pela gestão física (peso, níveis, caixas, etc.).
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor,
        tipo_equipamento,
        numero_operadores: int = 1,
        status_ativo: bool = True,
    ):
        self.id = id
        self.nome = nome
        self.setor = setor
        self.tipo_equipamento = tipo_equipamento
        self.numero_operadores = numero_operadores
        self.status_ativo = status_ativo
