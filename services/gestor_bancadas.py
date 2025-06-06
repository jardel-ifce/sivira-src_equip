from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.bancada import Bancada
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger

# 🪕 Logger específico para o gestor de bancadas
logger = setup_logger('GestorBancadas')


class GestorBancadas:
    """
    🪕 Gestor especializado para controle de bancadas,
    utilizando Backward Scheduling com FIPs.
    """

    def __init__(self, bancadas: List[Bancada]):
        self.bancadas = bancadas
    
    def _ordenar_por_fip(self, atividade: Atividade) -> List[Bancada]:
        ordenadas = sorted(
            self.bancadas,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem das bancadas por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[bool, Optional[Bancada], Optional[datetime], Optional[datetime]]:
        """
        🪕 Realiza a alocação utilizando backward scheduling (do fim para o início),
        ordenando por FIP (menor valor tem prioridade).
        """
        duracao = atividade.duracao

        equipamentos_ordenados = self._ordenar_por_fip(atividade)

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"(duração: {duracao}) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in equipamentos_ordenados:
                fracoes_necessarias = self._obter_fracoes_necessarias(atividade, bancada)

                if bancada.fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa) >= fracoes_necessarias:
                    sucesso = bancada.ocupar(
                        atividade_id=atividade.id,
                        quantidade_fracoes=fracoes_necessarias,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )

                    if sucesso:
                        atividade.equipamento_alocado = bancada
                        atividade.equipamentos_selecionados = [bancada]
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na bancada {bancada.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )

                        return True, bancada, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    def _obter_fracoes_necessarias(self, atividade: Atividade, bancada: Bancada) -> int:
        """
        🔍 Busca no JSON a quantidade de frações necessárias para a bancada específica,
        retornando 1 se não encontrar.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_chave = bancada.nome.lower().replace(" ", "_")
                logger.debug(f"🔎 Procurando config para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config:
                    fracoes = config.get("fracoes_necessarias", 1)
                    logger.debug(f"✅ Encontrado: {fracoes} frações para {nome_chave}")
                    return fracoes
                else:
                    logger.debug(f"❌ Nenhuma configuração encontrada para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter frações para {bancada.nome}: {e}")
        return 1

    # ==========================================================
    # 🪝 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade) -> None:
        logger.info(
            f"🪝 Liberando frações associadas à atividade {atividade.id} em todas as bancadas."
        )
        for bancada in self.bancadas:
            bancada.liberar_por_atividade(atividade.id)

    def liberar_fracoes_finalizadas(self, horario_atual: datetime) -> None:
        logger.info(
            f"🔄 Liberando frações finalizadas das bancadas até {horario_atual.strftime('%H:%M')}."
        )
        for bancada in self.bancadas:
            bancada.liberar_fracoes_terminadas(horario_atual)

    def liberar_todas_fracoes(self) -> None:
        logger.info("🪝 Liberando todas as frações de todas as bancadas.")
        for bancada in self.bancadas:
            bancada.liberar_todas_fracoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("==============================================")
        logger.info("📅 Agenda das Bancadas")
        logger.info("==============================================")
        for bancada in self.bancadas:
            bancada.mostrar_agenda()
