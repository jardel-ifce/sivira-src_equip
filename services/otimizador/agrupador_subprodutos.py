"""
🔗 AGRUPADOR DE SUBPRODUTOS
===========================

Cria lotes otimizados de subprodutos para maximizar eficiência da produção.
Agrupa subprodutos similares de diferentes pedidos considerando:
- Compatibilidade temporal
- Economia de recursos
- Restrições de capacidade
- Prioridades de pedidos

Funcionalidades:
- Criação de lotes inteligentes
- Otimização de janelas temporais
- Cálculo de economia por lote
- Validação de viabilidade
"""

from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
from models.atividades.pedido_de_producao import PedidoDeProducao
from enums.producao.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger
import traceback
import uuid

# 🔗 Logger exclusivo do Agrupador de Subprodutos
logger = setup_logger('AgrupadorSubprodutos')

@dataclass
class LoteSubproduto:
    """Classe para representar um lote otimizado de subprodutos"""
    id: str
    tipo: str
    subproduto_id: int
    pedidos_ids: List[int]
    quantidade_total: float
    quantidade_individual: Dict[int, float]  # pedido_id -> quantidade
    janela_temporal: Tuple[datetime, datetime]
    prioridade: int
    economia_estimada: float
    viabilidade_score: float
    metadados: Dict

