from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Union, TYPE_CHECKING
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logger_factory import setup_logger
import unicodedata

# 🏭 Logger específico para o gestor de batedeiras
logger = setup_logger('GestorBatedeiras')

Batedeiras = Union[BatedeiraIndustrial, BatedeiraPlanetaria]


class GestorBatedeiras:
    """
    🏭 Gestor especializado para controle de batedeiras industriais e planetárias,
    utilizando backward scheduling com prioridade por FIP.
    """

    def __init__(self, batedeiras: List[Batedeiras]):
        self.batedeiras = batedeiras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Batedeiras]:
        ordenadas = sorted(
            self.batedeiras,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        # logger.info("📊 Ordem das batedeiras por FIP (prioridade):")
        # for b in ordenadas:
        #     fip = atividade.fips_equipamentos.get(b, 999)
        #     logger.info(f"🔹 {b.nome} (FIP: {fip})")
        return ordenadas

    # ==========================================================
    # 🔁 Obter velocidade 
    # ==========================================================
    def _obter_velocidade(self, atividade: "AtividadeModular", batedeira: Batedeiras) -> Optional[int]:
        """
        🔍 Busca no JSON a velocidade (inteira) configurada para a batedeira específica,
        retornando None se não encontrar.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = batedeira.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                logger.debug(f"🔎 Procurando velocidade para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")

                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "velocidade" in config:
                    velocidade = int(config["velocidade"])
                    logger.debug(f"✅ Velocidade encontrada para {nome_chave}: {velocidade}")
                    return velocidade
                else:
                    logger.debug(f"❌ Nenhuma velocidade definida para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter velocidade para {batedeira.nome}: {e}")
        return None

    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: float
    ) -> Tuple[bool, Optional[Batedeiras], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        # logger.info(
        #     f"🎯 Tentando alocar atividade {atividade.id} "
        #     f"(duração: {duracao}, quantidade: {quantidade}g) "
        #     f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        # )

        batedeiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for batedeira in batedeiras_ordenadas:
                if (
                    batedeira.validar_capacidade(quantidade)
                    and batedeira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    velocidade_configurada = self._obter_velocidade(atividade, batedeira)

                    sucesso = batedeira.ocupar(
                        ordem_id=atividade.ordem_id,
                        pedido_id=atividade.pedido_id,
                        atividade_id=atividade.id,
                        quantidade_gramas=quantidade,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        velocidade=velocidade_configurada
                    )
                    if sucesso:
                        atividade.equipamento_alocado = batedeira
                        atividade.equipamentos_selecionados = [batedeira]
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na batedeira {batedeira.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, batedeira, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma batedeira "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for batedeira in self.batedeiras:
            batedeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_atividade(atividade_id=atividade.id, pedido_id=atividade.pedido_id, ordem_id=atividade.ordem_id)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_ordem(atividade.ordem_id)

    def liberar_todas_ocupacoes(self):
        for batedeira in self.batedeiras:
            batedeira.ocupacoes.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Batedeiras")
        logger.info("==============================================")
        for batedeira in self.batedeiras:
            batedeira.mostrar_agenda()

