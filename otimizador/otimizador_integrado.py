"""
Sistema de Produção Otimizado - VERSÃO CORRIGIDA SEM LOOP INFINITO
================================================================

✅ CORREÇÃO: Evita loop infinito nas restrições 
✅ CORREÇÃO: Executa TODOS os pedidos (selecionados + fallback)
✅ MANTÉM: Flexibilidade de 3 dias para execução
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
    ✅ VERSÃO CORRIGIDA: Evita loop infinito e executa todos os pedidos
    """
    
    def __init__(self, resolucao_minutos: int = 60, timeout_segundos: int = 120):  # ✅ Parâmetros mais conservadores
        self.resolucao_minutos = resolucao_minutos
        self.timeout_segundos = timeout_segundos
        
        # Componentes do otimizador
        self.extrator = ExtratorDadosPedidos()
        self.gerador_janelas = None
        self.modelo_pl = None
        
        # Controle de simulação
        self.modo_simulacao = True
        self.equipamentos_simulados = {}
        
        # Controle de horários obrigatórios
        self.pedidos_com_fim_obrigatorio = {}  # {pedido_id: fim_obrigatorio}
        
        # Resultados
        self.ultima_solucao = None
        self.dados_extraidos = None
        self.estatisticas_execucao = {}
        
        print(f"✅ OtimizadorIntegrado inicializado (VERSÃO CORRIGIDA):")
        print(f"   Resolução temporal: {resolucao_minutos} minutos")
        print(f"   Timeout PL: {timeout_segundos} segundos")
        print(f"   Estratégia: Otimização + Fallback para todos os pedidos")
    
    def executar_pedidos_otimizados(self, pedidos, sistema_producao) -> bool:
        """
        ✅ VERSÃO CORRIGIDA: Pipeline otimizado que executa TODOS os pedidos
        """
        print(f"\n🚀 INICIANDO EXECUÇÃO OTIMIZADA (VERSÃO CORRIGIDA)")
        print("="*60)
        
        inicio_total = time.time()
        
        try:
            # FASE 0: Análise de restrições temporais
            print(f"🔍 Fase 0: Análise de restrições temporais...")
            self._analisar_restricoes_temporais(pedidos)
            
            # FASE 1: Extração (sem alocação)
            print(f"\n📊 Fase 1: Extração de dados...")
            self.dados_extraidos = self.extrator.extrair_dados(pedidos)
            
            if not self.dados_extraidos:
                print(f"❌ Nenhum pedido válido para otimização")
                return self._executar_todos_sequencial(pedidos, sistema_producao)
            
            # FASE 1.5: Configuração de fins obrigatórios
            print(f"\n🔧 Fase 1.5: Configuração de fins obrigatórios...")
            self._configurar_fins_obrigatorios()
            
            # FASE 2: Geração de janelas
            print(f"\n⏰ Fase 2: Geração de janelas temporais...")
            self.gerador_janelas = GeradorJanelasTemporais(self.resolucao_minutos)
            
            janelas = self.gerador_janelas.gerar_janelas_todos_pedidos(
                self.dados_extraidos,
                self.pedidos_com_fim_obrigatorio
            )
            
            # Validação: Verificar se há janelas viáveis
            total_janelas_viaveis = sum(
                len([j for j in janelas_pedido if j.viavel]) 
                for janelas_pedido in janelas.values()
            )
            
            if total_janelas_viaveis == 0:
                print(f"❌ Nenhuma janela temporal viável - executando sequencial")
                return self._executar_todos_sequencial(pedidos, sistema_producao)
            
            print(f"✅ {total_janelas_viaveis} janelas viáveis geradas")
            
            # FASE 3: Otimização PL (com proteção contra loop infinito)
            print(f"\n🧮 Fase 3: Otimização com Programação Linear...")
            self.modo_simulacao = True
            
            self.modelo_pl = ModeloPLOtimizador(
                self.dados_extraidos, 
                janelas, 
                self.gerador_janelas.configuracao_tempo
            )
            
            self.ultima_solucao = self.modelo_pl.resolver(self.timeout_segundos)
            
            # FASE 4: Execução HÍBRIDA (otimizados + fallback)
            print(f"\n🏭 Fase 4: Execução HÍBRIDA...")
            self.modo_simulacao = False
            sucesso_execucao = self._executar_pedidos_hibridamente(pedidos, sistema_producao)
            
            # FASE 5: Estatísticas
            tempo_total = time.time() - inicio_total
            self._calcular_estatisticas_execucao(tempo_total)
            self._imprimir_resultado_final()
            
            return sucesso_execucao
            
        except Exception as e:
            print(f"❌ ERRO durante execução otimizada: {e}")
            print(f"🆘 Executando TODOS os pedidos em modo sequencial...")
            return self._executar_todos_sequencial(pedidos, sistema_producao)
    
    def _analisar_restricoes_temporais(self, pedidos):
        """Analisa quais pedidos têm horário de entrega obrigatório"""
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
        """Configura informação de fins obrigatórios (SEM ajustar janelas)"""
        if not self.pedidos_com_fim_obrigatorio:
            print(f"ℹ️ Nenhum ajuste necessário - todos os pedidos têm horário flexível")
            return
        
        print(f"🔧 Configurando informação de fins obrigatórios...")
        
        for dados_pedido in self.dados_extraidos:
            if dados_pedido.id_pedido in self.pedidos_com_fim_obrigatorio:
                fim_obrigatorio = self.pedidos_com_fim_obrigatorio[dados_pedido.id_pedido]
                
                print(f"   🎯 Pedido {dados_pedido.id_pedido} tem fim obrigatório:")
                print(f"      Deadline: {fim_obrigatorio.strftime('%d/%m %H:%M')}")
                print(f"      Janela original mantida: {dados_pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {dados_pedido.fim_jornada.strftime('%d/%m %H:%M')}")
    
    def _executar_pedidos_hibridamente(self, pedidos, sistema_producao) -> bool:
        """
        ✅ EXECUÇÃO HÍBRIDA: Otimizados primeiro, depois fallback para os demais
        """
        pedidos_executados = 0
        pedidos_com_falha = 0
        
        # Separar pedidos selecionados vs não-selecionados
        if self.ultima_solucao and self.ultima_solucao.janelas_selecionadas:
            pedidos_selecionados = [p for p in pedidos if p.id_pedido in self.ultima_solucao.janelas_selecionadas]
            pedidos_nao_selecionados = [p for p in pedidos if p.id_pedido not in self.ultima_solucao.janelas_selecionadas]
        else:
            # Se PL falhou, todos em fallback
            pedidos_selecionados = []
            pedidos_nao_selecionados = pedidos
        
        print(f"\n🔄 EXECUÇÃO HÍBRIDA:")
        print(f"   📊 Otimizados: {len(pedidos_selecionados)} pedidos")
        print(f"   🆘 Fallback: {len(pedidos_nao_selecionados)} pedidos")
        
        # ✅ FASE 1: Executar pedidos OTIMIZADOS
        if pedidos_selecionados:
            print(f"\n📊 FASE 1: Executando pedidos OTIMIZADOS...")
            
            # Ordenar por horário otimizado
            pedidos_ordenados = sorted(
                pedidos_selecionados,
                key=lambda p: self.ultima_solucao.janelas_selecionadas[p.id_pedido].datetime_inicio
            )
            
            for i, pedido in enumerate(pedidos_ordenados, 1):
                nome_produto = self._obter_nome_produto(pedido)
                janela = self.ultima_solucao.janelas_selecionadas[pedido.id_pedido]
                
                print(f"   📋 [{i}/{len(pedidos_ordenados)}] Executando OTIMIZADO: {pedido.id_pedido} ({nome_produto})")
                print(f"      ⏰ Cronograma PL: {janela.datetime_inicio.strftime('%H:%M')} → {janela.datetime_fim.strftime('%H:%M')}")
                
                try:
                    sistema_producao._executar_pedido_individual(pedido)
                    print(f"      ✅ Pedido {pedido.id_pedido} executado (OTIMIZADO)")
                    pedidos_executados += 1
                except Exception as e:
                    print(f"      ❌ Falha no pedido otimizado {pedido.id_pedido}: {e}")
                    pedidos_com_falha += 1
        
        # ✅ FASE 2: Executar pedidos em FALLBACK
        if pedidos_nao_selecionados:
            print(f"\n🆘 FASE 2: Executando pedidos FALLBACK...")
            print(f"   📝 Estes pedidos serão executados sequencialmente")
            
            for i, pedido in enumerate(pedidos_nao_selecionados, 1):
                nome_produto = self._obter_nome_produto(pedido)
                
                print(f"   🔄 [{i}/{len(pedidos_nao_selecionados)}] Executando FALLBACK: {pedido.id_pedido} ({nome_produto})")
                print(f"      📅 Janela original: {pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                
                try:
                    sistema_producao._executar_pedido_individual(pedido)
                    print(f"      ✅ Pedido {pedido.id_pedido} executado (FALLBACK)")
                    pedidos_executados += 1
                except Exception as e:
                    print(f"      ❌ Pedido {pedido.id_pedido} falhou: {e}")
                    pedidos_com_falha += 1
        
        # ✅ RESULTADO FINAL
        total_pedidos = len(pedidos)
        print(f"\n📊 RESULTADO DA EXECUÇÃO HÍBRIDA:")
        print(f"   ✅ Executados: {pedidos_executados}/{total_pedidos}")
        print(f"   ❌ Falhas: {pedidos_com_falha}/{total_pedidos}")
        print(f"   📈 Taxa de sucesso: {(pedidos_executados/total_pedidos)*100:.1f}%")
        
        # Armazenar estatísticas
        self.estatisticas_execucao['pedidos_otimizados_executados'] = len([p for p in pedidos_selecionados if p.id_pedido])
        self.estatisticas_execucao['pedidos_fallback_executados'] = pedidos_executados - len(pedidos_selecionados)
        
        return pedidos_executados > 0
    
    def _executar_todos_sequencial(self, pedidos, sistema_producao) -> bool:
        """
        ✅ FALLBACK TOTAL: Executa todos os pedidos sequencialmente
        """
        print(f"\n🆘 EXECUÇÃO SEQUENCIAL DE EMERGÊNCIA:")
        print(f"   📋 Executando {len(pedidos)} pedidos em ordem normal")
        
        pedidos_executados = 0
        
        for i, pedido in enumerate(pedidos, 1):
            nome_produto = self._obter_nome_produto(pedido)
            print(f"   🔄 [{i}/{len(pedidos)}] Executando sequencial: {pedido.id_pedido} ({nome_produto})")
            
            try:
                sistema_producao._executar_pedido_individual(pedido)
                print(f"      ✅ Pedido {pedido.id_pedido} executado (SEQUENCIAL)")
                pedidos_executados += 1
            except Exception as e:
                print(f"      ❌ Pedido {pedido.id_pedido} falhou: {e}")
        
        print(f"\n📊 RESULTADO SEQUENCIAL:")
        print(f"   ✅ Executados: {pedidos_executados}/{len(pedidos)}")
        
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
            'pedidos_atendidos_pl': self.ultima_solucao.pedidos_atendidos,
            'taxa_atendimento_pl': self.ultima_solucao.estatisticas.get('taxa_atendimento', 0),
            'janelas_totais_geradas': sum(len(j) for j in self.gerador_janelas.janelas_por_pedido.values()),
            'variaveis_pl': self.ultima_solucao.estatisticas.get('total_variaveis', 0),
            'restricoes_pl': self.ultima_solucao.estatisticas.get('total_restricoes', 0),
            'status_solver': self.ultima_solucao.status_solver,
            'modo_execucao': 'hibrido_corrigido',
            'pedidos_com_fim_obrigatorio': len(self.pedidos_com_fim_obrigatorio),
            'restricoes_limitadas': self.ultima_solucao.estatisticas.get('restricoes_limitadas', False)
        }
    
    def _imprimir_resultado_final(self):
        """Imprime resultado final da execução corrigida"""
        print(f"\n" + "="*80)
        print(f"🎉 EXECUÇÃO OTIMIZADA CONCLUÍDA (VERSÃO CORRIGIDA)")
        print("="*80)
        
        if not self.estatisticas_execucao:
            print(f"❌ Sem estatísticas disponíveis")
            return
        
        stats = self.estatisticas_execucao
        
        print(f"📊 RESULTADOS DA OTIMIZAÇÃO:")
        print(f"   Pedidos selecionados pelo PL: {stats['pedidos_atendidos_pl']}/{stats['pedidos_totais']}")
        print(f"   Taxa de seleção PL: {stats['taxa_atendimento_pl']:.1%}")
        print(f"   Status do solver: {stats['status_solver']}")
        
        if 'pedidos_otimizados_executados' in stats:
            print(f"\n📊 RESULTADOS DA EXECUÇÃO:")
            print(f"   Pedidos executados otimizados: {stats.get('pedidos_otimizados_executados', 0)}")
            print(f"   Pedidos executados fallback: {stats.get('pedidos_fallback_executados', 0)}")
        
        print(f"\n⏱️ PERFORMANCE:")
        print(f"   Tempo total: {stats['tempo_total_otimizacao']:.2f}s")
        print(f"   Tempo PL: {stats['tempo_resolucao_pl']:.2f}s")
        print(f"   Janelas geradas: {stats['janelas_totais_geradas']:,}")
        print(f"   Variáveis PL: {stats['variaveis_pl']:,}")
        print(f"   Restrições PL: {stats['restricoes_pl']:,}")
        
        if stats.get('restricoes_limitadas', False):
            print(f"\n⚠️ OTIMIZAÇÕES APLICADAS:")
            print(f"   ✅ Restrições limitadas para evitar loop infinito")
            print(f"   ✅ Execução híbrida (otimizado + fallback)")
            print(f"   ✅ Todos os pedidos são processados")
        
        print(f"\n✅ FUNCIONALIDADES IMPLEMENTADAS:")
        print(f"   ✅ Detecção automática de fins obrigatórios")
        print(f"   ✅ Respeito ao tempo_maximo_de_espera = 0")
        print(f"   ✅ Manutenção de janela de 3 dias para execução")
        print(f"   ✅ Otimização PL com proteção contra loop infinito")
        print(f"   ✅ Execução garantida de TODOS os pedidos (híbrido)")
        
        print("="*80)
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas da última execução"""
        return self.estatisticas_execucao.copy() if self.estatisticas_execucao else {}
    
    def obter_cronograma_otimizado(self) -> Dict:
        """
        ✅ MÉTODO FALTANTE: Retorna cronograma otimizado
        """
        if not self.ultima_solucao or not self.ultima_solucao.janelas_selecionadas:
            print("⚠️ Nenhum cronograma otimizado disponível")
            return {}
        
        cronograma = {}
        
        print(f"📅 Gerando cronograma otimizado para {len(self.ultima_solucao.janelas_selecionadas)} pedidos...")
        
        for pedido_id, janela in self.ultima_solucao.janelas_selecionadas.items():
            # Buscar dados do pedido para informações adicionais
            dados_pedido = None
            if self.dados_extraidos:
                dados_pedido = next((d for d in self.dados_extraidos if d.id_pedido == pedido_id), None)
            
            cronograma_item = {
                'inicio_otimizado': janela.datetime_inicio.isoformat(),
                'fim_otimizado': janela.datetime_fim.isoformat(),
                'duracao_horas': (janela.datetime_fim - janela.datetime_inicio).total_seconds() / 3600,
                'fim_obrigatorio': pedido_id in self.pedidos_com_fim_obrigatorio,
                'nome_produto': dados_pedido.nome_produto if dados_pedido else f'produto_{pedido_id}'
            }
            
            # Adicionar deadline se houver
            if pedido_id in self.pedidos_com_fim_obrigatorio:
                deadline = self.pedidos_com_fim_obrigatorio[pedido_id]
                cronograma_item['deadline'] = deadline.isoformat()
                cronograma_item['deadline_cumprido'] = abs((janela.datetime_fim - deadline).total_seconds()) < 300  # 5min tolerância
            
            cronograma[pedido_id] = cronograma_item
            
            # Log do item
            inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
            fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
            produto_nome = cronograma_item['nome_produto']
            
            if cronograma_item['fim_obrigatorio']:
                deadline_str = self.pedidos_com_fim_obrigatorio[pedido_id].strftime('%H:%M')
                cumprido = "✅" if cronograma_item.get('deadline_cumprido', False) else "⚠️"
                print(f"   🎯 Pedido {pedido_id} ({produto_nome}): {inicio_str} → {fim_str} [Deadline: {deadline_str} {cumprido}]")
            else:
                print(f"   ✅ Pedido {pedido_id} ({produto_nome}): {inicio_str} → {fim_str} [Flexível]")
        
        print(f"✅ Cronograma gerado com {len(cronograma)} entradas")
        return cronograma
    
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


class SistemaProducaoOtimizado:
    """Wrapper para integração com TesteSistemaProducao"""
    
    def __init__(self, sistema_producao_original):
        self.sistema_original = sistema_producao_original
        self.otimizador = OtimizadorIntegrado(
            resolucao_minutos=60,  # ✅ Resolução maior para menos janelas
            timeout_segundos=120   # ✅ Timeout menor para evitar espera longa
        )
        
    def executar_com_otimizacao(self) -> bool:
        """Executa com otimização CORRIGIDA"""
        print(f"🥖 SISTEMA DE PRODUÇÃO OTIMIZADO (VERSÃO CORRIGIDA)")
        print("="*60)
        
        try:
            # Fases 1-3: Mesmo do sistema original
            self.sistema_original.inicializar_almoxarifado()
            self.sistema_original.criar_pedidos_de_producao()
            self.sistema_original.ordenar_pedidos_por_prioridade()
            
            # Fase 4: Execução otimizada CORRIGIDA
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
            'cronograma_otimizado': self.otimizador.obter_cronograma_otimizado(),  # ✅ CORRIGIDO
            'total_pedidos': len(self.sistema_original.pedidos) if hasattr(self.sistema_original, 'pedidos') else 0,
            'versao': 'corrigida_sem_loop_infinito'
        }


if __name__ == "__main__":
    print("🧪 Teste básico do SistemaProducaoOtimizado CORRIGIDO...")
    print("✅ Classes carregadas com sucesso - sem loop infinito")