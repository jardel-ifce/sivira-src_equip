from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.pressao_chama import PressaoChama
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger


# 🔥 Logger específico para Fogão
logger = setup_logger('Fogao')

class Fogao(Equipamento):
    """
    Classe que representa um Fogão com controle de ocupação por bocas,
    considerando janelas de tempo.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        chamas_suportadas: List[TipoChama],
        capacidade_por_boca_gramas_min: int,
        capacidade_por_boca_gramas_max: int,
        numero_bocas: int,
        pressao_chamas_suportadas: List[PressaoChama]
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.FOGOES,
            status_ativo=True
        )

        self.chamas_suportadas = chamas_suportadas
        self.capacidade_por_boca_gramas_min = capacidade_por_boca_gramas_min
        self.capacidade_por_boca_gramas_max = capacidade_por_boca_gramas_max
        self.numero_bocas = numero_bocas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas

        self.bocas_ocupadas: List[Tuple[int, datetime, datetime]] = []

    # ==========================================================
    # 🔍 Verificar disponibilidade
    # ==========================================================
    def bocas_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        ocupadas = sum(
            1 for _, ini, f in self.bocas_ocupadas
            if not (fim <= ini or inicio >= f)
        )
        return self.numero_bocas - ocupadas

    # ==========================================================
    # 🔥 Ocupação
    # ==========================================================
    def ocupar(
        self, 
        inicio: datetime, 
        fim: datetime, 
        quantidade_gramas: int, 
        atividade: TipoAtividade
    ) -> bool:
        quantidade_restante = quantidade_gramas

        while quantidade_restante > 0:
            if self.bocas_disponiveis(inicio, fim) <= 0:
                logger.warning(
                    f"❌ Todas as bocas do fogão {self.nome} estão ocupadas nesse período "
                    f"({inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')})."
                )
                return False

            quantidade_para_boca = min(
                quantidade_restante, self.capacidade_por_boca_gramas_max
            )

            if quantidade_para_boca < self.capacidade_por_boca_gramas_min:
                logger.error(
                    f"❌ A quantidade restante ({quantidade_restante}g) é inferior "
                    f"ao mínimo permitido por boca ({self.capacidade_por_boca_gramas_min}g) no fogão {self.nome}."
                )
                return False

            self.bocas_ocupadas.append(
                (quantidade_para_boca, inicio, fim)
            )
            quantidade_restante -= quantidade_para_boca

            logger.info(
                f"🔥 Ocupou uma boca do fogão {self.nome} com {quantidade_para_boca}g "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

        logger.info(
            f"✅ Ocupação completa registrada no fogão {self.nome} "
            f"para atividade {atividade.name} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_bocas_terminadas(self, horario_atual: datetime):
        antes = len(self.bocas_ocupadas)
        self.bocas_ocupadas = [
            (qtd, ini, fim) for (qtd, ini, fim) in self.bocas_ocupadas
            if fim > horario_atual
        ]
        liberadas = antes - len(self.bocas_ocupadas)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} bocas do fogão {self.nome} "
                f"que estavam ocupadas até {horario_atual.strftime('%H:%M')}."
            )

    def liberar_todas_bocas(self):
        total = len(self.bocas_ocupadas)
        self.bocas_ocupadas.clear()
        logger.info(
            f"🟩 Liberou todas as {total} bocas do fogão {self.nome}."
        )

    # ==========================================================
    # 🗓️ Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"\n============================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"============================")
        if not self.bocas_ocupadas:
            logger.info("🔹 Nenhuma ocupação.")
            return
        for i, (qtd, inicio, fim) in enumerate(self.bocas_ocupadas, start=1):
            logger.info(
                f"🔸 Ocupação {i}: {qtd}g | "
                f"Início: {inicio.strftime('%H:%M')} | "
                f"Fim: {fim.strftime('%H:%M')}"
            )

    # ==========================================================
    # 🔍 Status
    # ==========================================================
    def __str__(self):
        return (
            f"\n🔥 Fogão: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativo' if self.status_ativo else 'Inativo'}"
            f"\nBocas: {self.numero_bocas} | Ocupadas agora: {len(self.bocas_ocupadas)}"
            f"\nCapacidade por boca: {self.capacidade_por_boca_gramas_min}g até {self.capacidade_por_boca_gramas_max}g"
            f"\nChamas suportadas: {[chama.name for chama in self.chamas_suportadas]}"
            f"\nPressão das chamas: {[pressao.name for pressao in self.pressao_chamas_suportadas]}"
        )
