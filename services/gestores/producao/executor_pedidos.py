"""
Executor de Pedidos - CORRIGIDO
===============================

Executa pedidos de produção REAL gerando comandas e logs de equipamentos.
✅ CORREÇÃO: Agora gera comandas antes da execução!
"""

from typing import List, Dict, Optional
from datetime import datetime


class ExecutorPedidos:
    """
    Executor de pedidos de produção REAL.
    
    Responsabilidades:
    - Execução sequencial de pedidos
    - Execução otimizada com PL  
    - Coleta de estatísticas
    - 🎯 GERAÇÃO DE COMANDAS (CORRIGIDO!)
    - 🎯 GERAÇÃO DE LOGS DE EQUIPAMENTOS
    """
    
    def __init__(self, configuracoes: Optional[Dict] = None):
        """
        Inicializa executor.
        
        Args:
            configuracoes: Configurações do executor
        """
        self.configuracoes = configuracoes or {}
        self.estatisticas_execucao = {}
        print("⚡ ExecutorPedidos criado")
    
    def executar_sequencial(self, pedidos_convertidos: List) -> bool:
        """
        Executa pedidos em modo sequencial REAL.
        
        🎯 AQUI QUE AS COMANDAS E LOGS DE EQUIPAMENTOS SÃO GERADOS!
        
        Args:
            pedidos_convertidos: Lista de PedidoDeProducao convertidos
            
        Returns:
            bool: True se sucesso
        """
        try:
            print(f"🔄 Executando {len(pedidos_convertidos)} pedidos sequencialmente...")
            print("🎯 MODO REAL: Comandas e logs de equipamentos serão gerados automaticamente!")
            
            # ✅ CORREÇÃO: Importa geração de comandas
            try:
                from services.gestores.comandas.gestor_comandas import gerar_comanda_reserva
                print("   📋 Módulo de comandas carregado")
            except ImportError as e:
                print(f"   ❌ Erro ao importar geração de comandas: {e}")
                print("   ⚠️ Continuando sem geração de comandas...")
                gerar_comanda_reserva = None
            
            inicio_execucao = datetime.now()
            pedidos_executados = 0
            pedidos_com_erro = 0
            comandas_geradas = 0
            
            for idx, pedido in enumerate(pedidos_convertidos, 1):
                print(f"\n📋 Executando pedido {idx}/{len(pedidos_convertidos)}: {pedido.id_pedido}")
                print(f"   📦 Item: {pedido.id_produto} (Quantidade: {pedido.quantidade})")
                print(f"   ⏰ Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                
                
                try:
                    # ✅ CORREÇÃO: PASSO 1 - Gerar comanda ANTES da execução
                    if gerar_comanda_reserva:
                        print(f"   📋 Gerando comanda para pedido {pedido.id_pedido}...")
                        
                        # Verifica se o pedido tem gestor_almoxarifado
                        if not hasattr(pedido, 'gestor_almoxarifado') or not pedido.gestor_almoxarifado:
                            print(f"   ⚠️ AVISO: Pedido {pedido.id_pedido} sem gestor_almoxarifado!")
                            print(f"   💡 Tentando usar ficha técnica mesmo assim...")
                        
                        try:
                            gerar_comanda_reserva(
                                id_ordem=pedido.id_ordem,
                                id_pedido=pedido.id_pedido,
                                ficha=pedido.ficha_tecnica_modular,
                                gestor=pedido.gestor_almoxarifado,
                                data_execucao=pedido.fim_jornada
                            )
                            print(f"   ✅ Comanda gerada: data/comandas/comanda_ordem_{pedido.id_ordem}_pedido_{pedido.id_pedido}.json")
                            comandas_geradas += 1
                        except Exception as e_comanda:
                            print(f"   ⚠️ Erro ao gerar comanda: {e_comanda}")
                            print(f"   💡 Continuando com execução mesmo sem comanda...")
                    else:
                        print(f"   ⚠️ Geração de comandas não disponível")
                    
                    # ✅ PASSO 2: Criar atividades modulares
                    print(f"   🏗️ Criando atividades modulares...")
                    pedido.criar_atividades_modulares_necessarias()
                    print(f"   ✅ {len(pedido.atividades_modulares)} atividades criadas")
                    
                    # ✅ PASSO 3: Executar atividades (AQUI OS LOGS SÃO GERADOS!)
                    print(f"   ⚡ Executando atividades em ordem...")
                    print(f"   📝 LOG SENDO GERADO: logs/equipamentos/ordem: {pedido.id_ordem} | pedido: {pedido.id_pedido}.log")
                    
                    pedido.executar_atividades_em_ordem()
                    
                    print(f"   ✅ Pedido {pedido.id_pedido} executado com sucesso!")
                    print(f"   📝 Log salvo em: logs/equipamentos/ordem: {pedido.id_ordem} | pedido: {pedido.id_pedido}.log")
                    pedidos_executados += 1
                    
                except RuntimeError as e:
                    print(f"   ❌ Falha no pedido {pedido.id_pedido}: {e}")
                    pedidos_com_erro += 1
                    
                    # Log do erro (mas continua execução)
                    erro_resumido = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                    print(f"   📝 Erro resumido: {erro_resumido}")
                    continue
                    
                except Exception as e:
                    print(f"   ❌ Erro inesperado no pedido {pedido.id_pedido}: {e}")
                    pedidos_com_erro += 1
                    continue
            
            # ✅ ESTATÍSTICAS FINAIS
            fim_execucao = datetime.now()
            tempo_total = (fim_execucao - inicio_execucao).total_seconds()
            
            self.estatisticas_execucao = {
                'modo': 'sequencial',
                'total_pedidos': len(pedidos_convertidos),
                'pedidos_executados': pedidos_executados,
                'pedidos_com_erro': pedidos_com_erro,
                'comandas_geradas': comandas_geradas,  # ✅ NOVA MÉTRICA
                'tempo_execucao': tempo_total,
                'inicio_execucao': inicio_execucao.isoformat(),
                'fim_execucao': fim_execucao.isoformat()
            }
            
            # 📊 RELATÓRIO FINAL
            print(f"\n📊 RELATÓRIO DE EXECUÇÃO SEQUENCIAL:")
            print(f"   ✅ Executados: {pedidos_executados}/{len(pedidos_convertidos)}")
            print(f"   ❌ Com erro: {pedidos_com_erro}")
            print(f"   📋 Comandas geradas: {comandas_geradas}")  # ✅ NOVA INFORMAÇÃO
            print(f"   ⏱️ Tempo total: {tempo_total:.1f}s")
            print(f"   📝 Logs gerados em: logs/equipamentos/")
            print(f"   📋 Comandas salvas em: data/comandas/")  # ✅ NOVA INFORMAÇÃO
            
            # ✅ LISTAR ARQUIVOS GERADOS
            self._listar_arquivos_gerados()
            
            sucesso_geral = pedidos_executados > 0
            if sucesso_geral:
                print("🎉 Execução sequencial concluída com sucesso!")
            else:
                print("❌ Nenhum pedido foi executado com sucesso!")
            
            return sucesso_geral
            
        except Exception as e:
            print(f"❌ Erro crítico durante execução: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def executar_otimizado(self, pedidos_convertidos: List) -> bool:
        """
        Executa pedidos com otimização PL v3.0 usando OR-Tools CP-SAT.

        Utiliza o ExecutorUnificadoPL do otimizador para:
        - Detectar modo (DETERMINISTICO/FLEXIVEL)
        - Calcular horários via backward scheduling
        - Otimizar ordem de execução
        - Executar pedidos na ordem otimizada

        Args:
            pedidos_convertidos: Lista de PedidoDeProducao convertidos

        Returns:
            bool: True se sucesso
        """
        try:
            print(f"🚀 Executando {len(pedidos_convertidos)} pedidos com OTIMIZAÇÃO PL v3.0...")

            # Verifica disponibilidade do OR-Tools
            try:
                from ortools.sat.python import cp_model
                print("   ✅ OR-Tools CP-SAT disponível")
            except ImportError:
                print("   ❌ OR-Tools não encontrado!")
                print("   💡 Instale com: pip install ortools")
                return False

            # Importa otimizador v3
            try:
                from otimizador import ExecutorUnificadoPL
                print("   ✅ Módulos de otimização v3.0 carregados")
            except ImportError as e:
                print(f"   ❌ Erro ao importar otimizador: {e}")
                return False

            inicio_execucao = datetime.now()

            # Cria executor unificado
            print(f"\n🔧 Inicializando ExecutorUnificadoPL v3.0...")
            executor = ExecutorUnificadoPL()

            # Define início da jornada
            inicio_jornada = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)

            # Executa otimização e execução
            print(f"\n🎯 Iniciando otimização com OR-Tools CP-SAT...")
            print(f"   📊 {len(pedidos_convertidos)} pedidos a otimizar")
            print(f"   🔍 Modelo: Ordenação por deadline + CP-SAT")
            print(f"   🧮 Solver: OR-Tools CP-SAT\n")

            resultado = executor.otimizar_e_executar(pedidos_convertidos, inicio_jornada)

            fim_execucao = datetime.now()
            tempo_total = (fim_execucao - inicio_execucao).total_seconds()

            # Verifica resultado
            if resultado.get('status') == 'CONCLUIDO':
                stats = resultado.get('estatisticas_gerais', {})
                exec_result = resultado.get('execucao', {})

                self.estatisticas_execucao = {
                    'modo': 'otimizado_pl_v2',
                    'total_pedidos': len(pedidos_convertidos),
                    'pedidos_executados': exec_result.get('pedidos_executados', []),
                    'pedidos_falhados': exec_result.get('pedidos_com_erro', []),
                    'tempo_execucao': tempo_total,
                    'tempo_otimizacao': stats.get('tempo_otimizacao', 0),
                    'status_solver': resultado.get('otimizacao', {}).get('status', 'N/A'),
                    'taxa_atendimento': stats.get('taxa_sucesso', 0) / 100
                }

                print(f"\n🎉 Otimização PL v2.0 concluída!")
                print(f"   📊 Modo: {resultado.get('modo', 'N/A')}")
                print(f"   🎯 Método: {resultado.get('otimizacao', {}).get('metodo', 'N/A')}")
                print(f"   ✅ Pedidos executados: {stats.get('pedidos_sucesso', 0)}/{len(pedidos_convertidos)}")
                print(f"   ❌ Pedidos com erro: {stats.get('pedidos_erro', 0)}")
                print(f"   📈 Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1f}%")
                print(f"   ⏱️ Tempo total: {tempo_total:.2f}s")
                print(f"   ⚡ Tempo otimização: {stats.get('tempo_otimizacao', 0):.3f}s")

                # Lista arquivos gerados
                self._listar_arquivos_gerados()

                return stats.get('pedidos_sucesso', 0) > 0
            else:
                print(f"❌ Otimização PL v2.0 falhou: {resultado.get('status', 'ERRO')}")
                if 'erro' in resultado:
                    print(f"   Erro: {resultado['erro']}")
                return False

        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            import traceback
            traceback.print_exc()
            return False

        except Exception as e:
            print(f"❌ Erro durante execução otimizada: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _listar_arquivos_gerados(self):
        """✅ CORRIGIDO: Lista tanto logs quanto comandas geradas"""
        try:
            import os
            
            # ✅ LISTAR LOGS DE EQUIPAMENTOS
            pasta_logs = "logs/equipamentos"
            if os.path.exists(pasta_logs):
                arquivos_log = [f for f in os.listdir(pasta_logs) if f.endswith(".log")]
                
                if arquivos_log:
                    print(f"\n📝 LOGS DE EQUIPAMENTOS GERADOS ({len(arquivos_log)} arquivo(s)):")
                    for arquivo in sorted(arquivos_log):
                        caminho = os.path.join(pasta_logs, arquivo)
                        try:
                            with open(caminho, 'r', encoding='utf-8') as f:
                                linhas = f.readlines()
                            print(f"   📄 {arquivo} ({len(linhas)} linhas)")
                        except Exception:
                            print(f"   📄 {arquivo} (erro ao ler)")
                else:
                    print(f"   📝 Nenhum log encontrado em {pasta_logs}")
            else:
                print(f"   📝 Pasta de logs não encontrada: {pasta_logs}")
            
            # ✅ LISTAR COMANDAS GERADAS
            pasta_comandas = "data/comandas"
            if os.path.exists(pasta_comandas):
                arquivos_comanda = [f for f in os.listdir(pasta_comandas) if f.endswith(".json")]
                
                if arquivos_comanda:
                    print(f"\n📋 COMANDAS GERADAS ({len(arquivos_comanda)} arquivo(s)):")
                    for arquivo in sorted(arquivos_comanda):
                        caminho = os.path.join(pasta_comandas, arquivo)
                        try:
                            # Verifica se é uma comanda recente (baseado no nome)
                            if "ordem_" in arquivo and "pedido_" in arquivo:
                                print(f"   📄 {arquivo}")
                        except Exception:
                            print(f"   📄 {arquivo} (erro ao verificar)")
                else:
                    print(f"   📋 Nenhuma comanda encontrada em {pasta_comandas}")
            else:
                print(f"   📋 Pasta de comandas não encontrada: {pasta_comandas}")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao listar arquivos: {e}")
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas da última execução.
        
        Returns:
            Dict: Estatísticas
        """
        return self.estatisticas_execucao.copy()
    
    
    def limpar_estatisticas(self) -> None:
        """Limpa estatísticas acumuladas"""
        self.estatisticas_execucao.clear()
        print("🧹 Estatísticas do executor limpas")
    
    def verificar_logs_existentes(self) -> Dict:
        """
        Verifica logs existentes no sistema.
        
        Returns:
            Dict: Informações sobre logs
        """
        try:
            import os
            
            pastas_log = [
                "logs/equipamentos",
                "logs/funcionarios", 
                "logs/equipamentos/erros"
            ]
            
            resultado = {}
            
            for pasta in pastas_log:
                if os.path.exists(pasta):
                    arquivos = [f for f in os.listdir(pasta) if f.endswith(('.log', '.json'))]
                    resultado[pasta] = {
                        'existe': True,
                        'total_arquivos': len(arquivos),
                        'arquivos': arquivos[:5]  # Primeiros 5
                    }
                else:
                    resultado[pasta] = {'existe': False, 'total_arquivos': 0, 'arquivos': []}
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}