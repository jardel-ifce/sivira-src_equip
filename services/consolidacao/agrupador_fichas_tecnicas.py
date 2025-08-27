"""
AGRUPADOR DE FICHAS TÉCNICAS
============================

Cria fichas técnicas temporárias agrupadas, combinando quantidades de pedidos similares
antes da execução, permitindo que o sistema trate o agrupamento como um único pedido
com quantidade maior.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import os
import tempfile
from collections import defaultdict
from utils.logs.logger_factory import setup_logger

logger = setup_logger('AgrupadorFichasTecnicas')


class AgrupadorFichasTecnicas:
    """
    Agrupa pedidos similares em fichas técnicas temporárias com quantidades somadas.
    """
    
    def __init__(self):
        self.fichas_temporarias_criadas: List[str] = []
        self.agrupamentos_criados: Dict[str, List] = {}
        
    def agrupar_pedidos_similares(self, pedidos_convertidos: List) -> Tuple[List, Dict]:
        """
        Analisa pedidos e cria fichas técnicas agrupadas para pedidos similares.
        
        Args:
            pedidos_convertidos: Lista de pedidos originais
            
        Returns:
            Tuple[List, Dict]: (pedidos_modificados, info_agrupamentos)
        """
        logger.info(f"🔗 Iniciando agrupamento de fichas técnicas para {len(pedidos_convertidos)} pedidos")
        
        if len(pedidos_convertidos) < 2:
            return pedidos_convertidos, {}
        
        # 1. Mapear pedidos por item similar
        grupos_similares = self._mapear_pedidos_similares(pedidos_convertidos)
        
        # 2. Criar fichas agrupadas para grupos com múltiplos pedidos
        pedidos_resultado = []
        info_agrupamentos = {}
        
        for grupo_id, pedidos_grupo in grupos_similares.items():
            if len(pedidos_grupo) > 1:
                # Criar ficha técnica agrupada
                pedido_agrupado, info_grupo = self._criar_pedido_agrupado(pedidos_grupo, grupo_id)
                
                if pedido_agrupado:
                    pedidos_resultado.append(pedido_agrupado)
                    info_agrupamentos[grupo_id] = info_grupo
                    logger.info(
                        f"✅ Grupo {grupo_id} agrupado: {len(pedidos_grupo)} pedidos → "
                        f"{info_grupo['quantidade_total']} unidades"
                    )
                else:
                    # Se não conseguiu agrupar, manter pedidos originais
                    pedidos_resultado.extend(pedidos_grupo)
            else:
                # Pedido único, manter original
                pedidos_resultado.extend(pedidos_grupo)
        
        logger.info(f"📊 Resultado: {len(pedidos_convertidos)} pedidos → {len(pedidos_resultado)} pedidos (após agrupamento)")
        
        return pedidos_resultado, info_agrupamentos
    
    def _mapear_pedidos_similares(self, pedidos: List) -> Dict[str, List]:
        """Mapeia pedidos em grupos similares que podem ser agrupados."""
        grupos = defaultdict(list)
        
        for pedido in pedidos:
            # Criar chave baseada no item produzido
            chave = self._gerar_chave_pedido(pedido)
            if chave:
                grupos[chave].append(pedido)
                nome_item = getattr(pedido, 'nome_item', f'Item_{getattr(pedido, "id_produto", "desconhecido")}')
                logger.debug(f"   Pedido {pedido.id_pedido} ({nome_item}) → grupo {chave}")
        
        return grupos
    
    def _gerar_chave_pedido(self, pedido) -> Optional[str]:
        """Gera chave única para agrupar pedidos similares baseada em subprodutos compartilhados."""
        try:
            # Tentar identificar subprodutos principais do pedido
            subprodutos_chave = self._identificar_subprodutos_principais(pedido)
            
            if subprodutos_chave:
                # Agrupar por subproduto principal (ex: massa suave)
                return f"subproduto_{subprodutos_chave}"
            
            # Fallback: agrupar por item individual  
            id_item = getattr(pedido, 'id_produto', None) or getattr(pedido, 'id_item', None)
            nome_item = getattr(pedido, 'nome_item', f'Item_{id_item}')
            
            if id_item:
                return f"item_{id_item}|{nome_item}"
                
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao gerar chave: {e}")
            return None
    
    def _identificar_subprodutos_principais(self, pedido) -> Optional[str]:
        """Identifica subprodutos principais que podem ser agrupados (ex: massas)."""
        try:
            # PedidoDeProducao usa id_produto em vez de id_item
            id_item = getattr(pedido, 'id_produto', None) or getattr(pedido, 'id_item', None)
            if not id_item:
                return None
            
            # Mapear produtos conhecidos para seus subprodutos principais
            mapa_subprodutos = {
                1002: "massa_suave_2002",  # Pão Hambúrguer → massa suave
                1003: "massa_suave_2002",  # Pão de Forma → massa suave  
                1004: "massa_suave_2002",  # Pão Baguete → massa suave
                1005: "massa_suave_2002",  # Pão Trança → massa suave
                1001: "massa_crocante_2001",  # Pão Francês → massa crocante
                # Adicionar outros mapeamentos conforme necessário
            }
            
            subproduto_principal = mapa_subprodutos.get(id_item)
            if subproduto_principal:
                logger.debug(f"   Produto {id_item} mapeado para subproduto: {subproduto_principal}")
                return subproduto_principal
            
            logger.debug(f"   Produto {id_item} não tem mapeamento de subproduto")
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao identificar subprodutos: {e}")
            return None
    
    def _criar_pedido_agrupado(self, pedidos_grupo: List, grupo_id: str) -> Tuple[Optional[object], Dict]:
        """
        Cria um pedido agrupado com ficha técnica temporária contendo quantidades somadas.
        Para produtos diferentes que compartilham subprodutos, cria um pedido virtual.
        """
        try:
            # Verificar se são produtos diferentes (agrupamento por subproduto)
            if grupo_id.startswith("subproduto_"):
                return self._criar_pedido_virtual_subproduto(pedidos_grupo, grupo_id)
            
            # Agrupamento de produtos idênticos (lógica original)
            # Usar o primeiro pedido como base
            pedido_base = pedidos_grupo[0]
            
            # Calcular quantidade total
            quantidade_total = sum(getattr(p, 'quantidade', 0) for p in pedidos_grupo)
            
            # Obter prazo mais cedo (mais restritivo)
            prazo_mais_cedo = min(
                getattr(p, 'fim_jornada', datetime.now()) for p in pedidos_grupo
                if hasattr(p, 'fim_jornada')
            )
            
            # Criar cópia do pedido base
            import copy
            pedido_agrupado = copy.deepcopy(pedido_base)
            
            # Modificar atributos do pedido agrupado
            pedido_agrupado.quantidade = quantidade_total
            pedido_agrupado.fim_jornada = prazo_mais_cedo
            
            # Adicionar informações de agrupamento
            pedido_agrupado.eh_pedido_agrupado = True
            pedido_agrupado.pedidos_originais = [p.id_pedido for p in pedidos_grupo]
            pedido_agrupado.grupo_agrupamento = grupo_id
            
            # Criar ficha técnica temporária (se necessário)
            if hasattr(pedido_agrupado, 'ficha_tecnica_modular'):
                self._atualizar_ficha_tecnica_agrupada(pedido_agrupado, quantidade_total)
            
            info_grupo = {
                'pedidos_agrupados': [p.id_pedido for p in pedidos_grupo],
                'quantidades_originais': [getattr(p, 'quantidade', 0) for p in pedidos_grupo],
                'quantidade_total': quantidade_total,
                'prazo_mais_restritivo': prazo_mais_cedo.isoformat(),
                'item': getattr(pedido_base, 'nome_item', f'Item_{getattr(pedido_base, "id_produto", "desconhecido")}')
            }
            
            return pedido_agrupado, info_grupo
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar pedido agrupado: {e}")
            return None, {}
    
    def _criar_pedido_virtual_subproduto(self, pedidos_grupo: List, grupo_id: str) -> Tuple[Optional[object], Dict]:
        """
        Cria um pedido virtual que representa apenas o subproduto compartilhado.
        Isso permite agrupar produtos diferentes que usam a mesma massa.
        """
        try:
            import copy
            
            # Extrair ID do subproduto do grupo_id (ex: "subproduto_massa_suave_2002" -> 2002)
            subproduto_id = int(grupo_id.split('_')[-1])
            
            # Usar o primeiro pedido como base para estrutura
            pedido_base = pedidos_grupo[0]
            
            # Calcular quantidade total de subproduto necessária
            # Para massa: aproximadamente 65g por unidade de pão
            peso_por_unidade = 65  # gramas
            quantidade_total_unidades = sum(getattr(p, 'quantidade', 0) for p in pedidos_grupo)
            quantidade_subproduto = quantidade_total_unidades * peso_por_unidade  # em gramas
            
            # Obter prazo mais restritivo
            prazo_mais_cedo = min(
                getattr(p, 'fim_jornada', datetime.now()) for p in pedidos_grupo
                if hasattr(p, 'fim_jornada')
            )
            
            # Criar pedido virtual para o subproduto
            pedido_virtual = copy.deepcopy(pedido_base)
            
            # Modificar para representar o subproduto
            pedido_virtual.id_item = subproduto_id
            pedido_virtual.id_produto = subproduto_id
            # Adicionar nome_item se não existir
            if not hasattr(pedido_virtual, 'nome_item'):
                pedido_virtual.nome_item = self._obter_nome_subproduto(subproduto_id)
            else:
                pedido_virtual.nome_item = self._obter_nome_subproduto(subproduto_id)
            pedido_virtual.quantidade = quantidade_subproduto
            pedido_virtual.fim_jornada = prazo_mais_cedo
            
            # Marcar como agrupamento de subproduto
            pedido_virtual.eh_pedido_agrupado = True
            pedido_virtual.eh_agrupamento_subproduto = True
            pedido_virtual.pedidos_originais = [p.id_pedido for p in pedidos_grupo]
            pedido_virtual.produtos_originais = [(p.id_pedido, getattr(p, 'id_produto', 0), getattr(p, 'nome_item', 'Item_' + str(getattr(p, 'id_produto', 0))), getattr(p, 'quantidade', 0)) for p in pedidos_grupo]
            pedido_virtual.grupo_agrupamento = grupo_id
            
            # Informações para relatório
            info_grupo = {
                'pedidos_agrupados': [p.id_pedido for p in pedidos_grupo],
                'produtos_agrupados': [f"{getattr(p, 'nome_item', 'Item_' + str(getattr(p, 'id_produto', 'N/A')))} ({getattr(p, 'quantidade', 0)} uni)" for p in pedidos_grupo],
                'quantidades_originais': [getattr(p, 'quantidade', 0) for p in pedidos_grupo],
                'quantidade_total': quantidade_subproduto,
                'unidade': 'gramas',
                'item': f"{pedido_virtual.nome_item} (Virtual - {quantidade_total_unidades} unidades de produtos)",
                'tipo_agrupamento': 'subproduto'
            }
            
            logger.debug(f"   Pedido virtual criado: {pedido_virtual.nome_item} - {quantidade_subproduto}g")
            
            return pedido_virtual, info_grupo
            
        except Exception as e:
            logger.error(f"Erro ao criar pedido virtual: {e}")
            return None, {}
    
    def _obter_nome_subproduto(self, subproduto_id: int) -> str:
        """Retorna o nome do subproduto baseado no ID."""
        nomes_subprodutos = {
            2001: "Massa Crocante",
            2002: "Massa Suave",
            2003: "Massa para Brownie",
            # Adicionar outros conforme necessário
        }
        return nomes_subprodutos.get(subproduto_id, f"Subproduto {subproduto_id}")
    
    def _atualizar_ficha_tecnica_agrupada(self, pedido_agrupado, quantidade_total: int):
        """Atualiza a ficha técnica para refletir a quantidade total agrupada."""
        try:
            if hasattr(pedido_agrupado, 'ficha_tecnica_modular') and pedido_agrupado.ficha_tecnica_modular:
                # A ficha técnica modular deve automaticamente calcular proporções
                # baseadas na nova quantidade do pedido
                logger.debug(f"   Ficha técnica será recalculada para {quantidade_total} unidades")
            
        except Exception as e:
            logger.debug(f"Erro ao atualizar ficha técnica: {e}")
    
    def limpar_fichas_temporarias(self):
        """Remove fichas técnicas temporárias criadas."""
        for arquivo in self.fichas_temporarias_criadas:
            try:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    logger.debug(f"   Removido arquivo temporário: {arquivo}")
            except Exception as e:
                logger.debug(f"Erro ao remover {arquivo}: {e}")
        
        self.fichas_temporarias_criadas.clear()
        self.agrupamentos_criados.clear()


# Instância global do agrupador
agrupador_fichas = AgrupadorFichasTecnicas()