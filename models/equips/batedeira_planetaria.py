from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from datetime import datetime
from typing import List, Tuple
from utils.logger_factory import setup_logger

# 🪐 Logger específico para a Batedeira Planetária
logger = setup_logger('BatedeiraPlanetaria')


class BatedeiraPlanetaria(Equipamento):
    """
    🪐 Representa uma Batedeira Planetária.
    ✅ Controle de velocidade mínima e máxima.
    ✅ Ocupação exclusiva no tempo.
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

        # 📦 Ocupações: (ordem_id, atividade_id, quantidade, inicio, fim, velocidade)
        self.ocupacoes: List[Tuple[int, int, float, datetime, datetime, int]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, ocup_inicio, ocup_fim, _ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def validar_velocidade(self, velocidade: int) -> bool:
        return self.velocidade_min <= velocidade <= self.velocidade_max

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        ordem_id: int,
        quantidade_gramas: float,
        inicio: datetime,
        fim: datetime,
        atividade_id: int,
        velocidade: int
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

        if velocidade is None:
            logger.error(f"❌ Velocidade não fornecida para ocupação da batedeira {self.nome}.")
            return False

        if not self.validar_velocidade(velocidade):
            logger.error(
                f"❌ Velocidade {velocidade} fora da faixa da batedeira {self.nome} "
                f"({self.velocidade_min} - {self.velocidade_max})."
            )
            return False

        self.ocupacoes.append((ordem_id, atividade_id, quantidade_gramas, inicio, fim, velocidade))
        logger.info(
            f"🪐 {self.nome} | Ocupação registrada: {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Atividade {atividade_id}, Ordem {ordem_id}) com velocidade {velocidade}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, vel)
            for (oid, aid, qtd, ini, fim, vel) in self.ocupacoes
            if fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}."
            )


    def liberar_por_atividade(self, atividade_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, vel)
            for (oid, aid, qtd, ini, fim, vel) in self.ocupacoes
            if aid != atividade_id
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🟩 {self.nome} | Liberadas {liberadas} ocupações da atividade {atividade_id}.")

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, vel)
            for (oid, aid, qtd, ini, fim, vel) in self.ocupacoes
            if oid != ordem_id
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🟩 {self.nome} | Liberadas {liberadas} ocupações da ordem {ordem_id}.")

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for oid, aid, qtd, ini, fim, vel in self.ocupacoes:
            logger.info(
                f"🌀 Atividade ID {aid} | Ordem {oid} | Quantidade: {qtd}g | "
                f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Velocidade: {vel}"
            )
