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
    🪵 Classe que representa uma Bancada com controle de ocupação por frações,
    considerando janelas de tempo. A ocupação é EXCLUSIVA por fração no tempo,
    e rastreada por atividade e ordem.
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
        # Ocupações: (ordem_id, atividade_id, quantidade, inicio, fim)
        self.fracoes_ocupadas: List[Tuple[int, int, int, datetime, datetime]] = []

    # ==========================================================
    # 🔍 Verificar disponibilidade
    # ==========================================================
    def fracoes_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        ocupadas = sum(
            qtd for (oid, aid, qtd, ini, f) in self.fracoes_ocupadas
            if not (fim <= ini or inicio >= f)
        )
        return self.numero_fracoes - ocupadas

    # ==========================================================
    # 🪵 Ocupação
    # ==========================================================
    def ocupar(
        self,
        ordem_id: int,
        atividade_id: int,
        quantidade_fracoes: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if self.fracoes_disponiveis(inicio, fim) < quantidade_fracoes:
            logger.warning(
                f"❌ Frações insuficientes na bancada {self.nome} "
                f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.fracoes_ocupadas.append(
            (ordem_id, atividade_id, quantidade_fracoes, inicio, fim)
        )

        logger.info(
            f"🪵 Ocupou {quantidade_fracoes} frações da bancada {self.nome} | "
            f"Ordem {ordem_id} | Atividade {atividade_id} | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.fracoes_ocupadas
            if not (aid == atividade_id and oid == ordem_id)
        ]
        liberadas = antes - len(self.fracoes_ocupadas)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} registros da bancada {self.nome} "
                f"relacionados à atividade {atividade_id} da ordem {ordem_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma fração da bancada {self.nome} estava associada à atividade {atividade_id} da ordem {ordem_id}."
            )

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.fracoes_ocupadas
            if oid != ordem_id
        ]
        liberadas = antes - len(self.fracoes_ocupadas)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} relacionadas à ordem {ordem_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma fração da bancada {self.nome} estava associada à ordem {ordem_id}."
            )

    def liberar_fracoes_terminadas(self, horario_atual: datetime):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.fracoes_ocupadas
            if fim > horario_atual
        ]
        liberadas = antes - len(self.fracoes_ocupadas)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )

    def liberar_todas_fracoes(self):
        total = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas.clear()
        logger.info(f"🟩 Liberou todas as {total} frações da bancada {self.nome}.")

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (oid, aid, qtd, ini, f)
            for (oid, aid, qtd, ini, f) in self.fracoes_ocupadas
            if not (ini >= inicio and f <= fim)
        ]
        liberadas = antes - len(self.fracoes_ocupadas)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} frações da bancada {self.nome} no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma fração da bancada {self.nome} estava ocupada no intervalo de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")
        if not self.fracoes_ocupadas:
            logger.info("🔹 Nenhuma ocupação.")
            return
        for i, (oid, aid, qtd, inicio, fim) in enumerate(self.fracoes_ocupadas, start=1):
            logger.info(
                f"🪵 Ordem: {oid} | Atividade: {aid} | Frações: {qtd} | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
            )

    # ==========================================================
    # 🔍 Status
    # ==========================================================
    def __str__(self):
        return (
            f"\n🪵 Bancada: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativa' if self.status_ativo else 'Inativa'}"
            f"\nFrações totais: {self.numero_fracoes} | Ocupações registradas: {len(self.fracoes_ocupadas)}"
        )
