"""
Restaurador para Câmara Refrigerada
===================================

Restaura o estado de ocupações de câmaras refrigeradas.
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.camara_refrigerada import CamaraRefrigerada


class RestauradorCamaraRefrigerada(RestauradorBase):
    """Restaurador especializado para Câmaras Refrigeradas"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: CamaraRefrigerada) -> bool:
        self.limpar_erros()

        if not self.validar_tipo_equipamento(equipamento, CamaraRefrigerada):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                nivel_numero = ocupacao.obter_detalhe("nivel_numero")
                caixa_numero = ocupacao.obter_detalhe("caixa_numero")
                temperatura = ocupacao.obter_detalhe("temperatura")
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)

                # Restaurar em nível
                if nivel_numero is not None:
                    nivel_index = nivel_numero - 1

                    if not self.validar_indice_valido(
                        nivel_index,
                        equipamento.qtd_niveis_total,
                        "níveis de câmara"
                    ):
                        continue

                    tupla_ocupacao = (
                        ocupacao.id_ordem,
                        ocupacao.id_pedido,
                        ocupacao.id_atividade,
                        ocupacao.id_item,
                        quantidade,
                        ocupacao.inicio,
                        ocupacao.fim
                    )
                    equipamento.niveis_ocupacoes[nivel_index].append(tupla_ocupacao)

                # Restaurar em caixa
                elif caixa_numero is not None:
                    caixa_index = caixa_numero - 1

                    if not self.validar_indice_valido(
                        caixa_index,
                        equipamento.qtd_caixas,
                        "caixas de câmara"
                    ):
                        continue

                    tupla_ocupacao = (
                        ocupacao.id_ordem,
                        ocupacao.id_pedido,
                        ocupacao.id_atividade,
                        ocupacao.id_item,
                        quantidade,
                        ocupacao.inicio,
                        ocupacao.fim
                    )
                    equipamento.caixas_ocupacoes[caixa_index].append(tupla_ocupacao)

                # Restaurar temperatura
                if temperatura is not None:
                    intervalo_temp = (temperatura, ocupacao.inicio, ocupacao.fim)
                    if intervalo_temp not in equipamento.intervalos_temperatura:
                        equipamento.intervalos_temperatura.append(intervalo_temp)

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