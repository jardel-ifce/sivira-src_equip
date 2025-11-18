"""
Otimizador Integrado v2.0 - Usa Modelo PL COMPLETO
===================================================

Integra o modelo PL completo (com todas as restrições) ao pipeline de execução.
Usa a mesma estrutura de extração de dados e geração de janelas do otimizador v1,
mas aplica o modelo corrigido.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Imports do otimizador v1 (extração e janelas)
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos, DadosPedido
from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais, JanelaTemporal

# Import do modelo v2
from otimizador_v2.modelo_pl_completo import ModeloPLCompleto, SolucaoPLCompleta

# Imports de serviços
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente
from models.atividades.pedido_de_producao import PedidoDeProducao


class OtimizadorIntegradoV2:
    """
    Otimizador integrado que usa o modelo PL COMPLETO v2.0

    Fluxo:
    1. Extrai dados dos pedidos
    2. Gera janelas temporais viáveis
    3. Resolve modelo PL COMPLETO (com todas as restrições)
    4. Retorna solução
    """

    def __init__(self, configurador_ambiente: ConfiguradorAmbiente):
        self.configurador = configurador_ambiente
        self.extrator = ExtratorDadosPedidos()  # Não recebe configurador
        self.gerador_janelas = None
        self.modelo_pl = None

        print(f"🚀 Otimizador Integrado v2.0 inicializado")
        print(f"   ✅ Modelo PL COMPLETO com TODAS as restrições")

    def otimizar(self,
                 pedidos: List[PedidoDeProducao],
                 timeout_segundos: int = 600,
                 resolucao_minutos: int = 60) -> SolucaoPLCompleta:
        """
        Otimiza conjunto de pedidos usando modelo PL COMPLETO

        Args:
            pedidos: Lista de pedidos a otimizar
            timeout_segundos: Timeout para resolução do PL
            resolucao_minutos: Resolução temporal (para discretização)

        Returns:
            Solução PL completa
        """

        print(f"\n{'='*70}")
        print(f"🎯 OTIMIZAÇÃO v2.0 - MODELO PL COMPLETO")
        print(f"{'='*70}")
        print(f"📋 Pedidos a processar: {len(pedidos)}")
        print(f"⏱️ Timeout: {timeout_segundos}s")
        print(f"📊 Resolução temporal: {resolucao_minutos} min")
        print(f"")

        inicio_total = time.time()

        # ETAPA 1: Extração de dados
        print(f"\n📥 [1/3] Extraindo dados dos pedidos...")
        dados_pedidos = self._extrair_dados(pedidos)

        if not dados_pedidos:
            print(f"❌ Nenhum pedido válido para processar")
            return self._criar_solucao_vazia()

        print(f"   ✅ {len(dados_pedidos)} pedidos extraídos")

        # ETAPA 2: Geração de janelas temporais
        print(f"\n🪟 [2/3] Gerando janelas temporais...")
        janelas_por_pedido, pedidos_com_fim_obrigatorio = self._gerar_janelas(dados_pedidos, resolucao_minutos)

        total_janelas = sum(len(j) for j in janelas_por_pedido.values())
        janelas_viaveis = sum(len([x for x in j if x.viavel]) for j in janelas_por_pedido.values())

        print(f"   ✅ {total_janelas} janelas geradas ({janelas_viaveis} viáveis)")

        if janelas_viaveis == 0:
            print(f"❌ Nenhuma janela viável gerada")
            return self._criar_solucao_vazia()

        # ETAPA 3: Resolução do modelo PL COMPLETO
        print(f"\n🧮 [3/3] Resolvendo modelo PL COMPLETO...")
        solucao = self._resolver_modelo_pl(dados_pedidos, janelas_por_pedido,
                                          timeout_segundos, resolucao_minutos,
                                          pedidos_com_fim_obrigatorio)

        tempo_total = time.time() - inicio_total

        print(f"\n{'='*70}")
        print(f"✅ OTIMIZAÇÃO CONCLUÍDA")
        print(f"{'='*70}")
        print(f"⏱️ Tempo total: {tempo_total:.2f}s")
        print(f"📊 Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
        print(f"{'='*70}\n")

        return solucao

    def _extrair_dados(self, pedidos: List[PedidoDeProducao]) -> List[DadosPedido]:
        """Extrai dados dos pedidos"""
        try:
            # ExtratorDadosPedidos.extrair_dados() recebe lista completa de pedidos
            dados_pedidos = self.extrator.extrair_dados(pedidos)
            print(f"   ✅ {len(dados_pedidos)} pedidos extraídos com sucesso")
            return dados_pedidos
        except Exception as e:
            print(f"   ❌ Erro ao extrair dados: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _gerar_janelas(self, dados_pedidos: List[DadosPedido], resolucao_minutos: int) -> tuple[Dict[int, List[JanelaTemporal]], Dict[int, datetime]]:
        """Gera janelas temporais para todos os pedidos

        Returns:
            tuple: (janelas_por_pedido, pedidos_com_fim_obrigatorio)
        """

        # ✅ NOVO: Detectar pedidos com fim obrigatório
        pedidos_com_fim_obrigatorio = {}

        print(f"\n🔍 Analisando fins obrigatórios (última atividade PRODUTO com tempo_maximo_espera = 0)...")

        for dados_pedido in dados_pedidos:
            if dados_pedido.atividades:
                # ✅ CORREÇÃO CRÍTICA: Filtrar apenas atividades do tipo PRODUTO
                # (não incluir atividades de SUBPRODUTO que podem vir depois)
                atividades_produto = [
                    a for a in dados_pedido.atividades
                    if hasattr(a, 'tipo_item') and str(a.tipo_item) == 'TipoItem.PRODUTO'
                ]

                if not atividades_produto:
                    print(f"   ⚠️ Pedido {dados_pedido.id_pedido}: sem atividades de PRODUTO encontradas")
                    continue

                # IMPORTANTE: Sistema usa backward scheduling com ordenação REVERSA por id_atividade
                # Então MAIOR id_atividade = ÚLTIMA a executar = deve terminar no deadline
                ultima_atividade_produto = max(atividades_produto, key=lambda a: a.id_atividade)

                # Verificar tempo_maximo_espera
                if hasattr(ultima_atividade_produto, 'tempo_maximo_espera') and ultima_atividade_produto.tempo_maximo_espera == timedelta(0):
                    # Marcar como fim obrigatório
                    pedidos_com_fim_obrigatorio[dados_pedido.id_pedido] = dados_pedido.fim_jornada
                    print(f"   ⚠️ Pedido {dados_pedido.id_pedido} ({dados_pedido.nome_produto}): FIM OBRIGATÓRIO às {dados_pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                    print(f"      (última ativ. PRODUTO: ID {ultima_atividade_produto.id_atividade})")
                else:
                    espera = ultima_atividade_produto.tempo_maximo_espera if hasattr(ultima_atividade_produto, 'tempo_maximo_espera') else 'N/A'
                    print(f"   ✅ Pedido {dados_pedido.id_pedido} ({dados_pedido.nome_produto}): flexível (espera: {espera})")

        total_obrigatorios = len(pedidos_com_fim_obrigatorio)
        total_flexiveis = len(dados_pedidos) - total_obrigatorios

        print(f"\n📊 Resumo de fins obrigatórios:")
        print(f"   Pedidos com fim obrigatório: {total_obrigatorios}/{len(dados_pedidos)}")
        print(f"   Pedidos com horário flexível: {total_flexiveis}/{len(dados_pedidos)}")

        # Criar gerador de janelas
        self.gerador_janelas = GeradorJanelasTemporais(
            resolucao_minutos=resolucao_minutos
        )

        # ✅ CORRETO: Chamar método com fins obrigatórios detectados
        janelas_por_pedido = self.gerador_janelas.gerar_janelas_todos_pedidos(
            dados_pedidos=dados_pedidos,
            pedidos_com_fim_obrigatorio=pedidos_com_fim_obrigatorio  # ✅ NOVO: passa dicionário real
        )

        # Mostrar resumo de janelas geradas
        for pedido_id, janelas in janelas_por_pedido.items():
            viaveis = len([j for j in janelas if j.viavel])
            fim_obrig = "🎯 FIM OBRIG" if pedido_id in pedidos_com_fim_obrigatorio else ""
            print(f"   Pedido {pedido_id}: {len(janelas)} janelas ({viaveis} viáveis) {fim_obrig}")

        return janelas_por_pedido, pedidos_com_fim_obrigatorio

    def _resolver_modelo_pl(self,
                           dados_pedidos: List[DadosPedido],
                           janelas_por_pedido: Dict[int, List[JanelaTemporal]],
                           timeout_segundos: int,
                           resolucao_minutos: int,
                           pedidos_com_fim_obrigatorio: Dict[int, datetime]) -> SolucaoPLCompleta:
        """Resolve modelo PL completo com fins obrigatórios"""

        # Criar modelo PL completo
        self.modelo_pl = ModeloPLCompleto(
            dados_pedidos=dados_pedidos,
            janelas_por_pedido=janelas_por_pedido,
            configuracao_tempo=None,  # ✅ CORRETO: ModeloPLCompleto calcula horizonte das janelas
            resolucao_minutos=resolucao_minutos,
            pedidos_com_fim_obrigatorio=pedidos_com_fim_obrigatorio  # ✅ NOVO
        )

        # Resolver
        solucao = self.modelo_pl.resolver(timeout_segundos=timeout_segundos)

        return solucao

    def _criar_solucao_vazia(self) -> SolucaoPLCompleta:
        """Cria solução vazia"""
        return SolucaoPLCompleta(
            pedidos_atendidos=0,
            pedidos_selecionados={},
            janelas_selecionadas={},
            tempo_resolucao=0.0,
            status_solver="EMPTY",
            objetivo_otimo=0.0,
            estatisticas={
                'pedidos_totais': 0,
                'pedidos_atendidos': 0,
                'taxa_atendimento': 0.0
            }
        )


def criar_otimizador_v2(configurador_ambiente: ConfiguradorAmbiente) -> OtimizadorIntegradoV2:
    """Factory function para criar otimizador v2"""
    return OtimizadorIntegradoV2(configurador_ambiente)
