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
    ⚖️ Classe que representa uma Balança Digital com controle por peso.
    ✔️ Permite múltiplas alocações simultâneas, com registro de tempo.
    """
        
    # ============================================
    # 🔧 Inicialização
    # ============================================

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

        # 📦 Ocupações: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, float, datetime, datetime]] = []

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
    def ocupar(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.aceita_quantidade(quantidade):
            logger.error(
                f"❌ Peso inválido na balança {self.nome}: {quantidade}g "
                f"(Limites: {self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        self.ocupacoes.append((ordem_id, pedido_id, atividade_id, quantidade, inicio, fim))
        logger.info(
            f"⚖️ Ocupação registrada na balança {self.nome}: "
            f"Ordem {ordem_id}, pedido {pedido_id}, atividade {atividade_id}, quantidade {quantidade}g, "
            f"início {inicio.strftime('%H:%M')}, fim {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade_id: int):
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacoes
            if not (oid == ordem_id and pid == pedido_id and aid == atividade_id)
        ]
    
        logger.info(
            f"🔓 Liberadas ocupações da balança {self.nome} "
            f"relacionadas à atividade {atividade_id} da ordem {ordem_id} e pedido {pedido_id}."
        )

    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacoes
            if (oid != ordem_id and pid != pedido_id)
        ]

        logger.info(
            f"🔓 Liberadas ocupações da balança {self.nome} "
            f"relacionadas à ordem {ordem_id} e pedido {pedido_id}."
        )

    def liberar_por_ordem(self, ordem_id: int):
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacoes
            if (oid != ordem_id)
        ]

        logger.info(
            f"🔓 Liberadas ocupações da balança {self.nome} "
            f"relacionadas à ordem {ordem_id}."
        )

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Liberou todas as {total} ocupações da balança {self.nome}.")

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
        for i, (oid, pid, aid, qtd, ini, fim) in enumerate(self.ocupacoes, start=1):
            logger.info(
                f"⚖️ Ordem: {oid} | Pedido: {pid} | Atividade: {aid} | Quantidade: {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}"
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
