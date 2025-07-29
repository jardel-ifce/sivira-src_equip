# =============== CLASSE MODELADORA DE PÃES ===============

from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ModeladoraDePaes')

class ModeladoraDePaes(Equipamento):
    """
    🍞 Classe que representa uma Modeladora de Pães.
    ✔️ Sempre disponível para alocação (sem ocupação exclusiva).
    ✔️ Registro simples de atividades para controle e histórico.
    ✔️ Capacidade de produção por minuto para referência.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_min_unidades_por_minuto: int,
        capacidade_max_unidades_por_minuto: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.MODELADORAS,
            status_ativo=True
        )

        self.capacidade_min_unidades_por_minuto = capacidade_min_unidades_por_minuto
        self.capacidade_max_unidades_por_minuto = capacidade_max_unidades_por_minuto

        # Histórico de ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, int, datetime, datetime]] = []

    # ==========================================================
    # 🔒 Ocupação (Sempre Aceita)
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        **kwargs
    ) -> bool:
        """
        Registra uma ocupação na modeladora.
        Sempre retorna True pois modeladoras estão sempre disponíveis.
        """
        self.ocupacoes.append((id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim))
        logger.info(
            f"✅ {self.nome} | Atividade {id_atividade} (Item {id_item}) registrada | "
            f"Quantidade {quantidade} unidades | "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Remove registros específicos por atividade."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Removidos {liberadas} registros da atividade {id_atividade} "
                f"(Ordem {id_ordem}, Pedido {id_pedido})."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Remove registros específicos por pedido."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Removidos {liberadas} registros do pedido {id_pedido} "
                f"(Ordem {id_ordem})."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Remove registros específicos por ordem."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} | Removidos {liberadas} registros da ordem {id_ordem}.")

    def liberar_por_item(self, id_item: int):
        """Remove registros específicos por item."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] != id_item
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} | Removidos {liberadas} registros do item {id_item}.")

    def liberar_todas_ocupacoes(self):
        """Limpa todos os registros da modeladora."""
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 {self.nome} removeu todos os {total} registros.")

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Remove registros que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[6] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Removidos {liberadas} registros finalizados até {horario_atual.strftime('%H:%M')}."
            )
        return liberadas

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Remove registros que se sobrepõem ao intervalo especificado."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[5] < fim and ocupacao[6] > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Removidos {liberadas} registros no intervalo de "
                f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda e Consultas
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra histórico detalhado da modeladora."""
        logger.info("==============================================")
        logger.info(f"📅 Histórico da {self.nome}")
        logger.info(f"🔧 Capacidade: {self.capacidade_min_unidades_por_minuto}-{self.capacidade_max_unidades_por_minuto} unidades/min")
        logger.info("==============================================")
        
        if not self.ocupacoes:
            logger.info("🔹 Nenhum registro encontrado.")
            return
        
        # Ordenar registros por horário de início
        ocupacoes_ordenadas = sorted(self.ocupacoes, key=lambda x: x[5])  # ordenar por inicio
        
        for ocupacao in ocupacoes_ordenadas:
            logger.info(
                f"🍞 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                f"Quantidade: {ocupacao[4]} unidades | "
                f"{ocupacao[5].strftime('%H:%M')} → {ocupacao[6].strftime('%H:%M')}"
            )

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, datetime, datetime]]:
        """Retorna registros que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    def obter_ocupacoes_item(self, id_item: int) -> List[Tuple[int, int, int, int, int, datetime, datetime]]:
        """Retorna todos os registros de um item específico."""
        return [ocupacao for ocupacao in self.ocupacoes if ocupacao[3] == id_item]

