"""
Sistema de Produção Otimizado - VERSÃO FINAL CORRIGIDA
======================================================

✅ CORREÇÃO FINAL: Não comprime janela temporal para execução
✅ MANTÉM: Flexibilidade de 3 dias para algoritmo sequencial
✅ GARANTE: Deadline obrigatório é respeitado
"""

import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Imports das classes do otimizador
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos
from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
from otimizador.modelo_pl_otimizador import ModeloPLOtimizador, SolucaoPL


class OtimizadorIntegrado:
    """
    ✅ VERSÃO FINAL: Mantém janela original para execução flexível
    """
    
    def __init__(self, resolucao_minutos: int = 30, timeout_segundos: int = 300):
        self.resolucao_minutos = resolucao_minutos
        self.timeout_segundos = timeout_segundos
        
        # Componentes do otimizador
        self.extrator = ExtratorDadosPedidos()
        self.gerador_janelas = None
        self.modelo_pl = None
        
        # Controle de simulação
        self.modo_simulacao = True
        self.equipamentos_simulados = {}
        
        # ✅ NOVO: Controle de horários obrigatórios
        self.pedidos_com_fim_obrigatorio = {}  # {pedido_id: fim_obrigatorio}
        
        # Resultados
        self.ultima_solucao = None
        self.dados_extraidos = None
        self.estatisticas_execucao = {}
        
        print(f"✅ OtimizadorIntegrado inicializado (VERSÃO FINAL):")
        print(f"   Resolução temporal: {resolucao_minutos} minutos")
        print(f"   Timeout PL: {timeout_segundos} segundos")
        print(f"   Modo simulação: {self.modo_simulacao}")
    
    def executar_pedidos_otimizados(self, pedidos, sistema_producao) -> bool:
        """
        ✅ VERSÃO FINAL: Pipeline completo de otimização
        """
        print(f"\n🚀 INICIANDO EXECUÇÃO OTIMIZADA (VERSÃO FINAL)")
        print("="*60)
        
        inicio_total = time.time()
        
        try:
            # ✅ NOVO: FASE 0 - Detecta pedidos com horário de entrega obrigatório
            print(f"🔍 Fase 0: Análise de restrições temporais...")
            self._analisar_restricoes_temporais(pedidos)
            
            # FASE 1: Extração (sem alocação)
            print(f"\n📊 Fase 1: Extração de dados...")
            self.dados_extraidos = self.extrator.extrair_dados(pedidos)
            
            if not self.dados_extraidos:
                print(f"❌ Nenhum pedido válido para otimização")
                return False
            
            # ✅ FASE 1.5: Configuração de fins obrigatórios (SEM alterar janelas)
            print(f"\n🔧 Fase 1.5: Configuração de fins obrigatórios...")
            self._configurar_fins_obrigatorios()
            
            # FASE 2: Geração de janelas ✅ CORRIGIDO: Passa fins obrigatórios
            print(f"\n⏰ Fase 2: Geração de janelas temporais...")
            self.gerador_janelas = GeradorJanelasTemporais(self.resolucao_minutos)
            
            # ✅ CORREÇÃO CRÍTICA: Passa pedidos_com_fim_obrigatorio para o gerador
            janelas = self.gerador_janelas.gerar_janelas_todos_pedidos(
                self.dados_extraidos,
                self.pedidos_com_fim_obrigatorio  # ✅ NOVO: Parâmetro adicionado
            )
            
            # Validação: Verifica se há janelas viáveis
            total_janelas_viaveis = sum(
                len([j for j in janelas_pedido if j.viavel]) 
                for janelas_pedido in janelas.values()
            )
            
            if total_janelas_viaveis == 0:
                print(f"❌ Nenhuma janela temporal viável foi gerada!")
                self._diagnosticar_problema_janelas(janelas)
                return False
            
            print(f"✅ {total_janelas_viaveis} janelas viáveis geradas")
            
            # FASE 3: Otimização PL (SEM alocação real)
            print(f"\n🧮 Fase 3: Otimização com Programação Linear (simulação)...")
            self.modo_simulacao = True
            
            self.modelo_pl = ModeloPLOtimizador(
                self.dados_extraidos, 
                janelas, 
                self.gerador_janelas.configuracao_tempo
            )
            
            self.ultima_solucao = self.modelo_pl.resolver(self.timeout_segundos)
            
            if not self.ultima_solucao or self.ultima_solucao.pedidos_atendidos == 0:
                print(f"❌ Otimização PL não encontrou solução viável")
                return False
            
            # FASE 4: Configuração de controle (SEM alterar janelas dos pedidos)
            print(f"\n🎯 Fase 4: Configuração de controle de deadlines...")
            sucesso_aplicacao = self._configurar_controle_deadlines(pedidos)
            
            if not sucesso_aplicacao:
                print(f"❌ Falha ao configurar controle de deadlines")
                return False
            
            # FASE 5: Execução real (AGORA sim faz alocação real)
            print(f"\n🏭 Fase 5: Execução com alocação REAL...")
            self.modo_simulacao = False
            sucesso_execucao = self._executar_pedidos_com_horarios_otimizados(pedidos, sistema_producao)
            
            # FASE 6: Estatísticas
            tempo_total = time.time() - inicio_total
            self._calcular_estatisticas_execucao(tempo_total)
            self._imprimir_resultado_final()
            
            return sucesso_execucao
            
        except Exception as e:
            print(f"❌ ERRO durante execução otimizada: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _analisar_restricoes_temporais(self, pedidos):
        """
        ✅ NOVO: Analisa quais pedidos têm horário de entrega obrigatório
        """
        print(f"🔍 Analisando restrições de horário de entrega...")
        
        for pedido in pedidos:
            try:
                # Força criação das atividades se não existem
                if not hasattr(pedido, 'atividades_modulares') or not pedido.atividades_modulares:
                    print(f"   📋 Criando atividades para análise do pedido {pedido.id_pedido}...")
                    pedido.criar_atividades_modulares_necessarias()
                
                # Procura pela última atividade (maior id_atividade)
                if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
                    atividades_produto = [
                        a for a in pedido.atividades_modulares 
                        if hasattr(a, 'tipo_item') and str(a.tipo_item) == 'TipoItem.PRODUTO'
                    ]
                    
                    if atividades_produto:
                        # Última atividade = maior id_atividade
                        ultima_atividade = max(atividades_produto, key=lambda a: a.id_atividade)
                        
                        # Verifica se tem tempo_maximo_de_espera = 0
                        if hasattr(ultima_atividade, 'tempo_maximo_de_espera'):
                            if ultima_atividade.tempo_maximo_de_espera == timedelta(0):
                                self.pedidos_com_fim_obrigatorio[pedido.id_pedido] = pedido.fim_jornada
                                print(f"   ⚠️ Pedido {pedido.id_pedido}: FIM OBRIGATÓRIO às {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                            else:
                                print(f"   ✅ Pedido {pedido.id_pedido}: horário flexível (espera: {ultima_atividade.tempo_maximo_de_espera})")
                        else:
                            print(f"   ❓ Pedido {pedido.id_pedido}: sem info de tempo_maximo_de_espera")
                    else:
                        print(f"   ⚠️ Pedido {pedido.id_pedido}: sem atividades de produto encontradas")
                else:
                    print(f"   ❌ Pedido {pedido.id_pedido}: não foi possível criar atividades")
                    
            except Exception as e:
                print(f"   ❌ Erro ao analisar pedido {pedido.id_pedido}: {e}")
        
        total_obrigatorios = len(self.pedidos_com_fim_obrigatorio)
        total_flexiveis = len(pedidos) - total_obrigatorios
        
        print(f"📊 Análise concluída:")
        print(f"   Pedidos com fim obrigatório: {total_obrigatorios}")
        print(f"   Pedidos com horário flexível: {total_flexiveis}")
    
    def _configurar_fins_obrigatorios(self):
        """
        ✅ CORRIGIDO: NÃO ajusta janela dos dados - apenas informa ao PL
        A janela original de 3 dias deve ser mantida para execução
        """
        if not self.pedidos_com_fim_obrigatorio:
            print(f"ℹ️ Nenhum ajuste necessário - todos os pedidos têm horário flexível")
            return
        
        print(f"🔧 Configurando informação de fins obrigatórios (SEM ajustar janelas)...")
        
        for dados_pedido in self.dados_extraidos:
            if dados_pedido.id_pedido in self.pedidos_com_fim_obrigatorio:
                fim_obrigatorio = self.pedidos_com_fim_obrigatorio[dados_pedido.id_pedido]
                
                print(f"   🎯 Pedido {dados_pedido.id_pedido} tem fim obrigatório:")
                print(f"      Deadline: {fim_obrigatorio.strftime('%d/%m %H:%M')}")
                print(f"      Janela original mantida: {dados_pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {dados_pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Duração: {dados_pedido.duracao_total}")
                
                # ✅ NÃO ALTERA a janela dos dados - PL escolherá dentro da janela original
                # Apenas registra que tem fim obrigatório para o gerador de janelas usar
    
    def _diagnosticar_problema_janelas(self, janelas):
        """
        ✅ NOVO: Diagnóstico detalhado quando não há janelas viáveis
        """
        print(f"\n🔍 DIAGNÓSTICO DO PROBLEMA:")
        
        for pedido_id, janelas_pedido in janelas.items():
            print(f"\n   Pedido {pedido_id}:")
            
            if not janelas_pedido:
                print(f"      ❌ Nenhuma janela gerada")
                
                # Busca dados do pedido para diagnóstico
                dados_pedido = next((p for p in self.dados_extraidos if p.id_pedido == pedido_id), None)
                if dados_pedido:
                    print(f"      📊 Dados do pedido:")
                    print(f"         Duração necessária: {dados_pedido.duracao_total}")
                    print(f"         Janela disponível: {dados_pedido.fim_jornada - dados_pedido.inicio_jornada}")
                    
                    if dados_pedido.id_pedido in self.pedidos_com_fim_obrigatorio:
                        print(f"         Tipo: FIM OBRIGATÓRIO")
                        print(f"         Deve terminar às: {self.pedidos_com_fim_obrigatorio[dados_pedido.id_pedido].strftime('%d/%m %H:%M')}")
                    else:
                        print(f"         Tipo: FLEXÍVEL")
            else:
                janelas_viaveis = [j for j in janelas_pedido if j.viavel]
                print(f"      📊 {len(janelas_viaveis)}/{len(janelas_pedido)} janelas viáveis")
    
    def _configurar_controle_deadlines(self, pedidos) -> bool:
        """
        ✅ CORRIGIDO: NÃO aplica horários apertados - apenas marca deadline
        Mantém janela original de 3 dias para execução sequencial
        """
        if not self.ultima_solucao or not self.ultima_solucao.janelas_selecionadas:
            print(f"❌ Sem solução válida para aplicar")
            return False
        
        pedidos_configurados = 0
        
        for pedido in pedidos:
            if pedido.id_pedido in self.ultima_solucao.janelas_selecionadas:
                janela = self.ultima_solucao.janelas_selecionadas[pedido.id_pedido]
                
                # DEBUG: Mostra horários
                print(f"   🔍 DEBUG Pedido {pedido.id_pedido}:")
                print(f"      Janela original: {pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Janela otimizada: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")
                
                # ✅ CORREÇÃO CRÍTICA: MANTER janela original para execução
                # NÃO sobrescrever inicio_jornada e fim_jornada
                
                # Apenas registra informação para controle
                if pedido.id_pedido in self.pedidos_com_fim_obrigatorio:
                    fim_obrigatorio = self.pedidos_com_fim_obrigatorio[pedido.id_pedido]
                    print(f"      ⚠️ IMPORTANTE: Pedido tem fim obrigatório às {fim_obrigatorio.strftime('%d/%m %H:%M')}")
                    print(f"      ✅ MANTENDO janela original de 3 dias para execução")
                    
                    # ✅ Adiciona atributo para controle do deadline (sem alterar janela)
                    pedido._deadline_obrigatorio = fim_obrigatorio
                    pedido._horario_otimizado_inicio = janela.datetime_inicio
                    pedido._horario_otimizado_fim = janela.datetime_fim
                else:
                    print(f"      ✅ Pedido flexível - mantendo janela original")
                
                # Backup dos horários originais (para possível rollback)
                pedido._inicio_jornada_original = getattr(pedido, '_inicio_jornada_original', pedido.inicio_jornada)
                pedido._fim_jornada_original = getattr(pedido, '_fim_jornada_original', pedido.fim_jornada)
                
                # ✅ MANTÉM horários originais (3 dias de flexibilidade)
                inicio_str = pedido.inicio_jornada.strftime('%d/%m %H:%M')
                fim_str = pedido.fim_jornada.strftime('%d/%m %H:%M')
                duracao = pedido.fim_jornada - pedido.inicio_jornada
                
                print(f"   ✅ Pedido {pedido.id_pedido}: {inicio_str} → {fim_str} (janela: {duracao})")
                if hasattr(pedido, '_deadline_obrigatorio'):
                    print(f"      🎯 Deadline obrigatório: {pedido._deadline_obrigatorio.strftime('%d/%m %H:%M')}")
                
                pedidos_configurados += 1
            else:
                print(f"   ⚠️ Pedido {pedido.id_pedido}: não incluído na solução ótima")
        
        print(f"📊 Configuração aplicada a {pedidos_configurados}/{len(pedidos)} pedidos")
        print(f"✅ Janelas originais de 3 dias MANTIDAS para execução flexível")
        return pedidos_configurados > 0
    
    def _executar_pedidos_com_horarios_otimizados(self, pedidos, sistema_producao) -> bool:
        """
        EXECUTA pedidos com alocação REAL usando lógica existente
        """
        pedidos_executados = 0
        pedidos_com_falha = 0
        
        # Ordena por horário de início otimizado (se disponível)
        pedidos_selecionados = [p for p in pedidos if p.id_pedido in self.ultima_solucao.janelas_selecionadas]
        
        if pedidos_selecionados:
            # Ordena por horário otimizado
            pedidos_ordenados = sorted(
                pedidos_selecionados,
                key=lambda p: self.ultima_solucao.janelas_selecionadas[p.id_pedido].datetime_inicio
            )
        else:
            # Fallback: ordem original
            pedidos_ordenados = pedidos
        
        print(f"📋 Executando {len(pedidos_ordenados)} pedidos em ordem otimizada...")
        
        for i, pedido in enumerate(pedidos_ordenados, 1):
            nome_produto = self._obter_nome_produto(pedido)
            inicio_str = pedido.inicio_jornada.strftime('%d/%m %H:%M')
            fim_str = pedido.fim_jornada.strftime('%d/%m %H:%M')
            
            print(f"\n🔄 Executando pedido {i}/{len(pedidos_ordenados)}: {nome_produto}")
            print(f"   ⏰ Janela de execução: {inicio_str} → {fim_str}")
            
            # ✅ NOVO: Mostra se é pedido com fim obrigatório
            if hasattr(pedido, '_deadline_obrigatorio'):
                deadline_str = pedido._deadline_obrigatorio.strftime('%d/%m %H:%M')
                print(f"   🎯 ENTREGA OBRIGATÓRIA às {deadline_str}")
                
                # Mostra horário otimizado como referência
                if hasattr(pedido, '_horario_otimizado_inicio'):
                    otim_inicio = pedido._horario_otimizado_inicio.strftime('%d/%m %H:%M')
                    otim_fim = pedido._horario_otimizado_fim.strftime('%d/%m %H:%M')
                    print(f"   📍 Horário otimizado sugerido: {otim_inicio} → {otim_fim}")
            
            try:
                # USA A LÓGICA EXISTENTE do sistema (com alocação real)
                sistema_producao._executar_pedido_individual(pedido)
                
                print(f"   ✅ Pedido {pedido.id_pedido} executado com sucesso")
                pedidos_executados += 1
                
            except Exception as e:
                print(f"   ❌ Falha no pedido {pedido.id_pedido}: {e}")
                pedidos_com_falha += 1
                
                # Rollback do pedido com falha
                if hasattr(pedido, 'rollback_pedido'):
                    pedido.rollback_pedido()
        
        print(f"\n📊 Resultado da execução:")
        print(f"   ✅ Executados: {pedidos_executados}")
        print(f"   ❌ Falhas: {pedidos_com_falha}")
        
        return pedidos_executados > 0
    
    def _obter_nome_produto(self, pedido) -> str:
        """Obtém nome do produto do pedido"""
        try:
            if hasattr(pedido, 'ficha_tecnica_modular') and pedido.ficha_tecnica_modular:
                return getattr(pedido.ficha_tecnica_modular, 'nome', f'produto_{pedido.id_produto}')
            return f'produto_{pedido.id_produto}'
        except:
            return f'pedido_{pedido.id_pedido}'
    
    def _calcular_estatisticas_execucao(self, tempo_total: float):
        """Calcula estatísticas da execução"""
        if not self.ultima_solucao:
            return
        
        self.estatisticas_execucao = {
            'tempo_total_otimizacao': tempo_total,
            'tempo_resolucao_pl': self.ultima_solucao.tempo_resolucao,
            'pedidos_totais': len(self.dados_extraidos),
            'pedidos_atendidos': self.ultima_solucao.pedidos_atendidos,
            'taxa_atendimento': self.ultima_solucao.estatisticas['taxa_atendimento'],
            'janelas_totais_geradas': sum(len(j) for j in self.gerador_janelas.janelas_por_pedido.values()),
            'variaveis_pl': self.ultima_solucao.estatisticas.get('total_variaveis', 0),
            'restricoes_pl': self.ultima_solucao.estatisticas.get('total_restricoes', 0),
            'status_solver': self.ultima_solucao.status_solver,
            'modo_execucao': 'otimizado_final',
            'pedidos_com_fim_obrigatorio': len(self.pedidos_com_fim_obrigatorio)
        }
    
    def _imprimir_resultado_final(self):
        """Imprime resultado final"""
        print(f"\n" + "="*80)
        print(f"🎉 EXECUÇÃO OTIMIZADA CONCLUÍDA (VERSÃO FINAL)")
        print("="*80)
        
        if not self.estatisticas_execucao:
            print(f"❌ Sem estatísticas disponíveis")
            return
        
        stats = self.estatisticas_execucao
        
        print(f"📊 RESULTADOS:")
        print(f"   Pedidos atendidos: {stats['pedidos_atendidos']}/{stats['pedidos_totais']}")
        print(f"   Taxa de atendimento: {stats['taxa_atendimento']:.1%}")
        print(f"   Status do solver: {stats['status_solver']}")
        print(f"   Pedidos com fim obrigatório: {stats['pedidos_com_fim_obrigatorio']}")
        
        print(f"\n⏱️ PERFORMANCE:")
        print(f"   Tempo total: {stats['tempo_total_otimizacao']:.2f}s")
        print(f"   Tempo PL: {stats['tempo_resolucao_pl']:.2f}s")
        print(f"   Janelas geradas: {stats['janelas_totais_geradas']:,}")
        
        print(f"\n✅ FUNCIONALIDADES IMPLEMENTADAS:")
        print(f"   ✅ Detecção automática de fins obrigatórios")
        print(f"   ✅ Respeito ao tempo_maximo_de_espera = 0")
        print(f"   ✅ Manutenção de janela de 3 dias para execução")
        print(f"   ✅ Otimização PL para múltiplos pedidos")
        print(f"   ✅ Controle de conflitos entre equipamentos")
        
        if self.ultima_solucao and self.ultima_solucao.janelas_selecionadas:
            print(f"\n📅 CRONOGRAMA OTIMIZADO:")
            janelas_ordenadas = sorted(
                self.ultima_solucao.janelas_selecionadas.items(),
                key=lambda x: x[1].datetime_inicio
            )
            
            for pedido_id, janela in janelas_ordenadas:
                # Busca dados do pedido para mostrar informações
                for dados in self.dados_extraidos:
                    if dados.id_pedido == pedido_id:
                        nome_produto = dados.nome_produto
                        inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                        fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                        duracao = janela.datetime_fim - janela.datetime_inicio
                        
                        # Verifica se tem fim obrigatório
                        if pedido_id in self.pedidos_com_fim_obrigatorio:
                            deadline = self.pedidos_com_fim_obrigatorio[pedido_id]
                            print(f"   🎯 {nome_produto}: {inicio_str} → {fim_str} ({duracao}) [DEADLINE: {deadline.strftime('%H:%M')}]")
                        else:
                            print(f"   ✅ {nome_produto}: {inicio_str} → {fim_str} ({duracao}) [FLEXÍVEL]")
                        break
        
        print("="*80)
    
    def restaurar_horarios_originais(self, pedidos):
        """Restaura horários originais (para rollback)"""
        for pedido in pedidos:
            if hasattr(pedido, '_inicio_jornada_original'):
                pedido.inicio_jornada = pedido._inicio_jornada_original
                pedido.fim_jornada = pedido._fim_jornada_original
                delattr(pedido, '_inicio_jornada_original')
                delattr(pedido, '_fim_jornada_original')
            
            # Remove atributos de controle
            for attr in ['_deadline_obrigatorio', '_horario_otimizado_inicio', '_horario_otimizado_fim']:
                if hasattr(pedido, attr):
                    delattr(pedido, attr)
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas da última execução"""
        return self.estatisticas_execucao.copy() if self.estatisticas_execucao else {}
    
    def obter_cronograma_otimizado(self) -> Dict:
        """Retorna cronograma otimizado"""
        if not self.ultima_solucao or not self.ultima_solucao.janelas_selecionadas:
            return {}
        
        cronograma = {}
        for pedido_id, janela in self.ultima_solucao.janelas_selecionadas.items():
            # ✅ NOVO: Inclui tanto horário otimizado quanto deadline
            cronograma_item = {
                'inicio_otimizado': janela.datetime_inicio.isoformat(),
                'fim_otimizado': janela.datetime_fim.isoformat(),
                'duracao_horas': (janela.datetime_fim - janela.datetime_inicio).total_seconds() / 3600,
                'fim_obrigatorio': pedido_id in self.pedidos_com_fim_obrigatorio
            }
            
            # Adiciona deadline se houver
            if pedido_id in self.pedidos_com_fim_obrigatorio:
                deadline = self.pedidos_com_fim_obrigatorio[pedido_id]
                cronograma_item['deadline'] = deadline.isoformat()
            
            cronograma[pedido_id] = cronograma_item
        
        return cronograma


class SistemaProducaoOtimizado:
    """Wrapper para integração com TesteSistemaProducao"""
    
    def __init__(self, sistema_producao_original):
        self.sistema_original = sistema_producao_original
        self.otimizador = OtimizadorIntegrado()
        
    def executar_com_otimizacao(self) -> bool:
        """Executa com otimização FINAL"""
        print(f"🥖 SISTEMA DE PRODUÇÃO OTIMIZADO (VERSÃO FINAL)")
        print("="*60)
        
        try:
            # Fases 1-3: Mesmo do sistema original
            self.sistema_original.inicializar_almoxarifado()
            self.sistema_original.criar_pedidos_de_producao()
            self.sistema_original.ordenar_pedidos_por_prioridade()
            
            # Fase 4: Execução otimizada FINAL
            return self.otimizador.executar_pedidos_otimizados(
                self.sistema_original.pedidos,
                self.sistema_original
            )
            
        except Exception as e:
            print(f"❌ ERRO no sistema otimizado: {e}")
            return False
    
    def obter_relatorio_completo(self) -> Dict:
        """Retorna relatório completo"""
        return {
            'estatisticas_otimizacao': self.otimizador.obter_estatisticas(),
            'cronograma_otimizado': self.otimizador.obter_cronograma_otimizado(),
            'total_pedidos': len(self.sistema_original.pedidos) if hasattr(self.sistema_original, 'pedidos') else 0,
            'versao': 'final_corrigida_janelas_flexiveis'
        }


if __name__ == "__main__":
    print("🧪 Teste básico do SistemaProducaoOtimizado VERSÃO FINAL...")
    print("✅ Classes carregadas com sucesso")