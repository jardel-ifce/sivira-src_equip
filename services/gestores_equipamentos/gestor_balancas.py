from typing import List, Tuple, Optional, TYPE_CHECKING
from models.equips.balanca_digital import BalancaDigital
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logger_factory import setup_logger
from datetime import datetime

# ⚖️ Logger específico para o gestor de balanças
logger = setup_logger('GestorBalancas')


class GestorBalancas:
    """
    ⚖️ Gestor especializado para controle de balanças digitais.
    Permite múltiplas alocações simultâneas com controle de tempo.
    """

    def __init__(self, balancas: List[BalancaDigital]):
        self.balancas = balancas

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[BalancaDigital]:
        ordenadas = sorted(
            self.balancas,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )

        # logger.info("📊 Ordem das balanças por FIP (prioridade):")
        # for b in ordenadas:
        #     fip = atividade.fips_equipamentos.get(b, 999)
        #     logger.info(f"🔹 {b.nome} (FIP: {fip})")
        return ordenadas

    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[BalancaDigital], Optional[datetime], Optional[datetime]]:
        
        balancas_ordenadas = self._ordenar_por_fip(atividade)

        for balanca in balancas_ordenadas:
            if not balanca.aceita_quantidade(quantidade_gramas):
                logger.info(
                    f"🚫 Balança {balanca.nome} não aceita {quantidade_gramas}g. Ignorando."
                )
                continue

            # Aloca informando início e fim
            sucesso = balanca.ocupar(
                ordem_id=atividade.ordem_id,
                pedido_id=atividade.pedido_id,
                atividade_id=atividade.id,
                quantidade=quantidade_gramas,
                inicio=inicio,
                fim=fim
            )

            if sucesso:
                atividade.equipamento_alocado = balanca
                atividade.equipamentos_selecionados = [balanca]
                atividade.alocada = True

                logger.info(
                    f"✅ Atividade {atividade.id} alocada na balança {balanca.nome} | "
                        f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} "
                )
                return True, balanca, inicio, fim

            else:
                logger.warning(
                    f"⚠️ Falha ao registrar ocupação na balança {balanca.nome} "
                    f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
                )

        logger.error(
            f"❌ Nenhuma balança disponível ou compatível com {quantidade_gramas}g para atividade {atividade.id}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_ordem(ordem_id=atividade.ordem_id)

    def liberar_todas_ocupacoes(self):
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
