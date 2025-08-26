from typing import List, Dict, Tuple
from datetime import datetime
from enums.producao.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ConsolidadorSimples')


class ConsolidadorSimples:
    """
    Classe para consolidação simples de subprodutos entre pedidos.
    
    Funcionalidade:
    - Detecta subprodutos compartilhados entre pedidos
    - Consolida quantidades quando múltiplos pedidos precisam do mesmo subproduto
    - Designa um pedido "mestre" para produzir o lote consolidado
    - Marca outros pedidos para pular a produção individual
    """
    
    @staticmethod
    def processar_pedidos(pedidos: List['PedidoDeProducao']) -> None:
        """
        Processa uma lista de pedidos e consolida subprodutos compartilhados.
        
        Args:
            pedidos: Lista de pedidos de produção
        """
        if not pedidos:
            logger.debug("Lista de pedidos vazia. Nada a processar.")
            return
        
        # Verificar se algum pedido quer consolidação
        pedidos_com_consolidacao = [p for p in pedidos if p.consolidar_subprodutos]
        
        if not pedidos_com_consolidacao:
            logger.debug("Nenhum pedido configurado para consolidação.")
            return
        
        logger.info(f"Processando consolidação para {len(pedidos_com_consolidacao)} pedidos")
        
        # Mapear demandas por subproduto
        demandas = ConsolidadorSimples._mapear_demandas_subprodutos(pedidos_com_consolidacao)
        
        # Consolidar subprodutos com múltiplas demandas
        subprodutos_consolidados = 0
        for id_subproduto, lista_demandas in demandas.items():
            if len(lista_demandas) > 1:
                ConsolidadorSimples._consolidar_subproduto(id_subproduto, lista_demandas)
                subprodutos_consolidados += 1
        
        logger.info(f"Consolidação concluída: {subprodutos_consolidados} subprodutos consolidados")
    
    @staticmethod
    def _mapear_demandas_subprodutos(pedidos: List['PedidoDeProducao']) -> Dict[int, List[Tuple['PedidoDeProducao', float]]]:
        """
        Mapeia as demandas de subprodutos por ID.
        
        Returns:
            Dicionário {id_subproduto: [(pedido, quantidade), ...]}
        """
        demandas = {}
        
        for pedido in pedidos:
            try:
                subprodutos = ConsolidadorSimples._extrair_subprodutos(pedido)
                
                for id_subproduto, quantidade in subprodutos.items():
                    if id_subproduto not in demandas:
                        demandas[id_subproduto] = []
                    
                    demandas[id_subproduto].append((pedido, quantidade))
                    
                    logger.debug(
                        f"Mapeada demanda: Pedido {pedido.id_pedido} -> "
                        f"Subproduto {id_subproduto} ({quantidade} unidades)"
                    )
                    
            except Exception as e:
                logger.error(f"Erro ao mapear demandas do pedido {pedido.id_pedido}: {e}")
                continue
        
        return demandas
    
    @staticmethod
    def _extrair_subprodutos(pedido: 'PedidoDeProducao') -> Dict[int, float]:
        """
        Extrai subprodutos necessários de um pedido.
        
        Returns:
            Dicionário {id_subproduto: quantidade_necessaria}
        """
        if not pedido.ficha_tecnica_modular:
            logger.warning(f"Pedido {pedido.id_pedido} sem ficha técnica montada")
            return {}
        
        subprodutos = {}
        
        try:
            estimativas = pedido.ficha_tecnica_modular.calcular_quantidade_itens()
            
            for item_dict, quantidade in estimativas:
                tipo_item = item_dict.get("tipo_item")
                id_ficha = item_dict.get("id_ficha_tecnica")
                
                if tipo_item == "SUBPRODUTO" and id_ficha:
                    subprodutos[id_ficha] = quantidade
                    
            logger.debug(f"Subprodutos extraídos do pedido {pedido.id_pedido}: {subprodutos}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair subprodutos do pedido {pedido.id_pedido}: {e}")
        
        return subprodutos
    
    @staticmethod
    def _consolidar_subproduto(id_subproduto: int, demandas: List[Tuple['PedidoDeProducao', float]]) -> None:
        """
        Consolida um subproduto específico entre múltiplos pedidos.
        
        Args:
            id_subproduto: ID do subproduto a ser consolidado
            demandas: Lista de tuplas (pedido, quantidade)
        """
        if len(demandas) < 2:
            logger.warning(f"Tentativa de consolidar subproduto {id_subproduto} com menos de 2 demandas")
            return
        
        # Calcular quantidade total
        quantidade_total = sum(quantidade for _, quantidade in demandas)
        
        # Ordenar pedidos por ID para ter comportamento determinístico
        demandas_ordenadas = sorted(demandas, key=lambda x: x[0].id_pedido)
        
        # Primeiro pedido se torna o "mestre" (produz o lote consolidado)
        pedido_mestre, quantidade_mestre = demandas_ordenadas[0]
        pedido_mestre.lotes_consolidados[id_subproduto] = quantidade_total
        
        # Outros pedidos são marcados para pular este subproduto
        pedidos_dependentes = []
        for pedido, quantidade_original in demandas_ordenadas[1:]:
            pedido.lotes_consolidados[id_subproduto] = 0  # 0 = já processado em lote
            pedidos_dependentes.append(f"Pedido {pedido.id_pedido} ({quantidade_original} un)")
        
        logger.info(
            f"CONSOLIDAÇÃO REALIZADA:\n"
            f"  Subproduto: {id_subproduto}\n"
            f"  Quantidade total: {quantidade_total} unidades\n"
            f"  Pedido mestre: {pedido_mestre.id_pedido} (produzirá {quantidade_total} un)\n"
            f"  Pedidos dependentes: {', '.join(pedidos_dependentes)}\n"
            f"  Economia: {len(demandas) - 1} atividades evitadas"
        )
    
    @staticmethod
    def obter_resumo_consolidacoes(pedidos: List['PedidoDeProducao']) -> Dict:
        """
        Gera um resumo das consolidações realizadas.
        
        Returns:
            Dicionário com estatísticas das consolidações
        """
        total_consolidacoes = 0
        total_economia = 0
        detalhes = {}
        
        for pedido in pedidos:
            if hasattr(pedido, 'lotes_consolidados') and pedido.lotes_consolidados:
                for id_sub, quantidade in pedido.lotes_consolidados.items():
                    if quantidade > 0:  # É um pedido mestre
                        total_consolidacoes += 1
                        detalhes[id_sub] = {
                            'pedido_mestre': pedido.id_pedido,
                            'quantidade_consolidada': quantidade
                        }
                    else:  # É um pedido dependente
                        total_economia += 1
        
        return {
            'total_subprodutos_consolidados': total_consolidacoes,
            'total_atividades_economizadas': total_economia,
            'detalhes_por_subproduto': detalhes,
            'timestamp': datetime.now()
        }