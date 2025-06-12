from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from models.equips.divisora_de_massas import DivisoraDeMassas
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger
import unicodedata

logger = setup_logger('GestorDivisoras')


class GestorDivisorasBoleadoras:
    """
    🏭 Gestor especializado para controle de divisoras de massas com ou sem boleadora,
    utilizando backward scheduling com prioridade por FIP.
    """

    def __init__(self, divisoras: List[DivisoraDeMassas]):
        self.divisoras = divisoras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: Atividade) -> List[DivisoraDeMassas]:
        ordenadas = sorted(
            self.divisoras,
            key=lambda d: atividade.fips_equipamentos.get(d, 999)
        )
        logger.info("📊 Ordem das divisoras por FIP (prioridade):")
        for d in ordenadas:
            fip = atividade.fips_equipamentos.get(d, 999)
            logger.info(f"🔹 {d.nome} (FIP: {fip})")
        return ordenadas
    
    # ==========================================================
    # 🔁 Obter flag de boleamento 
    # ==========================================================
    def _obter_flag_boleadora(self, atividade: Atividade, divisora: DivisoraDeMassas) -> bool:
        try:
            nome_bruto = divisora.nome.lower().replace(" ", "_")
            nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

            config = atividade.configuracoes_equipamentos.get(nome_chave)
            if config:
                return str(config.get("boleadora", "False")).lower() == "true"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter flag boleadora para {divisora.nome}: {e}")
        return False
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[DivisoraDeMassas], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} (duração: {duracao}, quantidade: {quantidade_gramas}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        divisoras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for divisora in divisoras_ordenadas:
                if (
                    divisora.validar_capacidade(quantidade_gramas)
                    and divisora.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    boleadora_flag = self._obter_flag_boleadora(atividade, divisora)

                    sucesso = divisora.ocupar(
                        ordem_id=atividade.ordem_id,
                        atividade_id=atividade.id,
                        quantidade=quantidade_gramas,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )

                    if sucesso:
                        atividade.equipamento_alocado = divisora
                        atividade.equipamentos_selecionados = [divisora]
                        atividade.alocada = True
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na divisora {divisora.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}"
                            f" com boleadora={boleadora_flag}."
                        )
                        return True, divisora, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma divisora dentro da janela entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None
    
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_anteriores_a(self, momento: datetime):
        for divisora in self.divisoras:
            divisora.liberar_ocupacoes_anteriores_a(momento)

    def liberar_por_ordem(self, atividade: Atividade):
        for divisora in self.divisoras:
            divisora.liberar_por_ordem(atividade.ordem_id)

    def liberar_por_atividade(self, atividade:Atividade):
        for divisora in self.divisoras:
            divisora.liberar_por_atividade(atividade.id, atividade.ordem_id)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Divisoras")
        logger.info("==============================================")
        for divisora in self.divisoras:
            divisora.mostrar_agenda()
