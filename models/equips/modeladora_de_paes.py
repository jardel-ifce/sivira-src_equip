from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from typing import List, Dict
from datetime import datetime


class ModeladoraDePaes(Equipamento):
    """
    Representa uma modeladora de pães com capacidade mínima e máxima de unidades por minuto.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_min_unidades_por_minuto: int,
        capacidade_max_unidades_por_minuto: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.MODELADORAS,
            status_ativo=True
        )

        self.capacidade_min_unidades_por_minuto = capacidade_min_unidades_por_minuto
        self.capacidade_max_unidades_por_minuto = capacidade_max_unidades_por_minuto

        # Ocupações registradas
        self.ocupacoes: List[Dict] = []

    def ocupar(
        self,
        ordem_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        **kwargs
    ) -> bool:
       
        print(
            f"🕑 {self.nome} | Ocupada de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} | "
            f"Atividade {atividade_id} | Ordem {ordem_id} | Quantidade: {quantidade} unidades."
        )
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for ocup in self.ocupacoes:
            if not (fim <= ocup["inicio"] or inicio >= ocup["fim"]):
                return False
        return True

    def liberar_ocupacoes_anteriores_a(self, momento: datetime):
        ocupacoes_ativas = [o for o in self.ocupacoes if o["fim"] > momento]
        liberadas = len(self.ocupacoes) - len(ocupacoes_ativas)
        self.ocupacoes = ocupacoes_ativas
        if liberadas > 0:
            print(f"🟩 {self.nome} | Liberou {liberadas} ocupações anteriores a {momento.strftime('%H:%M')}.")

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [o for o in self.ocupacoes if o.get("ordem_id") != ordem_id]
        depois = len(self.ocupacoes)
        if antes != depois:
            print(f"🧹 {self.nome} | Ocupações da ordem {ordem_id} removidas ({antes - depois} entradas).")

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o.get("ordem_id") == ordem_id and o.get("atividade_id") == atividade_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            print(f"🧹 {self.nome} | Ocupações da atividade {atividade_id} (ordem {ordem_id}) removidas ({antes - depois} entradas).")

    def mostrar_agenda(self):
        print(f"📋 Agenda da Modeladora {self.nome}:")
        if not self.ocupacoes:
            print("  (sem ocupações registradas)")
            return
        for ocup in self.ocupacoes:
            print(
                f"  🔸 Atividade {ocup['atividade_id']} | Ordem {ocup.get('ordem_id')} | "
                f"{ocup['quantidade']} unidades | {ocup['inicio'].strftime('%H:%M')} - {ocup['fim'].strftime('%H:%M')}"
            )

    def __str__(self):
        return (
            super().__str__() +
            f"\n⚙️ Capacidade: {self.capacidade_min_unidades_por_minuto} a {self.capacidade_max_unidades_por_minuto} unidades/minuto"
            f"\n🗂️ Ocupações registradas: {len(self.ocupacoes)}"
        )
