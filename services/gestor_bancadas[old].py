from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.bancada import Bancada
from models.atividade_base import Atividade
from fractions import Fraction
from utils.logger_factory import setup_logger


# 🔥 Logger específico do Gestor de Bancadas
logger = setup_logger('GestorBancadas')


class GestorBancadas:
    """
    🪵 Gestor especializado no controle de Bancadas.
    ✔️ Gerencia ocupações fracionadas no tempo.
    ✔️ Utiliza Backward Scheduling (agendamento reverso).
    ✔️ Logs completos para auditoria e rastreabilidade.
    """

    def __init__(self, bancadas: List[Bancada]):
        """
        🔧 Inicializa o gestor com uma lista de bancadas.

        Args:
            bancadas (List[Bancada]): Lista de bancadas disponíveis.
        """
        self.bancadas = bancadas

    # ==========================================================
    # 🏗️ Alocação de Bancada
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        fracao: Tuple[int, int]
    ) -> Tuple[bool, Optional[Bancada], Optional[datetime], Optional[datetime]]:
        """
        🎯 Faz a alocação backward (reversa) buscando o horário mais próximo do fim.

        ✔️ Valida capacidade fracionada da bancada no tempo.
        ✔️ Retorna (sucesso, bancada, inicio_real, fim_real).

        Args:
            inicio (datetime): Janela de início permitida.
            fim (datetime): Janela de fim permitida.
            atividade (Atividade): Objeto da atividade.
            fracao (Tuple[int, int]): Fração da bancada (ex.: (1, 4) representa 1/4).

        Returns:
            Tuple: (bool sucesso, Bancada, datetime inicio_real, datetime fim_real)
        """
        duracao = atividade.duracao
        horario_final_tentativa = fim
        frac = Fraction(*fracao)

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {atividade.quantidade_produto}g, fração: {frac}) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in self.bancadas:
                if bancada.esta_disponivel(frac, horario_inicio_tentativa, horario_final_tentativa):
                    sucesso = bancada.ocupar(
                        fracao=fracao,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamentos_selecionados.append(bancada)
                        atividade.alocada = True
                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na {bancada.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, bancada, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=5)  # 🔁 Retrocede 5 minutos por tentativa

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma bancada "
            f"dentro da janela até {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔍 Consulta de Janelas Livres
    # ==========================================================
    def obter_horarios_disponiveis(
        self, inicio: datetime, fim: datetime, duracao: timedelta, fracao: Tuple[int, int]
    ) -> List[Tuple[Bancada, datetime, datetime]]:
        """
        🔍 Consulta todas as bancadas e retorna uma lista de (bancada, inicio, fim) com janelas livres,
        considerando a fração.

        Args:
            inicio (datetime): Limite inferior da janela.
            fim (datetime): Limite superior da janela.
            duracao (timedelta): Duração da atividade.
            fracao (Tuple[int, int]): Fração da bancada requerida.

        Returns:
            List: Lista de janelas disponíveis para cada bancada.
        """
        horarios_disponiveis = []
        horario_final_tentativa = fim
        frac = Fraction(*fracao)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in self.bancadas:
                if bancada.esta_disponivel(frac, horario_inicio_tentativa, horario_final_tentativa):
                    horarios_disponiveis.append(
                        (bancada, horario_inicio_tentativa, horario_final_tentativa)
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
        for bancada in self.bancadas:
            bancada.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """
        🚨 Libera todas as ocupações de todas as bancadas.
        🔥 Reset total — use com cautela!
        """
        for bancada in self.bancadas:
            bancada.ocupacoes.clear()

    # ==========================================================
    # 📅 Visualização de Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        📅 Mostra a agenda de todas as bancadas gerenciadas.
        """
        print("\n============================")
        print("📅 Agenda das Bancadas")
        print("============================")
        for bancada in self.bancadas:
            bancada.mostrar_agenda()

    # ==========================================================
    # 🔍 Consulta de Equipamento Específico
    # ==========================================================
    def obter_bancada_por_id(self, id: int) -> Optional[Bancada]:
        """
        🔍 Retorna uma bancada específica pelo ID.

        Args:
            id (int): ID da bancada.

        Returns:
            Bancada ou None: A bancada encontrada ou None se não encontrada.
        """
        for bancada in self.bancadas:
            if bancada.id == id:
                return bancada
        return None
