from typing import List, Tuple, Optional, TYPE_CHECKING
from models.equipamentos.balanca_digital import BalancaDigital
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
from datetime import datetime
import unicodedata

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
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _obter_peso_explicito_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "balanca" in chave_normalizada:
                    peso_gramas = conteudo.get("peso_gramas")
                    if peso_gramas is not None:
                        return peso_gramas
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar peso_gramas no JSON da atividade: {e}")
            return None


    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float | None = None
    ) -> Tuple[bool, Optional[BalancaDigital], Optional[datetime], Optional[datetime]]:

        peso_json = self._obter_peso_explicito_do_json(atividade)
        if peso_json is not None:
            quantidade_final = peso_json
        else:
            quantidade_final = quantidade_gramas

        if quantidade_final is None:
            logger.error("❌ Nenhuma quantidade definida para balança.")
            return False, None, None, None

        balancas_ordenadas = self._ordenar_por_fip(atividade)

        for balanca in balancas_ordenadas:
            if not balanca.aceita_quantidade(quantidade_final):
                logger.info(
                    f"🚫 Balança {balanca.nome} não aceita {quantidade_final}g. Ignorando."
                )
                continue

            sucesso = balanca.ocupar(
                ordem_id=atividade.ordem_id,
                pedido_id=atividade.pedido_id,
                atividade_id=atividade.id_atividade,
                quantidade=quantidade_final,
                inicio=inicio,
                fim=fim
            )

            if sucesso:
                atividade.equipamento_alocado = balanca
                atividade.equipamentos_selecionados = [balanca]
                atividade.alocada = True

                logger.info(
                    f"✅ Atividade {atividade.id_atividade} alocada na {balanca.nome} | "
                    f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} "
                )
                return True, balanca, inicio, fim

            else:
                logger.warning(
                    f"⚠️ Falha ao registrar ocupação na {balanca.nome} "
                    f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
                )

        logger.error(
            f"❌ Nenhuma balança disponível ou compatível com {quantidade_final}g para atividade {atividade.id_atividade}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id_atividade)

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
