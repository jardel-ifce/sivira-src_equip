"""
Executor de Produção - CORRIGIDO
=================================

Corrige a inicialização do gestor de almoxarifado para ser idêntica ao producao_paes_backup.py
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Adiciona path do sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos, DadosPedidoMenu
from menu.utils_menu import MenuUtils


class ExecutorProducao:
    """Executa produção usando TesteSistemaProducao diretamente"""
    
    def __init__(self):
        self.utils = MenuUtils()
        self.configuracoes = {
            'resolucao_minutos': 30,
            'timeout_pl': 300,
        }
        self.sistema_producao = None
        
        # ✅ NOVO: Limpa logs e pedidos automaticamente na inicialização
        self._limpar_logs_inicializacao()
        self._limpar_pedidos_inicializacao()
        
    def _limpar_pedidos_inicializacao(self):
        """
        ✅ NOVO: Limpa pedidos salvos automaticamente quando ExecutorProducao é inicializado.
        Remove arquivo de pedidos salvos para garantir início limpo.
        """
        try:
            print("🗑️ Limpando pedidos de execuções anteriores...")
            
            # Define caminho do arquivo de pedidos salvos
            arquivo_pedidos = "menu/pedidos_salvos.json"
            
            if os.path.exists(arquivo_pedidos):
                # Lê arquivo para mostrar quantos pedidos serão removidos
                try:
                    import json
                    with open(arquivo_pedidos, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    total_pedidos = len(dados.get('pedidos', []))
                    if total_pedidos > 0:
                        print(f"   📋 Removendo {total_pedidos} pedido(s) de execuções anteriores...")
                        
                        # Remove o arquivo
                        os.remove(arquivo_pedidos)
                        print(f"   ✅ Arquivo {arquivo_pedidos} removido")
                    else:
                        print("   📭 Nenhum pedido anterior encontrado")
                        # Remove arquivo vazio mesmo assim
                        os.remove(arquivo_pedidos)
                        
                except (json.JSONDecodeError, KeyError):
                    print(f"   ⚠️ Arquivo {arquivo_pedidos} corrompido, removendo...")
                    os.remove(arquivo_pedidos)
                    
            else:
                print("   📭 Nenhum arquivo de pedidos anteriores encontrado")
            
            print("✅ Pedidos de execuções anteriores limpos automaticamente")
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar pedidos na inicialização: {e}")
        
    def _limpar_logs_inicializacao(self):
        """
        ✅ NOVO: Limpa logs automaticamente quando ExecutorProducao é inicializado.
        Garante ambiente limpo a cada execução do menu.
        """
        try:
            print("🧹 Limpando logs anteriores automaticamente...")
            
            # Importa módulos de limpeza
            from utils.logs.gerenciador_logs import limpar_todos_os_logs
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            
            # Executa limpeza
            limpar_todos_os_logs()
            apagar_todas_as_comandas()
            
            print("✅ Logs e comandas limpos automaticamente")
            
        except ImportError as e:
            print(f"⚠️ Módulos de limpeza não disponíveis: {e}")
        except Exception as e:
            print(f"⚠️ Erro ao limpar logs na inicialização: {e}")
        
    def executar_sequencial(self, pedidos_menu: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos em modo sequencial usando TesteSistemaProducao.
        ✅ CORRIGIDO: Usa estrutura EXATA do producao_paes_backup.py (sem otimização).
        """
        print(f"\n📄 INICIANDO EXECUÇÃO SEQUENCIAL")
        print("=" * 50)
        
        try:
            # Importa TesteSistemaProducao do backup (sequencial puro)
            from producao_paes_backup import TesteSistemaProducao
            
            # ✅ CORREÇÃO: Cria sistema SIMPLES (como no backup - sem parâmetros de otimização)
            print("🔧 Inicializando sistema de produção em modo sequencial...")
            self.sistema_producao = TesteSistemaProducao()  # ✅ SEM PARÂMETROS - PURO SEQUENCIAL
            print("✅ Sistema sequencial inicializado (baseado em producao_paes_backup.py)")
            
            # ✅ CORREÇÃO: Configura logging (como no script original)
            log_filename = self.sistema_producao.configurar_log()
            print(f"📄 Log será salvo em: {log_filename}")
            
            # ✅ CORREÇÃO: Inicializa almoxarifado ANTES de criar pedidos
            print("🏪 Inicializando almoxarifado...")
            self.sistema_producao.inicializar_almoxarifado()
            
            # ✅ CORREÇÃO: Substitui método para usar APENAS pedidos do menu (modo sequencial)
            self._substituir_pedidos_sistema_sequencial(self.sistema_producao, pedidos_menu)
            
            # ✅ EXECUÇÃO SEQUENCIAL PURA: Usa fluxo EXATO do backup
            sucesso = self._executar_sequencial_puro(self.sistema_producao, log_filename)
            
            if sucesso:
                # Mostra estatísticas simples
                total_pedidos = len(self.sistema_producao.pedidos) if hasattr(self.sistema_producao, 'pedidos') else 0
                print(f"\n📊 Execução sequencial finalizada:")
                print(f"   📋 Total de pedidos processados: {total_pedidos}")
                
            return sucesso
            
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("💡 Verifique se producao_paes_backup.py está disponível")
            return False
        except Exception as e:
            print(f"❌ Erro durante execução sequencial: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def executar_otimizado(self, pedidos_menu: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos com otimização PL usando TesteSistemaProducao.
        ✅ CORRIGIDO: Inicializa almoxarifado corretamente.
        """
        print(f"\n🚀 INICIANDO EXECUÇÃO OTIMIZADA")
        print("=" * 50)
        
        # Verifica OR-Tools
        ortools_ok, ortools_msg = self.utils.validar_or_tools()
        if not ortools_ok:
            print(f"❌ {ortools_msg}")
            print("💡 Execute: pip install ortools")
            return False
        
        print(f"✅ {ortools_msg}")
        
        try:
            # Importa TesteSistemaProducao da versão otimizada
            from producao_paes import TesteSistemaProducao  # ✅ USA VERSÃO OTIMIZADA
            
            # ✅ CORREÇÃO 1: Cria sistema em modo otimizado
            print("🔧 Inicializando sistema de produção em modo otimizado...")
            try:
                # Tenta criar com parâmetros de otimização
                self.sistema_producao = TesteSistemaProducao(
                    usar_otimizacao=True,
                    resolucao_minutos=self.configuracoes['resolucao_minutos'],
                    timeout_pl=self.configuracoes['timeout_pl']
                )
                print("✅ Sistema otimizado inicializado (baseado em producao_paes.py)")
            except TypeError:
                # Se versão não suporta parâmetros, cria simples
                print("⚠️ Versão não suporta parâmetros de otimização, usando padrão...")
                self.sistema_producao = TesteSistemaProducao()
                print("✅ Sistema inicializado em modo padrão (fallback)")
            
            # ✅ CORREÇÃO 2: Configura logging
            log_filename = self.sistema_producao.configurar_log()
            print(f"📄 Log será salvo em: {log_filename}")
            print(f"⚙️ Configuração PL: {self.configuracoes['resolucao_minutos']}min, timeout {self.configuracoes['timeout_pl']}s")
            
            # ✅ CORREÇÃO 3: Inicializa almoxarifado ANTES de criar pedidos
            print("🏪 Inicializando almoxarifado...")
            self.sistema_producao.inicializar_almoxarifado()
            
            # ✅ CORREÇÃO 4: Substitui completamente o método de criação para usar APENAS pedidos do menu
            self._substituir_pedidos_sistema_corrigido(self.sistema_producao, pedidos_menu)
            
            print("\n🧮 Iniciando otimização com Programação Linear...")
            print("⏱️ Isso pode levar alguns minutos...")
            
            # Executa sistema completo usando logging duplo (como no script original)
            sucesso = self._executar_com_logging_duplo(self.sistema_producao, log_filename)
            
            if sucesso:
                # Mostra estatísticas
                stats = self.sistema_producao.obter_estatisticas() if hasattr(self.sistema_producao, 'obter_estatisticas') else {}
                self._mostrar_resultado_execucao(stats, "OTIMIZADO")
                
                # Tenta mostrar cronograma (com tratamento de erro)
                try:
                    cronograma = self.sistema_producao.obter_cronograma_otimizado() if hasattr(self.sistema_producao, 'obter_cronograma_otimizado') else {}
                    self._mostrar_cronograma_otimizado(cronograma)
                except Exception as e:
                    print(f"\n⚠️ Erro ao obter cronograma: {e}")
                    print("📊 Execução concluída, mas cronograma não disponível")
                
                return True
            else:
                print("❌ Falha na execução otimizada!")
                return False
            
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("💡 Verifique se producao_paes.py e otimizador estão disponíveis")
            return False
        except Exception as e:
            print(f"❌ Erro durante execução otimizada: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _substituir_pedidos_sistema_sequencial(self, sistema: 'TesteSistemaProducao', pedidos_menu: List[DadosPedidoMenu]):
        """
        ✅ MODO SEQUENCIAL: Substitui método para usar APENAS pedidos do menu.
        Estrutura específica para execução sequencial pura.
        """
        # ✅ CRÍTICO: Verifica se almoxarifado foi inicializado
        if not hasattr(sistema, 'gestor_almoxarifado') or sistema.gestor_almoxarifado is None:
            raise RuntimeError("❌ ERRO CRÍTICO: Sistema não tem gestor_almoxarifado inicializado!")
        
        # ✅ SEQUENCIAL: Verifica se há pedidos do menu
        if not pedidos_menu:
            print("⚠️ MODO SEQUENCIAL: Nenhum pedido registrado no menu!")
            print("💡 Dica: Use a opção '1' para registrar pedidos antes de executar")
            print("📋 Sistema executará com lista vazia de pedidos")
        
        # Converte pedidos do menu para o formato do sistema
        pedidos_convertidos = self._converter_pedidos_menu_para_sistema_corrigido(pedidos_menu, sistema.gestor_almoxarifado)
        
        # Substitui o método criar_pedidos_de_producao para usar APENAS pedidos do menu
        def criar_pedidos_sequencial():
            print(f"📋 SEQUENCIAL: Carregando {len(pedidos_convertidos)} pedido(s) registrado(s) pelo usuário...")
            print("🚫 SEQUENCIAL: Ignorando pedidos hardcoded do script baseline")
            sistema.pedidos = pedidos_convertidos  # ✅ USA APENAS PEDIDOS DO MENU
            print(f"✅ SEQUENCIAL: {len(sistema.pedidos)} pedido(s) carregado(s) do menu!")
            
            # ✅ DEBUG SEQUENCIAL: Verifica se pedidos têm gestor_almoxarifado
            for i, pedido in enumerate(sistema.pedidos):
                has_gestor = hasattr(pedido, 'gestor_almoxarifado') and pedido.gestor_almoxarifado is not None
                print(f"   🔍 Pedido {i+1}: gestor_almoxarifado = {'✅' if has_gestor else '❌'}")
            
            print()
        
        # Substitui o método no sistema
        sistema.criar_pedidos_de_producao = criar_pedidos_sequencial
    
    def _substituir_pedidos_sistema_corrigido(self, sistema: 'TesteSistemaProducao', pedidos_menu: List[DadosPedidoMenu]):
        """
        ✅ VERSÃO CORRIGIDA: Substitui o método criar_pedidos_de_producao do sistema para usar APENAS pedidos do menu.
        Menu funciona de forma completamente independente do script baseline.
        """
        # ✅ CRÍTICO: Verifica se almoxarifado foi inicializado
        if not hasattr(sistema, 'gestor_almoxarifado') or sistema.gestor_almoxarifado is None:
            raise RuntimeError("❌ ERRO CRÍTICO: Sistema não tem gestor_almoxarifado inicializado!")
        
        # ✅ NOVO: Verifica se há pedidos do menu
        if not pedidos_menu:
            print("⚠️ ATENÇÃO: Nenhum pedido registrado no menu!")
            print("💡 Dica: Use a opção '1' para registrar pedidos antes de executar")
            print("📋 Sistema executará com lista vazia de pedidos")
        
        # Converte pedidos do menu para o formato do sistema
        pedidos_convertidos = self._converter_pedidos_menu_para_sistema_corrigido(pedidos_menu, sistema.gestor_almoxarifado)
        
        # Substitui o método criar_pedidos_de_producao para usar APENAS pedidos do menu
        def criar_pedidos_personalizados():
            print(f"📋 MENU: Carregando {len(pedidos_convertidos)} pedido(s) registrado(s) pelo usuário...")
            print("🚫 MENU: Ignorando pedidos hardcoded do script baseline")
            sistema.pedidos = pedidos_convertidos  # ✅ USA APENAS PEDIDOS DO MENU
            print(f"✅ MENU: {len(sistema.pedidos)} pedido(s) carregado(s) do menu!")
            
            # ✅ DEBUG: Verifica se pedidos têm gestor_almoxarifado
            for i, pedido in enumerate(sistema.pedidos):
                has_gestor = hasattr(pedido, 'gestor_almoxarifado') and pedido.gestor_almoxarifado is not None
                print(f"   🔍 Pedido {i+1}: gestor_almoxarifado = {'✅' if has_gestor else '❌'}")
            
            print()
        
        # Substitui o método no sistema
        sistema.criar_pedidos_de_producao = criar_pedidos_personalizados
    
    def _executar_sequencial_puro(self, sistema: 'TesteSistemaProducao', log_filename: str) -> bool:
        """
        ✅ EXECUÇÃO SEQUENCIAL PURA: Usa EXATAMENTE o fluxo do producao_paes_backup.py
        """
        from producao_paes_backup import TeeOutput
        
        # Configura saída dupla (terminal + arquivo) EXATAMENTE como no backup
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            tee = TeeOutput(log_file)
            sys.stdout = tee
            
            try:
                # ✅ FLUXO EXATO DO BACKUP: producao_paes_backup.py
                
                # Escreve cabeçalho (como no backup)
                sistema.escrever_cabecalho_log()
                
                # 1. Configuração do ambiente (já feito na inicialização)
                print("🏪 SEQUENCIAL: Almoxarifado já inicializado")
                
                # 2. Criação dos pedidos (substituído para usar pedidos do menu)
                sistema.criar_pedidos_de_producao()
                print(f"📊 SEQUENCIAL: {len(sistema.pedidos)} pedido(s) carregado(s)")
                
                # 3. Ordenação por prioridade (EXATAMENTE como no backup)
                sistema.ordenar_pedidos_por_prioridade()
                print(f"📊 SEQUENCIAL: {len(sistema.pedidos)} pedido(s) ordenado(s)")
                
                # 4. Execução (EXATAMENTE como no backup)
                sistema.executar_pedidos_ordenados()
                
                # Escreve rodapé de sucesso (como no backup)
                sistema.escrever_rodape_log(True)
                
                return True
                
            except Exception as e:
                print(f"❌ ERRO CRÍTICO NA EXECUÇÃO SEQUENCIAL: {e}")
                import traceback
                traceback.print_exc()
                sistema.escrever_rodape_log(False)
                return False
            
            finally:
                # Restaura stdout original (como no backup)
                sys.stdout = tee.stdout
        
        return True
        """
        ✅ VERSÃO CORRIGIDA: Substitui o método criar_pedidos_de_producao do sistema para usar APENAS pedidos do menu.
        Menu funciona de forma completamente independente do script baseline.
        """
        # ✅ CRÍTICO: Verifica se almoxarifado foi inicializado
        if not hasattr(sistema, 'gestor_almoxarifado') or sistema.gestor_almoxarifado is None:
            raise RuntimeError("❌ ERRO CRÍTICO: Sistema não tem gestor_almoxarifado inicializado!")
        
        # ✅ NOVO: Verifica se há pedidos do menu
        if not pedidos_menu:
            print("⚠️ ATENÇÃO: Nenhum pedido registrado no menu!")
            print("💡 Dica: Use a opção '1' para registrar pedidos antes de executar")
            print("📋 Sistema executará com lista vazia de pedidos")
        
        # Converte pedidos do menu para o formato do sistema
        pedidos_convertidos = self._converter_pedidos_menu_para_sistema_corrigido(pedidos_menu, sistema.gestor_almoxarifado)
        
        # Substitui o método criar_pedidos_de_producao para usar APENAS pedidos do menu
        def criar_pedidos_personalizados():
            print(f"📋 MENU: Carregando {len(pedidos_convertidos)} pedido(s) registrado(s) pelo usuário...")
            print("🚫 MENU: Ignorando pedidos hardcoded do script baseline")
            sistema.pedidos = pedidos_convertidos  # ✅ USA APENAS PEDIDOS DO MENU
            print(f"✅ MENU: {len(sistema.pedidos)} pedido(s) carregado(s) do menu!")
            
            # ✅ DEBUG: Verifica se pedidos têm gestor_almoxarifado
            for i, pedido in enumerate(sistema.pedidos):
                has_gestor = hasattr(pedido, 'gestor_almoxarifado') and pedido.gestor_almoxarifado is not None
                print(f"   🔍 Pedido {i+1}: gestor_almoxarifado = {'✅' if has_gestor else '❌'}")
            
            print()
        
        # Substitui o método no sistema
        sistema.criar_pedidos_de_producao = criar_pedidos_personalizados
        
    def _converter_pedidos_menu_para_sistema_corrigido(self, pedidos_menu: List[DadosPedidoMenu], gestor_almoxarifado) -> List:
        """
        ✅ VERSÃO CORRIGIDA: Converte pedidos do menu para o formato usado pelo TesteSistemaProducao.
        Agora inclui o gestor_almoxarifado na criação de cada pedido.
        """
        from models.atividades.pedido_de_producao import PedidoDeProducao
        from factory.fabrica_funcionarios import funcionarios_disponiveis
        from enums.producao.tipo_item import TipoItem
        
        print(f"🔍 Debug - Convertendo {len(pedidos_menu)} pedido(s) do menu...")
        print(f"🏪 Debug - Gestor almoxarifado disponível: {gestor_almoxarifado is not None}")
        
        # Debug: mostra pedidos de entrada
        for i, pedido in enumerate(pedidos_menu):
            print(f"   📋 Pedido {i+1}: ID={pedido.id_pedido}, Item={pedido.nome_item}, Qtd={pedido.quantidade}")
        
        pedidos_convertidos = []
        
        for pedido_menu in pedidos_menu:
            try:
                print(f"   Convertendo pedido {pedido_menu.id_pedido}: {pedido_menu.nome_item} ({pedido_menu.quantidade} uni)...")
                
                # Converte tipo string para enum
                if pedido_menu.tipo_item == "PRODUTO":
                    tipo_enum = TipoItem.PRODUTO
                else:
                    tipo_enum = TipoItem.SUBPRODUTO
                
                # ✅ CORREÇÃO PRINCIPAL: Inclui gestor_almoxarifado (como no script original)
                pedido_producao = PedidoDeProducao(
                    id_ordem=1,  # Fixo para menu
                    id_pedido=pedido_menu.id_pedido,  # Usa ID único do menu
                    id_produto=pedido_menu.id_item,
                    tipo_item=tipo_enum,
                    quantidade=pedido_menu.quantidade,
                    inicio_jornada=pedido_menu.inicio_jornada,
                    fim_jornada=pedido_menu.fim_jornada,
                    todos_funcionarios=funcionarios_disponiveis,
                    gestor_almoxarifado=gestor_almoxarifado  # ✅ INCLUÍDO!
                )
                
                # ✅ DEBUG: Verifica se gestor foi anexado corretamente
                if hasattr(pedido_producao, 'gestor_almoxarifado') and pedido_producao.gestor_almoxarifado is not None:
                    print(f"   🔍 Debug - Gestor anexado corretamente ao pedido {pedido_menu.id_pedido}")
                else:
                    print(f"   ⚠️ Debug - ERRO: Gestor NÃO anexado ao pedido {pedido_menu.id_pedido}")
                
                # Monta estrutura (como no script original)
                print(f"   🔧 Montando estrutura do pedido {pedido_menu.id_pedido}...")
                pedido_producao.montar_estrutura()
                pedidos_convertidos.append(pedido_producao)
                
                print(f"   ✅ Pedido {pedido_menu.id_pedido} convertido (PedidoProducao.id_pedido={pedido_producao.id_pedido})")
                
            except Exception as e:
                print(f"   ❌ Erro ao converter pedido {pedido_menu.id_pedido}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"🔍 Debug - Total convertido: {len(pedidos_convertidos)} pedido(s)")
        
        # Debug: verifica se há duplicatas
        ids_convertidos = [p.id_pedido for p in pedidos_convertidos]
        if len(set(ids_convertidos)) != len(ids_convertidos):
            print(f"⚠️ ATENÇÃO: Detectadas duplicatas nos IDs convertidos: {ids_convertidos}")
        
        return pedidos_convertidos
    
    def _executar_com_logging_duplo(self, sistema: 'TesteSistemaProducao', log_filename: str) -> bool:
        """
        Executa o sistema com logging duplo (terminal + arquivo) como no script original.
        ✅ CORRIGIDO: Fluxo adaptado para modo otimizado vs sequencial.
        """
        from producao_paes_backup import TeeOutput  # Importa da versão correta
        
        # Configura saída dupla (terminal + arquivo) exatamente como no script original
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            tee = TeeOutput(log_file)
            sys.stdout = tee
            
            try:
                # Escreve cabeçalho (como no script original)
                sistema.escrever_cabecalho_log()
                
                # ✅ CORREÇÃO CRÍTICA: Adapta fluxo baseado no tipo de execução
                if hasattr(sistema, 'usar_otimizacao') and sistema.usar_otimizacao:
                    print("🚀 MODO OTIMIZADO DETECTADO")
                    
                    # Fluxo otimizado: criar_pedidos → executar_otimizado (sem ordenação)
                    sistema.criar_pedidos_de_producao()  # Carrega pedidos do menu
                    print(f"📊 Debug - Pedidos após criação: {len(sistema.pedidos)}")
                    
                    # Pula ordenação no modo otimizado (otimizador define ordem)
                    if hasattr(sistema, 'executar_pedidos_otimizados'):
                        sucesso_exec = sistema.executar_pedidos_otimizados()
                    else:
                        print("⚠️ Método de otimização não disponível, usando execução sequencial")
                        sistema.ordenar_pedidos_por_prioridade()
                        sistema.executar_pedidos_ordenados()
                        sucesso_exec = True
                        
                else:
                    print("📄 MODO SEQUENCIAL DETECTADO")
                    
                    # Fluxo sequencial original: criar_pedidos → ordenar → executar
                    sistema.criar_pedidos_de_producao()  # Carrega pedidos do menu
                    print(f"📊 Debug - Pedidos após criação: {len(sistema.pedidos)}")
                    
                    sistema.ordenar_pedidos_por_prioridade()
                    print(f"📊 Debug - Pedidos após ordenação: {len(sistema.pedidos)}")
                    
                    sistema.executar_pedidos_ordenados()
                    sucesso_exec = True
                
                # Escreve rodapé de sucesso
                sistema.escrever_rodape_log(True)
                
                return True
                
            except Exception as e:
                print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
                import traceback
                traceback.print_exc()
                sistema.escrever_rodape_log(False)
                return False
            
            finally:
                # Restaura stdout original (como no script original)
                sys.stdout = tee.stdout
        
        return True
    
    def _mostrar_resultado_execucao(self, stats: Dict, modo: str):
        """Mostra resultado da execução"""
        print(f"\n📊 RESULTADO DA EXECUÇÃO {modo}")
        print("=" * 50)
        
        if stats:
            total = stats.get('total_pedidos', 0)
            executados = stats.get('pedidos_executados', 0)
            
            print(f"📋 Total de pedidos: {total}")
            print(f"✅ Pedidos executados: {executados}")
            
            if total > 0:
                taxa = (executados / total) * 100
                print(f"📈 Taxa de sucesso: {taxa:.1f}%")
            
            if modo == "OTIMIZADO" and 'otimizacao' in stats:
                opt_stats = stats['otimizacao']
                print(f"⏱️ Tempo otimização: {opt_stats.get('tempo_total_otimizacao', 0):.2f}s")
                print(f"🎯 Status solver: {opt_stats.get('status_solver', 'N/A')}")
                if 'janelas_totais_geradas' in opt_stats:
                    print(f"🔧 Janelas geradas: {opt_stats.get('janelas_totais_geradas', 0):,}")
                if 'variaveis_pl' in opt_stats:
                    print(f"📊 Variáveis PL: {opt_stats.get('variaveis_pl', 0):,}")
        else:
            print("❌ Estatísticas não disponíveis")
    
    def _mostrar_cronograma_otimizado(self, cronograma: Dict):
        """Mostra cronograma otimizado"""
        if not cronograma:
            print("\n📅 CRONOGRAMA OTIMIZADO")
            print("=" * 50)
            print("⚠️ Cronograma não disponível ou vazio")
            return
        
        print(f"\n📅 CRONOGRAMA OTIMIZADO")
        print("=" * 50)
        
        try:
            # Debug: mostra estrutura do cronograma
            print(f"🔍 Debug - Estrutura do cronograma: {list(cronograma.keys())[:3]}...")
            
            # Verifica formato do cronograma
            if not cronograma:
                print("⚠️ Cronograma vazio")
                return
            
            # Pega primeiro item para verificar estrutura
            primeiro_item = next(iter(cronograma.values()))
            print(f"🔍 Debug - Chaves disponíveis: {list(primeiro_item.keys())}")
            
            # Ordena por horário de início (adapta para diferentes formatos)
            itens_ordenados = []
            for pedido_id, dados in cronograma.items():
                # Tenta diferentes chaves possíveis
                inicio = None
                fim = None
                duracao = None
                
                # Possíveis chaves para início
                for chave_inicio in ['inicio', 'inicio_execucao', 'data_inicio', 'timestamp_inicio']:
                    if chave_inicio in dados:
                        if isinstance(dados[chave_inicio], str):
                            inicio = datetime.fromisoformat(dados[chave_inicio])
                        elif isinstance(dados[chave_inicio], datetime):
                            inicio = dados[chave_inicio]
                        break
                
                # Possíveis chaves para fim
                for chave_fim in ['fim', 'fim_execucao', 'data_fim', 'timestamp_fim']:
                    if chave_fim in dados:
                        if isinstance(dados[chave_fim], str):
                            fim = datetime.fromisoformat(dados[chave_fim])
                        elif isinstance(dados[chave_fim], datetime):
                            fim = dados[chave_fim]
                        break
                
                # Possíveis chaves para duração
                for chave_duracao in ['duracao_horas', 'duracao', 'tempo_execucao']:
                    if chave_duracao in dados:
                        duracao = dados[chave_duracao]
                        break
                
                if inicio:
                    itens_ordenados.append((inicio, pedido_id, dados, fim, duracao))
                else:
                    # Se não encontrou início, ainda adiciona mas sem ordenar
                    itens_ordenados.append((datetime.now(), pedido_id, dados, fim, duracao))
            
            # Ordena por horário de início
            itens_ordenados.sort(key=lambda x: x[0])
            
            # Exibe cronograma
            for inicio, pedido_id, dados, fim, duracao in itens_ordenados:
                inicio_str = inicio.strftime('%d/%m %H:%M') if inicio else "N/A"
                fim_str = fim.strftime('%d/%m %H:%M') if fim else "N/A"
                duracao_str = f"({duracao:.1f}h)" if duracao is not None else ""
                
                print(f"🎯 Pedido {pedido_id}: {inicio_str} → {fim_str} {duracao_str}")
                
                # Mostra dados extras se disponíveis
                extras = []
                if 'status' in dados:
                    extras.append(f"Status: {dados['status']}")
                if 'equipamento' in dados:
                    extras.append(f"Equip: {dados['equipamento']}")
                if extras:
                    print(f"   📋 {' | '.join(extras)}")
            
        except Exception as e:
            print(f"❌ Erro ao exibir cronograma: {e}")
            print(f"🔍 Cronograma bruto: {cronograma}")
            # Fallback: mostra dados básicos
            for pedido_id, dados in cronograma.items():
                print(f"🎯 Pedido {pedido_id}: {dados}")
                break  # Mostra só o primeiro para não poluir
    
    def configurar(self, **kwargs):
        """Configura parâmetros do executor"""
        for chave, valor in kwargs.items():
            if chave in self.configuracoes:
                self.configuracoes[chave] = valor
                print(f"⚙️ {chave} configurado para: {valor}")
    
    def obter_configuracoes(self) -> Dict:
        """Retorna configurações atuais"""
        ortools_ok, _ = self.utils.validar_or_tools()
        
        config = self.configuracoes.copy()
        config['ortools_disponivel'] = ortools_ok
        
        return config
    
    def testar_sistema(self) -> Dict:
        """
        Testa componentes do sistema.
        
        Returns:
            Dict com resultados dos testes
        """
        print("🧪 TESTANDO COMPONENTES DO SISTEMA")
        print("=" * 40)
        
        resultados = {}
        
        # Teste 1: OR-Tools
        print("1️⃣ Testando OR-Tools...")
        ortools_ok, ortools_msg = self.utils.validar_or_tools()
        resultados['ortools'] = {'ok': ortools_ok, 'msg': ortools_msg}
        print(f"   {'✅' if ortools_ok else '❌'} {ortools_msg}")
        
        # Teste 2: TesteSistemaProducao
        print("2️⃣ Testando TesteSistemaProducao...")
        try:
            from producao_paes_backup import TesteSistemaProducao
            resultados['teste_sistema_producao'] = {'ok': True, 'msg': 'TesteSistemaProducao importado'}
            print(f"   ✅ TesteSistemaProducao disponível")
        except ImportError as e:
            resultados['teste_sistema_producao'] = {'ok': False, 'msg': str(e)}
            print(f"   ❌ TesteSistemaProducao não encontrado: {e}")
        
        # Teste 3: Importações do sistema
        print("3️⃣ Testando importações do sistema...")
        importacoes = [
            ('models.atividades.pedido_de_producao', 'PedidoDeProducao'),
            ('enums.producao.tipo_item', 'TipoItem'),
            ('factory.fabrica_funcionarios', 'funcionarios_disponiveis')
        ]
        
        for modulo, classe in importacoes:
            try:
                exec(f"from {modulo} import {classe}")
                resultados[f'import_{classe}'] = {'ok': True, 'msg': 'OK'}
                print(f"   ✅ {modulo}.{classe}")
            except ImportError as e:
                resultados[f'import_{classe}'] = {'ok': False, 'msg': str(e)}
                print(f"   ❌ {modulo}.{classe}: {e}")
        
        # Teste 4: Contagem de arquivos
        print("4️⃣ Testando gerenciador de pedidos...")
        try:
            gerenciador = GerenciadorPedidos()
            
            produtos = gerenciador.listar_itens_disponiveis("PRODUTO")
            subprodutos = gerenciador.listar_itens_disponiveis("SUBPRODUTO")
            
            resultados['arquivos'] = {
                'produtos': len(produtos),
                'subprodutos': len(subprodutos)
            }
            
            print(f"   📦 Produtos: {len(produtos)} arquivos")
            print(f"   🔧 Subprodutos: {len(subprodutos)} arquivos")
        except Exception as e:
            resultados['arquivos'] = {'ok': False, 'msg': str(e)}
            print(f"   ❌ Erro ao testar gerenciador: {e}")
        
        # Resumo
        testes_ok = sum(1 for r in resultados.values() if isinstance(r, dict) and r.get('ok', False))
        total_testes = sum(1 for r in resultados.values() if isinstance(r, dict) and 'ok' in r)
        
        print(f"\n📊 Resultado: {testes_ok}/{total_testes} testes passaram")
        
        return resultados
    
    def limpar_logs_anteriores(self):
        """
        Limpa logs de execuções anteriores manualmente.
        ✅ ATUALIZADO: Método mantido para limpeza manual via menu.
        """
        try:
            from utils.logs.gerenciador_logs import limpar_todos_os_logs
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            
            print("🧹 Limpando logs anteriores manualmente...")
            limpar_todos_os_logs()
            apagar_todas_as_comandas()
            print("✅ Logs e comandas limpos manualmente")
            
        except ImportError:
            print("⚠️ Módulos de limpeza não disponíveis")
        except Exception as e:
            print(f"❌ Erro ao limpar logs: {e}")
    
    def limpar_pedidos_completo(self):
        """
        ✅ NOVO: Método adicional para limpeza completa de pedidos.
        Remove arquivo de pedidos salvos e limpa pedidos em memória.
        """
        try:
            print("🗑️ LIMPEZA COMPLETA DE PEDIDOS")
            print("=" * 40)
            
            # Remove arquivo de pedidos salvos
            arquivo_pedidos = "menu/pedidos_salvos.json"
            if os.path.exists(arquivo_pedidos):
                try:
                    import json
                    with open(arquivo_pedidos, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    total_pedidos = len(dados.get('pedidos', []))
                    print(f"📋 Removendo {total_pedidos} pedido(s) salvos...")
                    
                except (json.JSONDecodeError, KeyError):
                    print("📋 Removendo arquivo de pedidos (corrompido)...")
                
                os.remove(arquivo_pedidos)
                print(f"✅ Arquivo {arquivo_pedidos} removido")
            else:
                print("📭 Nenhum arquivo de pedidos salvos encontrado")
            
            # Remove outros arquivos relacionados se existirem
            arquivos_relacionados = [
                "menu/backup_pedidos.json",
                "menu/temp_pedidos.json",
                "pedidos.json",
                "pedidos_backup.json"
            ]
            
            for arquivo in arquivos_relacionados:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    print(f"✅ Arquivo {arquivo} removido")
            
            print("\n🎉 Limpeza completa de pedidos finalizada!")
            
        except Exception as e:
            print(f"❌ Erro durante limpeza completa de pedidos: {e}")
            import traceback
            traceback.print_exc()
    
    def limpar_logs_completo(self):
        """
        ✅ NOVO: Método adicional para limpeza completa e detalhada.
        Remove todos os arquivos de log e comandas com feedback detalhado.
        """
        try:
            import shutil
            from pathlib import Path
            
            print("🧹 LIMPEZA COMPLETA DE LOGS")
            print("=" * 40)
            
            # Lista diretórios a limpar
            diretorios_logs = ['logs', 'comandas', 'temp']
            
            for diretorio in diretorios_logs:
                if os.path.exists(diretorio):
                    arquivos = os.listdir(diretorio)
                    if arquivos:
                        print(f"📁 Limpando {diretorio}/: {len(arquivos)} arquivo(s)")
                        for arquivo in arquivos:
                            caminho_arquivo = os.path.join(diretorio, arquivo)
                            try:
                                if os.path.isfile(caminho_arquivo):
                                    os.remove(caminho_arquivo)
                                elif os.path.isdir(caminho_arquivo):
                                    shutil.rmtree(caminho_arquivo)
                            except Exception as e:
                                print(f"   ⚠️ Erro ao remover {arquivo}: {e}")
                        print(f"   ✅ {diretorio}/ limpo")
                    else:
                        print(f"📁 {diretorio}/ já está vazio")
                else:
                    print(f"📁 {diretorio}/ não existe")
            
            # Chama também os métodos específicos do sistema
            try:
                from utils.logs.gerenciador_logs import limpar_todos_os_logs
                from utils.comandas.limpador_comandas import apagar_todas_as_comandas
                
                limpar_todos_os_logs()
                apagar_todas_as_comandas()
                print("✅ Limpeza específica do sistema executada")
                
            except ImportError:
                print("⚠️ Módulos específicos de limpeza não disponíveis")
            
            print("\n🎉 Limpeza completa finalizada!")
            
        except Exception as e:
            print(f"❌ Erro durante limpeza completa: {e}")
            import traceback
            traceback.print_exc()

    def obter_sistema_producao(self):
        """Retorna a instância atual do sistema de produção"""
        return self.sistema_producao