"""
DTO para Ocupação de Equipamento
=================================

Representa uma ocupação extraída do log, independente do tipo de equipamento.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class OcupacaoDTO:
    """
    📦 DTO que representa uma ocupação extraída do log

    Atributos básicos (presentes em todos os equipamentos):
    - id_ordem: ID da ordem de produção
    - id_pedido: ID do pedido
    - id_atividade: ID da atividade
    - id_item: ID do item sendo produzido
    - inicio: Data/hora de início
    - fim: Data/hora de fim
    - nome_equipamento: Nome do equipamento
    - tipo_equipamento: Tipo do equipamento (classe)

    Atributos específicos (variam por tipo de equipamento):
    - detalhes: Dicionário com informações específicas do tipo

    Exemplos de detalhes por tipo:
    - Bancada: {"fracao_numero": 1}
    - Fogão: {"boca_numero": 2, "tipo_chama": "ALTA", "pressoes_chama": ["ALTA", "MEDIA"]}
    - Câmara: {"nivel_numero": 1, "caixa_numero": None, "temperatura": 4}
    - Masseira: {"quantidade_gramas": 3250.0, "velocidades": ["ALTA"], "tipo_mistura": "RAPIDA"}
    """

    # Atributos básicos (obrigatórios)
    id_ordem: int
    id_pedido: int
    id_atividade: int
    id_item: int
    inicio: datetime
    fim: datetime
    nome_equipamento: str
    tipo_equipamento: str

    # Atributos específicos (opcionais, variam por tipo)
    detalhes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validação básica após inicialização"""
        if self.fim <= self.inicio:
            raise ValueError(f"Fim ({self.fim}) deve ser posterior ao início ({self.inicio})")

    @property
    def duracao_minutos(self) -> int:
        """Retorna duração em minutos"""
        return int((self.fim - self.inicio).total_seconds() / 60)

    def obter_detalhe(self, chave: str, padrao: Any = None) -> Any:
        """Obtém detalhe específico com valor padrão"""
        return self.detalhes.get(chave, padrao)

    def __repr__(self) -> str:
        """Representação legível"""
        return (
            f"OcupacaoDTO("
            f"equipamento={self.nome_equipamento}, "
            f"ordem={self.id_ordem}, "
            f"pedido={self.id_pedido}, "
            f"atividade={self.id_atividade}, "
            f"item={self.id_item}, "
            f"periodo={self.inicio.strftime('%H:%M')}-{self.fim.strftime('%H:%M')}, "
            f"duracao={self.duracao_minutos}min"
            f")"
        )
