#!/usr/bin/env python3
"""
🚀 Executor de Pedidos - Sistema de Duas Fases
Responsável pela FASE 2 (EXECUÇÃO) do sistema de duas fases
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from enums.producao.status_pedido import StatusPedido
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ExecutorPedidosDuasFases')


class ExecutorPedidosDuasFases:
    """
    🎯 Executor responsável pela FASE 2 (EXECUÇÃO) do sistema de duas fases.
    
    RESPONSABILIDADES:
    1. Validar pedidos alocados que podem ser executados
    2. Agrupar pedidos por atividade para verificar capacidade mínima
    3. Confirmar ou cancelar grupos baseado na capacidade total
    4. Gerenciar transições de status entre fases
    """
    
    def __init__(self):
        self.pedidos_processados = []
        self.agrupamentos_confirmados = []
        self.pedidos_cancelados = []
    
    def executar_pedidos_alocados(self, pedidos: List[PedidoDeProducao]) -> Dict[str, List[PedidoDeProducao]]:
        """
        🎯 MÉTODO PRINCIPAL: Executa fase 2 para lista de pedidos alocados.
        
        Retorna:
        - confirmados: Pedidos que podem ser executados
        - cancelados: Pedidos cancelados por capacidade insuficiente
        - aguardando: Pedidos aguardando mais agrupamentos
        """
        logger.info(f"🚀 FASE 2 - EXECUÇÃO iniciada para {len(pedidos)} pedidos")
        
        # Filtrar apenas pedidos que podem ser executados
        pedidos_executaveis = [p for p in pedidos if p.pode_ser_executado()]
        
        if not pedidos_executaveis:
            logger.warning("⚠️ Nenhum pedido em status executável encontrado")
            return {"confirmados": [], "cancelados": [], "aguardando": []}
        
        logger.info(f"📋 {len(pedidos_executaveis)} pedidos executáveis encontrados")
        
        # Agrupar pedidos por atividade
        grupos_atividade = self._agrupar_pedidos_por_atividade(pedidos_executaveis)
        
        # Processar cada grupo
        confirmados = []
        cancelados = []
        aguardando = []
        
        for id_atividade, pedidos_grupo in grupos_atividade.items():
            resultado = self._processar_grupo_atividade(id_atividade, pedidos_grupo)
            
            confirmados.extend(resultado["confirmados"])
            cancelados.extend(resultado["cancelados"])
            aguardando.extend(resultado["aguardando"])
        
        logger.info(
            f"🎉 FASE 2 concluída: {len(confirmados)} confirmados, "
            f"{len(cancelados)} cancelados, {len(aguardando)} aguardando"
        )
        
        return {
            "confirmados": confirmados,
            "cancelados": cancelados,
            "aguardando": aguardando
        }
    
    def _agrupar_pedidos_por_atividade(self, pedidos: List[PedidoDeProducao]) -> Dict[int, List[PedidoDeProducao]]:
        """
        📊 Agrupa pedidos por ID de atividade para validação de capacidade.
        """
        grupos = {}
        
        for pedido in pedidos:
            # Obter ID da primeira atividade (assumindo que pedidos são da mesma atividade)
            if pedido.atividades_modulares:
                id_atividade = pedido.atividades_modulares[0].id_atividade
                
                if id_atividade not in grupos:
                    grupos[id_atividade] = []
                
                grupos[id_atividade].append(pedido)
        
        logger.info(f"📊 Agrupamento criado: {len(grupos)} grupos de atividades")
        for id_ativ, lista_pedidos in grupos.items():
            logger.debug(f"   Atividade {id_ativ}: {len(lista_pedidos)} pedidos")
        
        return grupos
    
    def _processar_grupo_atividade(self, id_atividade: int, pedidos_grupo: List[PedidoDeProducao]) -> Dict[str, List[PedidoDeProducao]]:
        """
        🎯 Processa um grupo de pedidos da mesma atividade.
        """
        logger.info(f"🎯 Processando grupo atividade {id_atividade}: {len(pedidos_grupo)} pedidos")
        
        # Calcular quantidade total e capacidades
        quantidade_total = 0.0
        equipamentos_utilizados = set()
        capacidade_minima_necessaria = float('inf')  # Iniciar com infinito para encontrar o mínimo
        
        for pedido in pedidos_grupo:
            for atividade in pedido.atividades_modulares:
                if atividade.id_atividade == id_atividade and atividade.alocada:
                    # Somar quantidade (assumindo que está em quantidade_alocada ou similar)
                    quantidade_atividade = getattr(atividade, 'quantidade', 0)
                    quantidade_total += quantidade_atividade
                    
                    # Coletar equipamentos utilizados
                    if atividade.equipamentos_selecionados:
                        for equip in atividade.equipamentos_selecionados:
                            equipamentos_utilizados.add(equip)
                            # Usar a menor capacidade mínima encontrada como referência
                            if hasattr(equip, 'capacidade_gramas_min'):
                                capacidade_minima_necessaria = min(
                                    capacidade_minima_necessaria, 
                                    equip.capacidade_gramas_min
                                )
        
        # Se não encontrou equipamentos, usar uma capacidade padrão alta para masseiras
        if capacidade_minima_necessaria == float('inf'):
            capacidade_minima_necessaria = 3000.0  # Capacidade mínima padrão para masseiras
            logger.warning(f"⚠️ Equipamentos não encontrados para atividade {id_atividade}, usando capacidade padrão 3000g")
        
        logger.info(
            f"📊 Grupo {id_atividade}: {quantidade_total}g total, "
            f"mínimo necessário: {capacidade_minima_necessaria}g, "
            f"{len(equipamentos_utilizados)} equipamentos"
        )
        
        # DECISÃO: Verificar se atende capacidade mínima
        if quantidade_total >= capacidade_minima_necessaria:
            # ✅ CONFIRMAR GRUPO
            return self._confirmar_grupo_execucao(id_atividade, pedidos_grupo, quantidade_total)
        else:
            # ❌ VERIFICAR POLÍTICA DO GRUPO
            return self._avaliar_grupo_insuficiente(id_atividade, pedidos_grupo, quantidade_total, capacidade_minima_necessaria)
    
    def _confirmar_grupo_execucao(self, id_atividade: int, pedidos_grupo: List[PedidoDeProducao], quantidade_total: float) -> Dict[str, List[PedidoDeProducao]]:
        """
        ✅ Confirma execução de um grupo que atende capacidade mínima.
        """
        logger.info(f"✅ Confirmando execução do grupo {id_atividade}: {quantidade_total}g")
        
        pedidos_confirmados = []
        
        for pedido in pedidos_grupo:
            pedido.marcar_como_em_execucao(
                f"Confirmado em grupo de atividade {id_atividade} com {quantidade_total}g total"
            )
            pedidos_confirmados.append(pedido)
            
            logger.info(f"   ✅ Pedido {pedido.id_pedido} confirmado para execução")
        
        # Registrar agrupamento confirmado
        self.agrupamentos_confirmados.append({
            "id_atividade": id_atividade,
            "quantidade_total": quantidade_total,
            "pedidos": len(pedidos_confirmados),
            "timestamp": datetime.now()
        })
        
        return {"confirmados": pedidos_confirmados, "cancelados": [], "aguardando": []}
    
    def _avaliar_grupo_insuficiente(
        self, 
        id_atividade: int, 
        pedidos_grupo: List[PedidoDeProducao], 
        quantidade_total: float,
        capacidade_minima: float
    ) -> Dict[str, List[PedidoDeProducao]]:
        """
        ❌ Avalia grupo que não atinge capacidade mínima.
        
        Estratégias possíveis:
        1. Aguardar mais pedidos (padrão)
        2. Cancelar se política for restritiva
        3. Timeout baseado em configuração
        """
        logger.warning(
            f"⚠️ Grupo {id_atividade} insuficiente: {quantidade_total}g < {capacidade_minima}g"
        )
        
        # Por enquanto: marcar como aguardando agrupamento
        pedidos_aguardando = []
        
        for pedido in pedidos_grupo:
            pedido.marcar_como_aguardando_agrupamento(
                f"Aguardando mais pedidos da atividade {id_atividade}. "
                f"Atual: {quantidade_total}g, necessário: {capacidade_minima}g"
            )
            pedidos_aguardando.append(pedido)
            
            logger.info(f"   ⏳ Pedido {pedido.id_pedido} aguardando agrupamento")
        
        return {"confirmados": [], "cancelados": [], "aguardando": pedidos_aguardando}
    
    def cancelar_pedidos_por_timeout(self, pedidos: List[PedidoDeProducao], timeout_minutos: int = 30) -> List[PedidoDeProducao]:
        """
        ⏰ Cancela pedidos que estão aguardando há muito tempo.
        """
        agora = datetime.now()
        pedidos_cancelados = []
        
        for pedido in pedidos:
            if pedido.status_pedido == StatusPedido.AGUARDANDO_AGRUPAMENTO:
                # Verificar se há timestamp de quando entrou em aguardando
                # Por simplicidade, usar horário de criação do pedido
                if hasattr(pedido, 'inicio_jornada'):
                    tempo_aguardando = agora - pedido.inicio_jornada
                    
                    if tempo_aguardando.total_seconds() / 60 > timeout_minutos:
                        pedido.marcar_como_cancelado_capacidade(
                            f"Timeout de {timeout_minutos} minutos aguardando agrupamento"
                        )
                        pedidos_cancelados.append(pedido)
                        
                        logger.warning(f"⏰ Pedido {pedido.id_pedido} cancelado por timeout")
        
        return pedidos_cancelados
    
    def obter_estatisticas_execucao(self) -> Dict[str, any]:
        """
        📊 Retorna estatísticas da execução de pedidos.
        """
        return {
            "pedidos_processados": len(self.pedidos_processados),
            "agrupamentos_confirmados": len(self.agrupamentos_confirmados),
            "pedidos_cancelados": len(self.pedidos_cancelados),
            "ultima_execucao": datetime.now().isoformat(),
            "detalhes_agrupamentos": self.agrupamentos_confirmados
        }