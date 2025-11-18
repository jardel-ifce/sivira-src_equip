"""
Calculador de Horários Determinísticos
======================================

Para cenários com todos tempo_maximo_espera = 0:
- Calcula horários FIXOS exatos para cada atividade
- Trabalha backward a partir do deadline
- Última atividade PRODUTO termina no deadline
- Atividades anteriores executam consecutivamente (gap=0)
- SUBPRODUTOS terminam quando PRODUTO correspondente começa

Criado em: 18/11/2025
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from utils.logs.logger_factory import setup_logger
from enums.producao.tipo_item import TipoItem

logger = setup_logger('CalculadorHorariosDeterministicos')


class CalculadorHorariosDeterministicos:
    """
    Calcula horários fixos exatos para cenários determinísticos (gaps=0).
    """

    def __init__(self):
        self.logger = setup_logger('CalculadorHorariosDeterministicos')

    def calcular_horarios_fixos(
        self,
        pedidos: List,
        inicio_jornada: datetime
    ) -> Dict[int, Dict[int, Tuple[datetime, datetime]]]:
        """
        Calcula horários fixos para todos os pedidos.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            inicio_jornada: Datetime do início da jornada

        Returns:
            Dict {id_pedido: {id_atividade: (inicio, fim)}}
        """
        horarios_calculados = {}

        for pedido in pedidos:
            try:
                horarios_pedido = self._calcular_horarios_pedido(
                    pedido,
                    inicio_jornada
                )
                horarios_calculados[pedido.id_pedido] = horarios_pedido

                self.logger.debug(
                    f"✅ Pedido {pedido.id_pedido}: "
                    f"{len(horarios_pedido)} atividades com horários calculados"
                )

            except Exception as e:
                self.logger.error(
                    f"❌ Erro ao calcular horários do pedido {pedido.id_pedido}: {e}"
                )
                horarios_calculados[pedido.id_pedido] = {}

        self.logger.info(
            f"📅 Horários calculados para {len(horarios_calculados)} pedidos"
        )

        return horarios_calculados

    def _calcular_horarios_pedido(
        self,
        pedido,
        inicio_jornada: datetime
    ) -> Dict[int, Tuple[datetime, datetime]]:
        """
        Calcula horários fixos para um pedido específico.

        Estratégia:
        1. Identificar última atividade PRODUTO (maior id_atividade)
        2. Colocar término dela no deadline (fim_jornada)
        3. Calcular backwards para atividades anteriores
        4. Tratar SUBPRODUTOS que devem terminar quando PRODUTO começa

        Args:
            pedido: Objeto PedidoDeProducao
            inicio_jornada: Datetime do início da jornada

        Returns:
            Dict {id_atividade: (inicio, fim)}
        """
        horarios = {}

        # Obter atividades modulares
        if not hasattr(pedido, 'atividades_modulares'):
            self.logger.warning(
                f"⚠️ Pedido {pedido.id_pedido} não possui atividades_modulares"
            )
            return horarios

        atividades = list(pedido.atividades_modulares)
        if not atividades:
            return horarios

        # Separar atividades por tipo
        atividades_produto = []
        atividades_subproduto = []

        for atividade in atividades:
            tipo_item = self._obter_tipo_item(atividade)

            if tipo_item == TipoItem.PRODUTO:
                atividades_produto.append(atividade)
            elif tipo_item == TipoItem.SUBPRODUTO:
                atividades_subproduto.append(atividade)

        # Ordenar atividades PRODUTO por id_atividade (ordem de execução backward)
        atividades_produto.sort(key=lambda a: a.id_atividade, reverse=True)

        # Deadline (fim da jornada)
        deadline = pedido.fim_jornada if hasattr(pedido, 'fim_jornada') else None
        if not deadline:
            self.logger.warning(
                f"⚠️ Pedido {pedido.id_pedido} sem deadline (fim_jornada)"
            )
            # Usar fim de jornada padrão (20 horas após início)
            deadline = inicio_jornada + timedelta(hours=20)

        # Calcular horários das atividades PRODUTO (backward scheduling)
        momento_atual = deadline

        for atividade in atividades_produto:
            duracao = self._obter_duracao_atividade(atividade)

            # Fim = momento_atual, Início = momento_atual - duração
            fim_atividade = momento_atual
            inicio_atividade = fim_atividade - duracao

            horarios[atividade.id_atividade] = (inicio_atividade, fim_atividade)

            self.logger.debug(
                f"   Atividade {atividade.id_atividade} (PRODUTO): "
                f"{inicio_atividade.strftime('%H:%M')} → "
                f"{fim_atividade.strftime('%H:%M')}"
            )

            # Próxima atividade termina quando esta começa (gap=0)
            momento_atual = inicio_atividade

        # Calcular horários dos SUBPRODUTOS
        # SUBPRODUTO deve terminar quando PRODUTO correspondente começa
        for subproduto in atividades_subproduto:
            # Encontrar PRODUTO correspondente (mesmo id_item)
            produto_correspondente = self._encontrar_produto_correspondente(
                subproduto,
                atividades_produto
            )

            if produto_correspondente and produto_correspondente.id_atividade in horarios:
                # SUBPRODUTO termina quando PRODUTO começa
                inicio_produto, _ = horarios[produto_correspondente.id_atividade]
                fim_subproduto = inicio_produto

                duracao_subproduto = self._obter_duracao_atividade(subproduto)
                inicio_subproduto = fim_subproduto - duracao_subproduto

                horarios[subproduto.id_atividade] = (inicio_subproduto, fim_subproduto)

                self.logger.debug(
                    f"   Atividade {subproduto.id_atividade} (SUBPRODUTO): "
                    f"{inicio_subproduto.strftime('%H:%M')} → "
                    f"{fim_subproduto.strftime('%H:%M')}"
                )
            else:
                self.logger.warning(
                    f"⚠️ SUBPRODUTO {subproduto.id_atividade} sem PRODUTO correspondente"
                )

        return horarios

    def _obter_tipo_item(self, atividade) -> Optional[TipoItem]:
        """Obtém o tipo do item da atividade."""
        if hasattr(atividade, 'tipo_item'):
            tipo = atividade.tipo_item
            # Se já é enum, retornar
            if isinstance(tipo, TipoItem):
                return tipo
            # Se é string, converter
            if isinstance(tipo, str):
                if 'PRODUTO' in tipo.upper():
                    return TipoItem.PRODUTO
                elif 'SUBPRODUTO' in tipo.upper():
                    return TipoItem.SUBPRODUTO
        return None

    def _obter_duracao_atividade(self, atividade) -> timedelta:
        """Obtém a duração da atividade."""
        if hasattr(atividade, 'duracao'):
            duracao = atividade.duracao
            if isinstance(duracao, timedelta):
                return duracao
            try:
                return timedelta(minutes=float(duracao))
            except (ValueError, TypeError):
                pass

        self.logger.warning(
            f"⚠️ Atividade {atividade.id_atividade} sem duração válida, usando 60min"
        )
        return timedelta(minutes=60)

    def _encontrar_produto_correspondente(
        self,
        subproduto,
        atividades_produto: List
    ):
        """
        Encontra o PRODUTO correspondente ao SUBPRODUTO.
        Usa o id_item para fazer a correspondência.
        """
        if not hasattr(subproduto, 'id_item'):
            return None

        id_item_subproduto = subproduto.id_item

        for produto in atividades_produto:
            if hasattr(produto, 'id_item') and produto.id_item == id_item_subproduto:
                return produto

        return None

    def gerar_relatorio_horarios(
        self,
        horarios_calculados: Dict[int, Dict[int, Tuple[datetime, datetime]]],
        pedidos: List
    ) -> str:
        """
        Gera relatório textual dos horários calculados.

        Args:
            horarios_calculados: Dict de horários calculados
            pedidos: Lista de pedidos

        Returns:
            String com relatório formatado
        """
        relatorio = []
        relatorio.append("📅 HORÁRIOS DETERMINÍSTICOS CALCULADOS")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Criar mapa de pedidos por ID
        mapa_pedidos = {p.id_pedido: p for p in pedidos}

        for id_pedido, horarios_atividades in sorted(horarios_calculados.items()):
            pedido = mapa_pedidos.get(id_pedido)

            relatorio.append(f"📦 Pedido {id_pedido}")

            if pedido and hasattr(pedido, 'fim_jornada'):
                relatorio.append(
                    f"   Deadline: {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}"
                )

            relatorio.append(f"   Total de atividades: {len(horarios_atividades)}")

            # Ordenar atividades por horário de início
            atividades_ordenadas = sorted(
                horarios_atividades.items(),
                key=lambda x: x[1][0]
            )

            for id_atividade, (inicio, fim) in atividades_ordenadas:
                duracao_min = int((fim - inicio).total_seconds() / 60)
                relatorio.append(
                    f"      • Atividade {id_atividade}: "
                    f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} "
                    f"({duracao_min} min)"
                )

            relatorio.append("")

        return "\n".join(relatorio)


# Função de conveniência para uso direto
def calcular_horarios_deterministicos(
    pedidos: List,
    inicio_jornada: datetime
) -> Dict[int, Dict[int, Tuple[datetime, datetime]]]:
    """
    Função de conveniência para calcular horários determinísticos.

    Args:
        pedidos: Lista de objetos PedidoDeProducao
        inicio_jornada: Datetime do início da jornada

    Returns:
        Dict {id_pedido: {id_atividade: (inicio, fim)}}
    """
    calculador = CalculadorHorariosDeterministicos()
    return calculador.calcular_horarios_fixos(pedidos, inicio_jornada)
