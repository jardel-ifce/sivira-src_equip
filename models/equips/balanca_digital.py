from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger


# ⚖️ Logger específico para a balança
logger = setup_logger('BalancaDigital')


class BalancaDigital(Equipamento):
    """
    ⚖️ Classe que representa uma Balança Digital com controle por peso e janelas de tempo.
    ✔️ Ocupação exclusiva no tempo, rastreada por atividade.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas_min: float,
        capacidade_gramas_max: float
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=1,
            tipo_equipamento=TipoEquipamento.BALANCAS,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max

        # 📦 Ocupações: (quantidade_gramas, inicio, fim, atividade_id)
        self.ocupacoes: List[Tuple[float, datetime, datetime, int]] = []

    # ==========================================================
    # 🔍 Verificar disponibilidade
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        ocupada = any(
            not (fim <= ini or inicio >= f)
            for _, ini, f, _ in self.ocupacoes
        )
        return not ocupada

    # ==========================================================
    # ⚖️ Validação de peso
    # ==========================================================
    def validar_peso(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        inicio: datetime,
        fim: datetime,
        quantidade_gramas: float,
        atividade_id: int
    ) -> bool:
        if not self.validar_peso(quantidade_gramas):
            logger.error(
                f"❌ Peso inválido na balança {self.nome}: {quantidade_gramas}g "
                f"(Limites: {self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        if not self.esta_disponivel(inicio, fim):
            logger.warning(
                f"❌ A balança {self.nome} está ocupada de "
                f"{inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )
            return False

        self.ocupacoes.append(
            (quantidade_gramas, inicio, fim, atividade_id)
        )

        logger.info(
            f"⚖️ Ocupou a balança {self.nome} com {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"para atividade {atividade_id}."
        )

        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (qtd, ini, fim, act_id) for (qtd, ini, fim, act_id) in self.ocupacoes
            if act_id != atividade_id
        ]
        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} ocupações da balança {self.nome} "
                f"relacionadas à atividade {atividade_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da balança {self.nome} estava associada "
                f"à atividade {atividade_id}."
            )

    def liberar_ocupacoes_terminadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (qtd, ini, fim, act_id) for (qtd, ini, fim, act_id) in self.ocupacoes
            if fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} ocupações da balança {self.nome} "
                f"até {horario_atual.strftime('%H:%M')}."
            )

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(
            f"🟩 Liberou todas as {total} ocupações da balança {self.nome}."
        )

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        """
        🧹 Libera ocupações que estão dentro de um intervalo específico.
        """
        antes = len(self.ocupacoes)

        self.ocupacoes = [
            (qtd, ini, f, act_id) for (qtd, ini, f, act_id) in self.ocupacoes
            if not (ini >= inicio and f <= fim)
        ]

        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} ocupações da balança {self.nome} "
                f"no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da balança {self.nome} "
                f"estava no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("\n============================")
        logger.info(f"📅 Agenda da Balança {self.nome}")
        logger.info("============================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação.")
            return
        for i, (qtd, inicio, fim, act_id) in enumerate(self.ocupacoes, start=1):
            logger.info(
                f"🔸 Ocupação {i}: {qtd}g | "
                f"Início: {inicio.strftime('%H:%M')} | "
                f"Fim: {fim.strftime('%H:%M')} | "
                f"Atividade: {act_id}"
            )

    # ==========================================================
    # 🔍 Status
    # ==========================================================
    def __str__(self):
        return (
            f"\n⚖️ Balança: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativa' if self.status_ativo else 'Inativa'}"
            f"\nCapacidade: {self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g"
            f"\nOcupações atuais: {len(self.ocupacoes)}"
        )
