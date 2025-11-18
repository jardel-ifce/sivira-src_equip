"""
Executor v2.0 - Interface Simplificada
=======================================

Interface de alto nível para executar otimizações com o modelo v2.
Esconde a complexidade de adaptação de dados e configuração.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import List, Optional, Dict
from datetime import datetime

# Imports internos do v2
from otimizador_v2.adaptador_dados import AdaptadorDados, FabricaAdaptador
from otimizador_v2.otimizador_integrado_v2 import OtimizadorIntegradoV2
from otimizador_v2.modelo_pl_completo import SolucaoPLCompleta

# Imports do sistema
from models.atividades.pedido_de_producao import PedidoDeProducao
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente


class ExecutorV2:
    """
    Executor de otimizações v2.0 com interface simplificada

    Uso:
        executor = ExecutorV2()
        executor.inicializar()
        solucao = executor.otimizar_csv('data/csv/exemplo_pedidos.csv')
    """

    def __init__(self):
        self.configurador = None
        self.adaptador = None
        self.otimizador = None
        self.inicializado = False

    def inicializar(self, limpar_logs: bool = True) -> bool:
        """
        Inicializa ambiente completo para otimização

        Args:
            limpar_logs: Se True, limpa logs e comandas anteriores

        Returns:
            True se sucesso
        """
        print(f"\n{'='*80}")
        print(f"🚀 INICIALIZANDO EXECUTOR v2.0")
        print(f"{'='*80}\n")

        try:
            # 1. Configurar ambiente
            print(f"[1/3] Configurando ambiente...")
            self.configurador = ConfiguradorAmbiente()

            if not self.configurador.inicializar_ambiente():
                print(f"❌ Erro ao inicializar ambiente")
                return False

            # 2. Criar adaptador de dados
            print(f"\n[2/3] Criando adaptador de dados...")
            self.adaptador = FabricaAdaptador.criar_com_configurador(self.configurador)
            print(f"✅ Adaptador criado")

            # 3. Criar otimizador
            print(f"\n[3/3] Criando otimizador v2...")
            self.otimizador = OtimizadorIntegradoV2(self.configurador)
            print(f"✅ Otimizador v2 criado")

            self.inicializado = True

            print(f"\n{'='*80}")
            print(f"✅ EXECUTOR v2.0 PRONTO")
            print(f"{'='*80}\n")

            return True

        except Exception as e:
            print(f"❌ Erro durante inicialização: {e}")
            import traceback
            traceback.print_exc()
            return False

    def otimizar_csv(self,
                     csv_path: str,
                     timeout_segundos: int = 600,
                     resolucao_minutos: int = 30,  # OTIMIZADO: 30min para maior precisão (antes 60min)
                     limitar_pedidos: Optional[int] = None) -> Optional[SolucaoPLCompleta]:
        """
        Otimiza pedidos a partir de arquivo CSV

        Args:
            csv_path: Caminho para arquivo CSV
            timeout_segundos: Timeout para solver PL
            resolucao_minutos: Resolução temporal para discretização
            limitar_pedidos: Se fornecido, processa apenas os N primeiros pedidos

        Returns:
            Solução PL ou None em caso de erro
        """
        if not self.inicializado:
            print(f"❌ Executor não inicializado. Execute .inicializar() primeiro")
            return None

        print(f"\n{'='*80}")
        print(f"📋 OTIMIZANDO PEDIDOS DO CSV")
        print(f"{'='*80}\n")
        print(f"Arquivo: {csv_path}")
        print(f"Timeout: {timeout_segundos}s")
        print(f"Resolução: {resolucao_minutos} min")
        if limitar_pedidos:
            print(f"Limite: {limitar_pedidos} primeiros pedidos")
        print()

        try:
            # 1. Carregar pedidos do CSV
            pedidos = self.adaptador.carregar_pedidos_do_csv(csv_path)

            if not pedidos:
                print(f"❌ Nenhum pedido carregado")
                return None

            # Limitar se solicitado
            if limitar_pedidos and limitar_pedidos < len(pedidos):
                print(f"\n📊 Limitando a {limitar_pedidos} primeiros pedidos...")
                pedidos = pedidos[:limitar_pedidos]

            # 2. Executar otimização
            solucao = self.otimizador.otimizar(
                pedidos=pedidos,
                timeout_segundos=timeout_segundos,
                resolucao_minutos=resolucao_minutos
            )

            return solucao

        except Exception as e:
            print(f"❌ Erro durante otimização: {e}")
            import traceback
            traceback.print_exc()
            return None

    def otimizar_pedidos(self,
                        pedidos: List[PedidoDeProducao],
                        timeout_segundos: int = 600,
                        resolucao_minutos: int = 30,
                        aplicar_solucao: bool = True) -> Optional[SolucaoPLCompleta]:  # OTIMIZADO: 30min para maior precisão (antes 60min)
        """
        Otimiza lista de objetos PedidoDeProducao

        Args:
            pedidos: Lista de pedidos já criados
            timeout_segundos: Timeout para solver PL
            resolucao_minutos: Resolução temporal
            aplicar_solucao: Se True, aplica a solução aos pedidos reais (gera logs)

        Returns:
            Solução PL ou None em caso de erro
        """
        if not self.inicializado:
            print(f"❌ Executor não inicializado. Execute .inicializar() primeiro")
            return None

        try:
            solucao = self.otimizador.otimizar(
                pedidos=pedidos,
                timeout_segundos=timeout_segundos,
                resolucao_minutos=resolucao_minutos
            )

            # Aplicar solução aos pedidos reais se solicitado
            if solucao and aplicar_solucao and solucao.pedidos_atendidos > 0:
                print(f"\n🔄 Aplicando solução aos pedidos reais...")
                from otimizador_v2.aplicador_solucao import aplicar_solucao_pl
                aplicar_solucao_pl(solucao, pedidos)

            return solucao

        except Exception as e:
            print(f"❌ Erro durante otimização: {e}")
            import traceback
            traceback.print_exc()
            return None

    def comparar_com_baseline(self, solucao: SolucaoPLCompleta, total_pedidos: int):
        """
        Compara solução v2 com resultados dos métodos v1

        Args:
            solucao: Solução obtida pelo v2
            total_pedidos: Total de pedidos no conjunto de teste
        """
        print(f"\n{'='*80}")
        print(f"📊 COMPARAÇÃO COM MÉTODOS ANTERIORES")
        print(f"{'='*80}\n")

        if total_pedidos == 13:
            # Dados dos testes anteriores (13 pedidos)
            print(f"{'Método':<30} {'Taxa Sucesso':<15} {'Pedidos':<15} {'Tempo':<15}")
            print(f"{'-'*80}")
            print(f"{'Sequencial (v1)':<30} {'84.6%':<15} {'11/13':<15} {'0.42s':<15}")
            print(f"{'PL Original (v1)':<30} {'30.8%':<15} {'4/13':<15} {'0.51s':<15}")

            taxa_v2 = (solucao.pedidos_atendidos / total_pedidos) * 100
            print(f"{'PL Completo (v2) ✨':<30} {f'{taxa_v2:.1f}%':<15} {f'{solucao.pedidos_atendidos}/{total_pedidos}':<15} {f'{solucao.tempo_resolucao:.2f}s':<15}")
            print(f"{'-'*80}\n")

            # Análise de melhoria
            print(f"🎯 Análise de Melhoria:")
            if solucao.pedidos_atendidos >= 11:
                print(f"   ✅ EXCELENTE: v2 alcançou/superou o método sequencial!")
                print(f"   ✅ Ganho vs PL v1: +{solucao.pedidos_atendidos - 4} pedidos ({taxa_v2 - 30.8:.1f} pontos percentuais)")
            elif solucao.pedidos_atendidos > 4:
                print(f"   ✅ BOM: v2 superou o PL original")
                print(f"   ✅ Ganho vs PL v1: +{solucao.pedidos_atendidos - 4} pedidos ({taxa_v2 - 30.8:.1f} pontos percentuais)")
                print(f"   ⚠️ Gap vs Sequencial: {11 - solucao.pedidos_atendidos} pedidos")
            else:
                print(f"   ⚠️ v2 não superou o PL original")
                print(f"   💡 Possíveis causas: timeout, infactibilidade, bugs na modelagem")
        else:
            # Conjunto de teste diferente
            taxa = (solucao.pedidos_atendidos / total_pedidos) * 100
            print(f"Taxa de sucesso: {taxa:.1f}% ({solucao.pedidos_atendidos}/{total_pedidos})")
            print(f"Tempo de resolução: {solucao.tempo_resolucao:.2f}s")

        print(f"\n{'='*80}\n")

    def imprimir_resumo_solucao(self, solucao: SolucaoPLCompleta, pedidos: List[PedidoDeProducao]):
        """
        Imprime resumo detalhado da solução

        Args:
            solucao: Solução obtida
            pedidos: Lista de pedidos originais
        """
        print(f"\n{'='*80}")
        print(f"📊 RESUMO DA SOLUÇÃO")
        print(f"{'='*80}\n")

        print(f"Status Solver: {solucao.status_solver}")
        print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
        print(f"Taxa de sucesso: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
        print(f"Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
        print(f"Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

        if 'total_variaveis' in solucao.estatisticas:
            print(f"\n📊 Estatísticas do Modelo:")
            print(f"   Variáveis: {solucao.estatisticas['total_variaveis']:,}")
            print(f"   Restrições: {solucao.estatisticas['total_restricoes']:,}")

            if 'restricoes_por_tipo' in solucao.estatisticas:
                restricoes = solucao.estatisticas['restricoes_por_tipo']
                print(f"\n   Restrições por tipo:")
                print(f"      Unicidade: {restricoes.get('unicidade_pedido', 0):,}")
                print(f"      Tempo máx espera: {restricoes.get('tempo_maximo_espera', 0):,}")
                print(f"      Equipamentos: {restricoes.get('equipamentos_capacidade', 0):,}")
                print(f"      Conflitos: {restricoes.get('conflitos_temporais', 0):,}")

        # Pedidos executados
        if solucao.pedidos_atendidos > 0:
            print(f"\n✅ Pedidos EXECUTADOS ({solucao.pedidos_atendidos}):")
            pedidos_dict = {p.id_pedido: p for p in pedidos}

            for pedido_id in sorted(solucao.pedidos_selecionados.keys()):
                janela = solucao.janelas_selecionadas[pedido_id]
                pedido = pedidos_dict.get(pedido_id)

                # Obter nome do pedido
                if pedido:
                    if hasattr(pedido, 'ficha_tecnica_modular') and pedido.ficha_tecnica_modular:
                        nome = pedido.ficha_tecnica_modular.nome
                    else:
                        nome = f"Produto {pedido.id_produto}"
                else:
                    nome = f"Pedido {pedido_id}"

                print(f"   • {nome}: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")
        else:
            print(f"\n❌ Nenhum pedido executado")

        # Pedidos NÃO executados
        pedidos_falharam = [p for p in pedidos if p.id_pedido not in solucao.pedidos_selecionados]
        if pedidos_falharam:
            print(f"\n❌ Pedidos NÃO executados ({len(pedidos_falharam)}):")
            for pedido in pedidos_falharam[:10]:  # Mostrar no máximo 10
                # Obter nome do pedido
                if hasattr(pedido, 'ficha_tecnica_modular') and pedido.ficha_tecnica_modular:
                    nome = pedido.ficha_tecnica_modular.nome
                else:
                    nome = f"Produto {pedido.id_produto}"
                print(f"   • Pedido {pedido.id_pedido} ({nome})")
            if len(pedidos_falharam) > 10:
                print(f"   ... e mais {len(pedidos_falharam)-10}")

        print(f"\n{'='*80}\n")


# Função de conveniência para execução rápida
def executar_otimizacao_rapida(csv_path: str,
                               timeout: int = 600,
                               limitar: Optional[int] = None) -> Optional[SolucaoPLCompleta]:
    """
    Executa otimização completa com uma única chamada

    Args:
        csv_path: Caminho para CSV
        timeout: Timeout em segundos
        limitar: Limitar aos N primeiros pedidos

    Returns:
        Solução ou None
    """
    executor = ExecutorV2()

    if not executor.inicializar():
        return None

    return executor.otimizar_csv(csv_path, timeout_segundos=timeout, limitar_pedidos=limitar)
