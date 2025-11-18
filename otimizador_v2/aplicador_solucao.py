"""
Aplicador de Solução PL v2.0
============================

Aplica a solução teórica do PL v2.0 aos pedidos reais,
executando as alocações de equipamentos e gerando logs.
"""

from datetime import datetime
from typing import List, Dict, Optional
from models.atividades.pedido_de_producao import PedidoDeProducao
from otimizador_v2.modelo_pl_completo import SolucaoPLCompleta


class AplicadorSolucao:
    """
    Aplica a solução do PL v2.0 aos pedidos reais,
    executando as atividades e salvando logs.
    """

    def __init__(self):
        self.pedidos_executados = []
        self.erros = []

    def aplicar_solucao(
        self,
        solucao: SolucaoPLCompleta,
        pedidos: List[PedidoDeProducao]
    ) -> Dict:
        """
        Aplica a solução PL aos pedidos reais

        Args:
            solucao: Solução retornada pelo otimizador
            pedidos: Lista de pedidos originais

        Returns:
            Dicionário com estatísticas da aplicação
        """
        print("\n" + "="*80)
        print("📋 APLICANDO SOLUÇÃO PL v2.0 AOS PEDIDOS REAIS")
        print("="*80)

        # Criar mapa de pedidos por ID
        pedidos_map = {p.id_pedido: p for p in pedidos}

        # Estatísticas
        stats = {
            'total_pedidos': len(pedidos),
            'pedidos_executados': 0,
            'pedidos_falhou': 0,
            'atividades_executadas': 0,
            'atividades_falharam': 0
        }

        # Processar cada pedido na solução
        for pedido_id, janela in solucao.janelas_selecionadas.items():
            pedido = pedidos_map.get(pedido_id)

            if not pedido:
                print(f"⚠️ Pedido {pedido_id} não encontrado na lista original")
                continue

            print(f"\n🔄 Aplicando solução para Pedido {pedido_id} ({pedido.ficha_tecnica_modular.nome})...")
            print(f"   Janela: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")

            sucesso = self._executar_pedido(pedido, janela.datetime_inicio, janela.datetime_fim)

            if sucesso:
                stats['pedidos_executados'] += 1
                self.pedidos_executados.append(pedido_id)
                print(f"   ✅ Pedido {pedido_id} executado com sucesso")
            else:
                stats['pedidos_falhou'] += 1
                print(f"   ❌ Falha ao executar Pedido {pedido_id}")

        # Resumo
        print("\n" + "="*80)
        print("📊 RESUMO DA APLICAÇÃO")
        print("="*80)
        print(f"Total de pedidos: {stats['total_pedidos']}")
        print(f"Pedidos executados: {stats['pedidos_executados']}")
        print(f"Pedidos falharam: {stats['pedidos_falhou']}")
        print(f"Taxa de sucesso: {(stats['pedidos_executados']/stats['total_pedidos']*100):.1f}%")
        print("="*80 + "\n")

        return stats

    def _executar_pedido(
        self,
        pedido: PedidoDeProducao,
        inicio_pedido: datetime,
        fim_pedido: datetime
    ) -> bool:
        """
        Executa as atividades de um pedido sequencialmente

        Args:
            pedido: Pedido a ser executado
            inicio_pedido: Horário de início do pedido
            fim_pedido: Horário de término do pedido

        Returns:
            True se todas as atividades foram executadas com sucesso
        """
        try:
            # Percorrer todas as atividades do pedido em ordem
            inicio_atual = inicio_pedido

            for atividade in pedido.atividades_modulares:
                # Calcular fim da atividade
                fim_atividade = inicio_atual + atividade.duracao

                # Verificar se cabe no prazo do pedido
                if fim_atividade > fim_pedido:
                    print(f"      ⚠️ Atividade {atividade.id_atividade} não cabe no prazo")
                    return False

                # Tentar alocar equipamentos para a atividade
                sucesso = self._alocar_atividade(atividade, inicio_atual, fim_atividade)

                if not sucesso:
                    print(f"      ❌ Falha ao alocar Atividade {atividade.id_atividade}")
                    return False

                # Próxima atividade começa quando esta termina
                inicio_atual = fim_atividade

            return True

        except Exception as e:
            print(f"      ❌ Erro ao executar pedido {pedido.id_pedido}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _alocar_atividade(
        self,
        atividade,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Aloca equipamentos para uma atividade

        Args:
            atividade: Atividade a ser alocada
            inicio: Horário de início
            fim: Horário de término

        Returns:
            True se alocação foi bem-sucedida
        """
        try:
            # Chamar método de alocação da atividade
            # Isso irá registrar os logs automaticamente via _registrar_sucesso_equipamentos
            resultado = atividade.tentar_alocar_e_iniciar_equipamentos(
                inicio_jornada=inicio,
                fim_jornada=fim
            )

            # resultado = (sucesso, inicio_real, fim_real, tempo_max_espera, equipamentos_alocados)
            if resultado[0]:  # sucesso
                print(f"         ✅ Atividade {atividade.id_atividade} alocada: {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}")
                return True
            else:
                print(f"         ❌ Atividade {atividade.id_atividade} falhou na alocação")
                return False

        except Exception as e:
            print(f"         ❌ Erro ao alocar atividade {atividade.id_atividade}: {e}")
            import traceback
            traceback.print_exc()
            return False


def aplicar_solucao_pl(
    solucao: SolucaoPLCompleta,
    pedidos: List[PedidoDeProducao]
) -> Dict:
    """
    Função auxiliar para aplicar solução PL

    Args:
        solucao: Solução do PL v2.0
        pedidos: Lista de pedidos originais

    Returns:
        Estatísticas da aplicação
    """
    aplicador = AplicadorSolucao()
    return aplicador.aplicar_solucao(solucao, pedidos)
