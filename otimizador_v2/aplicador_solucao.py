"""
Aplicador de Solução PL v2.0
============================

Aplica a solução teórica do PL v2.0 aos pedidos reais,
executando as alocações de equipamentos e gerando logs.
"""

from datetime import datetime, timedelta
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
        self.debug_log_file = "logs/debug_aplicador_pl.log"
        self._iniciar_log_debug()

    def _iniciar_log_debug(self):
        """Inicia arquivo de log de debug"""
        import os
        os.makedirs("logs", exist_ok=True)
        with open(self.debug_log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LOG DE DEBUG - APLICADOR PL v2.0\n")
            f.write("="*80 + "\n")
            f.write(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")

    def _log_debug(self, mensagem: str):
        """Adiciona mensagem ao log de debug"""
        with open(self.debug_log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {mensagem}\n")

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
                self.erros.append({
                    'pedido_id': pedido_id,
                    'nome': pedido.ficha_tecnica_modular.nome if hasattr(pedido, 'ficha_tecnica_modular') else f'Pedido {pedido_id}',
                    'motivo': 'Equipamentos indisponíveis no horário backward calculado'
                })
                print(f"   ❌ Falha ao executar Pedido {pedido_id} (equipamentos ocupados - esperado)")

        # Resumo
        print("\n" + "="*80)
        print("📊 RESUMO DA APLICAÇÃO")
        print("="*80)
        print(f"Total de pedidos: {stats['total_pedidos']}")
        print(f"Pedidos executados: {stats['pedidos_executados']}")
        print(f"Pedidos falharam: {stats['pedidos_falhou']}")
        print(f"Taxa de sucesso: {(stats['pedidos_executados']/stats['total_pedidos']*100):.1f}%")
        print("="*80 + "\n")

        # Mensagem sobre log de debug
        print(f"📝 Log de debug detalhado salvo em: {self.debug_log_file}")
        print(f"   Use: cat {self.debug_log_file}\n")

        return stats

    def _executar_pedido(
        self,
        pedido: PedidoDeProducao,
        inicio_pedido: datetime,
        fim_pedido: datetime
    ) -> bool:
        """
        Executa as atividades de um pedido respeitando a janela PL.

        ESTRATÉGIA CORRIGIDA:
        - Chama executar_atividades_em_ordem() que já implementa toda lógica complexa
        - Mas ajusta janelas para serem compatíveis com backward scheduling
        - Respeita deadlines estritos, gaps temporais, sequenciamento intra-atividade
        - Atomicidade: ou executa tudo ou faz rollback automático

        Args:
            pedido: Pedido a ser executado
            inicio_pedido: Horário de início da janela PL
            fim_pedido: Horário de término da janela PL (deadline)

        Returns:
            True se executado com sucesso, False se equipamentos indisponíveis
        """
        try:
            self._log_debug("\n" + "="*80)
            self._log_debug(f"EXECUTANDO PEDIDO {pedido.id_pedido}")
            self._log_debug("="*80)

            print(f"      🔄 Executando pedido {pedido.id_pedido} com janela PL...")
            print(f"         Janela: [{inicio_pedido.strftime('%d/%m %H:%M')} → {fim_pedido.strftime('%d/%m %H:%M')}]")

            # LOG 1: Janelas PL recebidas
            janela_duracao = (fim_pedido - inicio_pedido).total_seconds() / 3600
            self._log_debug(f"JANELA PL RECEBIDA:")
            self._log_debug(f"  inicio_pedido = {inicio_pedido.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  fim_pedido = {fim_pedido.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  Duração janela = {janela_duracao:.2f}h")

            # LOG 2: Estado ANTES de atualizar
            duracao_calculada = sum((a.duracao for a in pedido.atividades_modulares), timedelta())
            self._log_debug(f"ESTADO DO PEDIDO ANTES DE ATUALIZAR:")
            self._log_debug(f"  pedido.inicio_jornada = {pedido.inicio_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  pedido.fim_jornada = {pedido.fim_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  Duração total calculada = {duracao_calculada}")
            self._log_debug(f"  Total de atividades = {len(pedido.atividades_modulares)}")

            # Atualizar jornadas do pedido para refletir janela do PL
            pedido.inicio_jornada = inicio_pedido
            pedido.fim_jornada = fim_pedido

            # LOG 3: Estado DEPOIS de atualizar
            self._log_debug(f"ESTADO DO PEDIDO DEPOIS DE ATUALIZAR:")
            self._log_debug(f"  pedido.inicio_jornada = {pedido.inicio_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  pedido.fim_jornada = {pedido.fim_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            diferenca = (pedido.fim_jornada - pedido.inicio_jornada).total_seconds() / 3600
            self._log_debug(f"  Diferença = {diferenca:.2f}h")

            print(f"         DEBUG: Antes de executar_atividades_em_ordem()")
            print(f"           inicio_jornada = {pedido.inicio_jornada.strftime('%d/%m %H:%M')}")
            print(f"           fim_jornada = {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
            print(f"           Diferença = {diferenca:.1f}h")

            # LOG 4: Informações sobre atividades
            from enums.producao.tipo_item import TipoItem
            atividades_produto = [a for a in pedido.atividades_modulares if a.tipo_item == TipoItem.PRODUTO]
            atividades_subproduto = [a for a in pedido.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]

            self._log_debug(f"ATIVIDADES DO PEDIDO:")
            self._log_debug(f"  PRODUTO: {len(atividades_produto)} atividades")
            for atv in atividades_produto:
                self._log_debug(f"    - ID {atv.id_atividade}: {atv.nome_atividade} (duração: {atv.duracao})")
            self._log_debug(f"  SUBPRODUTO: {len(atividades_subproduto)} atividades")
            for atv in atividades_subproduto:
                self._log_debug(f"    - ID {atv.id_atividade}: {atv.nome_atividade} (duração: {atv.duracao})")

            self._log_debug(f"\nCHAMANDO executar_atividades_em_ordem()...")

            # Chamar método REAL de agendamento que implementa:
            # - Sequenciamento correto (SUBPRODUTO antes de PRODUTO)
            # - Backward scheduling com busca de slots
            # - Gaps temporais entre atividades
            # - Sequenciamento intra-atividade (múltiplos equipamentos por atividade)
            # - Deadlines estritos (tempo_maximo_espera = 0)
            # - Rollback automático em caso de falha
            # - Registro de logs
            pedido.executar_atividades_em_ordem()

            # LOG 5: Resultado da execução
            self._log_debug(f"RETORNOU de executar_atividades_em_ordem()")

            # Verificar se todas as atividades foram alocadas com sucesso
            atividades_alocadas = [a for a in pedido.atividades_modulares if a.alocada]
            total_atividades = len(pedido.atividades_modulares)
            sucesso = len(atividades_alocadas) == total_atividades

            # LOG 6: Resultado
            self._log_debug(f"RESULTADO DA EXECUÇÃO:")
            self._log_debug(f"  Atividades alocadas: {len(atividades_alocadas)}/{total_atividades}")
            self._log_debug(f"  Sucesso: {sucesso}")

            if sucesso:
                self._log_debug(f"  ✅ SUCESSO - Todas as atividades foram alocadas")
                for atv in atividades_alocadas:
                    if hasattr(atv, 'inicio_real') and atv.inicio_real:
                        self._log_debug(f"    - Atividade {atv.id_atividade}: {atv.inicio_real.strftime('%d/%m %H:%M')} → {atv.fim_real.strftime('%d/%m %H:%M')}")
                print(f"      ✅ Pedido {pedido.id_pedido} executado com sucesso ({len(atividades_alocadas)}/{total_atividades} atividades)")
            else:
                self._log_debug(f"  ❌ FALHA - Apenas {len(atividades_alocadas)}/{total_atividades} atividades alocadas")
                self._log_debug(f"  Atividades NÃO alocadas:")
                for atv in pedido.atividades_modulares:
                    if not atv.alocada:
                        self._log_debug(f"    - Atividade {atv.id_atividade}: {atv.nome_atividade}")
                print(f"      ❌ Pedido {pedido.id_pedido} falhou ({len(atividades_alocadas)}/{total_atividades} atividades - rollback automático)")

            # LOG 7: Estado final das jornadas
            self._log_debug(f"ESTADO FINAL DO PEDIDO:")
            self._log_debug(f"  pedido.inicio_jornada = {pedido.inicio_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug(f"  pedido.fim_jornada = {pedido.fim_jornada.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log_debug("="*80 + "\n")

            return sucesso

        except Exception as e:
            self._log_debug(f"❌ EXCEÇÃO CAPTURADA: {str(e)}")
            self._log_debug(f"Tipo: {type(e).__name__}")
            import traceback
            self._log_debug(f"Traceback:\n{traceback.format_exc()}")
            self._log_debug("="*80 + "\n")

            print(f"      ❌ Erro ao executar pedido {pedido.id_pedido}: {e}")
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
