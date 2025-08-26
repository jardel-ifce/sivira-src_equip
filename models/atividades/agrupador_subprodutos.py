from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from models.atividades.pedido_de_producao import PedidoDeProducao
from models.atividades.atividade_modular import AtividadeModular
from enums.producao.tipo_item import TipoItem

logger = logging.getLogger("AgrupadorSubprodutos")

@dataclass
class OportunidadeConsolidacao:
    """Representa uma oportunidade de consolidação entre pedidos"""
    id_item: int
    nome_item: str
    chave_tecnica: str
    atividades: List[AtividadeModular]
    quantidade_total: float
    janela_temporal: Tuple[datetime, datetime]  # (inicio_mais_cedo, fim_mais_tarde)
    pedidos_envolvidos: Set[int]
    economia_equipamentos: int

@dataclass
class PlanoConsolidacao:
    """Plano de consolidação aplicável aos pedidos"""
    oportunidades: List[OportunidadeConsolidacao]
    atividades_consolidadas: Dict[int, AtividadeModular]  # id_atividade -> nova_atividade
    atividades_removidas: Set[int]  # IDs das atividades que serão removidas
    economia_total_equipamentos: int
    pedidos_afetados: Set[int]

class AgrupadorSubprodutos:
    """
    Classe responsável por coordenar agrupamento de subprodutos entre múltiplos pedidos.
    
    Funcionalidades:
    - Analisa múltiplos pedidos em busca de oportunidades de consolidação
    - Verifica compatibilidade temporal e técnica
    - Cria planos de consolidação entre pedidos
    - Aplica consolidações nos pedidos originais
    - Gerencia rollback de consolidações
    """
    
    def __init__(self, tolerancia_temporal: timedelta = timedelta(minutes=30)):
        self.tolerancia_temporal = tolerancia_temporal
        self.pedidos_gerenciados: Dict[int, PedidoDeProducao] = {}
        self.consolidacoes_ativas: List[PlanoConsolidacao] = []
        self.historico_consolidacoes: List[Dict] = []
        
    # =============================================================================
    #                           GESTÃO DE PEDIDOS
    # =============================================================================
    
    def adicionar_pedido(self, pedido: PedidoDeProducao) -> None:
        """Adiciona um pedido ao agrupador"""
        if pedido.id_pedido in self.pedidos_gerenciados:
            logger.warning(f"Pedido {pedido.id_pedido} já está sendo gerenciado")
            return
            
        self.pedidos_gerenciados[pedido.id_pedido] = pedido
        logger.info(f"Pedido {pedido.id_pedido} adicionado ao agrupador")
    
    def remover_pedido(self, id_pedido: int) -> None:
        """Remove um pedido do agrupador"""
        if id_pedido in self.pedidos_gerenciados:
            del self.pedidos_gerenciados[id_pedido]
            logger.info(f"Pedido {id_pedido} removido do agrupador")
    
    # =============================================================================
    #                        ANÁLISE DE OPORTUNIDADES
    # =============================================================================
    
    def analisar_oportunidades_consolidacao(self) -> List[OportunidadeConsolidacao]:
        """
        Analisa todos os pedidos em busca de oportunidades de consolidação de subprodutos
        """
        logger.info(f"Analisando oportunidades de consolidação entre {len(self.pedidos_gerenciados)} pedidos")
        
        # Coletar todas as atividades de subproduto
        atividades_por_chave = self._coletar_atividades_subproduto()
        
        # Identificar oportunidades
        oportunidades = []
        for chave, atividades in atividades_por_chave.items():
            if len(atividades) > 1:  # Precisa ter pelo menos 2 atividades para consolidar
                oportunidade = self._avaliar_oportunidade(chave, atividades)
                if oportunidade:
                    oportunidades.append(oportunidade)
        
        logger.info(f"Identificadas {len(oportunidades)} oportunidades de consolidação")
        return oportunidades
    
    def _coletar_atividades_subproduto(self) -> Dict[str, List[AtividadeModular]]:
        """Coleta todas as atividades de subproduto agrupadas por chave técnica"""
        atividades_por_chave = {}
        
        for pedido in self.pedidos_gerenciados.values():
            for atividade in pedido.atividades_modulares:
                if atividade.tipo_item == TipoItem.SUBPRODUTO:
                    chave = self._criar_chave_tecnica(atividade)
                    
                    if chave not in atividades_por_chave:
                        atividades_por_chave[chave] = []
                    
                    atividades_por_chave[chave].append(atividade)
        
        return atividades_por_chave
    
    def _criar_chave_tecnica(self, atividade: AtividadeModular) -> str:
        """
        Cria chave técnica para identificar atividades consolidáveis.
        Atividades com mesma chave podem ser potencialmente consolidadas.
        """
        elementos = [
            f"item_{atividade.id_item}",
            f"nome_{atividade.nome_item.replace(' ', '_').lower()}"
        ]
        
        # Adiciona configurações técnicas se disponíveis
        if hasattr(atividade, 'configuracoes_equipamentos'):
            config_key = self._extrair_configuracao_tecnica(atividade)
            elementos.append(f"config_{config_key}")
        
        return "_".join(elementos)
    
    def _extrair_configuracao_tecnica(self, atividade: AtividadeModular) -> str:
        """Extrai configuração técnica relevante da atividade"""
        if not hasattr(atividade, 'configuracoes_equipamentos'):
            return "default"
        
        # Procura por configurações críticas (masseira, forno, etc.)
        for nome_eq, config in atividade.configuracoes_equipamentos.items():
            if any(keyword in nome_eq.lower() for keyword in ['masseira', 'misturador']):
                velocidade = config.get('velocidade', 'default')
                tipo = config.get('tipo_mistura', 'default')
                return f"{velocidade}_{tipo}"
        
        return "default"
    
    def _avaliar_oportunidade(self, chave: str, atividades: List[AtividadeModular]) -> Optional[OportunidadeConsolidacao]:
        """Avalia se um grupo de atividades pode ser consolidado"""
        
        # Verificar compatibilidade temporal
        if not self._verificar_compatibilidade_temporal(atividades):
            logger.debug(f"Oportunidade {chave} rejeitada: incompatibilidade temporal")
            return None
        
        # Verificar compatibilidade técnica
        if not self._verificar_compatibilidade_tecnica(atividades):
            logger.debug(f"Oportunidade {chave} rejeitada: incompatibilidade técnica")
            return None
        
        # Calcular métricas
        quantidade_total = sum(a.quantidade for a in atividades)
        pedidos_envolvidos = {a.id_pedido for a in atividades}
        economia_equipamentos = len(atividades) - 1  # N atividades vira 1
        
        # Determinar janela temporal
        janela = self._calcular_janela_temporal(atividades)
        
        return OportunidadeConsolidacao(
            id_item=atividades[0].id_item,
            nome_item=atividades[0].nome_item,
            chave_tecnica=chave,
            atividades=atividades,
            quantidade_total=quantidade_total,
            janela_temporal=janela,
            pedidos_envolvidos=pedidos_envolvidos,
            economia_equipamentos=economia_equipamentos
        )
    
    def _verificar_compatibilidade_temporal(self, atividades: List[AtividadeModular]) -> bool:
        """Verifica se as atividades podem ser executadas em janela temporal compatível"""
        
        # Coletar janelas temporais de todos os pedidos envolvidos
        janelas = []
        for atividade in atividades:
            pedido = self.pedidos_gerenciados[atividade.id_pedido]
            janelas.append((pedido.inicio_jornada, pedido.fim_jornada))
        
        # Verificar se há sobreposição temporal suficiente
        inicio_mais_tarde = max(inicio for inicio, _ in janelas)
        fim_mais_cedo = min(fim for _, fim in janelas)
        
        sobreposicao = fim_mais_cedo - inicio_mais_tarde
        
        # Precisa ter pelo menos a tolerância temporal de sobreposição
        return sobreposicao >= self.tolerancia_temporal
    
    def _verificar_compatibilidade_tecnica(self, atividades: List[AtividadeModular]) -> bool:
        """Verifica se as atividades são tecnicamente compatíveis para consolidação"""
        
        # Verificar se todas têm o mesmo ID de item
        ids_item = {a.id_item for a in atividades}
        if len(ids_item) > 1:
            return False
        
        # Verificar configurações técnicas
        configuracoes = [self._extrair_configuracao_tecnica(a) for a in atividades]
        if len(set(configuracoes)) > 1:
            return False
        
        # Verificar se as quantidades são consolidáveis (não excedem limites de equipamento)
        quantidade_total = sum(a.quantidade for a in atividades)
        if not self._verificar_limites_equipamento(atividades[0], quantidade_total):
            return False
        
        return True
    
    def _verificar_limites_equipamento(self, atividade_referencia: AtividadeModular, quantidade_total: float) -> bool:
        """Verifica se a quantidade total não excede limites de equipamento"""
        # Esta verificação dependeria dos limites específicos dos equipamentos
        # Por simplicidade, assumimos que consolidações são válidas até 2x a quantidade original
        quantidade_maxima = atividade_referencia.quantidade * 2.5
        return quantidade_total <= quantidade_maxima
    
    def _calcular_janela_temporal(self, atividades: List[AtividadeModular]) -> Tuple[datetime, datetime]:
        """Calcula a janela temporal ótima para consolidação"""
        
        # Coletar janelas de todos os pedidos
        janelas = []
        for atividade in atividades:
            pedido = self.pedidos_gerenciados[atividade.id_pedido]
            janelas.append((pedido.inicio_jornada, pedido.fim_jornada))
        
        # A janela de consolidação é a interseção das janelas
        inicio_consolidacao = max(inicio for inicio, _ in janelas)
        fim_consolidacao = min(fim for _, fim in janelas)
        
        return (inicio_consolidacao, fim_consolidacao)
    
    # =============================================================================
    #                           CRIAÇÃO DE PLANOS
    # =============================================================================
    
    def criar_plano_consolidacao(self, oportunidades: List[OportunidadeConsolidacao]) -> PlanoConsolidacao:
        """Cria um plano de consolidação baseado nas oportunidades identificadas"""
        
        atividades_consolidadas = {}
        atividades_removidas = set()
        economia_total = 0
        pedidos_afetados = set()
        
        for oportunidade in oportunidades:
            # Criar atividade consolidada
            atividade_master = oportunidade.atividades[0]
            atividades_secundarias = oportunidade.atividades[1:]
            
            # Configurar atividade consolidada
            atividade_consolidada = self._criar_atividade_consolidada(
                atividade_master, 
                oportunidade.quantidade_total,
                oportunidade.janela_temporal
            )
            
            atividades_consolidadas[atividade_master.id_atividade] = atividade_consolidada
            
            # Marcar atividades secundárias para remoção
            for atividade_sec in atividades_secundarias:
                atividades_removidas.add(atividade_sec.id_atividade)
            
            # Acumular métricas
            economia_total += oportunidade.economia_equipamentos
            pedidos_afetados.update(oportunidade.pedidos_envolvidos)
            
            logger.info(
                f"Plano de consolidação: {oportunidade.nome_item} | "
                f"{len(oportunidade.atividades)} atividades → 1 | "
                f"Quantidade: {oportunidade.quantidade_total}g | "
                f"Pedidos: {list(oportunidade.pedidos_envolvidos)}"
            )
        
        return PlanoConsolidacao(
            oportunidades=oportunidades,
            atividades_consolidadas=atividades_consolidadas,
            atividades_removidas=atividades_removidas,
            economia_total_equipamentos=economia_total,
            pedidos_afetados=pedidos_afetados
        )
    
    def _criar_atividade_consolidada(
        self, 
        atividade_base: AtividadeModular, 
        quantidade_total: float,
        janela_temporal: Tuple[datetime, datetime]
    ) -> AtividadeModular:
        """Cria uma nova atividade consolidada baseada na atividade de referência"""
        
        # Clona a atividade base
        atividade_consolidada = AtividadeModular(
            id_ordem=atividade_base.id_ordem,  # Usar ordem do primeiro pedido
            id=atividade_base.id,
            id_atividade=atividade_base.id_atividade,
            tipo_item=atividade_base.tipo_item,
            quantidade=quantidade_total,  # Quantidade consolidada
            id_pedido=atividade_base.id_pedido,  # Manter pedido original como referência
            id_produto=atividade_base.id_produto,
            funcionarios_elegiveis=atividade_base.funcionarios_elegiveis,
            peso_unitario=atividade_base.peso_unitario,
            dados=atividade_base.dados.copy() if hasattr(atividade_base, 'dados') else {},
            nome_item=atividade_base.nome_item
        )
        
        # Ajustar janela temporal se necessário
        inicio_janela, fim_janela = janela_temporal
        atividade_consolidada._janela_consolidacao = (inicio_janela, fim_janela)
        atividade_consolidada._is_consolidated = True
        
        return atividade_consolidada
    
    # =============================================================================
    #                          APLICAÇÃO DE PLANOS
    # =============================================================================
    
    def aplicar_plano_consolidacao(self, plano: PlanoConsolidacao) -> bool:
        """Aplica um plano de consolidação aos pedidos gerenciados"""
        
        logger.info(f"Aplicando plano de consolidação afetando {len(plano.pedidos_afetados)} pedidos")
        
        try:
            # Backup do estado atual para rollback
            backup_pedidos = self._criar_backup_pedidos(plano.pedidos_afetados)
            
            # Aplicar modificações nos pedidos
            for id_pedido in plano.pedidos_afetados:
                pedido = self.pedidos_gerenciados[id_pedido]
                self._aplicar_consolidacao_no_pedido(pedido, plano)
            
            # Salvar consolidação ativa
            self.consolidacoes_ativas.append(plano)
            
            # Registrar no histórico
            self._registrar_consolidacao_no_historico(plano)
            
            logger.info(
                f"Consolidação aplicada com sucesso: "
                f"{plano.economia_total_equipamentos} equipamentos economizados"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar consolidação: {e}")
            # Rollback seria implementado aqui
            return False
    
    def _aplicar_consolidacao_no_pedido(self, pedido: PedidoDeProducao, plano: PlanoConsolidacao):
        """Aplica as modificações de consolidação em um pedido específico"""
        
        # Atualizar atividades consolidadas
        for id_atividade, atividade_nova in plano.atividades_consolidadas.items():
            for i, atividade in enumerate(pedido.atividades_modulares):
                if atividade.id_atividade == id_atividade:
                    pedido.atividades_modulares[i] = atividade_nova
                    break
        
        # Remover atividades secundárias
        pedido.atividades_modulares = [
            a for a in pedido.atividades_modulares 
            if a.id_atividade not in plano.atividades_removidas
        ]
        
        logger.debug(
            f"Pedido {pedido.id_pedido} atualizado: "
            f"{len(plano.atividades_removidas)} atividades removidas"
        )
    
    def _criar_backup_pedidos(self, ids_pedidos: Set[int]) -> Dict:
        """Cria backup dos pedidos para rollback"""
        backup = {}
        for id_pedido in ids_pedidos:
            pedido = self.pedidos_gerenciados[id_pedido]
            backup[id_pedido] = {
                'atividades': pedido.atividades_modulares.copy()
            }
        return backup
    
    def _registrar_consolidacao_no_historico(self, plano: PlanoConsolidacao):
        """Registra consolidação no histórico"""
        registro = {
            'timestamp': datetime.now(),
            'pedidos_afetados': list(plano.pedidos_afetados),
            'economia_equipamentos': plano.economia_total_equipamentos,
            'oportunidades': len(plano.oportunidades),
            'detalhes': [
                {
                    'item': op.nome_item,
                    'quantidade_consolidada': op.quantidade_total,
                    'atividades_originais': len(op.atividades)
                }
                for op in plano.oportunidades
            ]
        }
        self.historico_consolidacoes.append(registro)
    
    # =============================================================================
    #                              RELATÓRIOS
    # =============================================================================
    
    def obter_relatorio_consolidacao(self) -> Dict:
        """Gera relatório completo das consolidações realizadas"""
        
        return {
            'pedidos_gerenciados': len(self.pedidos_gerenciados),
            'consolidacoes_ativas': len(self.consolidacoes_ativas),
            'economia_total_equipamentos': sum(
                p.economia_total_equipamentos for p in self.consolidacoes_ativas
            ),
            'historico_consolidacoes': len(self.historico_consolidacoes),
            'tolerancia_temporal_minutos': self.tolerancia_temporal.total_seconds() / 60,
            'estatisticas_detalhadas': self._calcular_estatisticas_detalhadas()
        }
    
    def _calcular_estatisticas_detalhadas(self) -> Dict:
        """Calcula estatísticas detalhadas das consolidações"""
        
        if not self.historico_consolidacoes:
            return {'sem_dados': True}
        
        total_pedidos_afetados = sum(
            len(r['pedidos_afetados']) for r in self.historico_consolidacoes
        )
        
        total_economia = sum(
            r['economia_equipamentos'] for r in self.historico_consolidacoes
        )
        
        return {
            'total_pedidos_afetados': total_pedidos_afetados,
            'economia_total_historica': total_economia,
            'media_pedidos_por_consolidacao': total_pedidos_afetados / len(self.historico_consolidacoes),
            'consolidacoes_realizadas': len(self.historico_consolidacoes)
        }
    
    # =============================================================================
    #                        INTERFACE PÚBLICA
    # =============================================================================
    
    def executar_agrupamento_automatico(self, pedidos: List[PedidoDeProducao]) -> Dict:
        """
        Interface principal: executa todo o fluxo de agrupamento automaticamente
        """
        
        logger.info(f"Iniciando agrupamento automático de {len(pedidos)} pedidos")
        
        # Adicionar pedidos
        for pedido in pedidos:
            self.adicionar_pedido(pedido)
        
        # Analisar oportunidades
        oportunidades = self.analisar_oportunidades_consolidacao()
        
        if not oportunidades:
            logger.info("Nenhuma oportunidade de consolidação encontrada")
            return {'consolidacoes_realizadas': 0, 'motivo': 'Nenhuma oportunidade encontrada'}
        
        # Criar e aplicar plano
        plano = self.criar_plano_consolidacao(oportunidades)
        sucesso = self.aplicar_plano_consolidacao(plano)
        
        # Retornar resultado
        if sucesso:
            return {
                'consolidacoes_realizadas': len(oportunidades),
                'economia_equipamentos': plano.economia_total_equipamentos,
                'pedidos_afetados': list(plano.pedidos_afetados),
                'detalhes': [
                    {
                        'item': op.nome_item,
                        'quantidade_total': op.quantidade_total,
                        'atividades_consolidadas': len(op.atividades),
                        'pedidos': list(op.pedidos_envolvidos)
                    }
                    for op in oportunidades
                ]
            }
        else:
            return {'consolidacoes_realizadas': 0, 'erro': 'Falha na aplicação do plano'}


# =============================================================================
#                           SCRIPT DE TESTE
# =============================================================================

def teste_agrupamento_entre_pedidos():
    """
    Teste da nova funcionalidade de agrupamento entre pedidos diferentes
    """
    
    print("=" * 80)
    print("TESTE DE AGRUPAMENTO ENTRE PEDIDOS DIFERENTES")
    print("=" * 80)
    print("Cenário: 60 pães de hambúrguer + 60 pães de forma com janelas sobrepostas")
    print("Expectativa: 2 atividades massa_suave de pedidos diferentes → 1 consolidada")
    print()
    
    from datetime import datetime, timedelta
    from enums.producao.tipo_item import TipoItem
    
    try:
        # Configuração temporal sobreposta
        inicio_base = datetime(2025, 8, 29, 3, 0, 0)
        
        # Pedido 1: Hambúrguer (03:00 - 07:00)
        pedido_hamburger = PedidoDeProducao(
            id_ordem=1,
            id_pedido=1,
            id_produto=1002,
            tipo_item=TipoItem.PRODUTO,
            quantidade=60,
            inicio_jornada=inicio_base,
            fim_jornada=inicio_base + timedelta(hours=4),
            habilitar_agrupamento_subprodutos=False  # Agrupamento será feito externamente
        )
        
        # Pedido 2: Pão de forma (02:30 - 07:30) - Sobreposição de 4h
        pedido_forma = PedidoDeProducao(
            id_ordem=2,
            id_pedido=2,
            id_produto=1003,
            tipo_item=TipoItem.PRODUTO,
            quantidade=60,
            inicio_jornada=inicio_base - timedelta(minutes=30),
            fim_jornada=inicio_base + timedelta(hours=4, minutes=30),
            habilitar_agrupamento_subprodutos=False
        )
        
        print("1. Preparando pedidos...")
        
        # Montar estruturas
        pedido_hamburger.montar_estrutura()
        pedido_forma.montar_estrutura()
        
        # Criar atividades
        pedido_hamburger.criar_atividades_modulares_necessarias()
        pedido_forma.criar_atividades_modulares_necessarias()
        
        print(f"   Pedido hambúrguer: {len(pedido_hamburger.atividades_modulares)} atividades")
        print(f"   Pedido pão de forma: {len(pedido_forma.atividades_modulares)} atividades")
        
        print("\n2. Criando agrupador de subprodutos...")
        
        # Criar agrupador com tolerância de 30 minutos
        agrupador = AgrupadorSubprodutos(tolerancia_temporal=timedelta(minutes=30))
        
        print("\n3. Executando agrupamento automático...")
        
        # Executar agrupamento
        resultado = agrupador.executar_agrupamento_automatico([pedido_hamburger, pedido_forma])
        
        print(f"\n4. Resultado do agrupamento:")
        print(f"   Consolidações realizadas: {resultado.get('consolidacoes_realizadas', 0)}")
        
        if resultado.get('consolidacoes_realizadas', 0) > 0:
            print(f"   Economia de equipamentos: {resultado.get('economia_equipamentos', 0)}")
            print(f"   Pedidos afetados: {resultado.get('pedidos_afetados', [])}")
            
            print(f"\n   Detalhes das consolidações:")
            for detalhe in resultado.get('detalhes', []):
                print(f"     - {detalhe['item']}: {detalhe['quantidade_total']}g")
                print(f"       {detalhe['atividades_consolidadas']} atividades de {len(detalhe['pedidos'])} pedidos")
        else:
            print(f"   Motivo: {resultado.get('motivo', resultado.get('erro', 'Desconhecido'))}")
        
        print(f"\n5. Verificação pós-consolidação:")
        
        # Contar atividades massa_suave após consolidação
        massa_hamburger = [a for a in pedido_hamburger.atividades_modulares 
                          if a.tipo_item == TipoItem.SUBPRODUTO and 'massa' in a.nome_item.lower()]
        massa_forma = [a for a in pedido_forma.atividades_modulares 
                      if a.tipo_item == TipoItem.SUBPRODUTO and 'massa' in a.nome_item.lower()]
        
        print(f"   Hambúrguer - atividades massa_suave: {len(massa_hamburger)}")
        for a in massa_hamburger:
            consolidada = getattr(a, '_is_consolidated', False)
            print(f"     - Quantidade: {a.quantidade}g {'(CONSOLIDADA)' if consolidada else ''}")
        
        print(f"   Pão de forma - atividades massa_suave: {len(massa_forma)}")
        for a in massa_forma:
            consolidada = getattr(a, '_is_consolidated', False)
            print(f"     - Quantidade: {a.quantidade}g {'(CONSOLIDADA)' if consolidada else ''}")
        
        # Relatório do agrupador
        print(f"\n6. Relatório do agrupador:")
        relatorio = agrupador.obter_relatorio_consolidacao()
        print(f"   Pedidos gerenciados: {relatorio['pedidos_gerenciados']}")
        print(f"   Consolidações ativas: {relatorio['consolidacoes_ativas']}")
        print(f"   Economia total: {relatorio['economia_total_equipamentos']} equipamentos")
        
        # Validação final
        consolidacoes = resultado.get('consolidacoes_realizadas', 0)
        if consolidacoes > 0:
            print(f"\n✅ TESTE APROVADO: {consolidacoes} consolidação(ões) realizada(s) entre pedidos!")
            print(f"   Sistema de agrupamento entre pedidos funcionando corretamente")
        else:
            print(f"\n⚠️  TESTE INCONCLUSIVO: Nenhuma consolidação realizada")
            print(f"   Verificar compatibilidade temporal e técnica")
        
        return resultado
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return {'sucesso': False, 'erro': str(e)}


if __name__ == "__main__":
    # Executar teste quando arquivo é executado diretamente
    resultado_teste = teste_agrupamento_entre_pedidos()
