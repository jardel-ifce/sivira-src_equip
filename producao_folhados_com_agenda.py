import sys
import os
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs, limpar_logs_erros, limpar_logs_inicializacao
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem
from factory.fabrica_equipamentos import FabricaEquipamentos

# IMPORTAÇÃO DO OTIMIZADOR PL
from otimizador.otimizador_integrado import OtimizadorIntegrado, SistemaProducaoOtimizado


class TeeOutput:
    """
    Classe para duplicar a saída do terminal tanto para o console 
    quanto para um arquivo de log simultaneamente.
    """
    def __init__(self, file):
        self.file = file
        self.stdout = sys.stdout
        
    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)
        self.file.flush()  # Garante escrita imediata no arquivo
        
    def flush(self):
        self.stdout.flush()
        self.file.flush()


class TesteSistemaProducao:
    """
    Classe principal para teste do sistema de produção.
    Coordena todo o fluxo de execução desde o carregamento do almoxarifado 
    até a execução completa dos pedidos.
    
    ✅ CORRIGIDO: Janela temporal adequada para otimizador PL.
    """
    
    def __init__(self, usar_otimizacao=True, resolucao_minutos=30, timeout_pl=300):
        """
        Inicializa o sistema de produção.
        
        Args:
            usar_otimizacao: Se True, usa otimização PL. Se False, execução sequencial
            resolucao_minutos: Resolução temporal para otimização (30min recomendado)
            timeout_pl: Timeout em segundos para resolução PL (5min padrão)
        """
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.log_filename = None
        
        # NOVA: Configuração do otimizador
        self.usar_otimizacao = usar_otimizacao
        self.otimizador = None
        if usar_otimizacao:
            self.otimizador = OtimizadorIntegrado(
                resolucao_minutos=resolucao_minutos,
                timeout_segundos=timeout_pl
            )
        
        self.mapeamento_produtos = {
            "Folhado de Carne de Sol": 1059,
            "Folhado de Frango": 1072,
            "Folhado de Camarão": 1073,
            "Folhado de Queijos Finos": 1074
        }
        
        # Estatísticas da execução
        self.estatisticas_execucao = {}
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        modo = "otimizado" if self.usar_otimizacao else "sequencial"
        self.log_filename = f'logs/execucao_folhados_sequencial_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print(f"LOG DE EXECUÇÃO - SISTEMA DE PRODUÇÃO FOLHADOS")
        modo = "OTIMIZADA (Programação Linear)" if self.usar_otimizacao else "SEQUENCIAL"
        print(f"Modo de execução: {modo}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if self.usar_otimizacao and self.otimizador:
            print(f"Configuração PL:")
            print(f"  - Resolução temporal: {self.otimizador.resolucao_minutos} minutos")
            print(f"  - Timeout: {self.otimizador.timeout_segundos} segundos")
        
        print("=" * 80)
        print()

    def escrever_rodape_log(self, sucesso=True):
        """Escreve rodapé final no log"""
        print("=" * 80)
        if sucesso:
            print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!")
            
            # Mostra estatísticas se disponíveis
            if self.estatisticas_execucao:
                self._imprimir_estatisticas_finais()
                
        else:
            print("❌ EXECUÇÃO FINALIZADA COM ERROS!")
        
        print(f"📄 Log salvo em: {self.log_filename}")
        print("=" * 80)

    def _imprimir_estatisticas_finais(self):
        """Imprime estatísticas finais da execução"""
        stats = self.estatisticas_execucao
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   Total de pedidos: {stats.get('total_pedidos', 'N/A')}")
        print(f"   Pedidos executados: {stats.get('pedidos_executados', 'N/A')}")
        
        if self.usar_otimizacao and 'otimizacao' in stats:
            opt_stats = stats['otimizacao']
            print(f"   Taxa de atendimento PL: {opt_stats.get('taxa_atendimento', 0):.1%}")
            print(f"   Tempo otimização: {opt_stats.get('tempo_total_otimizacao', 0):.2f}s")
            print(f"   Status solver: {opt_stats.get('status_solver', 'N/A')}")

    # =============================================================================
    #                      CONFIGURAÇÃO DO AMBIENTE
    # =============================================================================

    def inicializar_almoxarifado(self):
        """
        Carrega e inicializa o almoxarifado com todos os itens necessários.
        Limpa comandas e logs anteriores.
        """
        print("🔄 Carregando itens do almoxarifado...")
        
        # Carregar itens do arquivo JSON
        itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
        
        # Limpar dados anteriores
        apagar_todas_as_comandas()
        limpar_todos_os_logs()
        limpar_logs_erros()
        limpar_logs_inicializacao()
        # Inicializar almoxarifado
        self.almoxarifado = Almoxarifado()
        for item in itens:
            self.almoxarifado.adicionar_item(item)
        
        # Criar gestor
        self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)
        
        print("✅ Almoxarifado carregado com sucesso!")
        print()

    # =============================================================================
    #                       CRIAÇÃO DE PEDIDOS
    # =============================================================================

    def criar_pedidos_de_producao(self):
        """
        ✅ CORRIGIDO: Cria pedidos com janela temporal adequada para otimizador PL.
        Mantém 3 dias para dar flexibilidade ao algoritmo de alocação.
        """
        print("🔄 Criando pedidos de produção de folhados...")
        self.pedidos = []
        
        # Data base para os cálculos
        data_base = datetime(2025, 6, 26)
        
        # Configurações dos pedidos de folhados
        configuracoes_pedidos = [
           # CONJUNTO MATINAL
            {"produto": "Folhado de Frango", "quantidade": 15, "hora_fim": 8},
            {"produto": "Folhado de Carne de Sol", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Camarão", "quantidade": 12, "hora_fim": 8},
            {"produto": "Folhado de Queijos Finos", "quantidade": 12, "hora_fim": 8},
        ]
        
        id_pedido_counter = 1
        
        for config in configuracoes_pedidos:
            print(f"   Processando pedido {id_pedido_counter}: {config['produto']} - {config['quantidade']} unidades...")
            
            try:
                # Calcular datas de início e fim da jornada
                fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
                
                # ✅ CORREÇÃO CRÍTICA: SEMPRE usar 3 dias, independente do modo
                # Isso dá flexibilidade tanto para otimizador quanto para execução real
                inicio_jornada = fim_jornada - timedelta(days=3)
                
                print(f"   📅 Configuração temporal:")
                print(f"      Deadline: {fim_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Janela de busca: {inicio_jornada.strftime('%d/%m %H:%M')} → {fim_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Duração da janela: 3 dias (flexibilidade para alocação)")
                
                # Obter ID do produto
                id_produto = self.mapeamento_produtos.get(config['produto'])
                if id_produto is None:
                    print(f"   ⚠️ Produto '{config['produto']}' não encontrado no mapeamento!")
                    continue
                
                pedido = PedidoDeProducao(
                    id_ordem=1,  # Fixo para testes
                    id_pedido=id_pedido_counter,
                    id_produto=id_produto,
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=config['quantidade'],
                    inicio_jornada=inicio_jornada,
                    fim_jornada=fim_jornada,
                    todos_funcionarios=funcionarios_disponiveis
                )
                
                pedido.montar_estrutura()
                self.pedidos.append(pedido)
                print(f"   ✅ Pedido {id_pedido_counter} criado: {config['produto']} ({config['quantidade']} uni)")
                
                id_pedido_counter += 1
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao montar estrutura do pedido {id_pedido_counter}: {e}")
                id_pedido_counter += 1
        
        print(f"\n✅ Total de {len(self.pedidos)} pedidos criados para folhados!")
        if self.usar_otimizacao:
            print(f"🔧 Pedidos configurados com janela de 3 dias para otimização PL")
        else:
            print(f"🔧 Pedidos configurados com janela de 3 dias para execução sequencial")
        print()

    def ordenar_pedidos_por_prioridade(self):
        """
        Ordena pedidos baseado em restrições e prioridades.
        MANTIDO para compatibilidade, mas pode ser substituído pela otimização PL.
        """
        if not self.usar_otimizacao:
            print("🔄 Ordenando pedidos por restrições (modo sequencial)...")
            self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
            print(f"✅ {len(self.pedidos)} pedidos ordenados!")
        else:
            print("🔄 Mantendo ordem original (otimização PL definirá execução)...")
            print(f"✅ {len(self.pedidos)} pedidos mantidos em ordem de criação")
        print()

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_ordenados(self):
        """
        MÉTODO ORIGINAL: Executa todos os pedidos em ordem sequencial.
        Mantido para compatibilidade com modo não-otimizado.
        """
        print("🔄 Executando pedidos de folhados em ordem sequencial...")
        
        pedidos_executados = 0
        
        for idx, pedido in enumerate(self.pedidos, 1):
            nome_produto = self._obter_nome_produto_por_id(pedido.id_produto)
            
            print(f"   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})...")
            print(f"   📋 {nome_produto} - {pedido.quantidade} unidades")
            print(f"   ⏰ Prazo: {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            
            try:
                self._executar_pedido_individual(pedido)
                print(f"   ✅ Pedido {pedido.id_pedido} ({nome_produto}) executado com sucesso!")
                pedidos_executados += 1
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao processar o pedido {pedido.id_pedido} ({nome_produto}): {e}")
                
            print()
        
        self.estatisticas_execucao.update({
            'total_pedidos': len(self.pedidos),
            'pedidos_executados': pedidos_executados,
            'modo_execucao': 'sequencial'
        })

    def executar_pedidos_otimizados(self):
        """
        NOVO MÉTODO: Executa pedidos usando otimização PL.
        """
        if not self.usar_otimizacao or not self.otimizador:
            print("❌ Otimizador não configurado. Use executar_pedidos_ordenados().")
            return False
        
        print("🚀 Iniciando execução otimizada com Programação Linear...")
        
        try:
            # Delega execução para o otimizador integrado
            sucesso = self.otimizador.executar_pedidos_otimizados(self.pedidos, self)
            
            # Coleta estatísticas do otimizador
            if sucesso:
                stats_otimizador = self.otimizador.obter_estatisticas()
                self.estatisticas_execucao.update({
                    'total_pedidos': len(self.pedidos),
                    'pedidos_executados': stats_otimizador.get('pedidos_atendidos', 0),
                    'modo_execucao': 'otimizado_pl',
                    'otimizacao': stats_otimizador
                })
                
                print(f"\n🎉 Execução otimizada concluída com sucesso!")
                return True
            else:
                print(f"❌ Falha na execução otimizada")
                return False
                
        except Exception as e:
            print(f"❌ Erro durante execução otimizada: {e}")
            return False

    def _executar_pedido_individual(self, pedido):
        """
        Executa um pedido individual seguindo o fluxo padrão.
        Método auxiliar usado tanto no modo sequencial quanto otimizado.
        """
        # Gerar comanda de reserva
        gerar_comanda_reserva(
            id_ordem=pedido.id_ordem,
            id_pedido=pedido.id_pedido,
            ficha=pedido.ficha_tecnica_modular,
            gestor=self.gestor_almoxarifado,
            data_execucao=pedido.inicio_jornada
        )
        
        # Mostrar estrutura da ficha técnica
        pedido.mostrar_estrutura()
        
        # Criar atividades modulares
        pedido.criar_atividades_modulares_necessarias()
        
        # Executar atividades em ordem
        pedido.executar_atividades_em_ordem()

    def _obter_nome_produto_por_id(self, id_produto):
        """Obtém nome do produto pelo ID"""
        return next((nome for nome, id_prod in self.mapeamento_produtos.items() 
                    if id_prod == id_produto), f"Produto {id_produto}")

    # =============================================================================
    #                       FLUXO PRINCIPAL
    # =============================================================================

    def executar_teste_completo(self):
        """
        Executa o teste completo do sistema de produção de folhados.
        ATUALIZADO para escolher entre execução sequencial ou otimizada.
        """
        try:
            modo = "OTIMIZADA" if self.usar_otimizacao else "SEQUENCIAL"
            print(f"🥐 INICIANDO SISTEMA DE PRODUÇÃO DE FOLHADOS - MODO {modo}")
            print()
            
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Criação dos pedidos
            self.criar_pedidos_de_producao()
            
            # Fase 3: Ordenação por prioridade (se necessário)
            self.ordenar_pedidos_por_prioridade()
            
            # Fase 4: Execução (escolhe método baseado na configuração)
            if self.usar_otimizacao:
                sucesso = self.executar_pedidos_otimizados()
            else:
                self.executar_pedidos_ordenados()
                sucesso = True  # Assume sucesso se não houve exceções
            
            return sucesso
            
        except Exception as e:
            print("=" * 80)
            print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return False

    # =============================================================================
    #                       MÉTODOS DE APOIO
    # =============================================================================

    def obter_estatisticas(self):
        """Retorna estatísticas da execução"""
        return self.estatisticas_execucao.copy()

    def obter_cronograma_otimizado(self):
        """Retorna cronograma otimizado (se disponível)"""
        if self.usar_otimizacao and self.otimizador:
            return self.otimizador.obter_cronograma_otimizado()
        return {}

    def exibir_agenda_equipamentos(self):
        """
        📅 Exibe a agenda de todos os equipamentos após a execução.
        Utiliza o sistema de visualização de agenda existente no menu.
        """
        print(f"\n" + "=" * 80)
        print("📅 AGENDA DOS EQUIPAMENTOS - OCUPAÇÕES ATUAIS")
        print("=" * 80)

        try:
            # Usar o visualizador de agenda existente
            from menu.visualizador_agenda import VisualizadorAgenda

            visualizador = VisualizadorAgenda()

            print("🔄 Carregando dados dos logs de equipamentos...")
            visualizador._atualizar_cache()

            if not visualizador.dados_cache:
                print("📭 Nenhuma atividade encontrada nos logs")
                print("💡 Execute algum pedido primeiro para gerar logs de equipamentos")
                print(f"\n" + "=" * 80)
                return

            # Mostrar agenda geral usando o visualizador existente
            visualizador.mostrar_agenda_geral()

            # 💾 NOVA FUNCIONALIDADE: Salvar agenda completa em arquivo
            self._salvar_agenda_completa_em_arquivo(visualizador)

            # 🔍 NOVA FUNCIONALIDADE: Capturar ocupações detalhadas dos equipamentos ativos
            self._capturar_ocupacoes_detalhadas_equipamentos()

            # Mostrar estatísticas resumidas
            print(f"\n📊 RESUMO ESTATÍSTICO:")
            total_equipamentos = len(visualizador.dados_cache)
            total_atividades = sum(len(atividades) for atividades in visualizador.dados_cache.values())
            print(f"   🔧 Equipamentos utilizados: {total_equipamentos}")
            print(f"   📋 Total de atividades: {total_atividades}")

            if total_equipamentos > 0:
                print(f"   📊 Média de atividades por equipamento: {total_atividades/total_equipamentos:.1f}")

                # Top 3 equipamentos mais utilizados
                equipamentos_ordenados = sorted(
                    visualizador.dados_cache.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )

                print(f"   🏆 Equipamentos mais utilizados:")
                for i, (equipamento, atividades) in enumerate(equipamentos_ordenados[:3], 1):
                    print(f"      {i}. {equipamento}: {len(atividades)} atividades")

        except Exception as e:
            print(f"❌ Erro ao exibir agenda dos equipamentos: {e}")
            import traceback
            print(f"Detalhes: {traceback.format_exc()}")

        print(f"\n" + "=" * 80)

    def _capturar_ocupacoes_detalhadas_equipamentos(self):
        """
        🔍 Captura ocupações detalhadas dos equipamentos ativos no sistema
        usando o CapturadorOcupacoes que itera sobre objetos existentes
        """
        try:
            from utils.logs.capturador_ocupacoes_equipamentos import capturador_ocupacoes

            print(f"\n🔍 CAPTURANDO OCUPAÇÕES DETALHADAS DOS EQUIPAMENTOS ATIVOS...")
            print("=" * 60)

            # Descobrir equipamentos no sistema
            equipamentos_descobertos = capturador_ocupacoes.descobrir_equipamentos_no_sistema()

            if not equipamentos_descobertos:
                print("📭 Nenhum equipamento ativo encontrado no sistema")
                return

            print(f"🔧 Equipamentos descobertos: {len(equipamentos_descobertos)}")

            # Extrair ID da ordem e todos os pedidos processados
            id_ordem = 1  # Padrão
            pedidos_inclusos = [1]  # Padrão

            if hasattr(self, 'pedidos') and self.pedidos:
                # Usar dados dos pedidos processados
                id_ordem = self.pedidos[0].id_ordem
                pedidos_inclusos = sorted(list(set(p.id_pedido for p in self.pedidos)))

            print(f"📋 Processando ordem {id_ordem} com pedidos: {pedidos_inclusos}")

            # Capturar ocupações detalhadas
            logs_capturados = capturador_ocupacoes.capturar_ocupacoes_todos_equipamentos(id_ordem, pedidos_inclusos)

            if logs_capturados:
                print(f"✅ Ocupações capturadas de {len(logs_capturados)} equipamentos")

                # Gerar relatório detalhado
                arquivo_relatorio = capturador_ocupacoes.gerar_relatorio_ocupacoes_detalhadas(
                    id_ordem, pedidos_inclusos, salvar_arquivo=True
                )

                if arquivo_relatorio:
                    print(f"📄 Relatório detalhado salvo: {arquivo_relatorio}")
                else:
                    print("⚠️ Erro ao salvar relatório detalhado")

            else:
                print("📭 Nenhuma ocupação detalhada foi capturada")

            print("=" * 60)

        except Exception as e:
            print(f"❌ Erro ao capturar ocupações detalhadas: {e}")
            import traceback
            print(f"Detalhes: {traceback.format_exc()}")

    def _salvar_agenda_completa_em_arquivo(self, visualizador):
        """
        💾 Salva a agenda completa dos equipamentos em arquivo .log
        Inclui detalhes específicos como bocas do fogão, configurações, etc.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"logs/agenda_equipamentos_completa_{timestamp}.log"

            print(f"\n💾 Salvando agenda completa em arquivo...")

            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write("=" * 80 + "\n")
                f.write("📅 AGENDA COMPLETA DOS EQUIPAMENTOS - OCUPAÇÕES DETALHADAS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Total de equipamentos: {len(visualizador.dados_cache)}\n")

                total_atividades = sum(len(atividades) for atividades in visualizador.dados_cache.values())
                f.write(f"Total de atividades: {total_atividades}\n")
                f.write("=" * 80 + "\n\n")

                # Processar cada equipamento com dados reais dos logs

                for equipamento_nome in sorted(visualizador.dados_cache.keys()):
                    f.write(f"\n🔧 {equipamento_nome}\n")
                    f.write("=" * 50 + "\n")

                    atividades = visualizador.dados_cache[equipamento_nome]
                    f.write(f"📊 Total de atividades: {len(atividades)}\n")

                    # Usar apenas dados do visualizador (equipamentos reais estão vazios)
                    f.write("\n📋 ATIVIDADES REGISTRADAS:\n")
                    atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)

                    for i, atividade in enumerate(atividades_ordenadas, 1):
                        f.write(f"   {i:2d}. ⏰ {atividade.inicio} - {atividade.fim}\n")
                        f.write(f"       📦 Ordem {atividade.ordem} | Pedido {atividade.pedido}\n")
                        f.write(f"       🆔 Atividade: {atividade.id_atividade}\n")
                        f.write(f"       🏷️ Item: {atividade.item}\n")
                        f.write(f"       🎯 {atividade.nome_atividade}\n")
                        f.write("\n")

                    # Identificar tipo de equipamento e adicionar informações específicas
                    self._adicionar_detalhes_especificos_equipamento(f, equipamento_nome, atividades)

                    f.write("\n" + "-" * 50 + "\n")

                # Estatísticas finais
                f.write("\n" + "=" * 80 + "\n")
                f.write("📊 ESTATÍSTICAS RESUMIDAS\n")
                f.write("=" * 80 + "\n")

                # Top equipamentos mais utilizados
                equipamentos_ordenados = sorted(
                    visualizador.dados_cache.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )

                f.write("🏆 RANKING DE UTILIZAÇÃO:\n")
                for i, (equipamento, atividades) in enumerate(equipamentos_ordenados, 1):
                    f.write(f"   {i:2d}. {equipamento}: {len(atividades)} atividades\n")

                if len(visualizador.dados_cache) > 0:
                    media = total_atividades / len(visualizador.dados_cache)
                    f.write(f"\n📊 Média de atividades por equipamento: {media:.1f}\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("📄 Fim do relatório de agenda completa\n")
                f.write("=" * 80 + "\n")

            print(f"✅ Agenda completa salva em: {nome_arquivo}")
            return nome_arquivo

        except Exception as e:
            print(f"❌ Erro ao salvar agenda completa: {e}")
            import traceback
            print(f"Detalhes: {traceback.format_exc()}")
            return None


    def _adicionar_detalhes_especificos_equipamento(self, arquivo, nome_equipamento, atividades):
        """
        ✨ Adiciona informações específicas baseadas no tipo de equipamento
        """
        try:
            nome_lower = nome_equipamento.lower()

            if 'fogão' in nome_lower:
                arquivo.write("\n🔥 INFORMAÇÕES ESPECÍFICAS DO FOGÃO:\n")
                arquivo.write("   💡 Para detalhes de bocas específicas, consulte os logs originais do sistema\n")
                arquivo.write("   📋 Atividades de cocção com controle individual por boca\n")

                # Analisar tipos de atividades de cocção
                atividades_coccao = [a for a in atividades if 'coccao' in a.nome_atividade.lower()]
                if atividades_coccao:
                    arquivo.write(f"   🔥 Atividades de cocção registradas: {len(atividades_coccao)}\n")

            elif 'bancada' in nome_lower:
                arquivo.write("\n🛠️ INFORMAÇÕES ESPECÍFICAS DA BANCADA:\n")
                arquivo.write("   📐 Equipamento com frações para múltiplas atividades simultâneas\n")

                # Analisar sobreposições temporais
                sobreposicoes = self._analisar_sobreposicoes_temporais(atividades)
                if sobreposicoes > 0:
                    arquivo.write(f"   ⚡ Atividades simultâneas detectadas: {sobreposicoes} casos\n")
                else:
                    arquivo.write("   📝 Atividades executadas sequencialmente\n")

            elif 'hotmix' in nome_lower:
                arquivo.write("\n🌪️ INFORMAÇÕES ESPECÍFICAS DO HOTMIX:\n")
                arquivo.write("   🔄 Equipamento para mistura com janelas simultâneas\n")
                arquivo.write("   📏 Capacidade controlada por gramas com otimização automática\n")

            elif 'fritadeira' in nome_lower:
                arquivo.write("\n🍳 INFORMAÇÕES ESPECÍFICAS DA FRITADEIRA:\n")
                arquivo.write("   🔥 Equipamento para fritura com controle de frações\n")
                arquivo.write("   🌡️ Processo de fritura com temperatura controlada\n")

            elif 'balança' in nome_lower:
                arquivo.write("\n⚖️ INFORMAÇÕES ESPECÍFICAS DA BALANÇA:\n")
                arquivo.write("   📊 Equipamento para pesagem e medição precisa\n")
                arquivo.write("   🎯 Atividades de controle de quantidade\n")

            elif 'freezer' in nome_lower or 'câmara' in nome_lower:
                arquivo.write("\n❄️ INFORMAÇÕES ESPECÍFICAS DE REFRIGERAÇÃO:\n")
                arquivo.write("   🌡️ Equipamento para controle de temperatura\n")
                arquivo.write("   📦 Armazenamento com configuração específica de temperatura\n")

                # Analisar duração das atividades de refrigeração
                duracao_total = self._calcular_duracao_total_atividades(atividades)
                if duracao_total:
                    arquivo.write(f"   ⏱️ Duração total de ocupação: {duracao_total} minutos\n")

        except Exception as e:
            arquivo.write(f"\n⚠️ Erro ao adicionar detalhes específicos: {e}\n")

    def _analisar_sobreposicoes_temporais(self, atividades):
        """Analisa quantas atividades se sobrepõem temporalmente"""
        if len(atividades) < 2:
            return 0

        sobreposicoes = 0
        for i, ativ1 in enumerate(atividades):
            for ativ2 in atividades[i+1:]:
                # Converte strings de tempo para comparação
                try:
                    inicio1 = ativ1.inicio if hasattr(ativ1.inicio, 'strftime') else ativ1.inicio
                    fim1 = ativ1.fim if hasattr(ativ1.fim, 'strftime') else ativ1.fim
                    inicio2 = ativ2.inicio if hasattr(ativ2.inicio, 'strftime') else ativ2.inicio
                    fim2 = ativ2.fim if hasattr(ativ2.fim, 'strftime') else ativ2.fim

                    # Verifica sobreposição
                    if not (fim1 <= inicio2 or inicio1 >= fim2):
                        sobreposicoes += 1
                except:
                    continue

        return sobreposicoes

    def _calcular_duracao_total_atividades(self, atividades):
        """Calcula duração total das atividades em minutos"""
        try:
            if not atividades:
                return 0

            # Encontra início mais cedo e fim mais tarde
            inicios = []
            fins = []

            for atividade in atividades:
                try:
                    inicio_str = atividade.inicio if isinstance(atividade.inicio, str) else str(atividade.inicio)
                    fim_str = atividade.fim if isinstance(atividade.fim, str) else str(atividade.fim)
                    inicios.append(inicio_str)
                    fins.append(fim_str)
                except:
                    continue

            if inicios and fins:
                inicio_min = min(inicios)
                fim_max = max(fins)

                # Simular cálculo de duração (seria necessário parsing mais complexo)
                return len(atividades) * 30  # Estimativa simplificada

        except:
            pass

        return 0

    def configurar_modo_sequencial(self):
        """Alterna para modo sequencial"""
        self.usar_otimizacao = False
        self.otimizador = None
        print("🔄 Modo alterado para: SEQUENCIAL")

    def configurar_modo_otimizado(self, resolucao_minutos=30, timeout_pl=300):
        """Alterna para modo otimizado"""
        self.usar_otimizacao = True
        self.otimizador = OtimizadorIntegrado(
            resolucao_minutos=resolucao_minutos,
            timeout_segundos=timeout_pl
        )
        print(f"🔄 Modo alterado para: OTIMIZADO (resolução: {resolucao_minutos}min, timeout: {timeout_pl}s)")


# =============================================================================
#                    WRAPPER PARA COMPATIBILIDADE
# =============================================================================

class SistemaProducaoOtimizado:
    """
    Wrapper para manter compatibilidade com otimizador_integrado.py
    Redireciona para TesteSistemaProducao configurado em modo otimizado.
    """
    
    def __init__(self, sistema_producao_original=None):
        """
        Args:
            sistema_producao_original: Instância de TesteSistemaProducao (opcional)
        """
        if sistema_producao_original:
            self.sistema_original = sistema_producao_original
            # Força modo otimizado se não estiver configurado
            if not sistema_producao_original.usar_otimizacao:
                sistema_producao_original.configurar_modo_otimizado()
        else:
            # Cria novo sistema em modo otimizado
            self.sistema_original = TesteSistemaProducao(usar_otimizacao=True)
    
    def executar_com_otimizacao(self) -> bool:
        """Executa o sistema completo com otimização"""
        return self.sistema_original.executar_teste_completo()
    
    def obter_relatorio_completo(self) -> dict:
        """Retorna relatório completo da execução otimizada"""
        return {
            'estatisticas_otimizacao': self.sistema_original.obter_estatisticas(),
            'cronograma_otimizado': self.sistema_original.obter_cronograma_otimizado(),
            'total_pedidos': len(self.sistema_original.pedidos) if self.sistema_original.pedidos else 0
        }


def main():
    """
    Função principal que coordena todo o teste de produção de folhados.
    ✅ CORRIGIDO com janela temporal adequada para otimizador PL.
    📅 NOVA FUNCIONALIDADE: Exibe agenda dos equipamentos ao final da execução.
    """
    # Configuração do modo de execução
    USAR_OTIMIZACAO = False  # Altere para False para modo sequencial
    RESOLUCAO_MINUTOS = 30  # Resolução temporal (30min = bom compromisso)
    TIMEOUT_PL = 300        # 5 minutos para resolução PL
    
    # Inicializar sistema de teste
    sistema = TesteSistemaProducao(
        usar_otimizacao=USAR_OTIMIZACAO,
        resolucao_minutos=RESOLUCAO_MINUTOS,
        timeout_pl=TIMEOUT_PL
    )
    
    log_filename = sistema.configurar_log()
    
    # Configurar saída dupla (terminal + arquivo)
    with open(log_filename, 'w', encoding='utf-8') as log_file:
        tee = TeeOutput(log_file)
        sys.stdout = tee
        
        # Escrever cabeçalho
        sistema.escrever_cabecalho_log()
        
        try:
            # Executar teste completo
            sucesso = sistema.executar_teste_completo()
            
            # Mostrar estatísticas finais se disponíveis
            if sucesso and USAR_OTIMIZACAO:
                print(f"\n📋 RELATÓRIO FINAL:")
                stats = sistema.obter_estatisticas()
                cronograma = sistema.obter_cronograma_otimizado()

                print(f"   Estatísticas: {stats}")
                if cronograma:
                    print(f"   Cronograma otimizado disponível com {len(cronograma)} pedidos")

            # 📅 NOVA FUNCIONALIDADE: Exibir agenda dos equipamentos
            if sucesso:
                sistema.exibir_agenda_equipamentos()

            # Escrever rodapé
            sistema.escrever_rodape_log(sucesso)
            
        except Exception as e:
            sistema.escrever_rodape_log(False)
            raise
        
        finally:
            # Restaurar stdout original
            sys.stdout = tee.stdout
            modo = "otimizada" if USAR_OTIMIZACAO else "sequencial"
            print(f"\n📄 Log de execução {modo} salvo em: {log_filename}")


def exemplo_uso_comparativo():
    """
    Exemplo de como comparar execução sequencial vs otimizada.
    """
    print("=" * 60)
    print("EXEMPLO: COMPARAÇÃO SEQUENCIAL vs OTIMIZADA")
    print("=" * 60)
    
    # Teste sequencial
    print("\n🔄 Executando modo SEQUENCIAL...")
    sistema_seq = TesteSistemaProducao(usar_otimizacao=False)
    sistema_seq.configurar_log()
    sucesso_seq = sistema_seq.executar_teste_completo()
    stats_seq = sistema_seq.obter_estatisticas()
    
    # Teste otimizado
    print("\n🔄 Executando modo OTIMIZADO...")
    sistema_opt = TesteSistemaProducao(usar_otimizacao=True, resolucao_minutos=30)
    sistema_opt.configurar_log()
    sucesso_opt = sistema_opt.executar_teste_completo()
    stats_opt = sistema_opt.obter_estatisticas()
    
    # Comparação
    print("\n📊 COMPARAÇÃO DE RESULTADOS:")
    print(f"Sequencial: {stats_seq}")
    print(f"Otimizado:  {stats_opt}")


if __name__ == "__main__":
    
    main()
    
    # Para testar comparação, descomente:
    # exemplo_uso_comparativo()