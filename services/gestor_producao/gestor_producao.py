"""
Gestor de Produção Principal - CORRIGIDO
========================================

Classe principal que coordena a execução de pedidos de produção.
✅ CORREÇÃO: Passa gestor_almoxarifado corretamente para o conversor.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Imports do menu (mantém compatibilidade)
from menu.gerenciador_pedidos import DadosPedidoMenu


class GestorProducao:
    """
    Gestor principal de produção independente.
    
    Responsabilidades:
    - Coordenar execução sequencial e otimizada
    - Gerenciar configurações do sistema
    - Fornecer interface limpa para o menu
    """
    
    def __init__(self, configuracoes: Optional[Dict] = None):
        """
        Inicializa o gestor de produção.
        
        Args:
            configuracoes: Dict com configurações opcionais
        """
        # Configurações padrão
        self.configuracoes = {
            'resolucao_minutos': 30,
            'timeout_pl': 300,
            'limpar_logs_automatico': True,
            'limpar_pedidos_automatico': True,
            'usar_otimizacao_default': False
        }
        
        # Aplica configurações customizadas
        if configuracoes:
            self.configuracoes.update(configuracoes)
        
        # ✅ CORREÇÃO: Inicializa componentes como None primeiro
        self.configurador_ambiente = None
        self.conversor_pedidos = None
        self.executor_pedidos = None
        self.sistema_inicializado = False
        
        # Estatísticas da última execução
        self.ultima_execucao = {
            'sucesso': False,
            'modo': None,
            'total_pedidos': 0,
            'pedidos_executados': 0,
            'tempo_execucao': 0,
            'log_filename': None
        }
        
        print("🏭 GestorProducao inicializado")
        print(f"   📊 Configurações: {self.configuracoes}")
    
    def executar_sequencial(self, pedidos: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos em modo sequencial.
        
        Args:
            pedidos: Lista de pedidos do menu
            
        Returns:
            bool: True se sucesso, False se erro
        """
        print(f"\n🔄 EXECUTAR SEQUENCIAL - {len(pedidos)} pedido(s)")
        print("=" * 50)
        
        try:
            # Valida entrada
            if not pedidos:
                print("⚠️ Nenhum pedido para executar")
                return False
            
            # ✅ CORREÇÃO: Inicializa sistema se necessário
            if not self._inicializar_sistema():
                return False
            
            # Converte pedidos
            pedidos_convertidos = self._converter_pedidos(pedidos)
            if not pedidos_convertidos:
                print("❌ Erro na conversão de pedidos")
                return False
            
            # Executa
            inicio = datetime.now()
            sucesso = self._executar_pedidos_sequencial(pedidos_convertidos)
            fim = datetime.now()
            
            # Atualiza estatísticas
            self._atualizar_estatisticas('sequencial', pedidos, sucesso, (fim - inicio).total_seconds())
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro durante execução sequencial: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def executar_otimizado(self, pedidos: List[DadosPedidoMenu]) -> bool:
        """
        Executa pedidos com otimização PL.
        
        Args:
            pedidos: Lista de pedidos do menu
            
        Returns:
            bool: True se sucesso, False se erro
        """
        print(f"\n🚀 EXECUTAR OTIMIZADO - {len(pedidos)} pedido(s)")
        print("=" * 50)
        
        try:
            # Valida entrada
            if not pedidos:
                print("⚠️ Nenhum pedido para executar")
                return False
            
            # Verifica OR-Tools
            if not self._verificar_or_tools():
                print("❌ OR-Tools não disponível para otimização")
                return False
            
            # ✅ CORREÇÃO: Inicializa sistema se necessário  
            if not self._inicializar_sistema():
                return False
            
            # Converte pedidos
            pedidos_convertidos = self._converter_pedidos(pedidos)
            if not pedidos_convertidos:
                print("❌ Erro na conversão de pedidos")
                return False
            
            # Executa com otimização
            inicio = datetime.now()
            sucesso = self._executar_pedidos_otimizado(pedidos_convertidos)
            fim = datetime.now()
            
            # Atualiza estatísticas
            self._atualizar_estatisticas('otimizado', pedidos, sucesso, (fim - inicio).total_seconds())
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro durante execução otimizada: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas da última execução"""
        return self.ultima_execucao.copy()
    
    def configurar(self, **kwargs) -> None:
        """
        Atualiza configurações do gestor.
        
        Args:
            **kwargs: Configurações a atualizar
        """
        for chave, valor in kwargs.items():
            if chave in self.configuracoes:
                self.configuracoes[chave] = valor
                print(f"⚙️ {chave} configurado para: {valor}")
            else:
                print(f"⚠️ Configuração desconhecida: {chave}")
    
    def testar_sistema(self) -> Dict:
        """
        Testa componentes do sistema.
        
        Returns:
            Dict com resultados dos testes
        """
        print("🧪 TESTANDO SISTEMA")
        print("=" * 30)
        
        resultados = {}
        
        # Teste 1: OR-Tools
        ortools_ok = self._verificar_or_tools()
        resultados['ortools'] = {'ok': ortools_ok, 'msg': 'OR-Tools disponível' if ortools_ok else 'OR-Tools não encontrado'}
        print(f"   1️⃣ OR-Tools: {'✅' if ortools_ok else '❌'}")
        
        # Teste 2: Inicialização do sistema
        try:
            init_ok = self._inicializar_sistema()
            resultados['inicializacao'] = {'ok': init_ok, 'msg': 'Sistema inicializado' if init_ok else 'Erro na inicialização'}
            print(f"   2️⃣ Inicialização: {'✅' if init_ok else '❌'}")
        except Exception as e:
            resultados['inicializacao'] = {'ok': False, 'msg': str(e)}
            print(f"   2️⃣ Inicialização: ❌ {e}")
        
        # Teste 3: Componentes
        componentes_ok = all([
            self.configurador_ambiente is not None,
            self.conversor_pedidos is not None,
            self.executor_pedidos is not None
        ])
        resultados['componentes'] = {'ok': componentes_ok, 'msg': 'Todos componentes carregados' if componentes_ok else 'Componentes faltando'}
        print(f"   3️⃣ Componentes: {'✅' if componentes_ok else '❌'}")
        
        return resultados
    
    # =========================================================================
    #                           MÉTODOS PRIVADOS
    # =========================================================================
    
    def _inicializar_sistema(self) -> bool:
        """✅ CORRIGIDO: Inicializa componentes do sistema se necessário"""
        if self.sistema_inicializado:
            return True
        
        try:
            print("🔧 Inicializando componentes do sistema...")
            
            # ✅ PASSO 1: Inicializa configurador ambiente
            from services.gestor_producao.configurador_ambiente import ConfiguradorAmbiente
            self.configurador_ambiente = ConfiguradorAmbiente()
            
            if not self.configurador_ambiente.inicializar_ambiente():
                print("❌ Falha na inicialização do ambiente")
                return False
            
            # ✅ PASSO 2: Inicializa conversor COM gestor_almoxarifado
            from services.gestor_producao.conversor_pedidos import ConversorPedidos
            self.conversor_pedidos = ConversorPedidos(
                gestor_almoxarifado=self.configurador_ambiente.gestor_almoxarifado  # ← CRÍTICO!
            )
            
            # ✅ PASSO 3: Inicializa executor
            from services.gestor_producao.executor_pedidos import ExecutorPedidos
            self.executor_pedidos = ExecutorPedidos(self.configuracoes)
            
            print("✅ Sistema inicializado com sucesso")
            print(f"   🏪 Gestor almoxarifado: {'✅ Conectado' if self.configurador_ambiente.gestor_almoxarifado else '❌ Falha'}")
            self.sistema_inicializado = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _converter_pedidos(self, pedidos: List[DadosPedidoMenu]) -> Optional[List]:
        """Converte pedidos do menu para formato do sistema"""
        try:
            print(f"🔄 Convertendo {len(pedidos)} pedido(s)...")
            
            # ✅ VERIFICAÇÃO: Conversor foi inicializado?
            if not self.conversor_pedidos:
                print("❌ Conversor não foi inicializado!")
                return None
            
            # Usa o conversor real
            pedidos_convertidos = self.conversor_pedidos.converter_pedidos(pedidos)
            
            if pedidos_convertidos:
                print(f"✅ {len(pedidos_convertidos)} pedido(s) convertido(s)")
                
                # ✅ DEBUG: Verifica se gestor_almoxarifado foi passado
                for pedido in pedidos_convertidos:
                    if not pedido.gestor_almoxarifado:
                        print(f"⚠️ AVISO: Pedido {pedido.id_pedido} sem gestor_almoxarifado!")
                    else:
                        print(f"   ✅ Pedido {pedido.id_pedido} com gestor_almoxarifado")
            else:
                print("❌ Falha na conversão de pedidos")
            
            return pedidos_convertidos
            
        except Exception as e:
            print(f"❌ Erro na conversão: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _executar_pedidos_sequencial(self, pedidos_convertidos: List) -> bool:
        """Executa pedidos em modo sequencial"""
        try:
            print(f"🔄 Executando {len(pedidos_convertidos)} pedido(s) sequencialmente...")
            
            # ✅ VERIFICAÇÃO: Executor foi inicializado?
            if not self.executor_pedidos:
                print("❌ Executor não foi inicializado!")
                return False
            
            # Usa o executor real
            sucesso = self.executor_pedidos.executar_sequencial(pedidos_convertidos)
            
            if sucesso:
                # Atualiza estatísticas locais com dados do executor
                stats_executor = self.executor_pedidos.obter_estatisticas()
                self.ultima_execucao.update(stats_executor)
                print("✅ Execução sequencial concluída")
            else:
                print("❌ Falha na execução sequencial")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro na execução sequencial: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _executar_pedidos_otimizado(self, pedidos_convertidos: List) -> bool:
        """Executa pedidos com otimização PL"""
        try:
            print(f"🚀 Executando {len(pedidos_convertidos)} pedido(s) com otimização...")
            
            # ✅ VERIFICAÇÃO: Executor foi inicializado?
            if not self.executor_pedidos:
                print("❌ Executor não foi inicializado!")
                return False
            
            # Usa o executor real
            sucesso = self.executor_pedidos.executar_otimizado(pedidos_convertidos)
            
            if sucesso:
                # Atualiza estatísticas locais com dados do executor
                stats_executor = self.executor_pedidos.obter_estatisticas()
                self.ultima_execucao.update(stats_executor)
                print("✅ Execução otimizada concluída")
            else:
                print("❌ Falha na execução otimizada")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro na execução otimizada: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _verificar_or_tools(self) -> bool:
        """Verifica se OR-Tools está disponível"""
        try:
            from ortools.linear_solver import pywraplp
            return True
        except ImportError:
            return False
    
    def _atualizar_estatisticas(self, modo: str, pedidos: List[DadosPedidoMenu], 
                               sucesso: bool, tempo_execucao: float) -> None:
        """Atualiza estatísticas da execução"""
        self.ultima_execucao.update({
            'sucesso': sucesso,
            'modo': modo,
            'total_pedidos': len(pedidos),
            'pedidos_executados': len(pedidos) if sucesso else 0,  # Simplificado por enquanto
            'tempo_execucao': tempo_execucao,
            'log_filename': f'logs/gestor_producao_{modo}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        })