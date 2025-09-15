#!/usr/bin/env python3
"""
Cache de Atividades por Intervalo - Sistema de Agrupamento Automático
===================================================================

Sistema para detectar e agrupar automaticamente atividades do mesmo subproduto
que tentam alocar equipamentos no mesmo intervalo temporal.

Resolve o problema de capacidade mínima através de agrupamento implícito.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from threading import Lock
from utils.logs.logger_factory import setup_logger

logger = setup_logger("CacheAtividadesIntervalo")

@dataclass
class AtividadePendente:
    """Representa uma atividade aguardando agrupamento"""
    id_atividade: int
    id_item: int
    quantidade: float
    inicio: datetime
    fim: datetime
    atividade_obj: object  # Referência para o objeto AtividadeModular
    tipo_equipamento: str
    callback_sucesso: callable = None
    callback_falha: callable = None

@dataclass
class GrupoConsolidacao:
    """Representa um grupo de atividades consolidadas"""
    chave_intervalo: str
    id_item: int
    atividades: List[AtividadePendente]
    quantidade_total: float
    inicio: datetime
    fim: datetime
    tipo_equipamento: str
    status: str = "PENDENTE"  # PENDENTE, EXECUTANDO, CONCLUIDO, FALHOU

class CacheAtividadesIntervalo:
    """
    Cache global para detectar oportunidades de agrupamento automático.

    Funciona como singleton para coordenar atividades entre diferentes
    gestores de equipamento.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        # Cache principal: {chave_intervalo: {id_item: GrupoConsolidacao}}
        self._cache_intervalos: Dict[str, Dict[int, GrupoConsolidacao]] = {}

        # Atividades em execução para evitar duplicação
        self._atividades_em_execucao: Set[int] = set()

        # Lock para thread-safety
        self._cache_lock = Lock()

        # Estatísticas
        self._stats = {
            'total_atividades_adicionadas': 0,
            'total_grupos_criados': 0,
            'total_consolidacoes_realizadas': 0,
            'economia_capacidade_total': 0
        }

        self._initialized = True
        logger.info("🔄 Cache de Atividades por Intervalo inicializado")

    def _gerar_chave_intervalo(self, inicio: datetime, fim: datetime, tipo_equipamento: str) -> str:
        """Gera chave única para identificar um intervalo específico"""
        return f"{tipo_equipamento}_{inicio.strftime('%Y%m%d_%H%M')}_{fim.strftime('%H%M')}"

    def adicionar_atividade_pendente(
        self,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        atividade_obj: object,
        tipo_equipamento: str,
        callback_sucesso: callable = None,
        callback_falha: callable = None
    ) -> Optional[GrupoConsolidacao]:
        """
        Adiciona uma atividade ao cache e verifica oportunidades de agrupamento.

        Returns:
            GrupoConsolidacao se há agrupamento possível, None se deve tentar alocação individual
        """
        with self._cache_lock:
            # Evitar duplicação
            if id_atividade in self._atividades_em_execucao:
                logger.warning(f"⚠️ Atividade {id_atividade} já está em execução")
                return None

            chave_intervalo = self._gerar_chave_intervalo(inicio, fim, tipo_equipamento)

            # Criar atividade pendente
            atividade_pendente = AtividadePendente(
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=quantidade,
                inicio=inicio,
                fim=fim,
                atividade_obj=atividade_obj,
                tipo_equipamento=tipo_equipamento,
                callback_sucesso=callback_sucesso,
                callback_falha=callback_falha
            )

            # Verificar se já existe grupo para este intervalo e item
            if chave_intervalo not in self._cache_intervalos:
                self._cache_intervalos[chave_intervalo] = {}

            intervalos_item = self._cache_intervalos[chave_intervalo]

            if id_item in intervalos_item:
                # Já existe grupo - adicionar à consolidação
                grupo = intervalos_item[id_item]
                grupo.atividades.append(atividade_pendente)
                grupo.quantidade_total += quantidade

                logger.info(
                    f"🔗 Agrupamento detectado! Atividade {id_atividade} adicionada ao grupo "
                    f"(item {id_item}, intervalo {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')})"
                )
                logger.info(
                    f"   📊 Grupo agora tem {len(grupo.atividades)} atividades, "
                    f"quantidade total: {grupo.quantidade_total}g"
                )

                self._stats['total_atividades_adicionadas'] += 1

                return grupo
            else:
                # Primeiro do grupo - criar novo grupo
                grupo = GrupoConsolidacao(
                    chave_intervalo=chave_intervalo,
                    id_item=id_item,
                    atividades=[atividade_pendente],
                    quantidade_total=quantidade,
                    inicio=inicio,
                    fim=fim,
                    tipo_equipamento=tipo_equipamento
                )

                intervalos_item[id_item] = grupo

                logger.debug(
                    f"📝 Novo grupo criado para item {id_item} no intervalo "
                    f"{inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')} ({quantidade}g)"
                )

                self._stats['total_grupos_criados'] += 1
                self._stats['total_atividades_adicionadas'] += 1

                # Retornar None indica que deve tentar alocação individual primeiro
                return None

    def marcar_grupo_em_execucao(self, grupo: GrupoConsolidacao):
        """Marca um grupo como em execução para evitar duplicação"""
        with self._cache_lock:
            grupo.status = "EXECUTANDO"
            for atividade in grupo.atividades:
                self._atividades_em_execucao.add(atividade.id_atividade)

            logger.info(
                f"🚀 Grupo em execução: {len(grupo.atividades)} atividades "
                f"consolidadas ({grupo.quantidade_total}g)"
            )

    def marcar_grupo_concluido(self, grupo: GrupoConsolidacao, sucesso: bool):
        """Marca um grupo como concluído e remove do cache"""
        with self._cache_lock:
            grupo.status = "CONCLUIDO" if sucesso else "FALHOU"

            # Chamar callbacks das atividades
            for atividade in grupo.atividades:
                self._atividades_em_execucao.discard(atividade.id_atividade)

                if sucesso and atividade.callback_sucesso:
                    try:
                        atividade.callback_sucesso()
                    except Exception as e:
                        logger.error(f"❌ Erro no callback de sucesso da atividade {atividade.id_atividade}: {e}")
                elif not sucesso and atividade.callback_falha:
                    try:
                        atividade.callback_falha()
                    except Exception as e:
                        logger.error(f"❌ Erro no callback de falha da atividade {atividade.id_atividade}: {e}")

            # Remover do cache
            if grupo.chave_intervalo in self._cache_intervalos:
                intervalos_item = self._cache_intervalos[grupo.chave_intervalo]
                if grupo.id_item in intervalos_item:
                    del intervalos_item[grupo.id_item]

                # Limpar chave de intervalo se vazia
                if not intervalos_item:
                    del self._cache_intervalos[grupo.chave_intervalo]

            if sucesso:
                self._stats['total_consolidacoes_realizadas'] += 1
                self._stats['economia_capacidade_total'] += len(grupo.atividades) - 1

            status_msg = "✅ concluído com sucesso" if sucesso else "❌ falhou"
            logger.info(f"🏁 Grupo {status_msg}: {len(grupo.atividades)} atividades ({grupo.quantidade_total}g)")

    def verificar_oportunidade_agrupamento(
        self,
        id_item: int,
        inicio: datetime,
        fim: datetime,
        tipo_equipamento: str
    ) -> Optional[GrupoConsolidacao]:
        """
        Verifica se existe oportunidade de agrupamento para uma atividade específica.
        """
        with self._cache_lock:
            chave_intervalo = self._gerar_chave_intervalo(inicio, fim, tipo_equipamento)

            if (chave_intervalo in self._cache_intervalos and
                id_item in self._cache_intervalos[chave_intervalo]):

                grupo = self._cache_intervalos[chave_intervalo][id_item]
                if grupo.status == "PENDENTE":
                    return grupo

            return None

    def remover_atividade(self, id_atividade: int):
        """Remove uma atividade específica do cache"""
        with self._cache_lock:
            self._atividades_em_execucao.discard(id_atividade)

            # Buscar e remover dos grupos
            for chave_intervalo, intervalos_item in list(self._cache_intervalos.items()):
                for id_item, grupo in list(intervalos_item.items()):
                    grupo.atividades = [a for a in grupo.atividades if a.id_atividade != id_atividade]

                    if not grupo.atividades:
                        # Grupo ficou vazio - remover
                        del intervalos_item[id_item]
                        if not intervalos_item:
                            del self._cache_intervalos[chave_intervalo]
                    else:
                        # Recalcular quantidade total
                        grupo.quantidade_total = sum(a.quantidade for a in grupo.atividades)

            logger.debug(f"🗑️ Atividade {id_atividade} removida do cache")

    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas do cache"""
        with self._cache_lock:
            grupos_ativos = sum(
                len(intervalos_item)
                for intervalos_item in self._cache_intervalos.values()
            )

            atividades_pendentes = sum(
                len(grupo.atividades)
                for intervalos_item in self._cache_intervalos.values()
                for grupo in intervalos_item.values()
            )

            return {
                **self._stats,
                'grupos_ativos': grupos_ativos,
                'atividades_pendentes_total': atividades_pendentes,
                'atividades_em_execucao': len(self._atividades_em_execucao),
                'chaves_intervalo_ativas': len(self._cache_intervalos)
            }

    def limpar_cache(self):
        """Limpa completamente o cache - usar com cuidado"""
        with self._cache_lock:
            self._cache_intervalos.clear()
            self._atividades_em_execucao.clear()
            self._stats = {
                'total_atividades_adicionadas': 0,
                'total_grupos_criados': 0,
                'total_consolidacoes_realizadas': 0,
                'economia_capacidade_total': 0
            }
            logger.info("🧹 Cache limpo completamente")

# Singleton instance
cache_atividades_intervalo = CacheAtividadesIntervalo()