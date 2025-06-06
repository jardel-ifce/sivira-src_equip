from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from typing import List, Tuple
from utils.logger_factory import setup_logger

# ⚖️ Logger específico para a balança
logger = setup_logger('BalancaDigital')


class BalancaDigital(Equipamento):
    """
    ⚖️ Classe que representa uma Balança Digital com controle por peso.
    ✔️ Sem restrição de tempo, permite múltiplas alocações simultâneas.
    ✔️ Cada ocupação é registrada apenas com:
       - atividade_id
       - quantidade (em gramas)
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
        self.ocupacoes: List[Tuple[int, float]] = []  # (atividade_id, quantidade)

    # ==========================================================
    # ✅ Validação de quantidade
    # ==========================================================
    def aceita_quantidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def validar_peso(self, quantidade_gramas: float) -> bool:
        return self.aceita_quantidade(quantidade_gramas)

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(self, atividade_id: int, quantidade: float) -> bool:
        if not self.aceita_quantidade(quantidade):
            logger.error(
                f"❌ Peso inválido na balança {self.nome}: {quantidade}g "
                f"(Limites: {self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        self.ocupacoes.append((atividade_id, quantidade))
        logger.info(
            f"⚖️ Ocupação registrada na balança {self.nome}: "
            f"atividade {atividade_id}, quantidade {quantidade}g."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (aid, qtd) for (aid, qtd) in self.ocupacoes
            if aid != atividade_id
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} ocupações da balança {self.nome} "
                f"relacionadas à atividade {atividade_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da balança {self.nome} estava associada à atividade {atividade_id}."
            )

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🟩 Liberou todas as {total} ocupações da balança {self.nome}.")

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da Balança {self.nome}")
        logger.info("==============================================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return
        for i, (aid, qtd) in enumerate(self.ocupacoes, start=1):
            logger.info(f"⚖️ Atividade: {aid} | Quantidade: {qtd}g")

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
