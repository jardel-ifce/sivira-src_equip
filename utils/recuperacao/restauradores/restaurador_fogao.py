"""
Restaurador para Fogao
==================================================

Restaura o estado de ocupações de Fogao a partir de logs detalhados.

Estrutura restaurada:
- ocupacoes_por_boca: lista de listas com tuplas (id_ordem, id_pedido, id_atividade, id_item, quantidade, tipo_chama, pressoes, inicio, fim)
"""

from typing import List, Optional
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.fogao import Fogao
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama


class RestauradorFogao(RestauradorBase):
    """Restaurador especializado para Fogao"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Fogao) -> bool:
        """
        Restaura ocupações no equipamento

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        self.limpar_erros()

        if not self.validar_tipo_equipamento(equipamento, Fogao):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                boca = ocupacao.obter_detalhe("boca")
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)
                tipo_chama_str = ocupacao.obter_detalhe("tipo_chama")
                pressoes_str = ocupacao.obter_detalhe("pressoes", [])

                if boca is None:
                    self.adicionar_erro(f"Ocupação sem boca: {ocupacao}")
                    continue

                boca_index = boca - 1
                if not self.validar_indice_valido(boca_index, equipamento.numero_bocas, "bocas de fogão"):
                    continue

                tipo_chama = self._converter_tipo_chama(tipo_chama_str)
                pressoes = self._converter_pressoes(pressoes_str)

                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
                    tipo_chama,
                    pressoes,
                    ocupacao.inicio,
                    ocupacao.fim
                )

                equipamento.ocupacoes_por_boca[boca_index].append(tupla_ocupacao)
                total_restauradas += 1

            except Exception as e:
                self.adicionar_erro(f"Erro ao restaurar ocupação {ocupacao}: {e}")
                continue

        if total_restauradas > 0:
            self.log_restauracao_sucesso(equipamento, total_restauradas)
            return True
        else:
            self.log_restauracao_erro(equipamento, "Nenhuma ocupação foi restaurada")
            return False

    def _converter_tipo_chama(self, tipo_chama_str: Optional[str]) -> Optional[TipoChama]:
        """Converte string para enum TipoChama"""
        if not tipo_chama_str:
            return None
        try:
            if tipo_chama_str == "ALTA":
                return TipoChama.ALTA
            elif tipo_chama_str == "MEDIA":
                return TipoChama.MEDIA
            elif tipo_chama_str == "BAIXA":
                return TipoChama.BAIXA
        except Exception:
            pass
        return None

    def _converter_pressoes(self, pressoes_str: List[str]) -> List[TipoPressaoChama]:
        """Converte lista de strings para lista de enums TipoPressaoChama"""
        if not pressoes_str:
            return []

        pressoes = []
        for p in pressoes_str:
            try:
                if p == "ALTA":
                    pressoes.append(TipoPressaoChama.ALTA)
                elif p == "MEDIA":
                    pressoes.append(TipoPressaoChama.MEDIA)
                elif p == "BAIXA":
                    pressoes.append(TipoPressaoChama.BAIXA)
            except Exception:
                pass
        return pressoes
