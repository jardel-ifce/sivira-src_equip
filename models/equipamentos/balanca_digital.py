from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

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

        # 📦 Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, float, datetime, datetime]] = []

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
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.aceita_quantidade(quantidade):
            logger.error(
                f"❌ Peso inválido na {self.nome}: {quantidade}g "
                f"(Limites: {self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        self.ocupacoes.append((id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim))
        logger.info(
            f"⚖️ Ocupação registrada na {self.nome}: "
            f"Ordem {id_ordem}, pedido {id_pedido}, atividade {id_atividade}, item {id_item}, quantidade {quantidade}g, "
            f"início {inicio.strftime('%Y-%m-%d %H:%M')}, fim {fim.strftime('%Y-%m-%d %H:%M')}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        self.ocupacoes = [
            ocupacao
            for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
    
        logger.info(
            f"🔓 Liberadas ocupações da {self.nome} "
            f"relacionadas à atividade {id_atividade} da ordem {id_ordem} e pedido {id_pedido}."
        )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        self.ocupacoes = [
            ocupacao
            for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]

        logger.info(
            f"🔓 Liberadas ocupações da {self.nome} "
            f"relacionadas à ordem {id_ordem} e pedido {id_pedido}."
        )

    def liberar_por_ordem(self, id_ordem: int):
        self.ocupacoes = [
            ocupacao
            for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]

        logger.info(
            f"🔓 Liberadas ocupações da {self.nome} "
            f"relacionadas à ordem {id_ordem}."
        )
    
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao
            for ocupacao in self.ocupacoes
            if ocupacao[6] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        logger.info(
            f"🔓 Liberadas {liberadas} ocupações finalizadas da {self.nome}."
        )
        return liberadas

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Liberou todas as {total} ocupações da {self.nome}.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao
            for ocupacao in self.ocupacoes
            if not (ocupacao[5] < fim and ocupacao[6] > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacoes)
        logger.info(
            f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
            f"no intervalo de {inicio.strftime('%Y-%m-%d %H:%M')} a {fim.strftime('%Y-%m-%d %H:%M')}."
        )

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
        for i, ocupacao in enumerate(self.ocupacoes, start=1):
            logger.info(
                f"⚖️ Ordem: {ocupacao[0]} | Pedido: {ocupacao[1]} | Atividade: {ocupacao[2]} | Item: {ocupacao[3]} | "
                f"Quantidade: {ocupacao[4]}g | Início: {ocupacao[5].strftime('%Y-%m-%d %H:%M')} | Fim: {ocupacao[6].strftime('%Y-%m-%d %H:%M')}"
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