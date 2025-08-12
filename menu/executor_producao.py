"""
Executor de Produção
===================

Módulo responsável por executar pedidos usando TesteSistemaProducao diretamente.
Adaptado para usar exatamente o mesmo fluxo dos scripts originais.
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
        
    def executar_sequencial(self, pedidos_menu: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos em modo sequencial usando TesteSistemaProducao.
        
        Args:
            pedidos_menu: Lista de pedidos do menu
            
        Returns:
            bool: True se execução foi bem-sucedida
        """
        print(f"\n🔄 INICIANDO EXECUÇÃO SEQUENCIAL")
        print("=" * 50)
        
        try:
            # Importa TesteSistemaProducao
            from producao_paes import TesteSistemaProducao
            
            # Cria sistema em modo sequencial
            print("🔧 Inicializando sistema de produção em modo sequencial...")
            self.sistema_producao = TesteSistemaProducao(usar_otimizacao=False)
            
            # Configura logging
            log_filename = self.sistema_producao.configurar_log()
            print(f"📄 Log será salvo em: {log_filename}")
            
            # Substitui o método criar_pedidos_de_producao para usar pedidos do menu
            self._substituir_pedidos_sistema(self.sistema_producao, pedidos_menu)
            
            # Executa sistema completo usando logging duplo (como no script original)
            sucesso = self._executar_com_logging_duplo(self.sistema_producao, log_filename)
            
            if sucesso:
                # Mostra estatísticas
                stats = self.sistema_producao.obter_estatisticas()
                self._mostrar_resultado_execucao(stats, "SEQUENCIAL")
                
            return sucesso
            
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("💡 Verifique se producao_paes.py está disponível")
            return False
        except Exception as e:
            print(f"❌ Erro durante execução sequencial: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def executar_otimizado(self, pedidos_menu: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos com otimização PL usando TesteSistemaProducao.
        
        Args:
            pedidos_menu: Lista de pedidos do menu
            
        Returns:
            bool: True se execução foi bem-sucedida
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
            # Importa TesteSistemaProducao
            from producao_paes import TesteSistemaProducao
            
            # Cria sistema em modo otimizado
            print("🔧 Inicializando sistema de produção em modo otimizado...")
            self.sistema_producao = TesteSistemaProducao(
                usar_otimizacao=True,
                resolucao_minutos=self.configuracoes['resolucao_minutos'],
                timeout_pl=self.configuracoes['timeout_pl']
            )
            
            # Configura logging
            log_filename = self.sistema_producao.configurar_log()
            print(f"📄 Log será salvo em: {log_filename}")
            print(f"⚙️ Configuração PL: {self.configuracoes['resolucao_minutos']}min, timeout {self.configuracoes['timeout_pl']}s")
            
            # Substitui o método criar_pedidos_de_producao para usar pedidos do menu
            self._substituir_pedidos_sistema(self.sistema_producao, pedidos_menu)
            
            print("\n🧮 Iniciando otimização com Programação Linear...")
            print("⏱️ Isso pode levar alguns minutos...")
            
            # Executa sistema completo usando logging duplo (como no script original)
            sucesso = self._executar_com_logging_duplo(self.sistema_producao, log_filename)
            
            if sucesso:
                # Mostra estatísticas
                stats = self.sistema_producao.obter_estatisticas()
                self._mostrar_resultado_execucao(stats, "OTIMIZADO")
                
                # Tenta mostrar cronograma (com tratamento de erro)
                try:
                    cronograma = self.sistema_producao.obter_cronograma_otimizado()
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
            print(f"🔍 Erro completo: {type(e).__name__}: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Erro durante execução otimizada: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            print(f"🔍 Sistema de produção criado: {'Sim' if self.sistema_producao else 'Não'}")
            import traceback
            traceback.print_exc()
            return False
    
    def _substituir_pedidos_sistema(self, sistema: 'TesteSistemaProducao', pedidos_menu: List[DadosPedidoMenu]):
        """
        Substitui o método criar_pedidos_de_producao do sistema para usar pedidos do menu.
        """
        # Converte pedidos do menu para o formato do sistema
        pedidos_convertidos = self._converter_pedidos_menu_para_sistema(pedidos_menu)
        
        # Substitui o método criar_pedidos_de_producao
        def criar_pedidos_personalizados():
            print(f"🔄 Carregando {len(pedidos_convertidos)} pedido(s) do menu...")
            sistema.pedidos = pedidos_convertidos
            print(f"✅ {len(sistema.pedidos)} pedido(s) carregado(s) do menu!")
            print()
        
        # Substitui o método no sistema
        sistema.criar_pedidos_de_producao = criar_pedidos_personalizados
        
    def _converter_pedidos_menu_para_sistema(self, pedidos_menu: List[DadosPedidoMenu]) -> List:
        """
        Converte pedidos do menu para o formato usado pelo TesteSistemaProducao.
        """
        from models.atividades.pedido_de_producao import PedidoDeProducao
        from factory.fabrica_funcionarios import funcionarios_disponiveis
        from enums.producao.tipo_item import TipoItem
        
        print(f"🔍 Debug - Convertendo {len(pedidos_menu)} pedido(s) do menu...")
        
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
                
                # Cria PedidoDeProducao usando os mesmos parâmetros do script original
                pedido_producao = PedidoDeProducao(
                    id_ordem=1,  # Fixo para menu
                    id_pedido=pedido_menu.id_pedido,  # Usa ID único do menu
                    id_produto=pedido_menu.id_item,
                    tipo_item=tipo_enum,
                    quantidade=pedido_menu.quantidade,
                    inicio_jornada=pedido_menu.inicio_jornada,
                    fim_jornada=pedido_menu.fim_jornada,
                    todos_funcionarios=funcionarios_disponiveis
                )
                
                # Monta estrutura (como no script original)
                pedido_producao.montar_estrutura()
                pedidos_convertidos.append(pedido_producao)
                
                print(f"   ✅ Pedido {pedido_menu.id_pedido} convertido (PedidoProducao.id_pedido={pedido_producao.id_pedido})")
                
            except Exception as e:
                print(f"   ❌ Erro ao converter pedido {pedido_menu.id_pedido}: {e}")
        
        print(f"🔍 Debug - Total convertido: {len(pedidos_convertidos)} pedido(s)")
        
        # Debug: verifica se há duplicatas
        ids_convertidos = [p.id_pedido for p in pedidos_convertidos]
        if len(set(ids_convertidos)) != len(ids_convertidos):
            print(f"⚠️ ATENÇÃO: Detectadas duplicatas nos IDs convertidos: {ids_convertidos}")
        
        return pedidos_convertidos
    
    def _executar_com_logging_duplo(self, sistema: 'TesteSistemaProducao', log_filename: str) -> bool:
        """
        Executa o sistema com logging duplo (terminal + arquivo) como no script original.
        """
        from producao_paes import TeeOutput
        
        # Configura saída dupla (terminal + arquivo) exatamente como no script original
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            tee = TeeOutput(log_file)
            sys.stdout = tee
            
            try:
                # Escreve cabeçalho (como no script original)
                sistema.escrever_cabecalho_log()
                
                # Executa teste completo (exatamente como no script original)
                sucesso = sistema.executar_teste_completo()
                
                # Escreve rodapé (como no script original)
                sistema.escrever_rodape_log(sucesso)
                
                return sucesso
                
            except Exception as e:
                sistema.escrever_rodape_log(False)
                raise
            
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
            from producao_paes import TesteSistemaProducao
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
        """Limpa logs de execuções anteriores"""
        try:
            from utils.logs.gerenciador_logs import limpar_todos_os_logs
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            
            print("🧹 Limpando logs anteriores...")
            limpar_todos_os_logs()
            apagar_todas_as_comandas()
            print("✅ Logs e comandas limpos")
            
        except ImportError:
            print("⚠️ Módulos de limpeza não disponíveis")
        except Exception as e:
            print(f"❌ Erro ao limpar logs: {e}")

    def obter_sistema_producao(self):
        """Retorna a instância atual do sistema de produção"""
        return self.sistema_producao