"""
DETECTOR DE AGRUPAMENTOS EM RUNTIME
===================================

Detecta agrupamentos de atividades durante a execução, sem precisar de pré-análise.
Funciona interceptando as validações de quantidade e verificando se há outras atividades
similares sendo executadas ao mesmo tempo.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('DetectorAgrupamentos')


class DetectorAgrupamentosRuntime:
    """
    Detecta e gerencia agrupamentos de atividades em tempo real durante a execução.
    """
    
    def __init__(self):
        # Registro de validações em andamento
        self.validacoes_pendentes: Dict[str, List] = {}
        # Cache de atividades agrupadas já processadas
        self.agrupamentos_processados: Set[str] = set()
        
    def detectar_agrupamento(self, atividade, quantidade: float, gestor_equipamentos) -> Optional[float]:
        """
        Detecta se a atividade atual pode ser agrupada com outras atividades similares
        que estão sendo executadas no mesmo período.
        
        Args:
            atividade: Atividade sendo validada
            quantidade: Quantidade individual da atividade
            gestor_equipamentos: Gestor de equipamentos (ex: GestorMisturadoras)
            
        Returns:
            float: Quantidade total agrupada se agrupamento foi detectado, None caso contrário
        """
        try:
            # Gerar chave única para a atividade
            chave_atividade = self._gerar_chave_atividade(atividade)
            
            if not chave_atividade:
                return None
                
            logger.info(f"🔍 Verificando agrupamento para atividade: {chave_atividade}")
            
            # Verificar se há atividades similares no mesmo equipamento no mesmo período
            atividades_similares = self._buscar_atividades_similares(
                atividade, gestor_equipamentos
            )
            
            if len(atividades_similares) > 0:
                # Calcular quantidade total do grupo
                quantidade_total = quantidade + sum(ativ['quantidade'] for ativ in atividades_similares)
                
                logger.info(
                    f"🔗 AGRUPAMENTO DETECTADO para {chave_atividade}:\n"
                    f"   Quantidade atual: {quantidade}g\n"
                    f"   Atividades similares: {len(atividades_similares)}\n"
                    f"   Quantidade total agrupada: {quantidade_total}g"
                )
                
                return quantidade_total
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de agrupamento: {e}")
            return None
    
    def _gerar_chave_atividade(self, atividade) -> Optional[str]:
        """
        Gera chave única para identificar atividades que podem ser agrupadas.
        """
        try:
            elementos = [
                str(getattr(atividade, 'id_atividade', '')),
                str(getattr(atividade, 'nome_atividade', '')),
                str(getattr(atividade, 'tipo_item', ''))
            ]
            
            if not all(elementos):
                return None
                
            return '|'.join(elementos)
            
        except Exception as e:
            logger.debug(f"Erro ao gerar chave: {e}")
            return None
    
    def _buscar_atividades_similares(self, atividade_atual, gestor_equipamentos) -> List[Dict]:
        """
        Busca atividades similares que já estão alocadas nos equipamentos.
        """
        atividades_encontradas = []
        
        try:
            # Obter timing da atividade atual
            inicio = getattr(atividade_atual, 'inicio', None)
            fim = getattr(atividade_atual, 'fim', None)
            id_atividade = getattr(atividade_atual, 'id_atividade', None)
            
            if not all([inicio, fim, id_atividade]):
                logger.debug("Atividade sem timing ou ID definido - não pode agrupar")
                return []
            
            # Verificar todos os equipamentos do gestor
            for equipamento in getattr(gestor_equipamentos, 'masseiras', []):
                # Buscar ocupações da mesma atividade no mesmo período
                ocupacoes = equipamento.obter_ocupacoes_atividade_periodo(
                    id_atividade, inicio, fim
                )
                
                for ocupacao in ocupacoes:
                    # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, ...)
                    if len(ocupacao) >= 5:
                        atividades_encontradas.append({
                            'id_pedido': ocupacao[1],
                            'quantidade': ocupacao[4],
                            'equipamento': equipamento.nome
                        })
            
            return atividades_encontradas
            
        except Exception as e:
            logger.debug(f"Erro ao buscar atividades similares: {e}")
            return []


# Instância global do detector
detector_agrupamentos = DetectorAgrupamentosRuntime()