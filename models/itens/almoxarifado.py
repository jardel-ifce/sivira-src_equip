from datetime import datetime, date
from typing import List, Optional
from models.itens.item_almoxarifado import ItemAlmoxarifado

class Almoxarifado:
    def __init__(self):
        self.itens: List[ItemAlmoxarifado] = []

    def adicionar_item(self, item: ItemAlmoxarifado):
        self.itens.append(item)

    def buscar_por_id(self, id_item: int) -> Optional[ItemAlmoxarifado]:
        return next((i for i in self.itens if i.id_item == id_item), None)

    def buscar_por_nome(self, nome: str) -> Optional[ItemAlmoxarifado]:
        return next((i for i in self.itens if i.nome == nome), None)

    def listar_itens(self) -> List[ItemAlmoxarifado]:
        return self.itens
    
    def verificar_disponibilidade_projetada_para_data(self, id_item: int, data: date, quantidade: float = 0.0) -> float:
        """
        Retorna a quantidade projetada para o item em uma data futura.
        Se `quantidade` for informado, retorna True/False para disponibilidade.
        Caso contrário, retorna o valor do estoque projetado.
        """
        item = self.buscar_por_id(id_item)
        if not item:
            return 0.0 if not quantidade else False

        estoque = item.estoque_projetado_em(data)
        if quantidade > 0:
            return estoque >= quantidade
        return estoque