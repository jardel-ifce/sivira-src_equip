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
    utilizando Backward Scheduling com FIPs (Fatores de Importância de Prioridade).
    """

    def __init__(self, bancadas: List[Bancada]):
        """
        Inicializa o gestor com uma lista de bancadas disponíveis.
        """
        self.bancadas = bancadas

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: Atividade) -> List[Bancada]:
        """
        Ordena as bancadas com base no FIP da atividade.
        Equipamentos com menor FIP são priorizados.
        """
        ordenadas = sorted(
            self.bancadas,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem das bancadas por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas
    
    # ==========================================================
    # 🔁 Obter frações necessárias 
    # ==========================================================
    def _obter_fracoes_necessarias(self, atividade: Atividade, bancada: Bancada) -> int:
        """
        Consulta no dicionário `configuracoes_equipamentos` da atividade
        quantas frações são necessárias para essa bancada específica.

        Se não houver configuração específica, assume 1 fração.
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
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[bool, Optional[Bancada], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"(duração: {duracao}) entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in equipamentos_ordenados:
                fracoes_necessarias = self._obter_fracoes_necessarias(atividade, bancada)

                if bancada.fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa) >= fracoes_necessarias:
                    sucesso = bancada.ocupar(
                        ordem_id=atividade.ordem_id,  # Associando ocupação à ordem de produção
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

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade) -> None:
        for bancada in self.bancadas:
            bancada.liberar_por_atividade(atividade.id, atividade.ordem_id)

    def liberar_por_ordem(self, atividade: Atividade) -> None:
        for bancada in self.bancadas:
            bancada.liberar_por_ordem(atividade.ordem_id)

    def liberar_fracoes_finalizadas(self, horario_atual: datetime) -> None:
        for bancada in self.bancadas:
            bancada.liberar_fracoes_terminadas(horario_atual)

    def liberar_todas_fracoes(self) -> None:
         for bancada in self.bancadas:
            bancada.liberar_todas_fracoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        """
        Exibe o estado atual de ocupações de todas as bancadas monitoradas.
        """
        logger.info("==============================================")
        logger.info("📅 Agenda das Bancadas")
        logger.info("==============================================")
        for bancada in self.bancadas:
            bancada.mostrar_agenda()
