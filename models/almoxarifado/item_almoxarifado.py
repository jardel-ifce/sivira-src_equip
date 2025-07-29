from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Union
from enums.producao.unidade_medida import UnidadeMedida


class ItemAlmoxarifado:
    def __init__(
        self,
        id_item: int,
        nome: str,
        descricao: str,
        tipo_item: str,
        politica_producao: str,
        peso: float,
        unidade_medida: UnidadeMedida,
        estoque_min: float,
        estoque_max: float,
        estoque_atual: float,
        consumo_diario_estimado: float,
        reabastecimento_previsto_em: Optional[str] = None,
        reservas_futuras: Optional[List[dict]] = None,
        ficha_tecnica: Optional[int] = None
    ):
        self.id_item = id_item
        self.nome = nome
        self.descricao = descricao
        self.tipo_item = tipo_item
        self.politica_producao = politica_producao
        self.peso = peso
        self.unidade_medida = unidade_medida
        self.estoque_min = estoque_min
        self.estoque_max = estoque_max
        self.estoque_atual = estoque_atual
        self.consumo_diario_estimado = consumo_diario_estimado
        self.reabastecimento_previsto_em = (
            datetime.strptime(reabastecimento_previsto_em, "%Y-%m-%d")
            if reabastecimento_previsto_em else None
        )
        self.ficha_tecnica_id = ficha_tecnica
        self.reservas_futuras: List[Dict[str, Union[datetime, float, int]]] = self._parse_reservas_futuras(reservas_futuras)

    def _parse_reservas_futuras(self, reservas_raw: Optional[List[dict]]) -> List[dict]:
        if not reservas_raw:
            return []
        reservas_convertidas = []
        for r in reservas_raw:
            reservas_convertidas.append({
                "data": datetime.strptime(r["data"], "%Y-%m-%d"),
                "quantidade": r["quantidade_reservada"],
                "id_ordem": r.get("id_ordem", 0),
                "id_pedido": r.get("id_pedido", 0),
                "id_atividade": r.get("id_atividade")
            })
        return reservas_convertidas

    def reservar(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int, id_atividade: Optional[int] = None):
        self.reservas_futuras.append({
            "data": data,
            "quantidade": quantidade,
            "id_ordem": id_ordem,
            "id_pedido": id_pedido,
            "id_atividade": id_atividade
        })

    def cancelar_reserva(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int):
        self.reservas_futuras = [
            r for r in self.reservas_futuras
            if not (
                r["data"] == data and
                r["quantidade"] == quantidade and
                r["id_ordem"] == id_ordem and
                r["id_pedido"] == id_pedido
            )
        ]


    def estoque_projetado_em(self, data: Union[datetime, date]) -> float:
        """
        📉 Retorna o estoque projetado para uma data (datetime ou date).
        Subtrai as reservas feitas para o mesmo dia da data informada.
        """
        if isinstance(data, datetime):
            data_base = data.date()
        elif isinstance(data, date):
            data_base = data
        else:
            raise TypeError(f"Data inválida: esperado datetime ou date, mas recebeu {type(data)}")

        reservas_no_dia = sum(
            r["quantidade"]
            for r in self.reservas_futuras
            if r["data"].date() == data_base
        )
        return self.estoque_atual - reservas_no_dia


    def tem_estoque_para(self, data: datetime, quantidade: float) -> bool:
        if self.politica_producao == "SOB_DEMANDA":
            return True
        return self.estoque_projetado_em(data) >= quantidade

    def consumir(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int):
        if not self.tem_estoque_para(data, quantidade):
            raise ValueError(
                f"❌ Estoque insuficiente para {self.nome} na data {data.strftime('%Y-%m-%d')}."
            )
        self.estoque_atual -= quantidade
        self.cancelar_reserva(data, quantidade, id_ordem, id_pedido)

    def __repr__(self):
        return f"<ItemAlmoxarifado {self.nome} | Estoque Atual: {self.estoque_atual} {self.unidade_medida.value}>"
    
    def quantidade_reservada_em(self, data: Union[datetime, date]) -> float:
        data_base = data.date() if isinstance(data, datetime) else data
        return sum(
            r["quantidade"]
            for r in self.reservas_futuras
            if r["data"].date() == data_base
        )
