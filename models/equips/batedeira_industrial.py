from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from datetime import datetime
from typing import List, Tuple
from utils.logger_factory import setup_logger


# 🏭 Logger específico para a Batedeira Industrial
logger = setup_logger('BatedeiraIndustrial')


class BatedeiraIndustrial(Equipamento):
    """
    🏭 Classe que representa uma Batedeira Industrial.
    ✅ Controle de velocidade mínima e máxima.
    ✅ Ocupação com exclusividade no tempo.
    ✅ Capacidade de mistura validada por peso.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: float,
        capacidade_gramas_max: float,
        velocidade_min: int,
        velocidade_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            tipo_equipamento=TipoEquipamento.BATEDEIRAS,
            numero_operadores=numero_operadores,
            status_ativo=True
        )
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidade_min = velocidade_min
        self.velocidade_max = velocidade_max
        self.velocidade_atual = 0

        # 📦 Ocupações: (ocupacao_id, atividade_id, quantidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, float, datetime, datetime]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, ocup_inicio, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def selecionar_velocidade(self, velocidade: int) -> bool:
        if self.velocidade_min <= velocidade <= self.velocidade_max:
            self.velocidade_atual = velocidade
            logger.info(f"⚙️ {self.nome} | Velocidade ajustada para {velocidade}.")
            return True
        logger.error(
            f"❌ Velocidade {velocidade} fora da faixa da batedeira {self.nome} "
            f"({self.velocidade_min} - {self.velocidade_max})."
        )
        return False

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        ocupacao_id: int,
        quantidade_gramas: float,
        inicio: datetime,
        fim: datetime,
        atividade_id: int
    ) -> bool:
        if not self.validar_capacidade(quantidade_gramas):
            logger.error(
                f"❌ {self.nome} | {quantidade_gramas}g fora dos limites "
                f"({self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        if not self.esta_disponivel(inicio, fim):
            logger.warning(
                f"❌ {self.nome} | Ocupada entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.ocupacoes.append((ocupacao_id, atividade_id, quantidade_gramas, inicio, fim))
        logger.info(
            f"🏭 {self.nome} | Ocupação registrada: {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Atividade {atividade_id}, Ocupação ID: {ocupacao_id}) "
            f"com velocidade {self.velocidade_atual}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.ocupacoes
            if fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}."
            )

    def liberar(self, inicio: datetime, fim: datetime, atividade_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, aid, qtd, ini, f)
            for (oid, aid, qtd, ini, f) in self.ocupacoes
            if not (aid == atividade_id and ini == inicio and f == fim)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(
                f"🟩 {self.nome} | Ocupação da atividade {atividade_id} removida "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da Batedeira {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return
        for oid, aid, qtd, ini, fim in self.ocupacoes:
            logger.info(
                f"🔸 Ocupação {oid}: {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')} | "
                f"Atividade ID: {aid} | Velocidade: {self.velocidade_atual}"
            )
