from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger


# 🪵 Logger específico para Bancada
logger = setup_logger('Bancada')


class Bancada(Equipamento):
    """
    Classe que representa uma Bancada com controle de ocupação por frações,
    considerando janelas de tempo. A ocupação é EXCLUSIVA por fração no tempo,
    e rastreada por atividade.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        numero_fracoes: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.BANCADAS,
            status_ativo=True
        )

        self.numero_fracoes = numero_fracoes

        # (quantidade=1, inicio, fim, atividade_id)
        self.fracoes_ocupadas: List[Tuple[int, datetime, datetime, int]] = []

    # ==========================================================
    # 🔍 Verificar disponibilidade
    # ==========================================================
    def fracoes_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        ocupadas = sum(
            1 for _, ini, f, _ in self.fracoes_ocupadas
            if not (fim <= ini or inicio >= f)
        )
        return self.numero_fracoes - ocupadas

    # ==========================================================
    # 🪵 Ocupação
    # ==========================================================
    def ocupar(
        self,
        inicio: datetime,
        fim: datetime,
        quantidade_fracoes: int,
        atividade_id: int
    ) -> bool:
        quantidade_restante = quantidade_fracoes

        while quantidade_restante > 0:
            if self.fracoes_disponiveis(inicio, fim) <= 0:
                logger.warning(
                    f"❌ Todas as frações da bancada {self.nome} estão ocupadas nesse período "
                    f"({inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')})."
                )
                return False

            self.fracoes_ocupadas.append(
                (1, inicio, fim, atividade_id)
            )
            quantidade_restante -= 1

            logger.info(
                f"🪵 Ocupou uma fração da bancada {self.nome} "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
                f"para atividade {atividade_id}."
            )

        logger.info(
            f"✅ Ocupação completa registrada na bancada {self.nome} "
            f"para atividade {atividade_id} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (qtd, ini, fim, act_id) for (qtd, ini, fim, act_id) in self.fracoes_ocupadas
            if act_id != atividade_id
        ]
        liberadas = antes - len(self.fracoes_ocupadas)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} "
                f"relacionadas à atividade {atividade_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma fração da bancada {self.nome} estava associada "
                f"à atividade {atividade_id}."
            )

    def liberar_fracoes_terminadas(self, horario_atual: datetime):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (qtd, ini, fim, act_id) for (qtd, ini, fim, act_id) in self.fracoes_ocupadas
            if fim > horario_atual
        ]
        liberadas = antes - len(self.fracoes_ocupadas)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} "
                f"que estavam ocupadas até {horario_atual.strftime('%H:%M')}."
            )

    def liberar_todas_fracoes(self):
        total = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas.clear()
        logger.info(
            f"🟩 Liberou todas as {total} frações da bancada {self.nome}."
        )

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        """
        🧹 Libera todas as frações ocupadas dentro de um intervalo específico.
        """
        antes = len(self.fracoes_ocupadas)

        self.fracoes_ocupadas = [
            (qtd, ini, f, act_id) for (qtd, ini, f, act_id) in self.fracoes_ocupadas
            if not (ini >= inicio and f <= fim)
        ]

        liberadas = antes - len(self.fracoes_ocupadas)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} "
                f"no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma fração da bancada {self.nome} estava ocupada "
                f"no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 🗓️ Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"\n============================")
        logger.info(f"📅 Agenda da Bancada {self.nome}")
        logger.info(f"============================")
        if not self.fracoes_ocupadas:
            logger.info("🔹 Nenhuma ocupação.")
            return
        for i, (_, inicio, fim, act_id) in enumerate(self.fracoes_ocupadas, start=1):
            logger.info(
                f"🔸 Ocupação {i}: Fração 1 | "
                f"Início: {inicio.strftime('%H:%M')} | "
                f"Fim: {fim.strftime('%H:%M')} | "
                f"Atividade: {act_id}"
            )

    # ==========================================================
    # 🔍 Status
    # ==========================================================
    def __str__(self):
        return (
            f"\n🪵 Bancada: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativa' if self.status_ativo else 'Inativa'}"
            f"\nFrações totais: {self.numero_fracoes} | Ocupadas agora: {len(self.fracoes_ocupadas)}"
        )
