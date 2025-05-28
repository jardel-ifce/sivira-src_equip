from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.masseira import Masseira
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger


# 🔥 Logger exclusivo para o Gestor de Misturadoras
logger = setup_logger('GestorMisturadoras')


class GestorMisturadoras:
    """
    🌀 Gestor especializado no controle de Masseiras (Misturadoras).
    ✔️ Utiliza Backward Scheduling (agendamento reverso).
    ✔️ Controle rigoroso por janela de tempo e capacidade de mistura.
    ✔️ Logs completos para rastreabilidade e auditoria.
    """

    def __init__(self, masseiras: List[Masseira]):
        """
        🔧 Inicializa o gestor com uma lista de masseiras disponíveis.
        """
        self.masseiras = masseiras

    # ==========================================================
    # 🏗️ Alocação de Masseira
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade: float
    ) -> Tuple[bool, Optional[Masseira], Optional[datetime], Optional[datetime]]:
        """
        🎯 Faz a alocação backward (reversa) buscando o horário mais próximo do fim.

        ✔️ Valida capacidade da masseira (peso e disponibilidade).
        ✔️ Retorna (sucesso, masseira, inicio_real, fim_real).

        Args:
            inicio (datetime): Janela de início permitida.
            fim (datetime): Janela de fim permitida.
            atividade (Atividade): Objeto da atividade.
            quantidade (float): Peso a ser utilizado.

        Returns:
            Tuple: (bool sucesso, Masseira, datetime inicio_real, datetime fim_real)
        """
        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for masseira in self.masseiras:
                if (
                    masseira.validar_capacidade(quantidade)
                    and masseira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    sucesso = masseira.ocupar(
                        quantidade_gramas=quantidade,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamentos_selecionados.append(masseira)
                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na {masseira.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, masseira, horario_inicio_tentativa, horario_final_tentativa

            # 🔁 Retrocede 5 minutos e tenta novamente
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma masseira "
            f"dentro da janela até {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔍 Consulta de Janelas Livres
    # ==========================================================
    def obter_horarios_disponiveis(
        self, inicio: datetime, fim: datetime, duracao: timedelta
    ) -> List[Tuple[Masseira, datetime, datetime]]:
        """
        🔍 Consulta todas as masseiras e retorna uma lista de (masseira, inicio, fim) com janelas livres.

        Args:
            inicio (datetime): Limite inferior da janela.
            fim (datetime): Limite superior da janela.
            duracao (timedelta): Duração da atividade.

        Returns:
            List: Lista de janelas disponíveis para cada masseira.
        """
        horarios_disponiveis = []
        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for masseira in self.masseiras:
                if masseira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa):
                    horarios_disponiveis.append(
                        (masseira, horario_inicio_tentativa, horario_final_tentativa)
                    )

            horario_final_tentativa -= timedelta(minutes=5)

        return horarios_disponiveis

    # ==========================================================
    # 🧹 Limpeza de Ocupações
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """
        🧹 Libera automaticamente todas as ocupações que já finalizaram até o horário atual.

        Args:
            horario_atual (datetime): Momento atual.
        """
        for masseira in self.masseiras:
            masseira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """
        🚨 Libera todas as ocupações de todas as masseiras.
        🔥 Reset total — use com cautela!
        """
        for masseira in self.masseiras:
            masseira.ocupacoes.clear()

    # ==========================================================
    # 📅 Visualização de Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        📅 Mostra a agenda de todas as masseiras gerenciadas.
        """
        print("\n============================")
        print("📅 Agenda das Masseiras")
        print("============================")
        for masseira in self.masseiras:
            masseira.mostrar_agenda()

    # ==========================================================
    # 🔍 Consulta de Equipamento Específico
    # ==========================================================
    def obter_masseira_por_id(self, id: int) -> Optional[Masseira]:
        """
        🔍 Retorna uma masseira específica pelo ID.

        Args:
            id (int): ID da masseira.

        Returns:
            Masseira ou None: A masseira encontrada ou None se não encontrada.
        """
        for masseira in self.masseiras:
            if masseira.id == id:
                return masseira
        return None
