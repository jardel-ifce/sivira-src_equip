from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger

# 🔳 Logger específico para o ArmárrioFermentador
logger = setup_logger('ArmarioFermentador')


class ArmarioFermentador(Equipamento):
    """
    🔳 Representa um ArmárrioFermentador para fermentação.
    ✔️ Armazenamento exclusivo por níveis de tela.
    ✔️ Sem controle de temperatura.
    ✔️ Sem sobreposição de ocupação além do limite de níveis.
    """

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

        # 📦 Ocupações: (atividade_id, quantidade, inicio, fim)
        self.ocupacao_niveis: List[Tuple[int, int, datetime, datetime]] = []

    # ==========================================================
    # 🔍 Consulta de disponibilidade
    # ==========================================================
    def niveis_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """
        🔍 Calcula a quantidade de níveis disponíveis entre o intervalo informado.
        """
        ocupadas = sum(
            qtd for (_, qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return self.nivel_tela_max - ocupadas

    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        """
        ✅ Verifica se há espaço suficiente para armazenar a quantidade desejada de níveis.
        """
        return self.niveis_disponiveis(inicio, fim) >= quantidade

    # ==========================================================
    # 🔐 Ocupação
    # ==========================================================
    def ocupar_niveis(
        self,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        🔐 Realiza a ocupação dos níveis de tela no intervalo solicitado.
        """
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            logger.warning(
                f"❌ Níveis insuficientes no 🔳 {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.ocupacao_niveis.append((atividade_id, quantidade, inicio, fim))

        logger.info(
            f"📥 Ocupação registrada no 🔳 {self.nome} | "
            f"Atividade {atividade_id} | {quantidade} níveis | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        """
        🧹 Libera todas as ocupações associadas à atividade.
        """
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (aid, qtd, ini, fim)
            for (aid, qtd, ini, fim) in self.ocupacao_niveis
            if aid != atividade_id
        ]
        logger.info(
            f"🧹 Liberadas {antes - len(self.ocupacao_niveis)} ocupações do 🔳 {self.nome} para atividade {atividade_id}."
        )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """
        🔄 Libera ocupações finalizadas até o horário atual.
        """
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (aid, qtd, ini, fim)
            for (aid, qtd, ini, fim) in self.ocupacao_niveis
            if fim > horario_atual
        ]
        logger.info(
            f"🕒 {antes - len(self.ocupacao_niveis)} ocupações finalizadas liberadas no 🔳 {self.nome} até {horario_atual.strftime('%H:%M')}."
        )

    def liberar_todas_ocupacoes(self):
        """
        🧼 Remove todas as ocupações do armário.
        """
        total = len(self.ocupacao_niveis)
        self.ocupacao_niveis.clear()
        logger.info(f"🧼 Todas as {total} ocupações do 🔳 {self.nome} foram removidas.")

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        """
        ⏱️ Libera todas as ocupações dentro do intervalo solicitado.
        """
        antes = len(self.ocupacao_niveis)
        self.ocupacao_niveis = [
            (aid, qtd, ini, f)
            for (aid, qtd, ini, f) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]
        logger.info(
            f"🧹 Liberadas {antes - len(self.ocupacao_niveis)} ocupações do 🔳 {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        📅 Exibe a agenda atual do armário.
        """
        logger.info("==============================================")
        logger.info(f"📅 Agenda do 🔳 {self.nome}")
        logger.info("==============================================")

        if not self.ocupacao_niveis:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (aid, qtd, ini, fim) in self.ocupacao_niveis:
            logger.info(
                f"🗂️ Atividade {aid} | {qtd} níveis | "
                f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
            )

    # ==========================================================
    # 🔍 Status
    # ==========================================================
    def __str__(self):
        ocupadas = sum(
            qtd for (_, qtd, _, _) in self.ocupacao_niveis
        )
        return (
            f"\n🔳 ArmárrioFermentador: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativo' if self.status_ativo else 'Inativo'}"
            f"\nNíveis Ocupados: {ocupadas}/{self.nivel_tela_max}"
        )
