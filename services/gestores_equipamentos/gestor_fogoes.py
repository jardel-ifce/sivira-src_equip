import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from math import ceil
from models.equips.fogao import Fogao
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from utils.logger_factory import setup_logger

logger = setup_logger("GestorFogoes")


class GestorFogoes:
    """
    🔥 Gerenciador de fogões, responsável por alocar atividades de produção.
    Prioriza fogões com menor FIP e garante ocupação por boca.
    Suporta múltiplas chamas e pressões, com validação de capacidade.
    """
    def __init__(self, fogoes: List[Fogao]):
        self.fogoes = fogoes

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================    
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Fogao]:
        ordenadas = sorted(
            self.fogoes,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        # logger.info("📊 Ordem dos fogões por FIP (prioridade):")
        # for m in ordenadas:
        #     fip = atividade.fips_equipamentos.get(m, 999)
        #     logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    # ==========================================================
    # 🔁 Obter tipos de chama e pressões de chama
    # ==========================================================   
    def _obter_tipo_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> Optional[TipoChama]:
        chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        if not config or not config.get("tipo_chama"):
            logger.warning(f"⚠️ Tipo de chama não definido para '{chave}'")
            return None
        try:
            return TipoChama[config["tipo_chama"][0]]
        except Exception:
            logger.warning(f"⚠️ Valor inválido em tipo_chama para {chave}")
            return None

    def _obter_pressao_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> List[TipoPressaoChama]:
        chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        pressoes_raw = config.get("pressao_chama", []) if config else []
        pressoes = []
        for p in pressoes_raw:
            try:
                pressoes.append(TipoPressaoChama[p])
            except Exception:
                logger.warning(f"⚠️ Pressão inválida: '{p}' para fogão {chave}")
        return pressoes
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int
    ) -> Tuple[bool, Optional[Fogao], Optional[datetime], Optional[datetime]]:

        capacidade_total = sum(
            fogao.numero_bocas * fogao.capacidade_por_boca_gramas_max
            for fogao in self.fogoes
        )
        capacidade_por_boca = self.fogoes[0].capacidade_por_boca_gramas_max

        if quantidade_produto > capacidade_total:
            logger.error(
                f"❌ Quantidade ({quantidade_produto}g) excede capacidade total dos fogões ({capacidade_total}g)."
            )
            return False, None, None, None

        bocas_necessarias = ceil(quantidade_produto / capacidade_por_boca)
        quantidade_por_boca = quantidade_produto / bocas_necessarias


        duracao = atividade.duracao
        horario_final = fim

        equipamentos_ordenados = self._ordenar_por_fip(atividade)

        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            bocas_possiveis: List[Tuple[Fogao, int]] = []

            for fogao in equipamentos_ordenados:
                bocas_livres = fogao.bocas_disponiveis(horario_inicio, horario_final)

                tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
                pressoes_chama = self._obter_pressao_chama_para_fogao(atividade, fogao)

                if tipo_chama is None or not pressoes_chama:
                    continue

                for idx in bocas_livres:
                    bocas_possiveis.append((fogao, idx))
                    if len(bocas_possiveis) == bocas_necessarias:
                        break
                if len(bocas_possiveis) == bocas_necessarias:
                    break

            # ⚠️ Se não foi possível encontrar todas as bocas no intervalo
            if len(bocas_possiveis) < bocas_necessarias:
                horario_final -= timedelta(minutes=1)
                continue

            # ✅ Agora ocupamos de fato, pois já garantimos todas as bocas
            for fogao, idx_boca in bocas_possiveis:
                fogao.ocupar_boca(
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id,
                    quantidade=quantidade_por_boca,
                    inicio=horario_inicio,
                    fim=horario_final,
                    tipo_chama=tipo_chama,
                    pressao_chama=pressoes_chama,
                    boca=idx_boca
                )

            fogao_usado = bocas_possiveis[0][0]
            logger.info(
                f"✅ Atividade {atividade.id} alocada de {horario_inicio.strftime('%H:%M')} "
                f"até {horario_final.strftime('%H:%M')} usando {len(bocas_possiveis)} bocas."
            )
            return True, fogao_usado, horario_inicio, horario_final


    # ==========================================================
    # 🧹 Liberação de ocupações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular", ordem_id: int):
        for fogao in self.fogoes:
            fogao.liberar_por_atividade(ordem_id=ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for fogao in self.fogoes:
            fogao.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for fogao in self.fogoes:
            fogao.liberar_por_ordem(ordem_id=atividade.ordem_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for fogao in self.fogoes:
            fogao.liberar_bocas_terminadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for fogao in self.fogoes:
            fogao.liberar_todas_bocas() 

    # ==========================================================
    # 📅 Visualização de agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fogões")
        logger.info("==============================================")
        for fogao in self.fogoes:
            fogao.mostrar_agenda()
