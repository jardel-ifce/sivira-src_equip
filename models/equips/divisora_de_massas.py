from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from typing import List, Dict
from datetime import datetime


class DivisoraDeMassas(Equipamento):
    """
    Classe que representa uma divisora de massas com ou sem boleadora.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        boleadora: bool,
        capacidade_divisao_unidades_por_segundo: int,
        capacidade_boleamento_unidades_por_segundo: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.DIVISORAS_BOLEADORAS,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.boleadora = boleadora
        self.capacidade_divisao_unidades_por_segundo = capacidade_divisao_unidades_por_segundo
        self.capacidade_boleamento_unidades_por_segundo = capacidade_boleamento_unidades_por_segundo
        self.ocupacao: List[Dict] = []

    def validar_capacidade(self, gramas: int) -> bool:
        if gramas < self.capacidade_gramas_min:
            print(f"❌ Quantidade {gramas}g abaixo da capacidade mínima ({self.capacidade_gramas_min}g) da divisora {self.nome}.")
            return False
        if gramas > self.capacidade_gramas_max:
            print(f"❌ Quantidade {gramas}g excede a capacidade máxima ({self.capacidade_gramas_max}g) da divisora {self.nome}.")
            return False
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for ocup in self.ocupacao:
            if not (fim <= ocup["inicio"] or inicio >= ocup["fim"]):
                return False
        return True

    def ocupar(
        self,
        ordem_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        self.ocupacao.append({
            "ordem_id": ordem_id,
            "atividade_id": atividade_id,
            "quantidade": quantidade,
            "inicio": inicio,
            "fim": fim,
            "boleadora": self.boleadora
        })
        print(
            f"🔵 {self.nome} | Ordem {ordem_id} | Atividade {atividade_id} | {quantidade}g | "
            f"Boleadora: {'Sim' if self.boleadora else 'Não'} | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
        )
        return True

    def liberar_ocupacoes_anteriores_a(self, momento: datetime):
        ocupacoes_ativas = [o for o in self.ocupacao if o["fim"] > momento]
        liberadas = len(self.ocupacao) - len(ocupacoes_ativas)
        self.ocupacao = ocupacoes_ativas
        if liberadas > 0:
            print(f"🟩 {self.nome} | Liberou {liberadas} ocupações anteriores a {momento.strftime('%H:%M')}.")

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacao)
        self.ocupacao = [o for o in self.ocupacao if o["ordem_id"] != ordem_id]
        liberadas = antes - len(self.ocupacao)
        if liberadas > 0:
            print(f"🧼 {self.nome} | Liberou {liberadas} ocupações da ordem {ordem_id}.")

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        antes = len(self.ocupacao)
        self.ocupacao = [
            o for o in self.ocupacao
            if not (o["atividade_id"] == atividade_id and o["ordem_id"] == ordem_id)
        ]
        liberadas = antes - len(self.ocupacao)
        if liberadas > 0:
            print(f"🧼 {self.nome} | Liberou ocupações da atividade {atividade_id} da ordem {ordem_id}.")

    def mostrar_agenda(self):
        print("==============================================")
        print(f"📅 Agenda da Divisora {self.nome}")
        print("==============================================")
        if not self.ocupacao:
            print("🔸 Nenhuma ocupação registrada.")
            return

        ocupacoes_ordenadas = sorted(self.ocupacao, key=lambda o: (o["inicio"], o["atividade_id"]))
        for o in ocupacoes_ordenadas:
            print(
                f"🧾 Ordem {o['ordem_id']} | Atividade {o['atividade_id']} | {o['quantidade']}g | "
                f"{o['inicio'].strftime('%H:%M')} → {o['fim'].strftime('%H:%M')} | "
                f"Boleadora: {'Sim' if o['boleadora'] else 'Não'}"
            )

    def __str__(self):
        return (
            super().__str__() +
            f"\n🧠 Capacidade por lote: {self.capacidade_gramas_min}g até {self.capacidade_gramas_max}g"
            f"\n⚙️ Velocidade de divisão: {self.capacidade_divisao_unidades_por_segundo} unidades/segundo"
            f"\n⚙️ Velocidade de boleamento: {self.capacidade_boleamento_unidades_por_segundo} unidades/segundo"
            f"\n🔗 Possui boleadora: {'Sim' if self.boleadora else 'Não'}"
            f"\n🗂️ Ocupações registradas: {len(self.ocupacao)}"
        )
