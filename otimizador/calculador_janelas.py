"""
Calculador de Janelas Flexiveis
===============================

Calcula janelas temporais [inicio_min, inicio_max] para cada atividade
usando o tempo_maximo_de_espera (tau_max).

Algoritmo Backward:
1. Ultima atividade termina no deadline
2. Para cada atividade anterior:
   - fim_mais_tarde = inicio_mais_cedo_sucessora
   - fim_mais_cedo = fim_mais_tarde - tau_max_sucessora
   - inicio = fim - duracao

Criado em: 23/12/2025
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger('CalculadorJanelas')


@dataclass
class JanelaFlexivel:
    """Representa uma janela temporal flexivel para uma atividade."""
    id_atividade: int
    nome_atividade: str
    inicio_mais_cedo: datetime
    inicio_mais_tarde: datetime
    fim_mais_cedo: datetime
    fim_mais_tarde: datetime
    duracao: timedelta
    tau_max: timedelta

    @property
    def flexibilidade(self) -> timedelta:
        """Quantidade de flexibilidade (janela) disponivel em minutos."""
        return self.inicio_mais_tarde - self.inicio_mais_cedo

    @property
    def flexibilidade_minutos(self) -> float:
        """Flexibilidade em minutos."""
        return self.flexibilidade.total_seconds() / 60

    def __repr__(self):
        return (
            f"JanelaFlexivel(id={self.id_atividade}, "
            f"inicio=[{self.inicio_mais_cedo.strftime('%H:%M')}, {self.inicio_mais_tarde.strftime('%H:%M')}], "
            f"flex={self.flexibilidade_minutos:.0f}min)"
        )


class CalculadorJanelas:
    """
    Calcula janelas temporais usando backward scheduling com tau_max.

    Para cada atividade, determina:
    - Quando pode comecar mais cedo (inicio_mais_cedo)
    - Quando pode comecar mais tarde (inicio_mais_tarde)
    - Quando deve terminar mais cedo (fim_mais_cedo)
    - Quando deve terminar mais tarde (fim_mais_tarde)
    """

    def __init__(self):
        self.logger = setup_logger('CalculadorJanelas')

    def calcular(
        self,
        pedidos: List,
        inicio_jornada: datetime
    ) -> Dict[int, Dict[int, JanelaFlexivel]]:
        """
        Calcula janelas flexiveis para todas atividades de todos pedidos.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            inicio_jornada: Datetime do inicio da jornada

        Returns:
            Dict {id_pedido: {id_atividade: JanelaFlexivel}}
        """
        self.logger.info(f"Calculando janelas flexiveis para {len(pedidos)} pedidos...")

        resultado = {}

        for pedido in pedidos:
            self.logger.info(f"   Processando pedido {pedido.id_pedido}...")
            janelas_pedido = self._calcular_pedido(pedido, inicio_jornada)
            resultado[pedido.id_pedido] = janelas_pedido

            # Log resumo
            total_flex = sum(j.flexibilidade_minutos for j in janelas_pedido.values())
            self.logger.info(
                f"   Pedido {pedido.id_pedido}: {len(janelas_pedido)} janelas, "
                f"flexibilidade total: {total_flex:.0f} min"
            )

        return resultado

    def _calcular_pedido(
        self,
        pedido,
        inicio_jornada: datetime
    ) -> Dict[int, JanelaFlexivel]:
        """
        Calcula janelas para um pedido usando backward scheduling.

        Separa atividades de PRODUTO e SUBPRODUTO e calcula janelas
        para cada grupo.
        """
        from enums.producao.tipo_item import TipoItem

        janelas = {}
        deadline = pedido.fim_jornada

        # Separar atividades por tipo
        atividades_produto = [
            a for a in pedido.atividades_modulares
            if a.tipo_item == TipoItem.PRODUTO
        ]
        atividades_subproduto = [
            a for a in pedido.atividades_modulares
            if a.tipo_item == TipoItem.SUBPRODUTO
        ]

        # Ordenar por id_atividade (decrescente para backward)
        atividades_produto.sort(key=lambda a: a.id_atividade, reverse=True)

        # Calcular janelas para PRODUTO
        if atividades_produto:
            janelas_produto = self._calcular_janelas_grupo(
                atividades_produto,
                deadline,
                inicio_jornada,
                "PRODUTO"
            )
            janelas.update(janelas_produto)

        # Calcular janelas para SUBPRODUTOS
        # Subprodutos devem terminar quando o primeiro PRODUTO comeca
        if atividades_subproduto and janelas:
            # Encontrar inicio mais cedo do primeiro PRODUTO
            if atividades_produto:
                primeiro_produto_id = min(a.id_atividade for a in atividades_produto)
                deadline_subprodutos = janelas[primeiro_produto_id].inicio_mais_cedo
            else:
                deadline_subprodutos = deadline

            # Agrupar subprodutos por id_item (cada subproduto e um grupo)
            grupos_subproduto = self._agrupar_subprodutos(atividades_subproduto)

            for nome_grupo, atividades_grupo in grupos_subproduto.items():
                atividades_grupo.sort(key=lambda a: a.id_atividade, reverse=True)
                janelas_grupo = self._calcular_janelas_grupo(
                    atividades_grupo,
                    deadline_subprodutos,
                    inicio_jornada,
                    f"SUBPRODUTO_{nome_grupo}"
                )
                janelas.update(janelas_grupo)

        return janelas

    def _calcular_janelas_grupo(
        self,
        atividades: List,
        deadline: datetime,
        inicio_jornada: datetime,
        nome_grupo: str
    ) -> Dict[int, JanelaFlexivel]:
        """
        Calcula janelas para um grupo de atividades usando backward scheduling.

        Algoritmo:
        1. Ultima atividade deve terminar no deadline
        2. Para cada atividade anterior:
           - fim_mais_tarde = inicio_mais_cedo_sucessora
           - fim_mais_cedo = fim_mais_tarde - tau_max (da SUCESSORA, pois e o gap permitido antes dela)
           - inicio = fim - duracao
        """
        janelas = {}
        fim_mais_tarde = deadline

        self.logger.debug(f"      Calculando janelas para grupo {nome_grupo} ({len(atividades)} atividades)")

        for i, atividade in enumerate(atividades):
            duracao = atividade.duracao
            nome_atividade = getattr(atividade, 'nome_atividade', f'ativ_{atividade.id_atividade}')

            # Obter tau_max da atividade
            tau_max = getattr(atividade, 'tempo_maximo_de_espera', None)
            if tau_max is None:
                tau_max = timedelta(0)
            elif not isinstance(tau_max, timedelta):
                # Converter se for string ou outro tipo
                try:
                    if isinstance(tau_max, str):
                        partes = tau_max.split(':')
                        tau_max = timedelta(
                            hours=int(partes[0]),
                            minutes=int(partes[1]),
                            seconds=int(partes[2]) if len(partes) > 2 else 0
                        )
                    else:
                        tau_max = timedelta(0)
                except Exception:
                    tau_max = timedelta(0)

            if i == 0:
                # Ultima atividade: deve terminar exatamente no deadline
                fim_mais_cedo_ativ = deadline
                fim_mais_tarde_ativ = deadline
            else:
                # Atividades anteriores: podem terminar ate tau_max antes da sucessora comecar
                # tau_max usado aqui e o da SUCESSORA (atividades[i-1])
                sucessora = atividades[i - 1]
                tau_max_sucessora = getattr(sucessora, 'tempo_maximo_de_espera', None)
                if tau_max_sucessora is None or not isinstance(tau_max_sucessora, timedelta):
                    tau_max_sucessora = timedelta(0)

                fim_mais_tarde_ativ = fim_mais_tarde
                fim_mais_cedo_ativ = fim_mais_tarde - tau_max_sucessora

            # Garantir nao ultrapassar inicio da jornada
            fim_mais_cedo_ativ = max(fim_mais_cedo_ativ, inicio_jornada + duracao)

            # Calcular inicios
            inicio_mais_tarde = fim_mais_tarde_ativ - duracao
            inicio_mais_cedo = fim_mais_cedo_ativ - duracao

            # Garantir inicio nao negativo
            inicio_mais_cedo = max(inicio_mais_cedo, inicio_jornada)
            inicio_mais_tarde = max(inicio_mais_tarde, inicio_jornada)

            # Garantir coerencia (inicio_mais_cedo <= inicio_mais_tarde)
            if inicio_mais_cedo > inicio_mais_tarde:
                inicio_mais_cedo = inicio_mais_tarde

            janela = JanelaFlexivel(
                id_atividade=atividade.id_atividade,
                nome_atividade=nome_atividade,
                inicio_mais_cedo=inicio_mais_cedo,
                inicio_mais_tarde=inicio_mais_tarde,
                fim_mais_cedo=fim_mais_cedo_ativ,
                fim_mais_tarde=fim_mais_tarde_ativ,
                duracao=duracao,
                tau_max=tau_max
            )

            janelas[atividade.id_atividade] = janela

            self.logger.debug(
                f"         Ativ {atividade.id_atividade}: "
                f"inicio=[{inicio_mais_cedo.strftime('%H:%M')}, {inicio_mais_tarde.strftime('%H:%M')}], "
                f"fim=[{fim_mais_cedo_ativ.strftime('%H:%M')}, {fim_mais_tarde_ativ.strftime('%H:%M')}], "
                f"flex={janela.flexibilidade_minutos:.0f}min"
            )

            # Atualizar para proxima iteracao (atividade anterior)
            fim_mais_tarde = inicio_mais_cedo

        return janelas

    def _agrupar_subprodutos(self, atividades_subproduto: List) -> Dict[str, List]:
        """
        Agrupa atividades de subproduto por id_item.

        Cada subproduto (ex: massa_crocante, frango_refogado) e um grupo separado.
        """
        grupos = {}

        for atividade in atividades_subproduto:
            id_item = getattr(atividade, 'id_item', 0)
            nome_item = getattr(atividade, 'nome_item', f'subprod_{id_item}')

            if nome_item not in grupos:
                grupos[nome_item] = []

            grupos[nome_item].append(atividade)

        return grupos

    def imprimir_janelas(self, janelas: Dict[int, Dict[int, JanelaFlexivel]]):
        """Imprime resumo das janelas calculadas."""
        print("\n" + "=" * 70)
        print("JANELAS FLEXIVEIS CALCULADAS")
        print("=" * 70)

        for id_pedido, janelas_pedido in janelas.items():
            print(f"\nPedido {id_pedido}:")

            for id_atividade, janela in sorted(janelas_pedido.items()):
                print(
                    f"   Ativ {id_atividade} ({janela.nome_atividade[:30]}): "
                    f"inicio=[{janela.inicio_mais_cedo.strftime('%H:%M')}, {janela.inicio_mais_tarde.strftime('%H:%M')}], "
                    f"flex={janela.flexibilidade_minutos:.0f}min"
                )

        print("\n" + "=" * 70)
