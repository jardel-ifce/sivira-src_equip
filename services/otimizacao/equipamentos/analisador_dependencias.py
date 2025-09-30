"""
🔍 ANALISADOR DE DEPENDÊNCIAS
=============================

Analisa dependências entre pedidos através de subprodutos compartilhados.
Constrói grafo de dependências para identificar oportunidades de otimização.

Funcionalidades:
- Mapeamento de subprodutos por pedido
- Construção de grafo de dependências
- Identificação de clusters de otimização
- Análise de janelas temporais compatíveis
"""

from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from models.atividades.pedido_de_producao import PedidoDeProducao
from enums.producao.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger
import traceback

# 🔍 Logger exclusivo do Analisador de Dependências
logger = setup_logger('AnalisadorDependencias')

class AnalisadorDependencias:
    """
    🔍 Classe responsável por analisar dependências entre pedidos.
    
    Identifica:
    - Subprodutos compartilhados entre pedidos
    - Possibilidades de agrupamento temporal
    - Clusters de pedidos interdependentes
    - Métricas de economia potencial
    """
    
    def __init__(self):
        self.config = {
            'janela_agrupamento_horas': 12,  # Janela máxima para agrupar pedidos
            'margem_seguranca_horas': 1,    # Margem de segurança temporal
            'min_economia_percentual': 5,  # Economia mínima para considerar agrupamento
            'max_pedidos_por_cluster': 5,   # Máximo de pedidos por cluster
            'debug_detalhado': True
        }
        
        logger.info("🔍 Analisador de Dependências inicializado")
        logger.debug(f"⚙️ Configurações: {self.config}")

    # =============================================================================
    #                           MÉTODO PRINCIPAL
    # =============================================================================

    def construir_grafo_dependencias(self, pedidos: List[PedidoDeProducao]) -> Dict:
        """
        Constrói grafo completo de dependências entre pedidos.
        
        Args:
            pedidos: Lista de pedidos para análise
            
        Returns:
            Dict: Grafo com nós, arestas e metadados
        """
        logger.info("🔍 Construindo grafo de dependências...")
        logger.info(f"📦 Analisando {len(pedidos)} pedidos")
        
        try:
            # 1. Mapear subprodutos por pedido
            logger.debug("📋 Fase 1: Mapeamento de subprodutos")
            mapa_subprodutos = self._mapear_subprodutos_pedidos(pedidos)
            
            # 2. Identificar subprodutos compartilhados
            logger.debug("🔗 Fase 2: Identificação de subprodutos compartilhados")
            subprodutos_compartilhados = self._identificar_subprodutos_compartilhados(mapa_subprodutos)
            
            # 3. Construir nós do grafo
            logger.debug("🎯 Fase 3: Construção de nós")
            nos = self._construir_nos_grafo(pedidos, mapa_subprodutos)
            
            # 4. Construir arestas do grafo
            logger.debug("🔗 Fase 4: Construção de arestas")
            arestas = self._construir_arestas_grafo(pedidos, subprodutos_compartilhados)
            
            # 5. Analisar clusters
            logger.debug("🌐 Fase 5: Análise de clusters")
            clusters = self._identificar_clusters(nos, arestas)
            
            # 6. Calcular métricas
            logger.debug("📊 Fase 6: Cálculo de métricas")
            metricas = self._calcular_metricas_grafo(nos, arestas, clusters)
            
            # Construir resultado final
            grafo = {
                'nos': nos,
                'arestas': arestas,
                'subprodutos_compartilhados': subprodutos_compartilhados,
                'clusters': clusters,
                'metricas': metricas,
                'timestamp': datetime.now(),
                'total_pedidos': len(pedidos)
            }
            
            self._log_estatisticas_grafo(grafo)
            return grafo
            
        except Exception as e:
            logger.error(f"❌ Erro na construção do grafo: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return self._criar_grafo_vazio(pedidos)

    # =============================================================================
    #                        MAPEAMENTO DE SUBPRODUTOS
    # =============================================================================

    def _mapear_subprodutos_pedidos(self, pedidos: List[PedidoDeProducao]) -> Dict[int, Dict]:
        """
        Mapeia todos os subprodutos necessários para cada pedido.
        
        Returns:
            Dict: {pedido_id: {'subprodutos': {id_sub: quantidade}, 'metadados': {...}}}
        """
        logger.debug("📋 Iniciando mapeamento de subprodutos...")
        
        mapa_subprodutos = {}
        
        for pedido in pedidos:
            try:
                logger.debug(f"🔍 Analisando pedido {pedido.id_pedido}...")
                
                subprodutos_pedido = self._extrair_subprodutos_pedido(pedido)
                metadados_pedido = self._extrair_metadados_pedido(pedido)
                
                mapa_subprodutos[pedido.id_pedido] = {
                    'subprodutos': subprodutos_pedido,
                    'metadados': metadados_pedido
                }
                
                logger.debug(f"✅ Pedido {pedido.id_pedido}: {len(subprodutos_pedido)} subprodutos mapeados")
                
                if self.config['debug_detalhado']:
                    for id_sub, qtd in subprodutos_pedido.items():
                        logger.debug(f"   📦 Subproduto {id_sub}: {qtd:.2f} unidades")
                
            except Exception as e:
                logger.error(f"❌ Erro ao mapear subprodutos do pedido {pedido.id_pedido}: {e}")
                mapa_subprodutos[pedido.id_pedido] = {'subprodutos': {}, 'metadados': {}}
        
        total_subprodutos_unicos = len(set().union(*[
            data['subprodutos'].keys() for data in mapa_subprodutos.values()
        ]))
        
        logger.info(f"📊 Mapeamento concluído: {total_subprodutos_unicos} subprodutos únicos identificados")
        return mapa_subprodutos

    def _extrair_subprodutos_pedido(self, pedido: PedidoDeProducao) -> Dict[int, float]:
        """Extrai subprodutos e quantidades de um pedido"""
        subprodutos = {}
        
        if not pedido.ficha_tecnica_modular:
            logger.warning(f"⚠️ Pedido {pedido.id_pedido} sem ficha técnica")
            return subprodutos
        
        try:
            estimativas = pedido.ficha_tecnica_modular.calcular_quantidade_itens()
            
            for item_dict, quantidade in estimativas:
                tipo_item = item_dict.get("tipo_item")
                id_ficha = item_dict.get("id_ficha_tecnica")
                
                if tipo_item == "SUBPRODUTO" and id_ficha:
                    subprodutos[id_ficha] = quantidade
                    logger.debug(f"   🔍 Subproduto {id_ficha}: {quantidade:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair subprodutos do pedido {pedido.id_pedido}: {e}")
        
        return subprodutos

    def _extrair_metadados_pedido(self, pedido: PedidoDeProducao) -> Dict:
        """Extrai metadados relevantes de um pedido"""
        try:
            return {
                'id_produto': pedido.id_produto,
                'tipo_item': pedido.tipo_item.name if pedido.tipo_item else "DESCONHECIDO",
                'quantidade': pedido.quantidade,
                'inicio_jornada': pedido.inicio_jornada,
                'fim_jornada': pedido.fim_jornada,
                'duracao_janela': (pedido.fim_jornada - pedido.inicio_jornada).total_seconds() / 3600,  # em horas
                'prazo_restante': (pedido.fim_jornada - datetime.now()).total_seconds() / 3600  # em horas
            }
        except Exception as e:
            logger.error(f"❌ Erro ao extrair metadados do pedido {pedido.id_pedido}: {e}")
            return {}

    # =============================================================================
    #                    IDENTIFICAÇÃO DE COMPARTILHAMENTOS
    # =============================================================================

    def _identificar_subprodutos_compartilhados(self, mapa_subprodutos: Dict) -> Dict[int, Dict]:
        """
        Identifica subprodutos compartilhados entre múltiplos pedidos.
        
        Returns:
            Dict: {id_subproduto: {'pedidos': [ids], 'quantidades': {pedido_id: qtd}, ...}}
        """
        logger.debug("🔗 Identificando subprodutos compartilhados...")
        
        # Inverter o mapeamento: subproduto -> pedidos
        subprodutos_compartilhados = defaultdict(lambda: {
            'pedidos': [],
            'quantidades': {},
            'quantidade_total': 0.0,
            'economia_potencial': 0.0
        })
        
        for pedido_id, data in mapa_subprodutos.items():
            for id_subproduto, quantidade in data['subprodutos'].items():
                subprodutos_compartilhados[id_subproduto]['pedidos'].append(pedido_id)
                subprodutos_compartilhados[id_subproduto]['quantidades'][pedido_id] = quantidade
                subprodutos_compartilhados[id_subproduto]['quantidade_total'] += quantidade
        
        # Filtrar apenas subprodutos realmente compartilhados e calcular economia
        compartilhados_filtrados = {}
        for id_subproduto, info in subprodutos_compartilhados.items():
            if len(info['pedidos']) > 1:  # Compartilhado entre múltiplos pedidos
                # Calcular economia potencial
                economia = self._calcular_economia_subproduto(info)
                info['economia_potencial'] = economia
                
                compartilhados_filtrados[id_subproduto] = dict(info)
                
                logger.debug(f"🔗 Subproduto {id_subproduto}: {len(info['pedidos'])} pedidos, "
                           f"economia {economia:.1f}%")
        
        logger.info(f"🔗 Identificados {len(compartilhados_filtrados)} subprodutos compartilhados")
        return compartilhados_filtrados

    def _calcular_economia_subproduto(self, info_subproduto: Dict) -> float:
        """Calcula economia potencial de um subproduto compartilhado"""
        try:
            pedidos = info_subproduto['pedidos']
            quantidades = info_subproduto['quantidades']
            
            if len(pedidos) <= 1:
                return 0.0
            
            # Economia básica: porcentagem de redução na produção individual
            # Assume que agrupar reduz overhead de setup/limpeza
            num_pedidos = len(pedidos)
            economia_base = (num_pedidos - 1) / num_pedidos * 100  # % de economia
            
            # Ajustar por quantidade total (maiores quantidades = maior economia)
            quantidade_total = info_subproduto['quantidade_total']
            fator_quantidade = min(quantidade_total / 100.0, 2.0)  # Máximo 2x
            
            economia_ajustada = economia_base * fator_quantidade
            return min(economia_ajustada, 80.0)  # Máximo 80% de economia
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular economia de subproduto: {e}")
            return 0.0

    # =============================================================================
    #                        CONSTRUÇÃO DO GRAFO
    # =============================================================================

    def _construir_nos_grafo(self, pedidos: List[PedidoDeProducao], 
                            mapa_subprodutos: Dict) -> Dict[int, Dict]:
        """Constrói os nós do grafo (um nó por pedido)"""
        logger.debug("🎯 Construindo nós do grafo...")
        
        nos = {}
        
        for pedido in pedidos:
            try:
                pedido_id = pedido.id_pedido
                data_subprodutos = mapa_subprodutos.get(pedido_id, {})
                
                no = {
                    'id_pedido': pedido_id,
                    'subprodutos': data_subprodutos.get('subprodutos', {}),
                    'metadados': data_subprodutos.get('metadados', {}),
                    'grau_conectividade': 0,  # Será calculado após construir arestas
                    'clusters': [],  # Clusters aos quais pertence
                    'potencial_economia': 0.0  # Potencial de economia deste nó
                }
                
                nos[pedido_id] = no
                logger.debug(f"✅ Nó criado para pedido {pedido_id}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao criar nó para pedido {pedido.id_pedido}: {e}")
        
        logger.info(f"🎯 Criados {len(nos)} nós no grafo")
        return nos

    def _construir_arestas_grafo(self, pedidos: List[PedidoDeProducao], 
                                subprodutos_compartilhados: Dict) -> List[Dict]:
        """Constrói as arestas do grafo (conexões entre pedidos)"""
        logger.debug("🔗 Construindo arestas do grafo...")
        
        arestas = []
        mapa_pedidos = {p.id_pedido: p for p in pedidos}
        
        # Para cada subproduto compartilhado, criar arestas entre todos os pares de pedidos
        for id_subproduto, info in subprodutos_compartilhados.items():
            pedidos_ids = info['pedidos']
            
            # Criar arestas entre todos os pares
            for i in range(len(pedidos_ids)):
                for j in range(i + 1, len(pedidos_ids)):
                    pedido_origem = pedidos_ids[i]
                    pedido_destino = pedidos_ids[j]
                    
                    try:
                        # Verificar compatibilidade temporal
                        compatibilidade = self._verificar_compatibilidade_temporal(
                            mapa_pedidos[pedido_origem],
                            mapa_pedidos[pedido_destino]
                        )
                        
                        if compatibilidade['compativel']:
                            aresta = {
                                'origem': pedido_origem,
                                'destino': pedido_destino,
                                'subprodutos_comuns': [id_subproduto],
                                'peso': self._calcular_peso_aresta(info, compatibilidade),
                                'compatibilidade_temporal': compatibilidade,
                                'economia_estimada': info['economia_potencial']
                            }
                            
                            # Verificar se já existe aresta entre esses pedidos
                            aresta_existente = self._encontrar_aresta_existente(
                                arestas, pedido_origem, pedido_destino
                            )
                            
                            if aresta_existente:
                                # Adicionar subproduto à aresta existente
                                aresta_existente['subprodutos_comuns'].append(id_subproduto)
                                aresta_existente['peso'] += aresta['peso']
                                aresta_existente['economia_estimada'] += aresta['economia_estimada']
                            else:
                                # Criar nova aresta
                                arestas.append(aresta)
                            
                            logger.debug(f"🔗 Aresta: {pedido_origem} ↔ {pedido_destino} "
                                       f"(subproduto {id_subproduto})")
                    
                    except Exception as e:
                        logger.error(f"❌ Erro ao criar aresta {pedido_origem}-{pedido_destino}: {e}")
        
        logger.info(f"🔗 Criadas {len(arestas)} arestas no grafo")
        return arestas

    def _verificar_compatibilidade_temporal(self, pedido1: PedidoDeProducao, 
                                          pedido2: PedidoDeProducao) -> Dict:
        """Verifica se dois pedidos são temporalmente compatíveis para agrupamento"""
        try:
            # Extrair janelas temporais
            inicio1, fim1 = pedido1.inicio_jornada, pedido1.fim_jornada
            inicio2, fim2 = pedido2.inicio_jornada, pedido2.fim_jornada
            
            # Calcular sobreposição
            inicio_sobreposto = max(inicio1, inicio2)
            fim_sobreposto = min(fim1, fim2)
            
            if inicio_sobreposto >= fim_sobreposto:
                # Sem sobreposição
                return {
                    'compativel': False,
                    'razao': 'sem_sobreposicao_temporal',
                    'gap_horas': (inicio_sobreposto - fim_sobreposto).total_seconds() / 3600
                }
            
            # Calcular duração da sobreposição
            duracao_sobreposicao = (fim_sobreposto - inicio_sobreposto).total_seconds() / 3600
            
            # Verificar se sobreposição é suficiente
            min_sobreposicao = self.config['janela_agrupamento_horas']
            
            if duracao_sobreposicao < min_sobreposicao:
                return {
                    'compativel': False,
                    'razao': 'sobreposicao_insuficiente',
                    'sobreposicao_horas': duracao_sobreposicao
                }
            
            return {
                'compativel': True,
                'sobreposicao_horas': duracao_sobreposicao,
                'janela_comum': (inicio_sobreposto, fim_sobreposto),
                'margem_seguranca': duracao_sobreposicao - min_sobreposicao
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de compatibilidade temporal: {e}")
            return {'compativel': False, 'razao': 'erro_calculo'}

    def _calcular_peso_aresta(self, info_subproduto: Dict, compatibilidade: Dict) -> float:
        """Calcula o peso de uma aresta baseado na economia e compatibilidade"""
        try:
            # Peso base: economia potencial
            peso_base = info_subproduto.get('economia_potencial', 0.0)
            
            # Ajustar por compatibilidade temporal
            if compatibilidade.get('compativel'):
                sobreposicao = compatibilidade.get('sobreposicao_horas', 0)
                margem = compatibilidade.get('margem_seguranca', 0)
                
                # Maior sobreposição = maior peso
                fator_temporal = min(sobreposicao / 24.0, 1.0)  # Normalizar por 24h
                fator_margem = min(margem / 12.0, 1.0)  # Normalizar por 12h
                
                peso_final = peso_base * (0.7 + 0.2 * fator_temporal + 0.1 * fator_margem)
            else:
                peso_final = peso_base * 0.1  # Peso muito baixo se incompatível
            
            return max(peso_final, 0.0)
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de peso da aresta: {e}")
            return 0.0

    def _encontrar_aresta_existente(self, arestas: List[Dict], origem: int, destino: int) -> Optional[Dict]:
        """Encontra aresta existente entre dois pedidos (bidirecional)"""
        for aresta in arestas:
            if ((aresta['origem'] == origem and aresta['destino'] == destino) or
                (aresta['origem'] == destino and aresta['destino'] == origem)):
                return aresta
        return None

    # =============================================================================
    #                        ANÁLISE DE CLUSTERS
    # =============================================================================

    def _identificar_clusters(self, nos: Dict, arestas: List[Dict]) -> List[Dict]:
        """Identifica clusters de pedidos fortemente conectados"""
        logger.debug("🌐 Identificando clusters...")
        
        # Construir grafo de adjacência
        grafo_adj = defaultdict(set)
        pesos_arestas = {}
        
        for aresta in arestas:
            origem, destino = aresta['origem'], aresta['destino']
            peso = aresta['peso']
            
            grafo_adj[origem].add(destino)
            grafo_adj[destino].add(origem)
            pesos_arestas[(origem, destino)] = peso
            pesos_arestas[(destino, origem)] = peso
        
        # Encontrar componentes conectados
        visitados = set()
        clusters = []
        
        for pedido_id in nos.keys():
            if pedido_id not in visitados:
                cluster = self._dfs_cluster(pedido_id, grafo_adj, visitados, pesos_arestas)
                if len(cluster['pedidos']) > 1:  # Cluster deve ter pelo menos 2 pedidos
                    clusters.append(cluster)
        
        # Analisar qualidade dos clusters
        for i, cluster in enumerate(clusters):
            cluster['id'] = f"cluster_{i+1}"
            cluster['qualidade'] = self._avaliar_qualidade_cluster(cluster, nos)
        
        # Ordenar por qualidade
        clusters.sort(key=lambda c: c['qualidade'], reverse=True)
        
        logger.info(f"🌐 Identificados {len(clusters)} clusters")
        return clusters

    def _dfs_cluster(self, inicio: int, grafo: Dict, visitados: Set, 
                     pesos: Dict) -> Dict:
        """DFS para encontrar cluster conectado"""
        pilha = [inicio]
        pedidos_cluster = []
        arestas_cluster = []
        peso_total = 0.0
        
        while pilha:
            atual = pilha.pop()
            if atual in visitados:
                continue
            
            visitados.add(atual)
            pedidos_cluster.append(atual)
            
            for vizinho in grafo.get(atual, []):
                if vizinho not in visitados:
                    pilha.append(vizinho)
                
                # Adicionar aresta ao cluster
                peso_aresta = pesos.get((atual, vizinho), 0.0)
                if peso_aresta > 0:
                    arestas_cluster.append({
                        'origem': atual,
                        'destino': vizinho,
                        'peso': peso_aresta
                    })
                    peso_total += peso_aresta
        
        return {
            'pedidos': pedidos_cluster,
            'arestas': arestas_cluster,
            'peso_total': peso_total,
            'tamanho': len(pedidos_cluster)
        }

    def _avaliar_qualidade_cluster(self, cluster: Dict, nos: Dict) -> float:
        """Avalia a qualidade de um cluster baseado em métricas"""
        try:
            pedidos = cluster['pedidos']
            tamanho = len(pedidos)
            peso_total = cluster['peso_total']
            
            if tamanho <= 1:
                return 0.0
            
            # Métricas de qualidade
            densidade = len(cluster['arestas']) / max((tamanho * (tamanho - 1)) / 2, 1)
            peso_medio = peso_total / max(len(cluster['arestas']), 1)
            
            # Compatibilidade temporal média
            compatibilidades = []
            for aresta in cluster['arestas']:
                # Buscar compatibilidade temporal das arestas originais
                # Por simplicidade, usar peso como proxy
                compatibilidades.append(aresta['peso'] / 100.0)
            
            compatibilidade_media = sum(compatibilidades) / max(len(compatibilidades), 1)
            
            # Score final
            qualidade = (densidade * 0.3 + 
                        min(peso_medio / 50.0, 1.0) * 0.4 + 
                        compatibilidade_media * 0.3)
            
            return min(qualidade, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erro ao avaliar qualidade do cluster: {e}")
            return 0.0

    # =============================================================================
    #                        MÉTRICAS E ESTATÍSTICAS
    # =============================================================================

    def _calcular_metricas_grafo(self, nos: Dict, arestas: List[Dict], 
                                clusters: List[Dict]) -> Dict:
        """Calcula métricas estatísticas do grafo"""
        logger.debug("📊 Calculando métricas do grafo...")
        
        try:
            total_nos = len(nos)
            total_arestas = len(arestas)
            
            # Conectividade
            nos_conectados = len([n for n in nos.values() if self._calcular_grau_no(n, arestas) > 0])
            taxa_conectividade = nos_conectados / max(total_nos, 1) * 100
            
            # Pesos das arestas
            pesos = [a['peso'] for a in arestas]
            peso_medio = sum(pesos) / max(len(pesos), 1)
            peso_maximo = max(pesos) if pesos else 0
            
            # Economia potencial
            economia_total = sum(a.get('economia_estimada', 0) for a in arestas)
            economia_media = economia_total / max(total_arestas, 1)
            
            # Clusters
            pedidos_em_clusters = sum(len(c['pedidos']) for c in clusters)
            cobertura_clusters = pedidos_em_clusters / max(total_nos, 1) * 100
            
            metricas = {
                'total_nos': total_nos,
                'total_arestas': total_arestas,
                'densidade_grafo': total_arestas / max((total_nos * (total_nos - 1)) / 2, 1) * 100,
                'taxa_conectividade': taxa_conectividade,
                'peso_medio_arestas': peso_medio,
                'peso_maximo_arestas': peso_maximo,
                'economia_total_estimada': economia_total,
                'economia_media_por_aresta': economia_media,
                'total_clusters': len(clusters),
                'pedidos_em_clusters': pedidos_em_clusters,
                'cobertura_clusters': cobertura_clusters,
                'cluster_medio_tamanho': pedidos_em_clusters / max(len(clusters), 1)
            }
            
            # Atualizar grau de conectividade dos nós
            for no in nos.values():
                no['grau_conectividade'] = self._calcular_grau_no(no, arestas)
            
            return metricas
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de métricas: {e}")
            return {}

    def _calcular_grau_no(self, no: Dict, arestas: List[Dict]) -> int:
        """Calcula o grau de conectividade de um nó"""
        pedido_id = no['id_pedido']
        grau = 0
        
        for aresta in arestas:
            if aresta['origem'] == pedido_id or aresta['destino'] == pedido_id:
                grau += 1
        
        return grau

    # =============================================================================
    #                        LOGGING E DEBUG
    # =============================================================================

    def _log_estatisticas_grafo(self, grafo: Dict) -> None:
        """Log das estatísticas principais do grafo"""
        metricas = grafo.get('metricas', {})
        
        logger.info("📊 Estatísticas do Grafo de Dependências:")
        logger.info(f"   🎯 Nós (pedidos): {metricas.get('total_nos', 0)}")
        logger.info(f"   🔗 Arestas (conexões): {metricas.get('total_arestas', 0)}")
        logger.info(f"   📊 Densidade: {metricas.get('densidade_grafo', 0):.1f}%")
        logger.info(f"   🌐 Taxa conectividade: {metricas.get('taxa_conectividade', 0):.1f}%")
        logger.info(f"   💰 Economia estimada: {metricas.get('economia_total_estimada', 0):.1f}%")
        logger.info(f"   🔗 Clusters identificados: {metricas.get('total_clusters', 0)}")
        logger.info(f"   📦 Cobertura clusters: {metricas.get('cobertura_clusters', 0):.1f}%")

    def _criar_grafo_vazio(self, pedidos: List[PedidoDeProducao]) -> Dict:
        """Cria grafo vazio em caso de erro"""
        logger.warning("⚠️ Criando grafo vazio devido a erro...")
        
        return {
            'nos': {p.id_pedido: {'id_pedido': p.id_pedido, 'subprodutos': {}, 'metadados': {}} for p in pedidos},
            'arestas': [],
            'subprodutos_compartilhados': {},
            'clusters': [],
            'metricas': {'erro': True, 'total_nos': len(pedidos), 'total_arestas': 0},
            'timestamp': datetime.now(),
            'total_pedidos': len(pedidos)
        }

    # =============================================================================
    #                        MÉTODOS DE CONSULTA
    # =============================================================================

    def obter_pedidos_relacionados(self, grafo: Dict, pedido_id: int) -> List[int]:
        """Obtém lista de pedidos relacionados a um pedido específico"""
        pedidos_relacionados = set()
        
        for aresta in grafo.get('arestas', []):
            if aresta['origem'] == pedido_id:
                pedidos_relacionados.add(aresta['destino'])
            elif aresta['destino'] == pedido_id:
                pedidos_relacionados.add(aresta['origem'])
        
        return list(pedidos_relacionados)

    def obter_subprodutos_pedido(self, grafo: Dict, pedido_id: int) -> Dict[int, float]:
        """Obtém subprodutos de um pedido específico"""
        no = grafo.get('nos', {}).get(pedido_id, {})
        return no.get('subprodutos', {})

    def calcular_economia_cluster(self, cluster: Dict, grafo: Dict) -> float:
        """Calcula economia total estimada de um cluster"""
        economia_total = 0.0
        
        for aresta in cluster.get('arestas', []):
            # Buscar aresta correspondente no grafo principal
            for aresta_grafo in grafo.get('arestas', []):
                if ((aresta_grafo['origem'] == aresta['origem'] and 
                     aresta_grafo['destino'] == aresta['destino']) or
                    (aresta_grafo['origem'] == aresta['destino'] and 
                     aresta_grafo['destino'] == aresta['origem'])):
                    economia_total += aresta_grafo.get('economia_estimada', 0.0)
                    break
        
        return economia_total

    def obter_melhor_cluster(self, grafo: Dict) -> Optional[Dict]:
        """Obtém o cluster com maior potencial de otimização"""
        clusters = grafo.get('clusters', [])
        
        if not clusters:
            return None
        
        # Clusters já estão ordenados por qualidade
        return clusters[0]

    def verificar_viabilidade_agrupamento(self, grafo: Dict, pedidos_ids: List[int]) -> Dict:
        """Verifica viabilidade de agrupar pedidos específicos"""
        if len(pedidos_ids) < 2:
            return {'viavel': False, 'razao': 'insuficientes_pedidos'}
        
        # Verificar se todos os pedidos estão conectados
        subgrafo_arestas = []
        for aresta in grafo.get('arestas', []):
            if aresta['origem'] in pedidos_ids and aresta['destino'] in pedidos_ids:
                subgrafo_arestas.append(aresta)
        
        if len(subgrafo_arestas) == 0:
            return {'viavel': False, 'razao': 'sem_conexoes'}
        
        # Calcular métricas do subgrafo
        economia_total = sum(a.get('economia_estimada', 0) for a in subgrafo_arestas)
        peso_medio = sum(a.get('peso', 0) for a in subgrafo_arestas) / len(subgrafo_arestas)
        
        viavel = (economia_total >= self.config['min_economia_percentual'] and 
                 peso_medio >= 10.0)  # Peso mínimo arbitrário
        
        return {
            'viavel': viavel,
            'economia_estimada': economia_total,
            'peso_medio': peso_medio,
            'total_conexoes': len(subgrafo_arestas),
            'razao': 'aprovado' if viavel else 'economia_insuficiente'
        }