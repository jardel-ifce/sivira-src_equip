"""
INTERCEPTADOR DE VALIDAÇÃO
=========================

Sistema que intercepta validações de quantidade e verifica se há pedidos similares
na fila de execução que podem ser agrupados, mesmo antes das ocupações serem criadas.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('InterceptadorValidacao')


class InterceptadorValidacao:
    """
    Intercepta validações de quantidade e verifica agrupamentos possíveis
    analisando a fila de pedidos em execução.
    """
    
    def __init__(self):
        # Registro de validações interceptadas
        self.validacoes_interceptadas: Dict[str, Dict] = {}
        # Pedidos na fila de execução atual
        self.pedidos_em_execucao: List = []
        
    def registrar_pedidos_execucao(self, pedidos: List):
        """Registra a lista de pedidos que estão sendo executados."""
        self.pedidos_em_execucao = pedidos
        logger.info(f"📋 Registrados {len(pedidos)} pedidos para análise de agrupamento")
        
    def interceptar_validacao_quantidade(self, atividade, quantidade_individual: float) -> Optional[float]:
        """
        Intercepta validação de quantidade e verifica se pode ser agrupada
        com outras atividades similares dos pedidos em execução.
        
        Returns:
            float: Quantidade total agrupada se agrupamento foi detectado, None caso contrário
        """
        try:
            # Identificar a atividade atual
            id_atividade = getattr(atividade, 'id_atividade', None)
            id_pedido_atual = getattr(atividade, 'id_pedido', None)
            nome_atividade = getattr(atividade, 'nome_atividade', '')
            
            if not id_atividade or not id_pedido_atual:
                return None
                
            logger.info(f"🔍 Interceptando validação: {nome_atividade} (Pedido {id_pedido_atual})")
            
            # Buscar atividades similares nos outros pedidos
            atividades_similares = []
            
            for pedido in self.pedidos_em_execucao:
                if getattr(pedido, 'id_pedido', None) == id_pedido_atual:
                    continue  # Pular o próprio pedido
                    
                # Verificar se o pedido tem atividades modulares criadas
                if not hasattr(pedido, 'atividades_modulares'):
                    # Tentar criar as atividades
                    try:
                        pedido.criar_atividades_modulares_necessarias()
                    except Exception as e:
                        logger.debug(f"   Erro ao criar atividades do pedido {pedido.id_pedido}: {e}")
                        continue
                
                if not pedido.atividades_modulares:
                    continue
                    
                # Procurar atividades com mesmo ID
                for atividade_outro in pedido.atividades_modulares:
                    if getattr(atividade_outro, 'id_atividade', None) == id_atividade:
                        quantidade_outro = getattr(atividade_outro, 'quantidade', 0)
                        atividades_similares.append({
                            'pedido': pedido.id_pedido,
                            'quantidade': quantidade_outro,
                            'atividade': atividade_outro
                        })
                        
            if atividades_similares:
                # Calcular quantidade total agrupada
                quantidade_total = quantidade_individual + sum(a['quantidade'] for a in atividades_similares)
                
                logger.info(
                    f"🔗 AGRUPAMENTO INTERCEPTADO para {nome_atividade}:\n"
                    f"   Pedido atual ({id_pedido_atual}): {quantidade_individual}g\n"
                    f"   Pedidos similares: {[a['pedido'] for a in atividades_similares]}\n" 
                    f"   Quantidades: {[a['quantidade'] for a in atividades_similares]}\n"
                    f"   TOTAL AGRUPADO: {quantidade_total}g"
                )
                
                return quantidade_total
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na interceptação: {e}")
            return None
    
    def limpar_registros(self):
        """Limpa os registros após execução."""
        self.validacoes_interceptadas.clear()
        self.pedidos_em_execucao.clear()


# Instância global do interceptador
interceptador_validacao = InterceptadorValidacao()