import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from math import ceil
from models.equips.hot_mix import HotMix
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from utils.logger_factory import setup_logger

logger = setup_logger("GestorMisturadorasComCoccao")


class GestorMisturadorasComCoccao:
    def __init__(self, hotmixes: List[HotMix]):
        self.hotmixes = hotmixes
    
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================  
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[HotMix]:
        ordenadas = sorted(
            self.hotmixes,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        # logger.info("📊 Ordem dos HotMix por FIP (prioridade):")
        # for m in ordenadas:
        #     fip = atividade.fips_equipamentos.get(m, 999)
        #     logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")

    def _obter_velocidade(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoVelocidade]:
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("velocidade") if config else None
        try:
            return TipoVelocidade[valor] if valor else None
        except Exception:
            return None

    def _obter_chama(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoChama]:
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("tipo_chama") if config else None
        try:
            return TipoChama[valor] if valor else None
        except Exception:
            return None

    def _obter_pressoes(self, atividade: "AtividadeModular", hotmix: HotMix) -> List[TipoPressaoChama]:
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valores = config.get("pressao_chama") if config else []
        pressoes = []
        for p in valores:
            try:
                pressoes.append(TipoPressaoChama[p])
            except Exception:
                continue
        return pressoes

    # ==========================================================
    # 🎯 Alocação
    # ==========================================================    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float,
        **kwargs
    ) -> Tuple[bool, Optional[HotMix], Optional[datetime], Optional[datetime]]:


        duracao = atividade.duracao
        horario_final = fim

        hotmixes_ordenados = self._ordenar_por_fip(atividade)

        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            for hotmix in hotmixes_ordenados:
                if not hotmix.esta_disponivel(horario_inicio, horario_final):
                    continue

                if not (hotmix.capacidade_gramas_min <= quantidade_gramas <= hotmix.capacidade_gramas_max):
                    continue

                velocidade = self._obter_velocidade(atividade, hotmix)
                chama = self._obter_chama(atividade, hotmix)
                pressoes = self._obter_pressoes(atividade, hotmix)

                if velocidade is None or chama is None or not pressoes:
                    continue

                sucesso = hotmix.ocupar(
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id,
                    quantidade=quantidade_gramas,
                    inicio=horario_inicio,
                    fim=horario_final,
                    velocidade=velocidade,
                    chama=chama,
                    pressao_chamas=pressoes
                )

                if sucesso:
                    atividade.equipamento_alocado = hotmix
                    atividade.equipamentos_selecionados = [hotmix]
        
                    logger.info(
                        f"✅ Atividade {atividade.id} (Ordem {atividade.ordem_id}) alocada de "
                        f"{horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')} no HotMix {hotmix.nome}"
                    )
                    return True, hotmix, horario_inicio, horario_final

            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id} (Ordem {atividade.ordem_id}) não alocada entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None
    
    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for hotmix in self.hotmixes:
            hotmix.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for hotmix in self.hotmixes:
            hotmix.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for hotmix in self.hotmixes:
            hotmix.liberar_por_ordem(ordem_id=atividade.ordem_id)
      
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for hotmix in self.hotmixes:
            hotmix.liberar_concluidas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for hotmix in self.hotmixes:
            hotmix.ocupacoes.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Misturadoras com Cocção (HotMix)")
        logger.info("==============================================")
        for hotmix in self.hotmixes:
            hotmix.mostrar_agenda()

    