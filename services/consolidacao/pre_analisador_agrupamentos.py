"""
PRÉ-ANALISADOR DE AGRUPAMENTOS
================================

Identifica e marca atividades que serão agrupadas ANTES da execução sequencial.
Permite que o sistema valide capacidades considerando somas de quantidades agrupadas.

Funcionalidades:
- Análise prévia de pedidos para identificar agrupamentos possíveis
- Marcação de atividades como "agrupáveis" com referências mútuas
- Cálculo de quantidades totais agrupadas para validação
"""

from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict
from utils.logs.logger_factory import setup_logger

logger = setup_logger('PreAnalisadorAgrupamentos')


class PreAnalisadorAgrupamentos:
    """
    Analisa pedidos antes da execução para identificar e marcar agrupamentos.
    """
    
    @staticmethod
    def analisar_e_marcar_agrupamentos(pedidos_convertidos: List) -> Dict[str, Dict]:
        """
        Analisa lista de pedidos e marca atividades que serão agrupadas.
        
        Args:
            pedidos_convertidos: Lista de PedidoDeProducao convertidos
            
        Returns:
            Dict com estatísticas e detalhes dos agrupamentos identificados
        """
        import json
        from datetime import datetime
        
        # Criar arquivo de debug
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"logs/debug_agrupamento_{timestamp}.json"
        
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "pedidos_recebidos": len(pedidos_convertidos),
            "pedidos_detalhes": [],
            "mapeamento_atividades": {},
            "agrupamentos_identificados": [],
            "marcacao_aplicada": []
        }
        
        logger.info(f"🔍 Iniciando pré-análise de agrupamentos para {len(pedidos_convertidos)} pedidos")
        logger.info(f"📁 Debug será salvo em: {debug_file}")
        
        # Estatísticas
        estatisticas = {
            'total_pedidos': len(pedidos_convertidos),
            'agrupamentos_identificados': 0,
            'atividades_agrupadas': 0,
            'economia_estimada': 0,
            'detalhes_agrupamentos': []
        }
        
        if len(pedidos_convertidos) < 2:
            logger.info("📊 Menos de 2 pedidos - sem possibilidade de agrupamento")
            return estatisticas
        
        # 1. Criar todas as atividades modulares primeiro (sem executar)
        logger.info("📝 Criando atividades modulares para análise...")
        for pedido in pedidos_convertidos:
            try:
                pedido_info = {
                    "id_pedido": pedido.id_pedido,
                    "nome_item": getattr(pedido, 'nome_item', '?'),
                    "quantidade": getattr(pedido, 'quantidade', '?'),
                    "atividades": []
                }
                
                if not hasattr(pedido, 'atividades_modulares'):
                    logger.info(f"   Pedido {pedido.id_pedido}: Criando atividades modulares...")
                    pedido.criar_atividades_modulares_necessarias()
                    if hasattr(pedido, 'atividades_modulares'):
                        logger.info(f"   ✅ Pedido {pedido.id_pedido}: {len(pedido.atividades_modulares)} atividades criadas")
                    else:
                        logger.error(f"   ❌ Pedido {pedido.id_pedido}: Atributo atividades_modulares não foi criado!")
                        pedido_info["erro_atividades"] = "Atributo atividades_modulares não criado"
                        continue
                else:
                    if pedido.atividades_modulares:
                        logger.info(f"   Pedido {pedido.id_pedido}: Já possui {len(pedido.atividades_modulares)} atividades")
                    else:
                        logger.warning(f"   ⚠️ Pedido {pedido.id_pedido}: Tem atributo mas lista vazia")
                        pedido_info["aviso_atividades"] = "Lista de atividades está vazia"
                
                # Salvar detalhes das atividades no debug
                if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
                    for atividade in pedido.atividades_modulares:
                        ativ_info = {
                            "id_atividade": getattr(atividade, 'id_atividade', '?'),
                            "nome_atividade": getattr(atividade, 'nome_atividade', '?'),
                            "quantidade": getattr(atividade, 'quantidade', '?'),
                            "tipo_item": str(getattr(atividade, 'tipo_item', '?')),
                            "id_item": getattr(atividade, 'id_item', '?')
                        }
                        pedido_info["atividades"].append(ativ_info)
                else:
                    logger.warning(f"   ⚠️ Pedido {pedido.id_pedido}: Sem atividades para processar")
                    pedido_info["sem_atividades"] = True
                    
                debug_data["pedidos_detalhes"].append(pedido_info)
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao criar atividades do pedido {pedido.id_pedido}: {e}")
                debug_data["pedidos_detalhes"].append({
                    "id_pedido": pedido.id_pedido,
                    "erro": str(e)
                })
                continue
        
        # 2. Mapear atividades por características agrupáveis
        mapa_agrupamentos = PreAnalisadorAgrupamentos._mapear_atividades_agrupaveis(pedidos_convertidos)
        
        # Salvar mapeamento no debug
        for chave, atividades in mapa_agrupamentos.items():
            debug_data["mapeamento_atividades"][chave] = []
            for ativ in atividades:
                debug_data["mapeamento_atividades"][chave].append({
                    "id_pedido": ativ.id_pedido,
                    "nome_atividade": ativ.nome_atividade,
                    "quantidade": ativ.quantidade,
                    "id_atividade": ativ.id_atividade
                })
        
        # 3. Identificar e marcar agrupamentos viáveis
        for chave_agrupamento, lista_atividades in mapa_agrupamentos.items():
            if len(lista_atividades) > 1:
                # Verificar se as atividades podem ser agrupadas temporalmente
                if PreAnalisadorAgrupamentos._validar_agrupamento_temporal(lista_atividades):
                    # Marcar atividades como agrupáveis
                    logger.info(f"✅ Marcando agrupamento para chave: {chave_agrupamento}")
                    PreAnalisadorAgrupamentos._marcar_atividades_agrupadas(lista_atividades)
                    
                    agrupamento_info = {
                        "chave": chave_agrupamento,
                        "atividades_marcadas": []
                    }
                    
                    # Verificar se a marcação funcionou
                    for ativ in lista_atividades:
                        marcacao_info = {
                            "id_pedido": ativ.id_pedido,
                            "nome_atividade": ativ.nome_atividade,
                            "quantidade": ativ.quantidade,
                            "faz_parte_agrupamento": getattr(ativ, 'faz_parte_agrupamento', False),
                            "lider_agrupamento": getattr(ativ, 'lider_agrupamento', False),
                            "grupo_agrupamento_id": getattr(ativ, 'grupo_agrupamento_id', None),
                            "quantidade_agrupamento_total": getattr(ativ, 'quantidade_agrupamento_total', None)
                        }
                        agrupamento_info["atividades_marcadas"].append(marcacao_info)
                    
                    debug_data["agrupamentos_identificados"].append(agrupamento_info)
                    
                    # Coletar estatísticas
                    quantidade_total = sum(ativ.quantidade for ativ in lista_atividades)
                    pedidos_envolvidos = list(set(ativ.id_pedido for ativ in lista_atividades))
                    
                    detalhe = {
                        'chave': chave_agrupamento,
                        'quantidade_total': quantidade_total,
                        'num_atividades': len(lista_atividades),
                        'pedidos': pedidos_envolvidos,
                        'economia': len(lista_atividades) - 1  # Economia de execuções
                    }
                    
                    estatisticas['detalhes_agrupamentos'].append(detalhe)
                    estatisticas['agrupamentos_identificados'] += 1
                    estatisticas['atividades_agrupadas'] += len(lista_atividades)
                    estatisticas['economia_estimada'] += detalhe['economia']
                    
                    logger.info(
                        f"✅ AGRUPAMENTO IDENTIFICADO: {chave_agrupamento} "
                        f"({len(lista_atividades)} atividades, {quantidade_total}g total)"
                    )
        
        # 4. Relatório final e salvar debug
        debug_data["estatisticas_finais"] = estatisticas
        
        # Garantir que o diretório logs existe
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Salvar arquivo de debug
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"💾 Debug salvo em: {debug_file}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar debug: {e}")
        
        logger.info(f"📊 PRÉ-ANÁLISE CONCLUÍDA:")
        logger.info(f"   🔗 Agrupamentos identificados: {estatisticas['agrupamentos_identificados']}")
        logger.info(f"   📦 Atividades agrupadas: {estatisticas['atividades_agrupadas']}")
        logger.info(f"   💰 Economia estimada: {estatisticas['economia_estimada']} execuções")
        
        return estatisticas
    
    @staticmethod
    def _mapear_atividades_agrupaveis(pedidos: List) -> Dict[str, List]:
        """
        Mapeia atividades por características que permitem agrupamento.
        
        Returns:
            Dict onde chave é identificador único da atividade agrupável
        """
        mapa = defaultdict(list)
        
        for pedido in pedidos:
            if not hasattr(pedido, 'atividades_modulares'):
                continue
                
            for atividade in pedido.atividades_modulares:
                # Criar chave única baseada em características da atividade
                # Atividades com mesma chave podem ser agrupadas
                chave = PreAnalisadorAgrupamentos._gerar_chave_agrupamento(atividade)
                
                if chave:
                    mapa[chave].append(atividade)
                    logger.debug(
                        f"   Mapeada: {atividade.nome_atividade} "
                        f"(Pedido {pedido.id_pedido}) → {chave}"
                    )
        
        return mapa
    
    @staticmethod
    def _gerar_chave_agrupamento(atividade) -> Optional[str]:
        """
        Gera chave única para identificar atividades agrupáveis.
        
        Atividades com mesma chave podem potencialmente ser agrupadas.
        """
        try:
            # Elementos que devem ser iguais para permitir agrupamento
            elementos_chave = [
                str(getattr(atividade, 'id_atividade', '')),
                str(getattr(atividade, 'nome_atividade', '')),
                str(getattr(atividade, 'tipo_item', '')),
                str(getattr(atividade, 'id_item', ''))
            ]
            
            # Verificar se tem informações suficientes
            if not all(elementos_chave):
                return None
            
            return '|'.join(elementos_chave)
            
        except Exception as e:
            logger.debug(f"   Erro ao gerar chave para atividade: {e}")
            return None
    
    @staticmethod
    def _validar_agrupamento_temporal(atividades: List) -> bool:
        """
        Valida se atividades podem ser agrupadas temporalmente.
        
        Para serem agrupáveis, devem ter janelas temporais compatíveis.
        """
        if len(atividades) < 2:
            return False
        
        try:
            # Verificar se todas têm atributos temporais
            for ativ in atividades:
                if not hasattr(ativ, 'inicio') or not hasattr(ativ, 'fim'):
                    # Se não tem timing definido ainda, assumir que pode agrupar
                    return True
            
            # Se têm timing, verificar compatibilidade
            # Por simplicidade, verificar se têm sobreposição significativa
            inicio_min = min(ativ.inicio for ativ in atividades if hasattr(ativ, 'inicio'))
            fim_max = max(ativ.fim for ativ in atividades if hasattr(ativ, 'fim'))
            
            # Janela total não pode ser muito grande (ex: max 4 horas)
            duracao_total = (fim_max - inicio_min).total_seconds() / 3600
            
            if duracao_total > 4:
                logger.debug(f"   Janela temporal muito grande: {duracao_total:.1f}h")
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"   Erro na validação temporal: {e}")
            return False
    
    @staticmethod
    def _marcar_atividades_agrupadas(atividades: List) -> None:
        """
        Marca atividades como parte de um agrupamento.
        
        Adiciona atributos especiais que indicam:
        - Que a atividade faz parte de um agrupamento
        - Quantidade total do agrupamento
        - Referências às outras atividades do grupo
        """
        if len(atividades) < 2:
            return
        
        # Calcular quantidade total do agrupamento
        quantidade_total = sum(ativ.quantidade for ativ in atividades)
        
        # Criar ID único para o agrupamento
        import uuid
        grupo_id = str(uuid.uuid4())[:8]
        
        # Marcar cada atividade
        for idx, atividade in enumerate(atividades):
            # Adicionar atributos de agrupamento
            atividade.faz_parte_agrupamento = True
            atividade.grupo_agrupamento_id = grupo_id
            atividade.quantidade_agrupamento_total = quantidade_total
            atividade.posicao_no_agrupamento = idx
            atividade.tamanho_agrupamento = len(atividades)
            
            # Lista de IDs dos outros pedidos no grupo
            outros_pedidos = [
                ativ.id_pedido for ativ in atividades 
                if ativ.id_pedido != atividade.id_pedido
            ]
            atividade.pedidos_agrupados = outros_pedidos
            
            # Se é a primeira atividade, marca como "líder" do grupo
            if idx == 0:
                atividade.lider_agrupamento = True
                logger.debug(
                    f"   🏆 Atividade líder: {atividade.nome_atividade} "
                    f"(Pedido {atividade.id_pedido}) - Total grupo: {quantidade_total}g"
                )
            else:
                atividade.lider_agrupamento = False
                logger.debug(
                    f"   📎 Atividade agrupada: {atividade.nome_atividade} "
                    f"(Pedido {atividade.id_pedido})"
                )
    
    @staticmethod
    def obter_quantidade_validacao(atividade) -> float:
        """
        Retorna a quantidade que deve ser usada para validação de capacidade.
        
        Se a atividade faz parte de um agrupamento e é a líder,
        retorna a quantidade total do grupo. Caso contrário, retorna
        a quantidade individual.
        
        Args:
            atividade: Atividade modular
            
        Returns:
            float: Quantidade para validação
        """
        # Se faz parte de agrupamento e é líder, usar quantidade total
        if (hasattr(atividade, 'faz_parte_agrupamento') and 
            atividade.faz_parte_agrupamento and
            hasattr(atividade, 'lider_agrupamento') and
            atividade.lider_agrupamento):
            
            quantidade = getattr(atividade, 'quantidade_agrupamento_total', atividade.quantidade)
            logger.debug(
                f"🔗 Usando quantidade agrupada para validação: {quantidade}g "
                f"(grupo {atividade.grupo_agrupamento_id})"
            )
            return quantidade
        
        # Caso contrário, usar quantidade individual
        return atividade.quantidade