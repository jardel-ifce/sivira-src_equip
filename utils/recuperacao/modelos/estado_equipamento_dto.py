"""
DTO para Estado de Equipamento
===============================

Representa o estado completo de um equipamento recuperado.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .ocupacao_dto import OcupacaoDTO


@dataclass
class EstadoEquipamentoDTO:
    """
    🔧 DTO que representa o estado completo de um equipamento recuperado

    Contém:
    - nome_equipamento: Nome do equipamento
    - tipo_equipamento: Tipo/classe do equipamento
    - ocupacoes: Lista de ocupações extraídas
    - total_ocupacoes: Número total de ocupações
    - equipamento_restaurado: Se o estado foi restaurado no objeto
    - erros: Lista de erros encontrados durante parsing/restauração
    """

    nome_equipamento: str
    tipo_equipamento: str
    ocupacoes: List[OcupacaoDTO] = field(default_factory=list)
    equipamento_restaurado: bool = False
    erros: List[str] = field(default_factory=list)

    @property
    def total_ocupacoes(self) -> int:
        """Retorna total de ocupações"""
        return len(self.ocupacoes)

    @property
    def tem_erros(self) -> bool:
        """Verifica se houve erros"""
        return len(self.erros) > 0

    @property
    def tem_ocupacoes(self) -> bool:
        """Verifica se tem ocupações"""
        return len(self.ocupacoes) > 0

    def adicionar_erro(self, erro: str):
        """Adiciona erro à lista"""
        self.erros.append(erro)

    def adicionar_ocupacao(self, ocupacao: OcupacaoDTO):
        """Adiciona ocupação à lista"""
        self.ocupacoes.append(ocupacao)

    def __repr__(self) -> str:
        """Representação legível"""
        status = "✅ OK" if self.equipamento_restaurado and not self.tem_erros else "❌ ERRO" if self.tem_erros else "⏳ PENDENTE"
        return (
            f"EstadoEquipamentoDTO("
            f"{self.nome_equipamento} ({self.tipo_equipamento}): "
            f"{self.total_ocupacoes} ocupações, "
            f"status={status}"
            f")"
        )
