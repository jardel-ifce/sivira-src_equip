from datetime import date
from typing import List, Dict
from models.itens.item_almoxarifado import ItemAlmoxarifado


class GestorAlmoxarifado:
    def __init__(self, itens: List[ItemAlmoxarifado]):
        self.itens: Dict[int, ItemAlmoxarifado] = {item.id: item for item in itens}

    def reservar_item(self, id_item: int, data: date, quantidade: float):
        item = self.itens.get(id_item)
        if not item:
            raise ValueError(f"Item {id_item} não encontrado.")

        item.reservas_futuras.append({
            "data": data.strftime("%Y-%m-%d"),
            "quantidade_reservada": quantidade
        })

    def liberar_reserva(self, id_item: int, data: date):
        item = self.itens.get(id_item)
        if not item:
            raise ValueError(f"Item {id_item} não encontrado.")

        reservas_removidas = []
        for reserva in item.reservas_futuras:
            if reserva["data"] == data.strftime("%Y-%m-%d"):
                item.estoque_atual -= reserva["quantidade_reservada"]
                reservas_removidas.append(reserva)

        for r in reservas_removidas:
            item.reservas_futuras.remove(r)

    def verificar_disponibilidade_real_para_data(self, id_item: int, data: date) -> float:
        """
        Retorna o estoque real (estoque_atual), sem considerar reservas.
        """
        item = self.itens.get(id_item)
        if not item:
            raise ValueError(f"Item {id_item} não encontrado.")
        return item.estoque_atual

    def verificar_disponibilidade_projetada_para_data(self, id_item: int, data: date) -> float:
        """
        Retorna o estoque projetado considerando todas as reservas até a data informada (inclusive).
        """
        item = self.itens.get(id_item)
        if not item:
            raise ValueError(f"Item {id_item} não encontrado.")

        reservas_ate_data = sum(
            r["quantidade_reservada"]
            for r in item.reservas_futuras
            if r["data"] <= data.strftime("%Y-%m-%d")
        )
        return item.estoque_atual - reservas_ate_data

    def obter_item(self, id_item: int) -> ItemAlmoxarifado:
        return self.itens.get(id_item)
    def exibir_itens(self):
        
        print("📦 Itens no Almoxarifado:")
        for item in self.itens.values():
            print(f"🔹 ID: {item.id} | Descrição: {item.descricao} | Estoque Atual: {item.estoque_atual:.2f}")