class AgrupadorSubprodutos:
    """
    🔗 Classe responsável por agrupar subprodutos de forma otimizada.
    
    Estratégias:
    - Agrupamento temporal inteligente
    - Consolidação por tipo de subproduto
    - Otimização de lotes por capacidade
    - Priorização por urgência e economia
    """
    
    def __init__(self):
        self.config = {
            'tamanho_max_lote': 5,  # Máximo de pedidos por lote
            'janela_max_agrupamento_horas': 12,  # Janela máxima para agrupar
            'margem_temporal_horas': 2,  # Margem de segurança temporal
            'economia_minima_percentual': 15,  # Economia mínima para criar lote
            'fator_prioridade_urgencia': 0.4,  # Peso da urgência na priorização
            'fator_economia': 0.35,  # Peso da economia na priorização
            'fator_tamanho': 0.25,  # Peso do tamanho na priorização
            'permitir_lotes_parciais': True,  # Permite lotes menores
            'debug_detalhado': True
        }
        
        logger.info("🔗 Agrupador de Subprodutos inicializado")
        logger.debug(f"⚙️ Configurações: {self.config}")

    # =============================================================================
    #                           MÉTODO PRINCIPAL
    # =============================================================================

    def criar_lotes_otimizados(self, pedidos: List[PedidoDeProducao], 
                              grafo_dependencias: Dict) -> List[Dict]:
        """
        Cria lotes otimizados de subprodutos baseado no grafo de dependências.
        
        Args:
            pedidos: Lista de pedidos
            grafo_dependencias: Grafo construído pelo AnalisadorDependencias
            
        Returns:
            List[Dict]: Lista de lotes otimizados
        """
        logger.info("🔗 Iniciando criação de lotes otimizados...")
        logger.info(f"📦 Processando {len(pedidos)} pedidos")
        
        try:
            # 1. Extrair candidatos a agrupamento
            logger.debug("🎯 Fase 1: Extração de candidatos")
            candidatos = self._extrair_candidatos_agrupamento(pedidos, grafo_dependencias)
            
            # 2. Filtrar por viabilidade temporal
            logger.debug("⏰ Fase 2: Filtro de viabilidade temporal")
            candidatos_viaveis = self._filtrar_viabilidade_temporal(candidatos, pedidos)
            
            # 3. Criar lotes preliminares
            logger.debug("📦 Fase 3: Criação de lotes preliminares")
            lotes_preliminares = self._criar_lotes_preliminares(candidatos_viaveis, pedidos)
            
            # 4. Otimizar lotes
            logger.debug("⚙️ Fase 4: Otimização de lotes")
            lotes_otimizados = self._otimizar_lotes(lotes_preliminares, pedidos)
            
            # 5. Validar e finalizar
            logger.debug("✅ Fase 5: Validação final")
            lotes_finais = self._validar_e_finalizar_lotes(lotes_otimizados)
            
            # 6. Converter para formato de saída
            lotes_dict = self._converter_lotes_para_dict(lotes_finais)
            
            self._log_estatisticas_lotes(lotes_finais)
            return lotes_dict
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de lotes: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return []

    # =============================================================================
    #                    FASE 1: EXTRAÇÃO DE CANDIDATOS
    # =============================================================================

    def _extrair_candidatos_agrupamento(self, pedidos: List[PedidoDeProducao], 
                                       grafo: Dict) -> Dict[int, Dict]:
        """
        Extrai candidatos a agrupamento baseado nos subprodutos compartilhados.
        
        Returns:
            Dict: {subproduto_id: {'pedidos': [...], 'quantidades': {...}, ...}}
        """
        logger.debug("🎯 Extraindo candidatos a agrupamento...")
        
        candidatos = {}
        subprodutos_compartilhados = grafo.get('subprodutos_compartilhados', {})
        
        for subproduto_id, info in subprodutos_compartilhados.items():
            pedidos_ids = info.get('pedidos', [])
            quantidades = info.get('quantidades', {})
            
            if len(pedidos_ids) < 2:
                continue  # Precisa de pelo menos 2 pedidos
            
            # Buscar metadados dos pedidos
            pedidos_metadados = {}
            for pedido in pedidos:
                if pedido.id_pedido in pedidos_ids:
                    pedidos_metadados[pedido.id_pedido] = {
                        'pedido': pedido,
                        'prazo': pedido.fim_jornada,
                        'inicio': pedido.inicio_jornada,
                        'urgencia': self._calcular_urgencia_pedido(pedido)
                    }
            
            candidato = {
                'subproduto_id': subproduto_id,
                'pedidos_ids': pedidos_ids,
                'quantidades': quantidades,
                'quantidade_total': sum(quantidades.values()),
                'pedidos_metadados': pedidos_metadados,
                'economia_potencial': info.get('economia_potencial', 0.0),
                'prioridade_media': sum(meta['urgencia'] for meta in pedidos_metadados.values()) / len(pedidos_metadados)
            }
            
            candidatos[subproduto_id] = candidato
            
            logger.debug(f"🎯 Candidato {subproduto_id}: {len(pedidos_ids)} pedidos, "
                        f"economia {info.get('economia_potencial', 0):.1f}%")
        
        logger.info(f"🎯 Extraídos {len(candidatos)} candidatos a agrupamento")
        return candidatos

    def _calcular_urgencia_pedido(self, pedido: PedidoDeProducao) -> float:
        """Calcula urgência do pedido (0-1, maior = mais urgente)"""
        try:
            agora = datetime.now()
            tempo_restante = pedido.fim_jornada - agora
            
            # Normalizar urgência (assume máximo de 72 horas)
            horas_restantes = tempo_restante.total_seconds() / 3600
            urgencia = 1.0 - min(horas_restantes / 72.0, 1.0)
            
            return max(0.0, min(1.0, urgencia))
        except:
            return 0.5  # Valor padrão

    # =============================================================================
    #                    FASE 2: VIABILIDADE TEMPORAL
    # =============================================================================

    def _filtrar_viabilidade_temporal(self, candidatos: Dict, 
                                     pedidos: List[PedidoDeProducao]) -> Dict[int, Dict]:
        """Filtra candidatos por viabilidade temporal"""
        logger.debug("⏰ Filtrando candidatos por viabilidade temporal...")
        
        candidatos_viaveis = {}
        mapa_pedidos = {p.id_pedido: p for p in pedidos}
        
        for subproduto_id, candidato in candidatos.items():
            viabilidade = self._avaliar_viabilidade_temporal(candidato, mapa_pedidos)
            
            if viabilidade['viavel']:
                candidato['viabilidade_temporal'] = viabilidade
                candidatos_viaveis[subproduto_id] = candidato
                
                logger.debug(f"✅ Candidato {subproduto_id} temporalmente viável: "
                           f"janela {viabilidade['duracao_janela']:.1f}h")
            else:
                logger.debug(f"❌ Candidato {subproduto_id} inviável: {viabilidade['razao']}")
        
        logger.info(f"⏰ {len(candidatos_viaveis)}/{len(candidatos)} candidatos temporalmente viáveis")
        return candidatos_viaveis

    def _avaliar_viabilidade_temporal(self, candidato: Dict, 
                                     mapa_pedidos: Dict) -> Dict:
        """Avalia viabilidade temporal de um candidato"""
        try:
            pedidos_ids = candidato['pedidos_ids']
            
            if len(pedidos_ids) < 2:
                return {'viavel': False, 'razao': 'poucos_pedidos'}
            
            # Calcular janela de sobreposição
            inicios = []
            fins = []
            
            for pedido_id in pedidos_ids:
                pedido = mapa_pedidos.get(pedido_id)
                if pedido:
                    inicios.append(pedido.inicio_jornada)
                    fins.append(pedido.fim_jornada)
            
            if not inicios or not fins:
                return {'viavel': False, 'razao': 'dados_incompletos'}
            
            # Calcular sobreposição
            inicio_janela = max(inicios)
            fim_janela = min(fins)
            
            if inicio_janela >= fim_janela:
                gap_horas = (inicio_janela - fim_janela).total_seconds() / 3600
                return {
                    'viavel': False, 
                    'razao': 'sem_sobreposicao',
                    'gap_horas': gap_horas
                }
            
            duracao_janela = (fim_janela - inicio_janela).total_seconds() / 3600
            
            # Verificar se janela é suficiente
            min_janela = self.config['janela_max_agrupamento_horas']
            if duracao_janela < min_janela:
                return {
                    'viavel': False,
                    'razao': 'janela_insuficiente',
                    'duracao_janela': duracao_janela,
                    'minimo_requerido': min_janela
                }
            
            # Calcular margem de segurança
            margem = duracao_janela - self.config['margem_temporal_horas']
            
            return {
                'viavel': True,
                'janela_inicio': inicio_janela,
                'janela_fim': fim_janela,
                'duracao_janela': duracao_janela,
                'margem_seguranca': margem,
                'flexibilidade': margem / duracao_janela if duracao_janela > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na avaliação temporal: {e}")
            return {'viavel': False, 'razao': 'erro_calculo'}

    # =============================================================================
    #                    FASE 3: CRIAÇÃO DE LOTES PRELIMINARES
    # =============================================================================

    def _criar_lotes_preliminares(self, candidatos_viaveis: Dict, 
                                 pedidos: List[PedidoDeProducao]) -> List[LoteSubproduto]:
        """Cria lotes preliminares baseado nos candidatos viáveis"""
        logger.debug("📦 Criando lotes preliminares...")
        
        lotes_preliminares = []
        
        # Ordenar candidatos por potencial (economia + urgência)
        candidatos_ordenados = sorted(
            candidatos_viaveis.items(),
            key=lambda x: self._calcular_potencial_candidato(x[1]),
            reverse=True
        )
        
        for subproduto_id, candidato in candidatos_ordenados:
            try:
                # Verificar se já não está em outro lote
                pedidos_disponíveis = self._filtrar_pedidos_disponíveis(
                    candidato['pedidos_ids'], lotes_preliminares
                )
                
                if len(pedidos_disponíveis) < 2:
                    logger.debug(f"⏭️ Candidato {subproduto_id}: poucos pedidos disponíveis")
                    continue
                
                # Criar lote
                lote = self._criar_lote_individual(subproduto_id, candidato, pedidos_disponíveis)
                
                if lote and self._validar_lote_preliminar(lote):
                    lotes_preliminares.append(lote)
                    logger.debug(f"✅ Lote criado: {lote.id} ({len(lote.pedidos_ids)} pedidos)")
                else:
                    logger.debug(f"❌ Lote {subproduto_id} não passou na validação")
                
            except Exception as e:
                logger.error(f"❌ Erro ao criar lote para subproduto {subproduto_id}: {e}")
        
        logger.info(f"📦 Criados {len(lotes_preliminares)} lotes preliminares")
        return lotes_preliminares

    def _calcular_potencial_candidato(self, candidato: Dict) -> float:
        """Calcula potencial de um candidato para priorização"""
        try:
            economia = candidato.get('economia_potencial', 0.0)
            urgencia = candidato.get('prioridade_media', 0.0)
            tamanho = len(candidato.get('pedidos_ids', []))
            
            # Score baseado nos fatores configurados
            potencial = (economia * self.config['fator_economia'] +
                        urgencia * 100 * self.config['fator_prioridade_urgencia'] +
                        min(tamanho / 5, 1) * 100 * self.config['fator_tamanho'])
            
            return potencial
        except:
            return 0.0

    def _filtrar_pedidos_disponíveis(self, pedidos_ids: List[int], 
                                    lotes_existentes: List[LoteSubproduto]) -> List[int]:
        """Filtra pedidos que ainda não estão em outros lotes"""
        pedidos_ocupados = set()
        
        for lote in lotes_existentes:
            pedidos_ocupados.update(lote.pedidos_ids)
        
        return [pid for pid in pedidos_ids if pid not in pedidos_ocupados]

    def _criar_lote_individual(self, subproduto_id: int, candidato: Dict, 
                              pedidos_ids: List[int]) -> Optional[LoteSubproduto]:
        """Cria um lote individual"""
        try:
            viabilidade = candidato['viabilidade_temporal']
            quantidades = candidato['quantidades']
            
            # Limitar tamanho do lote
            pedidos_lote = pedidos_ids[:self.config['tamanho_max_lote']]
            
            # Calcular quantidades do lote
            quantidade_individual = {pid: quantidades.get(pid, 0) for pid in pedidos_lote}
            quantidade_total = sum(quantidade_individual.values())
            
            # Calcular prioridade (baseada na urgência média)
            urgencias = []
            for pid in pedidos_lote:
                meta = candidato['pedidos_metadados'].get(pid, {})
                urgencias.append(meta.get('urgencia', 0.5))
            
            prioridade = int(sum(urgencias) / len(urgencias) * 100) if urgencias else 50
            
            # Calcular score de viabilidade
            viabilidade_score = self._calcular_score_viabilidade(viabilidade, len(pedidos_lote))
            
            lote = LoteSubproduto(
                id=f"lote_{uuid.uuid4().hex[:8]}",
                tipo="agrupamento_subproduto",
                subproduto_id=subproduto_id,
                pedidos_ids=pedidos_lote,
                quantidade_total=quantidade_total,
                quantidade_individual=quantidade_individual,
                janela_temporal=(viabilidade['janela_inicio'], viabilidade['janela_fim']),
                prioridade=prioridade,
                economia_estimada=candidato['economia_potencial'],
                viabilidade_score=viabilidade_score,
                metadados={
                    'duracao_janela_horas': viabilidade['duracao_janela'],
                    'margem_seguranca_horas': viabilidade['margem_seguranca'],
                    'flexibilidade': viabilidade['flexibilidade'],
                    'candidato_original': candidato
                }
            )
            
            return lote
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar lote individual: {e}")
            return None

    def _calcular_score_viabilidade(self, viabilidade: Dict, num_pedidos: int) -> float:
        """Calcula score de viabilidade do lote (0-1)"""
        try:
            # Fatores de viabilidade
            duracao = viabilidade.get('duracao_janela', 0)
            margem = viabilidade.get('margem_seguranca', 0)
            flexibilidade = viabilidade.get('flexibilidade', 0)
            
            # Normalizar fatores
            score_duracao = min(duracao / 24.0, 1.0)  # Max 24h
            score_margem = min(margem / 12.0, 1.0)    # Max 12h margem
            score_tamanho = min(num_pedidos / 5.0, 1.0)  # Max 5 pedidos
            
            score_final = (score_duracao * 0.4 + 
                          score_margem * 0.3 + 
                          flexibilidade * 0.2 + 
                          score_tamanho * 0.1)
            
            return min(max(score_final, 0.0), 1.0)
            
        except:
            return 0.5

    def _validar_lote_preliminar(self, lote: LoteSubproduto) -> bool:
        """Valida se um lote preliminar atende aos critérios mínimos"""
        try:
            # Critérios de validação
            criterios = [
                len(lote.pedidos_ids) >= 2,  # Mínimo 2 pedidos
                lote.economia_estimada >= self.config['economia_minima_percentual'],
                lote.viabilidade_score >= 0.3,  # Score mínimo
                lote.quantidade_total > 0,
                lote.janela_temporal[1] > lote.janela_temporal[0]  # Janela válida
            ]
            
            valido = all(criterios)
            
            if not valido:
                logger.debug(f"❌ Lote {lote.id} falhou na validação: {criterios}")
            
            return valido
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do lote: {e}")
            return False

    # =============================================================================
    #                    FASE 4: OTIMIZAÇÃO DE LOTES
    # =============================================================================

    def _otimizar_lotes(self, lotes_preliminares: List[LoteSubproduto], 
                       pedidos: List[PedidoDeProducao]) -> List[LoteSubproduto]:
        """Otimiza os lotes preliminares"""
        logger.debug("⚙️ Otimizando lotes...")
        
        # Ordenar lotes por prioridade e viabilidade
        lotes_ordenados = sorted(
            lotes_preliminares,
            key=lambda l: (l.prioridade, l.viabilidade_score),
            reverse=True
        )
        
        lotes_otimizados = []
        pedidos_alocados = set()
        
        for lote in lotes_ordenados:
            # Verificar conflitos com lotes já otimizados
            pedidos_conflito = set(lote.pedidos_ids) & pedidos_alocados
            
            if pedidos_conflito:
                # Tentar resolver conflito removendo pedidos
                lote_resolvido = self._resolver_conflitos_lote(lote, pedidos_conflito)
                if lote_resolvido and len(lote_resolvido.pedidos_ids) >= 2:
                    lotes_otimizados.append(lote_resolvido)
                    pedidos_alocados.update(lote_resolvido.pedidos_ids)
                    logger.debug(f"🔧 Lote {lote.id} otimizado com resolução de conflitos")
                else:
                    logger.debug(f"❌ Lote {lote.id} descartado por conflitos irresolvíveis")
            else:
                # Sem conflitos, adicionar diretamente
                lotes_otimizados.append(lote)
                pedidos_alocados.update(lote.pedidos_ids)
                logger.debug(f"✅ Lote {lote.id} adicionado sem conflitos")
        
        # Tentar melhorar lotes existentes
        lotes_melhorados = self._melhorar_lotes_existentes(lotes_otimizados, pedidos)
        
        logger.info(f"⚙️ Otimização concluída: {len(lotes_melhorados)} lotes finais")
        return lotes_melhorados

    def _resolver_conflitos_lote(self, lote: LoteSubproduto, 
                                pedidos_conflito: Set[int]) -> Optional[LoteSubproduto]:
        """Resolve conflitos removendo pedidos de menor prioridade"""
        try:
            pedidos_sem_conflito = [pid for pid in lote.pedidos_ids if pid not in pedidos_conflito]
            
            if len(pedidos_sem_conflito) < 2:
                return None
            
            # Criar novo lote sem os pedidos em conflito
            novo_lote = LoteSubproduto(
                id=f"{lote.id}_resolvido",
                tipo=lote.tipo,
                subproduto_id=lote.subproduto_id,
                pedidos_ids=pedidos_sem_conflito,
                quantidade_total=sum(lote.quantidade_individual.get(pid, 0) for pid in pedidos_sem_conflito),
                quantidade_individual={pid: lote.quantidade_individual.get(pid, 0) for pid in pedidos_sem_conflito},
                janela_temporal=lote.janela_temporal,
                prioridade=lote.prioridade,
                economia_estimada=lote.economia_estimada * (len(pedidos_sem_conflito) / len(lote.pedidos_ids)),
                viabilidade_score=lote.viabilidade_score * 0.8,  # Reduzir score por conflito
                metadados={**lote.metadados, 'conflitos_resolvidos': list(pedidos_conflito)}
            )
            
            return novo_lote
            
        except Exception as e:
            logger.error(f"❌ Erro ao resolver conflitos: {e}")
            return None

    def _melhorar_lotes_existentes(self, lotes: List[LoteSubproduto], 
                                  pedidos: List[PedidoDeProducao]) -> List[LoteSubproduto]:
        """Tenta melhorar lotes existentes através de otimizações locais"""
        lotes_melhorados = []
        
        for lote in lotes:
            try:
                # Tentar otimizar janela temporal
                lote_otimizado = self._otimizar_janela_temporal(lote, pedidos)
                
                # Recalcular métricas
                lote_otimizado.economia_estimada = self._recalcular_economia_lote(lote_otimizado)
                lote_otimizado.viabilidade_score = self._recalcular_viabilidade_lote(lote_otimizado)
                
                lotes_melhorados.append(lote_otimizado)
                
            except Exception as e:
                logger.error(f"❌ Erro ao melhorar lote {lote.id}: {e}")
                lotes_melhorados.append(lote)  # Manter original se houver erro
        
        return lotes_melhorados

    def _otimizar_janela_temporal(self, lote: LoteSubproduto, 
                                 pedidos: List[PedidoDeProducao]) -> LoteSubproduto:
        """Otimiza a janela temporal de um lote"""
        # Por simplicidade, manter janela original
        # Em versões futuras, pode implementar otimização mais sofisticada
        return lote

    def _recalcular_economia_lote(self, lote: LoteSubproduto) -> float:
        """Recalcula economia de um lote"""
        # Economia baseada no número de pedidos e quantidade
        num_pedidos = len(lote.pedidos_ids)
        if num_pedidos <= 1:
            return 0.0
        
        economia_base = (num_pedidos - 1) / num_pedidos * 100
        fator_quantidade = min(lote.quantidade_total / 100.0, 2.0)
        
        return min(economia_base * fator_quantidade, 70.0)

    def _recalcular_viabilidade_lote(self, lote: LoteSubproduto) -> float:
        """Recalcula viabilidade de um lote"""
        # Manter score original por simplicidade
        return lote.viabilidade_score

    # =============================================================================
    #                    FASE 5: VALIDAÇÃO E FINALIZAÇÃO
    # =============================================================================

    def _validar_e_finalizar_lotes(self, lotes_otimizados: List[LoteSubproduto]) -> List[LoteSubproduto]:
        """Validação final e preparação dos lotes"""
        logger.debug("✅ Validando e finalizando lotes...")
        
        lotes_validos = []
        
        for lote in lotes_otimizados:
            if self._validacao_final_lote(lote):
                # Finalizar metadados
                lote.metadados.update({
                    'timestamp_criacao': datetime.now(),
                    'versao_algoritmo': '1.0',
                    'status': 'finalizado'
                })
                
                lotes_validos.append(lote)
                logger.debug(f"✅ Lote {lote.id} validado e finalizado")
            else:
                logger.debug(f"❌ Lote {lote.id} rejeitado na validação final")
        
        logger.info(f"✅ Validação final: {len(lotes_validos)}/{len(lotes_otimizados)} lotes aprovados")
        return lotes_validos

    def _validacao_final_lote(self, lote: LoteSubproduto) -> bool:
        """Validação final rigorosa de um lote"""
        try:
            criterios_finais = [
                len(lote.pedidos_ids) >= 2,
                lote.quantidade_total > 0,
                lote.economia_estimada >= self.config['economia_minima_percentual'] * 0.8,  # 80% do mínimo
                lote.viabilidade_score >= 0.25,
                lote.janela_temporal[1] > lote.janela_temporal[0],
                len(set(lote.pedidos_ids)) == len(lote.pedidos_ids)  # Sem duplicados
            ]
            
            return all(criterios_finais)
            
        except Exception as e:
            logger.error(f"❌ Erro na validação final: {e}")
            return False

    # =============================================================================
    #                    CONVERSÃO E SAÍDA
    # =============================================================================

    def _converter_lotes_para_dict(self, lotes: List[LoteSubproduto]) -> List[Dict]:
        """Converte lotes para formato de dicionário para saída"""
        logger.debug("🔄 Convertendo lotes para formato de saída...")
        
        lotes_dict = []
        
        for lote in lotes:
            try:
                lote_dict = {
                    'id': lote.id,
                    'tipo': lote.tipo,
                    'subproduto_id': lote.subproduto_id,
                    'pedidos_ids': lote.pedidos_ids,
                    'quantidade_total': lote.quantidade_total,
                    'itens': [  # Formato compatível com sistema existente
                        {
                            'id_subproduto': lote.subproduto_id,
                            'quantidade': lote.quantidade_total,
                            'pedidos_origem': lote.pedidos_ids
                        }
                    ],
                    'janela_temporal': {
                        'inicio': lote.janela_temporal[0].isoformat(),
                        'fim': lote.janela_temporal[1].isoformat(),
                        'duracao_horas': (lote.janela_temporal[1] - lote.janela_temporal[0]).total_seconds() / 3600
                    },
                    'prioridade': lote.prioridade,
                    'economia_estimada': lote.economia_estimada,
                    'viabilidade_score': lote.viabilidade_score,
                    'metricas': {
                        'num_pedidos': len(lote.pedidos_ids),
                        'quantidade_media_por_pedido': lote.quantidade_total / len(lote.pedidos_ids),
                        'economia_por_pedido': lote.economia_estimada / len(lote.pedidos_ids)
                    },
                    'metadados': lote.metadados
                }
                
                lotes_dict.append(lote_dict)
                
            except Exception as e:
                logger.error(f"❌ Erro ao converter lote {lote.id}: {e}")
        
        return lotes_dict

    # =============================================================================
    #                    LOGGING E ESTATÍSTICAS
    # =============================================================================

    def _log_estatisticas_lotes(self, lotes: List[LoteSubproduto]) -> None:
        """Log das estatísticas dos lotes criados"""
        if not lotes:
            logger.warning("⚠️ Nenhum lote foi criado")
            return
        
        # Estatísticas básicas
        total_lotes = len(lotes)
        total_pedidos = sum(len(l.pedidos_ids) for l in lotes)
        economia_media = sum(l.economia_estimada for l in lotes) / total_lotes
        viabilidade_media = sum(l.viabilidade_score for l in lotes) / total_lotes
        
        # Distribuição por tamanho
        tamanhos = [len(l.pedidos_ids) for l in lotes]
        tamanho_medio = sum(tamanhos) / len(tamanhos)
        
        # Distribuição por prioridade
        prioridades_altas = sum(1 for l in lotes if l.prioridade >= 70)
        prioridades_medias = sum(1 for l in lotes if 30 <= l.prioridade < 70)
        prioridades_baixas = sum(1 for l in lotes if l.prioridade < 30)
        
        logger.info("📊 Estatísticas dos Lotes Criados:")
        logger.info(f"   📦 Total de lotes: {total_lotes}")
        logger.info(f"   🎯 Pedidos agrupados: {total_pedidos}")
        logger.info(f"   📏 Tamanho médio dos lotes: {tamanho_medio:.1f} pedidos")
        logger.info(f"   💰 Economia média: {economia_media:.1f}%")
        logger.info(f"   ✅ Viabilidade média: {viabilidade_media:.2f}")
        logger.info(f"   🚨 Prioridades: {prioridades_altas} altas, {prioridades_medias} médias, {prioridades_baixas} baixas")
        
        # Top 3 melhores lotes
        melhores_lotes = sorted(lotes, key=lambda l: l.economia_estimada, reverse=True)[:3]
        logger.info("🏆 Top 3 lotes por economia:")
        for i, lote in enumerate(melhores_lotes, 1):
            logger.info(f"   {i}. {lote.id}: {lote.economia_estimada:.1f}% ({len(lote.pedidos_ids)} pedidos)")

    # =============================================================================
    #                    MÉTODOS DE CONSULTA
    # =============================================================================

    def obter_lote_por_pedido(self, lotes_dict: List[Dict], pedido_id: int) -> Optional[Dict]:
        """Encontra o lote que contém um pedido específico"""
        for lote in lotes_dict:
            if pedido_id in lote.get('pedidos_ids', []):
                return lote
        return None

    def calcular_economia_total(self, lotes_dict: List[Dict]) -> float:
        """Calcula economia total de todos os lotes"""
        return sum(lote.get('economia_estimada', 0.0) for lote in lotes_dict)

    def obter_estatisticas_resumidas(self, lotes_dict: List[Dict]) -> Dict:
        """Retorna estatísticas resumidas dos lotes"""
        if not lotes_dict:
            return {}
        
        return {
            'total_lotes': len(lotes_dict),
            'total_pedidos_agrupados': sum(len(l.get('pedidos_ids', [])) for l in lotes_dict),
            'economia_total': self.calcular_economia_total(lotes_dict),
            'economia_media': sum(l.get('economia_estimada', 0) for l in lotes_dict) / len(lotes_dict),
            'viabilidade_media': sum(l.get('viabilidade_score', 0) for l in lotes_dict) / len(lotes_dict),
            'prioridade_media': sum(l.get('prioridade', 0) for l in lotes_dict) / len(lotes_dict)
        }