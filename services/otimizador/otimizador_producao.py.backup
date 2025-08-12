"""
🎯 OTIMIZADOR DE PRODUÇÃO - Classe Principal
===============================================

Orquestra todo o processo de otimização da produção da padaria:
- Análise de dependências entre pedidos
- Agrupamento inteligente de subprodutos
- Maximização do número de pedidos atendidos

Fase 1: MVP com logs detalhados para validação
"""

from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from models.atividades.pedido_de_producao import PedidoDeProducao
from services.otimizador.analisador_dependencias import AnalisadorDependencias
from services.otimizador.agrupador_subprodutos import AgrupadorSubprodutos
from utils.logs.logger_factory import setup_logger
import traceback

# 🎯 Logger exclusivo do Otimizador
logger = setup_logger('OtimizadorProducao')

@dataclass
class ResultadoOtimizacao:
    """
    Resultado da otimização com métricas detalhadas
    """
    pedidos_originais: List[PedidoDeProducao]
    pedidos_otimizados: List[PedidoDeProducao]
    lotes_subprodutos: List[Dict]
    pedidos_atendidos: List[int]
    pedidos_rejeitados: List[int]
    metricas: Dict[str, float]
    tempo_processamento: float
    detalhes_debug: Dict[str, any]

class OtimizadorProducao:
    """
    🎯 Classe principal do otimizador de produção.
    
    Responsabilidades:
    - Coordenar análise de dependências
    - Gerenciar agrupamento de subprodutos  
    - Aplicar estratégias de otimização
    - Gerar relatórios detalhados com métricas
    """
    
    def __init__(self):
        self.analisador_dependencias = AnalisadorDependencias()
        self.agrupador_subprodutos = AgrupadorSubprodutos()
        
        # Configurações de otimização
        self.config = {
            'max_tentativas_agrupamento': 5,
            'timeout_otimizacao_segundos': 300,
            'priorizar_prazo_curto': True,
            'permitir_rejeicao_pedidos': True,
            'economia_minima_subprodutos': 0.15,  # 15% de economia mínima
            'debug_detalhado': True
        }
        
        logger.info("🎯 Otimizador de Produção inicializado")
        logger.debug(f"📋 Configurações: {self.config}")

    # =============================================================================
    #                           MÉTODO PRINCIPAL
    # =============================================================================

    def otimizar(self, pedidos: List[PedidoDeProducao]) -> ResultadoOtimizacao:
        """
        Método principal de otimização da produção.
        
        Args:
            pedidos: Lista de pedidos a serem otimizados
            
        Returns:
            ResultadoOtimizacao: Resultado completo com métricas e debug
        """
        tempo_inicio = datetime.now()
        
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO OTIMIZAÇÃO DA PRODUÇÃO")
        logger.info("=" * 80)
        logger.info(f"📦 Total de pedidos recebidos: {len(pedidos)}")
        
        try:
            # Validação inicial
            self._validar_entrada(pedidos)
            
            # 1. Análise de dependências
            logger.info("\n🔍 FASE 1: Análise de Dependências")
            grafo_dependencias = self._analisar_dependencias(pedidos)
            
            # 2. Agrupamento de subprodutos
            logger.info("\n🔗 FASE 2: Agrupamento de Subprodutos")
            lotes_otimizados = self._agrupar_subprodutos(pedidos, grafo_dependencias)
            
            # 3. Seleção de pedidos otimizada
            logger.info("\n🎯 FASE 3: Seleção Otimizada de Pedidos")
            pedidos_selecionados, pedidos_rejeitados = self._selecionar_pedidos_otimo(
                pedidos, lotes_otimizados
            )
            
            # 4. Aplicação das otimizações
            logger.info("\n⚙️ FASE 4: Aplicação das Otimizações")
            pedidos_otimizados = self._aplicar_otimizacoes(pedidos_selecionados, lotes_otimizados)
            
            # 5. Cálculo de métricas
            logger.info("\n📊 FASE 5: Cálculo de Métricas")
            metricas = self._calcular_metricas(pedidos, pedidos_otimizados, lotes_otimizados)
            
            # Preparar resultado
            tempo_fim = datetime.now()
            tempo_processamento = (tempo_fim - tempo_inicio).total_seconds()
            
            resultado = ResultadoOtimizacao(
                pedidos_originais=pedidos,
                pedidos_otimizados=pedidos_otimizados,
                lotes_subprodutos=lotes_otimizados,
                pedidos_atendidos=[p.id_pedido for p in pedidos_selecionados],
                pedidos_rejeitados=pedidos_rejeitados,
                metricas=metricas,
                tempo_processamento=tempo_processamento,
                detalhes_debug=self._gerar_debug_detalhado(pedidos, lotes_otimizados, grafo_dependencias)
            )
            
            self._log_resultado_final(resultado)
            return resultado
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na otimização: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            
            # Retornar resultado de fallback
            tempo_processamento = (datetime.now() - tempo_inicio).total_seconds()
            return self._criar_resultado_fallback(pedidos, tempo_processamento, str(e))

    # =============================================================================
    #                        VALIDAÇÃO E PREPARAÇÃO
    # =============================================================================

    def _validar_entrada(self, pedidos: List[PedidoDeProducao]) -> None:
        """Valida se os pedidos estão em formato adequado para otimização"""
        logger.debug("🔍 Validando entrada...")
        
        if not pedidos:
            raise ValueError("Lista de pedidos está vazia")
        
        for i, pedido in enumerate(pedidos):
            if not hasattr(pedido, 'ficha_tecnica_modular') or pedido.ficha_tecnica_modular is None:
                logger.warning(f"⚠️ Pedido {pedido.id_pedido} sem ficha técnica montada")
            
            if not hasattr(pedido, 'fim_jornada') or pedido.fim_jornada is None:
                raise ValueError(f"Pedido {pedido.id_pedido} sem prazo definido")
            
            logger.debug(f"✅ Pedido {i+1}/{len(pedidos)} validado: {pedido.id_pedido}")
        
        logger.info(f"✅ Validação concluída: {len(pedidos)} pedidos válidos")

    # =============================================================================
    #                        FASE 1: ANÁLISE DE DEPENDÊNCIAS
    # =============================================================================

    def _analisar_dependencias(self, pedidos: List[PedidoDeProducao]) -> Dict:
        """Analisa dependências entre pedidos via subprodutos comuns"""
        logger.info("🔍 Iniciando análise de dependências...")
        
        try:
            grafo = self.analisador_dependencias.construir_grafo_dependencias(pedidos)
            
            # Log detalhado do grafo
            total_nos = len(grafo.get('nos', {}))
            total_arestas = len(grafo.get('arestas', []))
            
            logger.info(f"📊 Grafo construído: {total_nos} nós, {total_arestas} arestas")
            
            if self.config['debug_detalhado']:
                self._debug_grafo_dependencias(grafo)
            
            return grafo
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de dependências: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return {'nos': {}, 'arestas': [], 'subprodutos_compartilhados': {}}

    def _debug_grafo_dependencias(self, grafo: Dict) -> None:
        """Log detalhado do grafo de dependências para debug"""
        logger.debug("🐛 DEBUG: Detalhes do grafo de dependências")
        
        for pedido_id, info in grafo.get('nos', {}).items():
            logger.debug(f"  📦 Pedido {pedido_id}: {info.get('subprodutos', [])}")
        
        for aresta in grafo.get('arestas', []):
            logger.debug(f"  🔗 {aresta['origem']} → {aresta['destino']}: {aresta['subprodutos_comuns']}")
        
        subprodutos_compartilhados = grafo.get('subprodutos_compartilhados', {})
        logger.debug(f"  📋 Subprodutos compartilhados: {len(subprodutos_compartilhados)} tipos")
        
        for subproduto, pedidos_ids in subprodutos_compartilhados.items():
            if len(pedidos_ids) > 1:
                logger.debug(f"    🔄 Subproduto {subproduto}: usado por pedidos {pedidos_ids}")

    # =============================================================================
    #                        FASE 2: AGRUPAMENTO DE SUBPRODUTOS
    # =============================================================================

    def _agrupar_subprodutos(self, pedidos: List[PedidoDeProducao], grafo: Dict) -> List[Dict]:
        """Agrupa subprodutos similares para otimizar produção"""
        logger.info("🔗 Iniciando agrupamento de subprodutos...")
        
        try:
            lotes = self.agrupador_subprodutos.criar_lotes_otimizados(pedidos, grafo)
            
            logger.info(f"📦 Criados {len(lotes)} lotes otimizados")
            
            # Estatísticas dos lotes
            total_subprodutos_originais = sum(
                len(p.ficha_tecnica_modular.calcular_quantidade_itens()) 
                for p in pedidos if p.ficha_tecnica_modular
            )
            
            total_subprodutos_lotes = sum(len(lote.get('itens', [])) for lote in lotes)
            economia_percentual = ((total_subprodutos_originais - total_subprodutos_lotes) / 
                                 max(total_subprodutos_originais, 1)) * 100
            
            logger.info(f"📊 Economia de subprodutos: {economia_percentual:.1f}%")
            logger.info(f"   Original: {total_subprodutos_originais} → Otimizado: {total_subprodutos_lotes}")
            
            if self.config['debug_detalhado']:
                self._debug_lotes_subprodutos(lotes)
            
            return lotes
            
        except Exception as e:
            logger.error(f"❌ Erro no agrupamento de subprodutos: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return []

    def _debug_lotes_subprodutos(self, lotes: List[Dict]) -> None:
        """Log detalhado dos lotes para debug"""
        logger.debug("🐛 DEBUG: Detalhes dos lotes de subprodutos")
        
        for i, lote in enumerate(lotes):
            logger.debug(f"  📦 Lote {i+1}:")
            logger.debug(f"    ID: {lote.get('id', 'N/A')}")
            logger.debug(f"    Tipo: {lote.get('tipo', 'N/A')}")
            logger.debug(f"    Pedidos: {lote.get('pedidos_ids', [])}")
            logger.debug(f"    Itens: {len(lote.get('itens', []))}")
            logger.debug(f"    Janela temporal: {lote.get('janela_temporal', 'N/A')}")
            logger.debug(f"    Prioridade: {lote.get('prioridade', 'N/A')}")
            
            if lote.get('economia_estimada'):
                logger.debug(f"    💰 Economia estimada: {lote['economia_estimada']:.1f}%")

    # =============================================================================
    #                        FASE 3: SELEÇÃO OTIMIZADA
    # =============================================================================

    def _selecionar_pedidos_otimo(self, pedidos: List[PedidoDeProducao], 
                                 lotes: List[Dict]) -> Tuple[List[PedidoDeProducao], List[int]]:
        """
        Seleciona quais pedidos atender para maximizar o aproveitamento.
        Usa algoritmo guloso baseado em valor/custo e restrições temporais.
        """
        logger.info("🎯 Iniciando seleção otimizada de pedidos...")
        
        # Calcular métricas para cada pedido
        metricas_pedidos = []
        for pedido in pedidos:
            metrica = self._calcular_metrica_pedido(pedido, lotes)
            metricas_pedidos.append((pedido, metrica))
            
            logger.debug(f"📊 Pedido {pedido.id_pedido}: score {metrica['score']:.2f}")
        
        # Ordenar por score (maior primeiro)
        metricas_pedidos.sort(key=lambda x: x[1]['score'], reverse=True)
        
        # Seleção gulosa considerando restrições
        pedidos_selecionados = []
        pedidos_rejeitados = []
        recursos_utilizados = set()
        
        for pedido, metrica in metricas_pedidos:
            if self._pode_atender_pedido(pedido, metrica, recursos_utilizados, lotes):
                pedidos_selecionados.append(pedido)
                self._marcar_recursos_utilizados(pedido, recursos_utilizados)
                logger.debug(f"✅ Pedido {pedido.id_pedido} selecionado (score: {metrica['score']:.2f})")
            else:
                pedidos_rejeitados.append(pedido.id_pedido)
                logger.debug(f"❌ Pedido {pedido.id_pedido} rejeitado (conflito de recursos)")
        
        logger.info(f"📊 Seleção concluída: {len(pedidos_selecionados)} atendidos, {len(pedidos_rejeitados)} rejeitados")
        
        return pedidos_selecionados, pedidos_rejeitados

    def _calcular_metrica_pedido(self, pedido: PedidoDeProducao, lotes: List[Dict]) -> Dict:
        """Calcula métrica de valor para um pedido"""
        # Fatores de score
        prazo_urgencia = self._calcular_urgencia_prazo(pedido)
        beneficio_lotes = self._calcular_beneficio_lotes(pedido, lotes)
        complexidade = self._calcular_complexidade_pedido(pedido)
        
        # Score final (quanto maior, melhor)
        score = (prazo_urgencia * 0.4 + 
                beneficio_lotes * 0.4 + 
                (1 - complexidade) * 0.2)
        
        return {
            'score': score,
            'prazo_urgencia': prazo_urgencia,
            'beneficio_lotes': beneficio_lotes,
            'complexidade': complexidade
        }

    def _calcular_urgencia_prazo(self, pedido: PedidoDeProducao) -> float:
        """Calcula urgência baseada no prazo (0-1, maior = mais urgente)"""
        try:
            agora = datetime.now()
            tempo_restante = pedido.fim_jornada - agora
            
            # Normalizar para 0-1 (assume até 3 dias como máximo)
            max_tempo = timedelta(days=3)
            urgencia = 1.0 - min(tempo_restante.total_seconds() / max_tempo.total_seconds(), 1.0)
            
            return max(0.0, min(1.0, urgencia))
        except:
            return 0.5  # Valor médio se houver erro

    def _calcular_beneficio_lotes(self, pedido: PedidoDeProducao, lotes: List[Dict]) -> float:
        """Calcula benefício do pedido para os lotes (0-1, maior = mais benefício)"""
        if not lotes:
            return 0.0
        
        beneficio_total = 0.0
        lotes_relevantes = 0
        
        for lote in lotes:
            if pedido.id_pedido in lote.get('pedidos_ids', []):
                lotes_relevantes += 1
                beneficio_total += lote.get('economia_estimada', 0.0) / 100.0
        
        return beneficio_total / max(lotes_relevantes, 1)

    def _calcular_complexidade_pedido(self, pedido: PedidoDeProducao) -> float:
        """Calcula complexidade do pedido (0-1, maior = mais complexo)"""
        if not pedido.ficha_tecnica_modular:
            return 1.0  # Máxima complexidade se não há dados
        
        try:
            # Fatores de complexidade
            num_atividades = len(pedido.atividades_modulares) if hasattr(pedido, 'atividades_modulares') else 5
            num_subprodutos = len(pedido.ficha_tecnica_modular.calcular_quantidade_itens())
            
            # Normalizar (assume máximo de 10 atividades e 20 subprodutos)
            complexidade_atividades = min(num_atividades / 10.0, 1.0)
            complexidade_subprodutos = min(num_subprodutos / 20.0, 1.0)
            
            return (complexidade_atividades + complexidade_subprodutos) / 2.0
        except:
            return 0.5  # Valor médio se houver erro

    def _pode_atender_pedido(self, pedido: PedidoDeProducao, metrica: Dict, 
                           recursos_utilizados: Set, lotes: List[Dict]) -> bool:
        """Verifica se é possível atender o pedido sem conflitos"""
        # Por enquanto, implementação simples
        # Em versões futuras, pode incluir verificação detalhada de recursos
        
        # Verificar se score mínimo é atingido
        if metrica['score'] < 0.3:
            return False
        
        # Verificar conflitos temporais básicos (simplificado)
        pedido_id = f"pedido_{pedido.id_pedido}"
        return pedido_id not in recursos_utilizados

    def _marcar_recursos_utilizados(self, pedido: PedidoDeProducao, recursos_utilizados: Set) -> None:
        """Marca recursos como utilizados por um pedido"""
        recursos_utilizados.add(f"pedido_{pedido.id_pedido}")

    # =============================================================================
    #                        FASE 4: APLICAÇÃO DAS OTIMIZAÇÕES
    # =============================================================================

    def _aplicar_otimizacoes(self, pedidos: List[PedidoDeProducao], 
                           lotes: List[Dict]) -> List[PedidoDeProducao]:
        """Aplica as otimizações aos pedidos selecionados"""
        logger.info("⚙️ Aplicando otimizações aos pedidos selecionados...")
        
        pedidos_otimizados = []
        
        for pedido in pedidos:
            try:
                pedido_otimizado = self._otimizar_pedido_individual(pedido, lotes)
                pedidos_otimizados.append(pedido_otimizado)
                
                logger.debug(f"✅ Pedido {pedido.id_pedido} otimizado com sucesso")
                
            except Exception as e:
                logger.error(f"❌ Erro ao otimizar pedido {pedido.id_pedido}: {e}")
                # Adicionar pedido original se otimização falhar
                pedidos_otimizados.append(pedido)
        
        logger.info(f"⚙️ Otimização aplicada a {len(pedidos_otimizados)} pedidos")
        return pedidos_otimizados

    def _otimizar_pedido_individual(self, pedido: PedidoDeProducao, lotes: List[Dict]) -> PedidoDeProducao:
        """Aplica otimizações a um pedido específico"""
        # Por enquanto, retorna o pedido original
        # Em versões futuras, pode modificar atividades baseado nos lotes
        
        logger.debug(f"🔧 Otimizando pedido {pedido.id_pedido}...")
        
        # Encontrar lotes relevantes para este pedido
        lotes_relevantes = [
            lote for lote in lotes 
            if pedido.id_pedido in lote.get('pedidos_ids', [])
        ]
        
        if lotes_relevantes:
            logger.debug(f"  📦 Pedido {pedido.id_pedido} participa de {len(lotes_relevantes)} lotes")
        
        return pedido

    # =============================================================================
    #                        FASE 5: MÉTRICAS E RESULTADOS
    # =============================================================================

    def _calcular_metricas(self, pedidos_originais: List[PedidoDeProducao],
                          pedidos_otimizados: List[PedidoDeProducao],
                          lotes: List[Dict]) -> Dict[str, float]:
        """Calcula métricas de performance da otimização"""
        logger.info("📊 Calculando métricas de performance...")
        
        try:
            metricas = {
                # Métricas básicas
                'total_pedidos_originais': len(pedidos_originais),
                'total_pedidos_atendidos': len(pedidos_otimizados),
                'taxa_atendimento': len(pedidos_otimizados) / max(len(pedidos_originais), 1) * 100,
                'total_lotes_criados': len(lotes),
                
                # Métricas de otimização
                'economia_subprodutos_estimada': self._calcular_economia_total(lotes),
                'reducao_tempo_estimada': self._calcular_reducao_tempo(lotes),
                'melhoria_utilizacao_recursos': self._calcular_melhoria_recursos(lotes),
                
                # Métricas de qualidade
                'score_medio_pedidos': self._calcular_score_medio(pedidos_otimizados, lotes),
                'distribuicao_prazos': self._analisar_distribuicao_prazos(pedidos_otimizados)
            }
            
            logger.info("📈 Métricas calculadas:")
            for nome, valor in metricas.items():
                if isinstance(valor, float):
                    logger.info(f"   {nome}: {valor:.2f}")
                else:
                    logger.info(f"   {nome}: {valor}")
            
            return metricas
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de métricas: {e}")
            return {'erro_calculo_metricas': True}

    def _calcular_economia_total(self, lotes: List[Dict]) -> float:
        """Calcula economia total estimada dos lotes"""
        if not lotes:
            return 0.0
        
        economia_media = sum(lote.get('economia_estimada', 0.0) for lote in lotes) / len(lotes)
        return economia_media

    def _calcular_reducao_tempo(self, lotes: List[Dict]) -> float:
        """Calcula redução de tempo estimada"""
        # Estimativa baseada no número de lotes e economia
        if not lotes:
            return 0.0
        
        # Estimativa simples: cada lote economiza em média 10% do tempo
        return len(lotes) * 10.0

    def _calcular_melhoria_recursos(self, lotes: List[Dict]) -> float:
        """Calcula melhoria na utilização de recursos"""
        # Estimativa baseada na consolidação de subprodutos
        if not lotes:
            return 0.0
        
        total_pedidos_consolidados = sum(len(lote.get('pedidos_ids', [])) for lote in lotes)
        return min(total_pedidos_consolidados * 5.0, 50.0)  # Máximo 50%

    def _calcular_score_medio(self, pedidos: List[PedidoDeProducao], lotes: List[Dict]) -> float:
        """Calcula score médio dos pedidos otimizados"""
        if not pedidos:
            return 0.0
        
        scores = []
        for pedido in pedidos:
            metrica = self._calcular_metrica_pedido(pedido, lotes)
            scores.append(metrica['score'])
        
        return sum(scores) / len(scores)

    def _analisar_distribuicao_prazos(self, pedidos: List[PedidoDeProducao]) -> float:
        """Analisa distribuição dos prazos dos pedidos"""
        if not pedidos:
            return 0.0
        
        try:
            agora = datetime.now()
            prazos = [(p.fim_jornada - agora).total_seconds() / 3600 for p in pedidos]  # em horas
            
            # Retorna prazo médio em horas
            return sum(prazos) / len(prazos)
        except:
            return 0.0

    # =============================================================================
    #                        DEBUG E RELATÓRIOS
    # =============================================================================

    def _gerar_debug_detalhado(self, pedidos: List[PedidoDeProducao], 
                              lotes: List[Dict], grafo: Dict) -> Dict:
        """Gera informações detalhadas para debug"""
        return {
            'configuracao_otimizador': self.config,
            'estatisticas_grafo': {
                'total_nos': len(grafo.get('nos', {})),
                'total_arestas': len(grafo.get('arestas', [])),
                'subprodutos_compartilhados': len(grafo.get('subprodutos_compartilhados', {}))
            },
            'estatisticas_lotes': {
                'total_lotes': len(lotes),
                'lotes_por_tipo': self._contar_lotes_por_tipo(lotes),
                'media_pedidos_por_lote': sum(len(l.get('pedidos_ids', [])) for l in lotes) / max(len(lotes), 1)
            },
            'distribuicao_prazos': {
                'prazos_urgentes': sum(1 for p in pedidos if self._calcular_urgencia_prazo(p) > 0.7),
                'prazos_normais': sum(1 for p in pedidos if 0.3 <= self._calcular_urgencia_prazo(p) <= 0.7),
                'prazos_flexiveis': sum(1 for p in pedidos if self._calcular_urgencia_prazo(p) < 0.3)
            }
        }

    def _contar_lotes_por_tipo(self, lotes: List[Dict]) -> Dict[str, int]:
        """Conta lotes por tipo"""
        contagem = {}
        for lote in lotes:
            tipo = lote.get('tipo', 'desconhecido')
            contagem[tipo] = contagem.get(tipo, 0) + 1
        return contagem

    def _log_resultado_final(self, resultado: ResultadoOtimizacao) -> None:
        """Log do resultado final da otimização"""
        logger.info("=" * 80)
        logger.info("🎉 OTIMIZAÇÃO CONCLUÍDA COM SUCESSO")
        logger.info("=" * 80)
        
        logger.info(f"⏱️ Tempo de processamento: {resultado.tempo_processamento:.2f}s")
        logger.info(f"📦 Pedidos atendidos: {len(resultado.pedidos_atendidos)}/{len(resultado.pedidos_originais)}")
        logger.info(f"📊 Taxa de atendimento: {resultado.metricas.get('taxa_atendimento', 0):.1f}%")
        logger.info(f"🔗 Lotes criados: {len(resultado.lotes_subprodutos)}")
        logger.info(f"💰 Economia estimada: {resultado.metricas.get('economia_subprodutos_estimada', 0):.1f}%")
        
        if resultado.pedidos_rejeitados:
            logger.warning(f"⚠️ Pedidos rejeitados: {resultado.pedidos_rejeitados}")

    def _criar_resultado_fallback(self, pedidos: List[PedidoDeProducao], 
                                 tempo_processamento: float, erro: str) -> ResultadoOtimizacao:
        """Cria resultado de fallback em caso de erro"""
        logger.warning("🔧 Criando resultado de fallback devido a erro...")
        
        return ResultadoOtimizacao(
            pedidos_originais=pedidos,
            pedidos_otimizados=pedidos,  # Sem otimização
            lotes_subprodutos=[],
            pedidos_atendidos=[p.id_pedido for p in pedidos],
            pedidos_rejeitados=[],
            metricas={
                'total_pedidos_originais': len(pedidos),
                'total_pedidos_atendidos': len(pedidos),
                'taxa_atendimento': 100.0,
                'erro_otimizacao': True,
                'mensagem_erro': erro
            },
            tempo_processamento=tempo_processamento,
            detalhes_debug={'erro': erro, 'fallback': True}
        )