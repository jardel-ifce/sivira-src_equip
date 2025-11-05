"""
Restaurador para Masseira
==================================================

Restaura o estado de ocupações de Masseira a partir de logs detalhados.

Estrutura restaurada:
- ocupacoes: tuplas com (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidades, tipo_mistura, inicio, fim)
"""

from typing import List, Optional
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.masseira import Masseira
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_mistura import TipoMistura


class RestauradorMasseira(RestauradorBase):
    """Restaurador especializado para Masseira"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Masseira) -> bool:
        """
        Restaura ocupações no equipamento

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        self.limpar_erros()

        # Validações
        if not self.validar_tipo_equipamento(equipamento, Masseira):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)
                velocidades_str = ocupacao.obter_detalhe("velocidades", [])
                tipo_mistura_str = ocupacao.obter_detalhe("tipo_mistura")

                # Converter velocidades de strings para enums
                velocidades = self._converter_velocidades(velocidades_str)

                # Converter tipo de mistura de string para enum
                tipo_mistura = self._converter_tipo_mistura(tipo_mistura_str)

                # Tupla para masseira: (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidades, tipo_mistura, inicio, fim)
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
                    velocidades,
                    tipo_mistura,
                    ocupacao.inicio,
                    ocupacao.fim
                )

                equipamento.ocupacoes.append(tupla_ocupacao)
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

    def _converter_velocidades(self, velocidades_str: Optional[List[str]]) -> List[TipoVelocidade]:
        """Converte lista de strings de velocidades para lista de enums"""
        if not velocidades_str:
            return []

        velocidades = []
        for vel_str in velocidades_str:
            try:
                # Mapear string para enum
                if vel_str == "ALTA":
                    velocidades.append(TipoVelocidade.ALTA)
                elif vel_str == "MEDIA":
                    velocidades.append(TipoVelocidade.MEDIA)
                elif vel_str == "BAIXA":
                    velocidades.append(TipoVelocidade.BAIXA)
            except Exception:
                pass

        return velocidades

    def _converter_tipo_mistura(self, tipo_mistura_str: Optional[str]) -> Optional[TipoMistura]:
        """Converte string de tipo de mistura para enum"""
        if not tipo_mistura_str:
            return None

        try:
            # Mapear string para enum
            if tipo_mistura_str == "RAPIDA":
                return TipoMistura.RAPIDA
            elif tipo_mistura_str == "LENTA":
                return TipoMistura.LENTA
            elif tipo_mistura_str == "SEMI_RAPIDA":
                return TipoMistura.SEMI_RAPIDA
        except Exception:
            pass

        return None
