from datetime import datetime, date
from typing import List, Tuple, Optional
from models.itens.almoxarifado import Almoxarifado
from models.itens.item_almoxarifado import ItemAlmoxarifado

class GestorAlmoxarifado:
    def __init__(self, almoxarifado: Almoxarifado):
        self.almoxarifado = almoxarifado

    def verificar_disponibilidade(self, reservas: List[Tuple[int, float, datetime]]) -> bool:
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_por_id(id_item)
            if item is None or not item.tem_estoque_para(data, quantidade):
                return False
        return True
    
    def verificar_disponibilidade_projetada_para_data(
            self,
            id_item: int,
            data: date,
            quantidade: float = 0.0
        ) -> float | bool:
            """
            Verifica a disponibilidade projetada de um item para uma data futura.
            - Se `quantidade` for informada, retorna True/False.
            - Se não for informada, retorna a quantidade projetada.
            """
            return self.almoxarifado.verificar_disponibilidade_projetada_para_data(
                id_item=id_item,
                data=data,
                quantidade=quantidade
            )
    def reservar_itens(self, reservas: List[Tuple[int, float, datetime]]):
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_por_id(id_item)
            if item:
                item.reservar(data, quantidade)

    def consumir_itens(self, consumos: List[Tuple[int, float, datetime]]):
        for id_item, quantidade, data in consumos:
            item = self.almoxarifado.buscar_por_id(id_item)
            if item:
                item.consumir(data, quantidade)

    def cancelar_reservas(self, reservas: List[Tuple[int, float, datetime]]):
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_por_id(id_item)
            if item:
                item.cancelar_reserva(data, quantidade)

    def separar_itens_para_producao(
        self,
        ordem_id: int,
        pedido_id: int,
        funcionario_id: int,
        itens: List[Tuple[int, float, datetime]]
    ):
        """
        Efetiva o consumo dos itens de uma ordem/pedido,
        registrando o funcionário responsável.
        """
        for id_item, quantidade, data in itens:
            item = self.almoxarifado.buscar_por_id(id_item)
            if item:
                item.consumir(data, quantidade, ordem_id, pedido_id)

        # Registrar separação
        print(
            f"📦 Estoque separado para Ordem {ordem_id}, Pedido {pedido_id} "
            f"por Funcionário {funcionario_id} em {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    def exibir_itens_estoque(self, data: Optional[datetime] = None):
        print("📦 Itens no Almoxarifado:")
        for item in self.almoxarifado.itens:
            if data:
                estoque = item.estoque_projetado_em(data)
                print(
                    f"🔹 ID: {item.id_item} | Descrição: {item.descricao} | "
                    f"Estoque Projetado ({data.strftime('%Y-%m-%d')}): {estoque:.2f} {item.unidade_medida.value}"
                )
            else:
                print(
                    f"🔹 ID: {item.id_item} | Descrição: {item.descricao} | "
                    f"Estoque Atual: {item.estoque_atual:.2f} {item.unidade_medida.value}"
                )

    def resumir_estoque_projetado(self, data: date):
        """
        📊 Gera um resumo de estoque projetado para uma data:
        - Estoque atual
        - Quantidade reservada nessa data
        - Estoque projetado
        """
        print(f"\n📅 Estoque projetado para {data.strftime('%Y-%m-%d')}:\n")

        for item in self.almoxarifado.itens:
            reservado = item.quantidade_reservada_em(data)
            projetado = item.estoque_projetado_em(data)

            print(
                f"🔹 ID: {item.id_item} | {item.descricao}\n"
                f"   Estoque atual: {item.estoque_atual:.2f} {item.unidade_medida.value}\n"
                f"   Reservado para {data.strftime('%Y-%m-%d')}: {reservado:.2f}\n"
                f"   📉 Estoque projetado: {projetado:.2f} {item.unidade_medida.value}\n"
            )
