from typing import Optional, List, Dict
from enums.tipo_item import TipoItem
from enums.politica_producao import PoliticaProducao
from enums.unidade_medida import UnidadeMedida
from models.ficha_tecnica_modular import FichaTecnicaModular


class ItemAlmoxarifado:
    def __init__(
        self,
        id: int,
        descricao: str,
        tipo_item: TipoItem,
        peso: float,
        unidade_medida: UnidadeMedida,
        estoque_min: float,
        estoque_max: float,
        politica_producao: PoliticaProducao,
        ficha_tecnica: Optional[FichaTecnicaModular] = None,
        consumo_diario_estimado: Optional[float] = None,
        reabastecimento_previsto_em: Optional[str] = None,
        reservas_futuras: Optional[List[Dict]] = None,
        estoque_atual: Optional[float] = None
    ):
        self.id = id
        self.descricao = descricao
        self.tipo_item = tipo_item
        self.peso = peso
        self.unidade_medida = unidade_medida
        self.estoque_min = estoque_min
        self.estoque_max = estoque_max
        self.estoque_atual = estoque_atual if estoque_atual is not None else estoque_min
        self.politica_producao = politica_producao
        self.ficha_tecnica = ficha_tecnica
        self.consumo_diario_estimado = consumo_diario_estimado
        self.reabastecimento_previsto_em = reabastecimento_previsto_em
        self.reservas_futuras = reservas_futuras or []
        self.historico: List[Dict] = []
