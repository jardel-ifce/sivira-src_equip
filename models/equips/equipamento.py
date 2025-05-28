from datetime import datetime
from typing import List, Tuple, Any
from utils.logger_factory import setup_logger

# 🔧 Logger específico para a classe Equipamento
logger = setup_logger('Equipamento')

class Equipamento:
    """
    Superclasse base para qualquer equipamento.
    Responsável pela gestão de identidade, setor, tipo, ocupação temporal e status.
    As subclasses são responsáveis pela gestão física (peso, níveis, caixas, etc.).
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor,
        tipo_equipamento,
        numero_operadores: int = 1,
        status_ativo: bool = True,
    ):
        self.id = id
        self.nome = nome
        self.setor = setor
        self.tipo_equipamento = tipo_equipamento
        self.numero_operadores = numero_operadores
        self.status_ativo = status_ativo

        # Ocupações no formato: (inicio, fim, atividade_id)
        self.ocupacao: List[Tuple[datetime, datetime, int]] = []

    # ============================================
    # 🕑 Ocupação Temporal
    # ============================================
    def registrar_ocupacao(
        self, inicio: datetime, fim: datetime, atividade: Any
    ) -> None:
        """
        Registra a ocupação do equipamento para uma atividade.
        """
        self.ocupacao.append((inicio, fim, atividade.id))
        logger.info(
            f"✅ Ocupação registrada: {self.nome} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"para atividade ID {atividade.id}."
        )

    def liberar_ocupacao(self, atividade: Any) -> bool:
        """
        Libera a ocupação referente a uma atividade.
        """
        ocupacao_removida = [o for o in self.ocupacao if o[2] == atividade.id]

        if not ocupacao_removida:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para a atividade ID {atividade.id} no equipamento {self.nome}."
            )
            return False

        self.ocupacao = [o for o in self.ocupacao if o[2] != atividade.id]
        logger.info(
            f"✅ Ocupação liberada no equipamento {self.nome} para atividade ID {atividade.id}."
        )
        return True

    def esta_disponivel_no_periodo(self, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se o equipamento está livre no período.
        """
        for ocupacao_inicio, ocupacao_fim, _ in self.ocupacao:
            if not (fim <= ocupacao_inicio or inicio >= ocupacao_fim):
                return False
        return True

    def esta_ocupado_no_periodo(self, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se o equipamento está ocupado no período.
        """
        return not self.esta_disponivel_no_periodo(inicio, fim)

    def limpar_agenda(self):
        """
        Remove todas as ocupações do equipamento.
        """
        quantidade = len(self.ocupacao)
        self.ocupacao.clear()
        logger.info(
            f"🧹 Agenda do equipamento {self.nome} limpa. {quantidade} ocupações removidas."
        )

    def exibir_agenda(self):
        """
        Exibe todas as ocupações do equipamento.
        """
        if not self.ocupacao:
            logger.info(f"📅 {self.nome} está livre durante todo o período.")
            return

        logger.info(f"📅 Agenda do equipamento {self.nome}:")
        for inicio, fim, atividade_id in sorted(self.ocupacao, key=lambda x: x[0]):
            logger.info(
                f" - Atividade ID {atividade_id} | {inicio.strftime('%d/%m %H:%M')} até {fim.strftime('%d/%m %H:%M')}"
            )

    # ============================================
    # 🔍 Representação
    # ============================================
    def __str__(self):
        return (
            f"\n🔧 Equipamento: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name if hasattr(self.setor, 'name') else self.setor}"
            f"\nTipo: {self.tipo_equipamento.name if hasattr(self.tipo_equipamento, 'name') else self.tipo_equipamento}"
            f"\nOperadores necessários: {self.numero_operadores}"
            f"\nStatus: {'Ativo' if self.status_ativo else 'Inativo'}"
            f"\nOcupações: {len(self.ocupacao)} registradas"
        )
