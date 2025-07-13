from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

# 🗄️ Logger específico para o ArmárrioFermentador
logger = setup_logger('ArmarioFermentador')


class ArmarioFermentador(Equipamento):
    """
    🗄️ Representa um ArmárioFermentador para fermentação.
    ✔️ Armazenamento exclusivo por níveis de tela.
    ✔️ Sem controle de temperatura.
    ✔️ Sem sobreposição de ocupação além do limite de níveis.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        nivel_tela_min: int,
        nivel_tela_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_max = nivel_tela_max

        # 📦 Ocupações: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim)
        self.ocupacao_niveis: List[Tuple[int, int, int, float, datetime, datetime]] = []

    # ==========================================================
    # ✅ Consulta de disponibilidade
    # ==========================================================
    def niveis_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        ocupadas = sum(
            qtd for (oid, pid, aid, qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return self.nivel_tela_max - ocupadas

    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        return self.niveis_disponiveis(inicio, fim) >= quantidade

    # ==========================================================
    # 🔐 Ocupação
    # ==========================================================
    def ocupar_niveis(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            logger.warning(
                f"❌ Níveis insuficientes no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.ocupacao_niveis.append((ordem_id, pedido_id,atividade_id, quantidade, inicio, fim))

        logger.info(
            f"📥 Ocupação registrada no {self.nome} | "
            f"Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id} | {quantidade} níveis | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade_id: int):
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if not (oid == ordem_id and pid == pedido_id and aid == atividade_id)
        ]
        liberadas = antes - len(self.ocupacao_niveis)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do {self.nome} "
                f"para Atividade {atividade_id}, Pedido {pedido_id}, Ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Atividade {atividade_id}, Pedido {pedido_id}, Ordem {ordem_id}."
            )


    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if not (oid == ordem_id and pid == pedido_id)
        ]
        liberadas = antes - len(self.ocupacao_niveis)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do {self.nome} "
                f"para Pedido {pedido_id}, Ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Pedido {pedido_id}, Ordem {ordem_id}."
            )


    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if not (oid == ordem_id)
        ]
        liberadas = antes - len(self.ocupacao_niveis)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do {self.nome} "
                f"para Ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Ordem {ordem_id}."
            )


    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (oid, pid, aid, qtd, ini, fim)
            for (oid, pid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if not (fim <= horario_atual)
        ]
        liberadas = antes - len(self.ocupacao_niveis)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar no {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return liberadas


    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacao_niveis)
        self.ocupacao_niveis.clear()
        logger.info(f"🔓 Todas as {total} ocupações do {self.nome} foram removidas.")


    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (oid, pid, aid, qtd, ini, f)
            for (oid, pid, aid, qtd, ini, f) in self.ocupacao_niveis
            if not (ini < fim and f > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacao_niveis)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )


    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")

        if not self.ocupacao_niveis:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (oid, pid, aid, qtd, ini, fim) in self.ocupacao_niveis:
            logger.info(
                f"🗂️ Ordem {oid} | Pedido {pid} |Atividade {aid} | {qtd} níveis | "
                f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
            )
