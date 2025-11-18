"""
Adaptador de Dados - Otimizador v2.0
=====================================

Módulo de interface que adapta diferentes fontes de dados de pedidos
para o formato esperado pelo otimizador v2.

Resolve incompatibilidades entre:
- PedidoDeProducao (objeto do sistema)
- DadosPedido (objeto do extrator)
- CSV (arquivo de entrada)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd

# Imports do sistema
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from enums.producao.tipo_item import TipoItem

# Imports do otimizador
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos, DadosPedido


class AdaptadorDados:
    """
    Adaptador que converte diferentes formatos de entrada em DadosPedido
    """

    def __init__(self, gestor_almoxarifado: Optional[GestorAlmoxarifado] = None):
        self.gestor_almoxarifado = gestor_almoxarifado
        self.extrator = ExtratorDadosPedidos()

    def carregar_pedidos_do_csv(self, csv_path: str) -> List[PedidoDeProducao]:
        """
        Carrega pedidos a partir de arquivo CSV

        Formato CSV esperado:
        - id: ID do produto
        - tipo_produto: PRODUTO
        - quantidade: Quantidade a produzir
        - fim_jornada: Data/hora de entrega (YYYY-MM-DD HH:MM:SS)

        Returns:
            Lista de objetos PedidoDeProducao prontos para otimização
        """
        if not self.gestor_almoxarifado:
            raise ValueError("AdaptadorDados precisa de gestor_almoxarifado para criar pedidos do CSV")

        print(f"\n📥 Carregando pedidos de {csv_path}...")

        df = pd.read_csv(csv_path)
        print(f"✅ {len(df)} linhas carregadas do CSV")

        pedidos = []

        for idx, row in df.iterrows():
            try:
                # Extrair dados do CSV
                id_produto = int(row['id'])
                quantidade = int(row['quantidade'])
                fim_jornada = datetime.strptime(row['fim_jornada'], '%Y-%m-%d %H:%M:%S')
                inicio_jornada = fim_jornada - timedelta(days=3)  # 3 dias de antecedência

                # Criar pedido
                pedido = PedidoDeProducao(
                    id_ordem=1,
                    id_pedido=idx + 1,
                    id_produto=id_produto,
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=quantidade,
                    inicio_jornada=inicio_jornada,
                    fim_jornada=fim_jornada,
                    gestor_almoxarifado=self.gestor_almoxarifado
                )

                # Montar estrutura (carrega atividades, subprodutos, etc)
                pedido.montar_estrutura()
                pedido.criar_atividades_modulares_necessarias()

                pedidos.append(pedido)

                print(f"✅ Pedido {idx+1} ({id_produto}): {quantidade} uni, prazo {fim_jornada.strftime('%d/%m %H:%M')}")

            except Exception as e:
                print(f"❌ Erro ao criar pedido {idx+1}: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n📊 Total: {len(pedidos)}/{len(df)} pedidos criados com sucesso")
        return pedidos

    def extrair_dados_de_pedidos(self, pedidos: List[PedidoDeProducao]) -> List[DadosPedido]:
        """
        Extrai dados de objetos PedidoDeProducao para formato DadosPedido

        Args:
            pedidos: Lista de objetos PedidoDeProducao

        Returns:
            Lista de objetos DadosPedido prontos para o otimizador
        """
        print(f"\n📤 Extraindo dados de {len(pedidos)} pedidos...")

        # Usar extrator existente
        dados_pedidos = self.extrator.extrair_dados(pedidos)

        print(f"✅ {len(dados_pedidos)} conjuntos de dados extraídos")

        return dados_pedidos

    def pipeline_completo_csv(self, csv_path: str) -> tuple[List[PedidoDeProducao], List[DadosPedido]]:
        """
        Pipeline completo: CSV -> PedidoDeProducao -> DadosPedido

        Args:
            csv_path: Caminho para arquivo CSV

        Returns:
            (pedidos_originais, dados_extraidos)
        """
        # 1. Carregar do CSV
        pedidos = self.carregar_pedidos_do_csv(csv_path)

        if not pedidos:
            return [], []

        # 2. Extrair dados
        dados = self.extrair_dados_de_pedidos(pedidos)

        return pedidos, dados


class FabricaAdaptador:
    """
    Factory para criar adaptadores com configuração correta
    """

    @staticmethod
    def criar_com_almoxarifado_padrao() -> AdaptadorDados:
        """
        Cria adaptador com almoxarifado padrão do sistema
        """
        print(f"🏪 Inicializando almoxarifado padrão...")

        # Carregar itens
        itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")

        # Criar almoxarifado
        almoxarifado = Almoxarifado()
        for item in itens:
            almoxarifado.adicionar_item(item)

        # Criar gestor
        gestor = GestorAlmoxarifado(almoxarifado)

        print(f"✅ Almoxarifado criado com {len(itens)} itens")

        return AdaptadorDados(gestor_almoxarifado=gestor)

    @staticmethod
    def criar_com_configurador(configurador) -> AdaptadorDados:
        """
        Cria adaptador usando ConfiguradorAmbiente existente
        """
        if not hasattr(configurador, 'gestor_almoxarifado'):
            raise ValueError("Configurador não possui gestor_almoxarifado")

        return AdaptadorDados(gestor_almoxarifado=configurador.gestor_almoxarifado)


# Funções de conveniência para uso direto
def carregar_pedidos_csv(csv_path: str, gestor_almoxarifado: GestorAlmoxarifado) -> List[PedidoDeProducao]:
    """Função de conveniência para carregar pedidos do CSV"""
    adaptador = AdaptadorDados(gestor_almoxarifado)
    return adaptador.carregar_pedidos_do_csv(csv_path)


def extrair_dados_pedidos(pedidos: List[PedidoDeProducao]) -> List[DadosPedido]:
    """Função de conveniência para extrair dados de pedidos"""
    adaptador = AdaptadorDados()
    return adaptador.extrair_dados_de_pedidos(pedidos)
