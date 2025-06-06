from typing import List, Tuple, Optional
from models.equips.balanca_digital import BalancaDigital
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger
from datetime import datetime

# ⚖️ Logger específico para o gestor de balanças
logger = setup_logger('GestorBalancas')


class GestorBalancas:
    """
    ⚖️ Gestor especializado para controle de balanças digitais.
    Permite múltiplas alocações simultâneas.
    """

    def __init__(self, balancas: List[BalancaDigital]):
        self.balancas = balancas

    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[BalancaDigital], Optional[datetime], Optional[datetime]]:
        """
        ⚖️ Tenta registrar a ocupação em alguma balança válida para o peso.
        Mesmo sem controle de tempo, retorna uma tupla padrão com (sucesso, equipamento, inicio, fim).
        """
        balancas_ordenadas = sorted(
            self.balancas,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )

        for balanca in balancas_ordenadas:
            if not balanca.aceita_quantidade(quantidade_gramas):
                logger.info(
                    f"🚫 Balança {balanca.nome} não aceita {quantidade_gramas}g. Ignorando."
                )
                continue

            sucesso = balanca.ocupar(
                atividade_id=atividade.id,
                quantidade=quantidade_gramas
            )
            if sucesso:
                atividade.equipamento_alocado = balanca
                atividade.equipamentos_selecionados = [balanca]
                atividade.alocada = True

                logger.info(
                    f"✅ Atividade {atividade.id} alocada na balança {balanca.nome} "
                    f"(sem intervalo de tempo)."
                )
                return True, balanca, None, None

            else:
                logger.warning(
                    f"⚠️ Falha ao registrar ocupação na balança {balanca.nome} mesmo após validação."
                )

        logger.error(
            f"❌ Nenhuma balança disponível ou compatível com {quantidade_gramas}g para atividade {atividade.id}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade):
        logger.info(
            f"🧹 Liberando ocupações associadas à atividade {atividade.id} em todas as balanças."
        )
        for balanca in self.balancas:
            balanca.liberar_por_atividade(atividade.id)

    def liberar_todas_ocupacoes(self):
        logger.info("🧹 Liberando todas as ocupações de todas as balanças.")
        for balanca in self.balancas:
            balanca.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Balanças")
        logger.info("==============================================")
        for balanca in self.balancas:
            balanca.mostrar_agenda()
