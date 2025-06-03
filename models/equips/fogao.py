from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from typing import List, Tuple
from typing import Optional
from datetime import datetime
from utils.logger_factory import setup_logger

# 🔥 Logger específico para Fogão
logger = setup_logger('Fogao')


class Fogao(Equipamento):
    """
    🔥 Classe que representa um Fogão com controle de ocupação por bocas,
    considerando janelas de tempo e vínculo com IDs de ocupação e atividade.
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
        pressao_chamas_suportadas: List[TipoPressaoChama]
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

        # 📂 Formato: ocupacao_id, atividade_id, quantidade, inicio, fim
        self.bocas_ocupadas: List[Tuple[int, int, int, datetime, datetime]] = []

    def bocas_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        ocupadas = sum(
            1 for _, _, _, ini, f in self.bocas_ocupadas
            if not (fim <= ini or inicio >= f)
        )
        return self.numero_bocas - ocupadas

    def ocupar(
        self,
        ocupacao_id: Optional[int],
        atividade_id: int,
        quantidade_gramas: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        bocas_disponiveis = self.bocas_disponiveis(inicio, fim)

        if bocas_disponiveis == 0:
            logger.warning(
                f"❌ Todas as bocas do fogão {self.nome} estão ocupadas nesse período "
                f"({inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')})."
            )
            return False

        for b in range(bocas_disponiveis, 0, -1):
            quantidade_por_boca = quantidade_gramas / b
            print(f"🔍 Tentando dividir {quantidade_gramas}g em {b} bocas: {quantidade_por_boca}g por boca.")
            if self.capacidade_por_boca_gramas_min <= quantidade_por_boca <= self.capacidade_por_boca_gramas_max:
                if ocupacao_id is None:
                    return True

                quantidade_por_boca = round(quantidade_por_boca)
                for _ in range(b):
                    self.bocas_ocupadas.append(
                        (ocupacao_id, atividade_id, quantidade_por_boca, inicio, fim)
                    )
                    logger.info(
                        f"🔥 Ocupou uma boca do fogão {self.nome} com {quantidade_por_boca}g "
                        f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
                    )

                logger.info(
                    f"✅ Ocupação completa registrada no fogão {self.nome} "
                    f"para atividade {atividade_id} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
                )
                return True

        logger.error(
            f"❌ Não foi possível dividir {quantidade_gramas}g em bocas disponíveis "
            f"respeitando limites ({self.capacidade_por_boca_gramas_min}-{self.capacidade_por_boca_gramas_max}g) "
            f"no fogão {self.nome}."
        )
        return False

    def liberar_bocas_terminadas(self, horario_atual: datetime):
        antes = len(self.bocas_ocupadas)
        self.bocas_ocupadas = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.bocas_ocupadas
            if fim > horario_atual
        ]
        liberadas = antes - len(self.bocas_ocupadas)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} bocas do fogão {self.nome} "
                f"que estavam ocupadas até {horario_atual.strftime('%H:%M')}."
            )

    def liberar_por_atividade(self, atividade_id: int):
        antes = len(self.bocas_ocupadas)
        self.bocas_ocupadas = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.bocas_ocupadas
            if aid != atividade_id
        ]
        depois = len(self.bocas_ocupadas)
        logger.info(
            f"🟩 Liberou {antes - depois} bocas associadas à atividade {atividade_id} no fogão {self.nome}."
        )

    def liberar_todas_bocas(self):
        total = len(self.bocas_ocupadas)
        self.bocas_ocupadas.clear()
        logger.info(
            f"🟩 Liberou todas as {total} bocas do fogão {self.nome}."
        )

    #==========================================================
    # 🗓️ Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"==============================================")
        if not self.bocas_ocupadas:
            logger.info("🔹 Nenhuma ocupação.")
            return
        for (oid, aid, qtd, inicio, fim) in self.bocas_ocupadas:
            logger.info(
                f"🔸 Ocupação {oid}: Atividade {aid} | {qtd}g | "
                f"Início: {inicio.strftime('%H:%M')} | "
                f"Fim: {fim.strftime('%H:%M')}"
            )



    def __str__(self):
        return (
            f"\n🔥 Fogão: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativo' if self.status_ativo else 'Inativo'}"
            f"\nBocas: {self.numero_bocas} | Ocupadas agora: {len(self.bocas_ocupadas)}"
            f"\nCapacidade por boca: {self.capacidade_por_boca_gramas_min}g até {self.capacidade_por_boca_gramas_max}g"
            f"\nChamas suportadas: {[chama.name for chama in self.chamas_suportadas]}"
            f"\nPressão das chamas: {[pressao.name for pressao in self.pressao_chamas_suportadas]}"
        )
