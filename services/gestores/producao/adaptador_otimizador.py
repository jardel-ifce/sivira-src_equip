"""
Adaptador para Otimizador Integrado
===================================

Adapta a interface entre OtimizadorIntegrado e ExecutorPedidos,
permitindo que o otimizador PL execute pedidos individuais.
"""


class AdaptadorSistemaProducao:
    """
    Adaptador para permitir que OtimizadorIntegrado use ExecutorPedidos.

    O OtimizadorIntegrado espera um objeto com método _executar_pedido_individual().
    Esta classe fornece essa interface.
    """

    def __init__(self):
        """Inicializa o adaptador"""
        self.pedidos_executados = []
        self.pedidos_falhados = []
        print("🔌 AdaptadorSistemaProducao inicializado")

    def _executar_pedido_individual(self, pedido):
        """
        Executa um pedido individual (chamado pelo OtimizadorIntegrado).

        Args:
            pedido: PedidoDeProducao a executar

        Raises:
            RuntimeError: Se execução falhar
        """
        try:
            print(f"   🔄 Executando pedido {pedido.id_pedido} via adaptador...")

            # PASSO 1: Gerar comanda (se disponível)
            self._gerar_comanda(pedido)

            # PASSO 2: Criar atividades
            print(f"      🏗️ Criando atividades modulares...")
            pedido.criar_atividades_modulares_necessarias()

            if not pedido.atividades_modulares:
                raise RuntimeError(f"Nenhuma atividade criada para pedido {pedido.id_pedido}")

            print(f"      ✅ {len(pedido.atividades_modulares)} atividades criadas")

            # PASSO 3: Executar atividades (gera logs de equipamentos)
            print(f"      ⚡ Executando atividades em ordem...")
            pedido.executar_atividades_em_ordem()

            print(f"      ✅ Pedido {pedido.id_pedido} executado com sucesso!")
            self.pedidos_executados.append(pedido.id_pedido)

        except RuntimeError as e:
            # RuntimeError deve ser propagado para o OtimizadorIntegrado
            print(f"      ❌ RuntimeError no pedido {pedido.id_pedido}: {e}")
            self.pedidos_falhados.append((pedido.id_pedido, str(e)))
            raise

        except Exception as e:
            # Outros erros também devem ser propagados
            print(f"      ❌ Erro no pedido {pedido.id_pedido}: {e}")
            self.pedidos_falhados.append((pedido.id_pedido, str(e)))
            raise RuntimeError(f"Falha na execução do pedido {pedido.id_pedido}: {e}")

    def _gerar_comanda(self, pedido):
        """
        Gera comanda para o pedido (se módulo disponível).

        Args:
            pedido: PedidoDeProducao
        """
        try:
            from services.gestores.comandas.gestor_comandas import gerar_comanda_reserva

            print(f"      📋 Gerando comanda...")
            gerar_comanda_reserva(
                id_ordem=pedido.id_ordem,
                id_pedido=pedido.id_pedido,
                ficha=pedido.ficha_tecnica_modular,
                gestor=pedido.gestor_almoxarifado,
                data_execucao=pedido.fim_jornada
            )
            print(f"      ✅ Comanda gerada: data/comandas/comanda_ordem_{pedido.id_ordem}_pedido_{pedido.id_pedido}.json")

        except ImportError:
            print(f"      ⚠️ Módulo de comandas não disponível - continuando sem comanda")

        except Exception as e:
            print(f"      ⚠️ Não foi possível gerar comanda: {e}")
            print(f"      💡 Continuando execução sem comanda...")

    def obter_estatisticas(self):
        """
        Retorna estatísticas de execução do adaptador.

        Returns:
            Dict com estatísticas
        """
        return {
            'pedidos_executados': len(self.pedidos_executados),
            'pedidos_falhados': len(self.pedidos_falhados),
            'taxa_sucesso': len(self.pedidos_executados) / (len(self.pedidos_executados) + len(self.pedidos_falhados)) if (len(self.pedidos_executados) + len(self.pedidos_falhados)) > 0 else 0,
            'lista_executados': self.pedidos_executados,
            'lista_falhados': self.pedidos_falhados
        }
