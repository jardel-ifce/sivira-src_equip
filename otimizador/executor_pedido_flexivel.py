"""
Executor de Pedido com Janelas Flexiveis
========================================

Backward scheduling que tenta multiplos horarios dentro da janela.
Quando uma alocacao falha no fim_mais_tarde, tenta horarios anteriores
ate fim_mais_cedo, respeitando o tau_max.

Criado em: 23/12/2025
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ExecutorPedidoFlexivel')


@dataclass
class ResultadoAlocacaoFlexivel:
    """Resultado de uma alocacao flexivel."""
    sucesso: bool
    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None
    tentativas: int = 0
    usou_retry: bool = False
    horario_original: Optional[datetime] = None
    horario_final: Optional[datetime] = None
    mensagem: str = ""


class ExecutorPedidoFlexivel:
    """
    Executa um pedido usando janelas flexiveis.

    Estrategia:
    1. Ordenar atividades em ordem reversa (backward)
    2. Para cada atividade:
       - Se tem janela: tentar alocar do fim_mais_tarde para fim_mais_cedo
       - Se nao tem janela: usar alocacao padrao
    3. Respeitar tau_max entre atividades consecutivas
    """

    def __init__(self, pedido, janelas: Dict):
        """
        Inicializa executor flexivel.

        Args:
            pedido: Objeto PedidoDeProducao
            janelas: Dict {id_atividade: JanelaFlexivel}
        """
        self.pedido = pedido
        self.janelas = janelas
        self.logger = setup_logger('ExecutorPedidoFlexivel')
        self.resultados_atividades = {}

    def executar(self) -> Dict:
        """
        Executa o pedido usando janelas flexiveis.

        Returns:
            Dict com resultado da execucao
        """
        from enums.producao.tipo_item import TipoItem

        self.logger.info(f"Executando pedido {self.pedido.id_pedido} com janelas flexiveis...")

        tentativas_totais = 0
        usou_retry = False

        try:
            # Separar atividades por tipo
            atividades_produto = sorted(
                [a for a in self.pedido.atividades_modulares if a.tipo_item == TipoItem.PRODUTO],
                key=lambda a: a.id_atividade,
                reverse=True  # Backward: maior ID primeiro
            )

            atividades_subproduto = sorted(
                [a for a in self.pedido.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO],
                key=lambda a: a.id_atividade,
                reverse=True
            )

            self.logger.info(
                f"   {len(atividades_produto)} atividades de PRODUTO, "
                f"{len(atividades_subproduto)} atividades de SUBPRODUTO"
            )

            # Executar atividades de PRODUTO (backward)
            current_deadline = self.pedido.fim_jornada

            for i, atividade in enumerate(atividades_produto):
                janela = self.janelas.get(atividade.id_atividade)

                self.logger.info(
                    f"   Alocando atividade {atividade.id_atividade} ({atividade.nome_atividade})..."
                )

                if janela:
                    resultado = self._alocar_com_janela(atividade, janela, current_deadline)
                else:
                    resultado = self._alocar_sem_janela(atividade, current_deadline)

                tentativas_totais += resultado.tentativas
                if resultado.usou_retry:
                    usou_retry = True

                if not resultado.sucesso:
                    self.logger.error(f"   Falha na atividade {atividade.id_atividade}: {resultado.mensagem}")
                    return {
                        'sucesso': False,
                        'tentativas': tentativas_totais,
                        'usou_retry': usou_retry,
                        'atividade_falha': atividade.id_atividade,
                        'mensagem': resultado.mensagem
                    }

                self.resultados_atividades[atividade.id_atividade] = resultado

                # Atualizar deadline para proxima atividade (backward)
                if resultado.inicio:
                    current_deadline = resultado.inicio
                    self.logger.info(
                        f"   Atividade {atividade.id_atividade} alocada: "
                        f"{resultado.inicio.strftime('%H:%M')} - {resultado.fim.strftime('%H:%M')}"
                    )

            # Executar atividades de SUBPRODUTO
            # SUBPRODUTOs devem terminar quando o primeiro PRODUTO comeca
            if atividades_subproduto and atividades_produto:
                primeiro_produto = min(atividades_produto, key=lambda a: a.id_atividade)
                resultado_primeiro = self.resultados_atividades.get(primeiro_produto.id_atividade)

                if resultado_primeiro and resultado_primeiro.inicio:
                    deadline_subprodutos = resultado_primeiro.inicio
                else:
                    deadline_subprodutos = self.pedido.fim_jornada

                # Agrupar subprodutos por id_item
                grupos_subproduto = self._agrupar_por_item(atividades_subproduto)

                for nome_grupo, atividades_grupo in grupos_subproduto.items():
                    self.logger.info(f"   Processando grupo de subproduto: {nome_grupo}")

                    current_deadline_grupo = deadline_subprodutos

                    for atividade in atividades_grupo:
                        janela = self.janelas.get(atividade.id_atividade)

                        if janela:
                            resultado = self._alocar_com_janela(atividade, janela, current_deadline_grupo)
                        else:
                            resultado = self._alocar_sem_janela(atividade, current_deadline_grupo)

                        tentativas_totais += resultado.tentativas
                        if resultado.usou_retry:
                            usou_retry = True

                        if not resultado.sucesso:
                            self.logger.error(
                                f"   Falha na atividade {atividade.id_atividade}: {resultado.mensagem}"
                            )
                            return {
                                'sucesso': False,
                                'tentativas': tentativas_totais,
                                'usou_retry': usou_retry,
                                'atividade_falha': atividade.id_atividade,
                                'mensagem': resultado.mensagem
                            }

                        self.resultados_atividades[atividade.id_atividade] = resultado

                        if resultado.inicio:
                            current_deadline_grupo = resultado.inicio

            self.logger.info(f"Pedido {self.pedido.id_pedido} executado com sucesso!")

            return {
                'sucesso': True,
                'tentativas': tentativas_totais,
                'usou_retry': usou_retry,
                'atividades_alocadas': len(self.resultados_atividades),
                'mensagem': 'Todas atividades alocadas com sucesso'
            }

        except Exception as e:
            self.logger.error(f"Erro ao executar pedido {self.pedido.id_pedido}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'sucesso': False,
                'tentativas': tentativas_totais,
                'usou_retry': usou_retry,
                'mensagem': str(e)
            }

    def _alocar_com_janela(
        self,
        atividade,
        janela,
        deadline_atividade: datetime
    ) -> ResultadoAlocacaoFlexivel:
        """
        Aloca atividade dentro da janela flexivel.

        Estrategia: Comecar pelo fim_mais_tarde, ir para fim_mais_cedo em steps de 5min.
        """
        self.logger.debug(
            f"      Janela: [{janela.inicio_mais_cedo.strftime('%H:%M')}, "
            f"{janela.inicio_mais_tarde.strftime('%H:%M')}], "
            f"flex={janela.flexibilidade_minutos:.0f}min"
        )

        # Gerar tentativas dentro da janela
        tentativas = self._gerar_tentativas_janela(janela, deadline_atividade)
        horario_original = tentativas[0] if tentativas else deadline_atividade

        for i, tentativa_fim in enumerate(tentativas):
            self.logger.debug(f"      Tentativa {i+1}/{len(tentativas)}: fim={tentativa_fim.strftime('%H:%M')}")

            try:
                sucesso, inicio, fim, tau_max, equipamentos = atividade.tentar_alocar_e_iniciar_equipamentos(
                    self.pedido.inicio_jornada,
                    tentativa_fim
                )

                if sucesso:
                    usou_retry = (i > 0)  # Usou retry se nao foi a primeira tentativa

                    if usou_retry:
                        self.logger.info(
                            f"      Alocacao bem-sucedida na tentativa {i+1} "
                            f"(horario ajustado de {horario_original.strftime('%H:%M')} "
                            f"para {tentativa_fim.strftime('%H:%M')})"
                        )

                    return ResultadoAlocacaoFlexivel(
                        sucesso=True,
                        inicio=inicio,
                        fim=fim,
                        tentativas=i + 1,
                        usou_retry=usou_retry,
                        horario_original=horario_original,
                        horario_final=tentativa_fim,
                        mensagem="Alocacao bem-sucedida"
                    )

            except Exception as e:
                self.logger.debug(f"      Tentativa {i+1} falhou: {e}")
                continue

        # Todas tentativas falharam
        return ResultadoAlocacaoFlexivel(
            sucesso=False,
            tentativas=len(tentativas),
            usou_retry=True,
            horario_original=horario_original,
            mensagem=f"Todas {len(tentativas)} tentativas falharam dentro da janela"
        )

    def _alocar_sem_janela(
        self,
        atividade,
        deadline_atividade: datetime
    ) -> ResultadoAlocacaoFlexivel:
        """
        Alocacao padrao sem janela (modo deterministico).
        """
        self.logger.debug(f"      Sem janela flexivel, usando alocacao padrao")

        try:
            sucesso, inicio, fim, tau_max, equipamentos = atividade.tentar_alocar_e_iniciar_equipamentos(
                self.pedido.inicio_jornada,
                deadline_atividade
            )

            if sucesso:
                return ResultadoAlocacaoFlexivel(
                    sucesso=True,
                    inicio=inicio,
                    fim=fim,
                    tentativas=1,
                    usou_retry=False,
                    horario_original=deadline_atividade,
                    horario_final=deadline_atividade,
                    mensagem="Alocacao padrao bem-sucedida"
                )
            else:
                return ResultadoAlocacaoFlexivel(
                    sucesso=False,
                    tentativas=1,
                    usou_retry=False,
                    horario_original=deadline_atividade,
                    mensagem="Alocacao padrao falhou"
                )

        except Exception as e:
            return ResultadoAlocacaoFlexivel(
                sucesso=False,
                tentativas=1,
                usou_retry=False,
                horario_original=deadline_atividade,
                mensagem=f"Erro na alocacao: {e}"
            )

    def _gerar_tentativas_janela(self, janela, deadline_atividade: datetime) -> List[datetime]:
        """
        Gera lista de horarios de fim a tentar dentro da janela.

        Comeca pelo fim_mais_tarde e vai decrementando em steps ate fim_mais_cedo.
        """
        tentativas = []
        step = timedelta(minutes=5)  # Step de 5 minutos

        # Usar o menor entre fim_mais_tarde e deadline_atividade
        fim_inicial = min(janela.fim_mais_tarde, deadline_atividade)
        fim_minimo = janela.fim_mais_cedo

        current = fim_inicial

        while current >= fim_minimo:
            tentativas.append(current)
            current -= step

        # Garantir que fim_mais_cedo esta na lista
        if tentativas and tentativas[-1] != fim_minimo:
            tentativas.append(fim_minimo)

        self.logger.debug(
            f"      Geradas {len(tentativas)} tentativas: "
            f"[{fim_inicial.strftime('%H:%M')} -> {fim_minimo.strftime('%H:%M')}]"
        )

        return tentativas

    def _agrupar_por_item(self, atividades: List) -> Dict[str, List]:
        """Agrupa atividades por id_item."""
        grupos = {}

        for atividade in atividades:
            id_item = getattr(atividade, 'id_item', 0)
            nome_item = getattr(atividade, 'nome_item', f'item_{id_item}')

            if nome_item not in grupos:
                grupos[nome_item] = []

            grupos[nome_item].append(atividade)

        # Ordenar cada grupo por id_atividade (decrescente para backward)
        for nome, lista in grupos.items():
            lista.sort(key=lambda a: a.id_atividade, reverse=True)

        return grupos

    def obter_resumo_execucao(self) -> Dict:
        """Retorna resumo da execucao do pedido."""
        total_tentativas = sum(
            r.tentativas for r in self.resultados_atividades.values()
        )
        atividades_com_retry = sum(
            1 for r in self.resultados_atividades.values() if r.usou_retry
        )

        return {
            'id_pedido': self.pedido.id_pedido,
            'atividades_alocadas': len(self.resultados_atividades),
            'total_tentativas': total_tentativas,
            'atividades_com_retry': atividades_com_retry,
            'detalhes': {
                id_ativ: {
                    'sucesso': r.sucesso,
                    'tentativas': r.tentativas,
                    'usou_retry': r.usou_retry,
                    'inicio': r.inicio.strftime('%H:%M') if r.inicio else None,
                    'fim': r.fim.strftime('%H:%M') if r.fim else None
                }
                for id_ativ, r in self.resultados_atividades.items()
            }
        }


def executar_com_janelas(pedido, janelas: Dict) -> bool:
    """
    Funcao helper para executar um pedido com janelas flexiveis.

    Args:
        pedido: Objeto PedidoDeProducao
        janelas: Dict {id_atividade: JanelaFlexivel}

    Returns:
        bool: True se sucesso
    """
    executor = ExecutorPedidoFlexivel(pedido, janelas)
    resultado = executor.executar()
    return resultado.get('sucesso', False)
