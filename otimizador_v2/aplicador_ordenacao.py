"""
Aplicador de Ordenação
======================

Executa pedidos na ordem otimizada pelo PL.

Similar ao Sistema Sequencial, mas:
- Executa na ordem otimizada (não sequencial 1,2,3...)
- Chama pedido.executar_atividades_em_ordem() para cada pedido
- Não modifica a lógica de execução existente
- Registra sucessos e falhas

Criado em: 18/11/2025
"""

from datetime import datetime
from typing import List, Dict, Tuple
from utils.logs.logger_factory import setup_logger

logger = setup_logger('AplicadorOrdenacao')


class AplicadorOrdenacao:
    """
    Aplica a ordem de execução otimizada aos pedidos.
    """

    def __init__(self):
        self.logger = setup_logger('AplicadorOrdenacao')
        self.pedidos_executados = []
        self.pedidos_com_erro = []
        self.tempo_inicio_execucao = None
        self.tempo_fim_execucao = None

    def executar_pedidos_em_ordem(
        self,
        pedidos: List,
        ordem_execucao: List[int]
    ) -> Dict:
        """
        Executa pedidos na ordem especificada.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            ordem_execucao: Lista de id_pedido na ordem desejada

        Returns:
            Dict com resultados da execução:
            - pedidos_executados: Lista de IDs executados com sucesso
            - pedidos_com_erro: Lista de IDs que falharam
            - taxa_sucesso: Percentual de sucesso
            - tempo_total: Tempo total de execução
            - detalhes: Informações detalhadas por pedido
        """
        self.logger.info("🚀 Iniciando execução de pedidos na ordem otimizada...")
        self.tempo_inicio_execucao = datetime.now()

        # Resetar listas
        self.pedidos_executados = []
        self.pedidos_com_erro = []
        detalhes_execucao = []

        # Criar mapa de pedidos por ID
        mapa_pedidos = {p.id_pedido: p for p in pedidos}

        # Executar pedidos na ordem especificada
        for posicao, id_pedido in enumerate(ordem_execucao, 1):
            pedido = mapa_pedidos.get(id_pedido)

            if not pedido:
                self.logger.error(
                    f"❌ Pedido {id_pedido} não encontrado no mapa de pedidos"
                )
                self.pedidos_com_erro.append(id_pedido)
                detalhes_execucao.append({
                    "id_pedido": id_pedido,
                    "posicao": posicao,
                    "status": "ERRO_NAO_ENCONTRADO",
                    "mensagem": "Pedido não encontrado"
                })
                continue

            # Executar pedido
            resultado_pedido = self._executar_pedido_individual(
                pedido,
                posicao,
                len(ordem_execucao)
            )

            detalhes_execucao.append(resultado_pedido)

        self.tempo_fim_execucao = datetime.now()

        # Calcular estatísticas
        total_pedidos = len(ordem_execucao)
        pedidos_sucesso = len(self.pedidos_executados)
        pedidos_erro = len(self.pedidos_com_erro)
        taxa_sucesso = (pedidos_sucesso / total_pedidos * 100) if total_pedidos > 0 else 0

        tempo_total = (self.tempo_fim_execucao - self.tempo_inicio_execucao).total_seconds()

        resultado_final = {
            "pedidos_executados": self.pedidos_executados,
            "pedidos_com_erro": self.pedidos_com_erro,
            "total_pedidos": total_pedidos,
            "pedidos_sucesso": pedidos_sucesso,
            "pedidos_erro": pedidos_erro,
            "taxa_sucesso": taxa_sucesso,
            "tempo_total": tempo_total,
            "detalhes": detalhes_execucao,
            "inicio_execucao": self.tempo_inicio_execucao,
            "fim_execucao": self.tempo_fim_execucao
        }

        # Log final
        self.logger.info("=" * 70)
        self.logger.info("📊 RESULTADO FINAL DA EXECUÇÃO")
        self.logger.info(f"✅ Pedidos executados: {pedidos_sucesso}/{total_pedidos}")
        self.logger.info(f"❌ Pedidos com erro: {pedidos_erro}/{total_pedidos}")
        self.logger.info(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        self.logger.info(f"⏱️ Tempo total: {tempo_total:.2f}s")
        self.logger.info("=" * 70)

        return resultado_final

    def _executar_pedido_individual(
        self,
        pedido,
        posicao: int,
        total: int
    ) -> Dict:
        """
        Executa um pedido individual.

        Args:
            pedido: Objeto PedidoDeProducao
            posicao: Posição na ordem de execução
            total: Total de pedidos

        Returns:
            Dict com resultado da execução do pedido
        """
        id_pedido = pedido.id_pedido

        self.logger.info(
            f"🔄 [{posicao}/{total}] Executando Pedido {id_pedido}..."
        )

        tempo_inicio_pedido = datetime.now()

        try:
            # PASSO 1: Criar atividades modulares (necessário antes da execução!)
            if not hasattr(pedido, 'criar_atividades_modulares_necessarias'):
                raise AttributeError(
                    f"Pedido {id_pedido} não possui método 'criar_atividades_modulares_necessarias'"
                )

            pedido.criar_atividades_modulares_necessarias()
            num_atividades = len(pedido.atividades_modulares) if hasattr(pedido, 'atividades_modulares') else 0
            self.logger.info(f"   ✅ {num_atividades} atividades modulares criadas")

            # PASSO 2: Executar atividades em ordem
            if not hasattr(pedido, 'executar_atividades_em_ordem'):
                raise AttributeError(
                    f"Pedido {id_pedido} não possui método 'executar_atividades_em_ordem'"
                )

            resultado_execucao = pedido.executar_atividades_em_ordem()

            tempo_fim_pedido = datetime.now()
            tempo_execucao = (tempo_fim_pedido - tempo_inicio_pedido).total_seconds()

            # Verificar se execução foi bem-sucedida
            # O método executar_atividades_em_ordem() retorna None quando bem-sucedido
            # (não levanta exceção), então verificamos se NÃO houve exceção
            sucesso = True  # Se chegou aqui sem exceção, foi bem-sucedido

            # Verificações adicionais para casos onde há retorno explícito
            if isinstance(resultado_execucao, bool):
                sucesso = resultado_execucao
            elif isinstance(resultado_execucao, dict):
                sucesso = resultado_execucao.get('sucesso', True)

            if sucesso:
                self.pedidos_executados.append(id_pedido)
                self.logger.info(
                    f"✅ Pedido {id_pedido} executado com sucesso "
                    f"({tempo_execucao:.2f}s)"
                )

                return {
                    "id_pedido": id_pedido,
                    "posicao": posicao,
                    "status": "SUCESSO",
                    "tempo_execucao": tempo_execucao,
                    "detalhes": resultado_execucao
                }
            else:
                self.pedidos_com_erro.append(id_pedido)
                self.logger.error(
                    f"❌ Pedido {id_pedido} falhou na execução "
                    f"({tempo_execucao:.2f}s)"
                )

                return {
                    "id_pedido": id_pedido,
                    "posicao": posicao,
                    "status": "FALHA_EXECUCAO",
                    "tempo_execucao": tempo_execucao,
                    "mensagem": "Execução retornou falha",
                    "detalhes": resultado_execucao
                }

        except Exception as e:
            tempo_fim_pedido = datetime.now()
            tempo_execucao = (tempo_fim_pedido - tempo_inicio_pedido).total_seconds()

            self.pedidos_com_erro.append(id_pedido)
            self.logger.error(
                f"❌ Erro ao executar Pedido {id_pedido}: {e} "
                f"({tempo_execucao:.2f}s)"
            )

            return {
                "id_pedido": id_pedido,
                "posicao": posicao,
                "status": "ERRO_EXCEPTION",
                "tempo_execucao": tempo_execucao,
                "erro": str(e),
                "tipo_erro": type(e).__name__
            }

    def gerar_relatorio_execucao(self, resultado_execucao: Dict) -> str:
        """
        Gera relatório textual da execução.

        Args:
            resultado_execucao: Dict retornado por executar_pedidos_em_ordem

        Returns:
            String com relatório formatado
        """
        relatorio = []
        relatorio.append("📊 RELATÓRIO DE EXECUÇÃO")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Resumo geral
        relatorio.append("📋 RESUMO GERAL:")
        relatorio.append(
            f"   Total de pedidos: {resultado_execucao['total_pedidos']}"
        )
        relatorio.append(
            f"   ✅ Executados com sucesso: {resultado_execucao['pedidos_sucesso']}"
        )
        relatorio.append(
            f"   ❌ Com erro: {resultado_execucao['pedidos_erro']}"
        )
        relatorio.append(
            f"   📈 Taxa de sucesso: {resultado_execucao['taxa_sucesso']:.1f}%"
        )
        relatorio.append(
            f"   ⏱️ Tempo total: {resultado_execucao['tempo_total']:.2f}s"
        )
        relatorio.append("")

        # Detalhes por pedido
        relatorio.append("📝 DETALHES POR PEDIDO:")
        relatorio.append("")

        for detalhe in resultado_execucao['detalhes']:
            id_pedido = detalhe['id_pedido']
            posicao = detalhe['posicao']
            status = detalhe['status']
            tempo = detalhe.get('tempo_execucao', 0)

            status_emoji = "✅" if status == "SUCESSO" else "❌"

            linha = (
                f"{status_emoji} [{posicao}] Pedido {id_pedido}: "
                f"{status} ({tempo:.2f}s)"
            )

            relatorio.append(f"   {linha}")

            # Adicionar mensagem de erro se houver
            if 'erro' in detalhe:
                relatorio.append(f"      Erro: {detalhe['erro']}")
            elif 'mensagem' in detalhe:
                relatorio.append(f"      Info: {detalhe['mensagem']}")

        relatorio.append("")

        # Lista de pedidos executados
        if resultado_execucao['pedidos_executados']:
            relatorio.append("✅ PEDIDOS EXECUTADOS COM SUCESSO:")
            relatorio.append(
                f"   {', '.join(map(str, resultado_execucao['pedidos_executados']))}"
            )
            relatorio.append("")

        # Lista de pedidos com erro
        if resultado_execucao['pedidos_com_erro']:
            relatorio.append("❌ PEDIDOS COM ERRO:")
            relatorio.append(
                f"   {', '.join(map(str, resultado_execucao['pedidos_com_erro']))}"
            )
            relatorio.append("")

        return "\n".join(relatorio)


# Função de conveniência para uso direto
def executar_pedidos_ordenados(
    pedidos: List,
    ordem_execucao: List[int]
) -> Dict:
    """
    Função de conveniência para executar pedidos em ordem.

    Args:
        pedidos: Lista de objetos PedidoDeProducao
        ordem_execucao: Lista de id_pedido na ordem desejada

    Returns:
        Dict com resultados da execução
    """
    aplicador = AplicadorOrdenacao()
    return aplicador.executar_pedidos_em_ordem(pedidos, ordem_execucao)
