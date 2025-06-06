import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from math import ceil
from models.equips.fogao import Fogao
from models.atividade_base import Atividade
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from utils.logger_factory import setup_logger

logger = setup_logger("GestorFogoes")


class GestorFogoes:
    def __init__(self, fogoes: List[Fogao]):
        self.fogoes = fogoes
    
    def _ordenar_por_fip(self, atividade: Atividade) -> List[Fogao]:
        ordenadas = sorted(
            self.fogoes,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem dos fogões por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
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

        logger.info(
            f"📐 Alocando {quantidade_produto}g usando {bocas_necessarias} bocas (~{quantidade_por_boca:.0f}g cada)"
        )

        duracao = atividade.duracao
        horario_final = fim

        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        

        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao
            bocas_alocadas = []

            for fogao in equipamentos_ordenados:
                bocas_livres = fogao.bocas_disponiveis(horario_inicio, horario_final)

                tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
                pressoes_chama = self._obter_pressao_chama_para_fogao(atividade, fogao)

                if tipo_chama is None or not pressoes_chama:
                    continue

                for idx in bocas_livres:
                    sucesso = fogao.ocupar_boca(
                        boca=idx,
                        atividade_id=atividade.id,
                        quantidade=int(quantidade_por_boca),
                        inicio=horario_inicio,
                        fim=horario_final,
                        tipo_chama=tipo_chama,
                        pressao_chama=pressoes_chama  # ✅ passa a lista completa
                    )

                    if sucesso:
                        bocas_alocadas.append((fogao, idx))
                        if len(bocas_alocadas) == bocas_necessarias:
                            break

                if len(bocas_alocadas) == bocas_necessarias:
                    break

            if len(bocas_alocadas) == bocas_necessarias:
                fogao_usado = bocas_alocadas[0][0]
                logger.info(
                    f"✅ Atividade {atividade.id} alocada de {horario_inicio.strftime('%H:%M')} "
                    f"até {horario_final.strftime('%H:%M')} usando {len(bocas_alocadas)} bocas."
                )
                return True, fogao_usado, horario_inicio, horario_final

            for fogao, idx_boca in bocas_alocadas:
                fogao.liberar_boca(idx_boca, atividade.id)

            horario_final -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não alocada entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    def _obter_tipo_chama_para_fogao(self, atividade: Atividade, fogao: Fogao) -> Optional[TipoChama]:
        chave = self._normalizar_nome(fogao.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        if not config or not config.get("tipo_chama"):
            logger.warning(f"⚠️ Tipo de chama não definido para '{chave}'")
            return None
        try:
            return TipoChama[config["tipo_chama"][0]]
        except Exception:
            logger.warning(f"⚠️ Valor inválido em tipo_chama para {chave}")
            return None

    def _obter_pressao_chama_para_fogao(self, atividade: Atividade, fogao: Fogao) -> List[TipoPressaoChama]:
        chave = self._normalizar_nome(fogao.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        pressoes_raw = config.get("pressao_chama", []) if config else []
        pressoes = []
        for p in pressoes_raw:
            try:
                pressoes.append(TipoPressaoChama[p])
            except Exception:
                logger.warning(f"⚠️ Pressão inválida: '{p}' para fogão {chave}")
        return pressoes

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")

    def liberar_por_atividade(self, atividade_id: int):
        for fogao in self.fogoes:
            fogao.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for fogao in self.fogoes:
            fogao.liberar_bocas_terminadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for fogao in self.fogoes:
            fogao.liberar_todas_bocas()

    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fogões")
        logger.info("==============================================")
        for fogao in self.fogoes:
            fogao.mostrar_agenda()
