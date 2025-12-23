"""
Sistema de Produção - Classe Principal
=====================================

Classe centralizada para gerenciar todo o sistema de produção da padaria.
Substitui o producao_paes.py com arquitetura mais limpa e modular.

Funcionalidades:
- Execução sequencial e otimizada
- Gerenciamento de pedidos de produção
- Integração com otimizador PL
- Sistema de logging integrado
- Estatísticas e cronogramas
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

# Imports do sistema de produção
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from services.gestores.comandas.gestor_comandas import gerar_comanda_reserva
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem


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
        self.file.flush()
        
    def flush(self):
        self.stdout.flush()
        self.file.flush()


class SistemaDeProducao:
    """
    Sistema principal de produção da padaria.
    
    Centraliza toda a lógica de execução, oferecendo modos sequencial e otimizado.
    Projetado para ser usado pelo ExecutorProducao e outros componentes.
    """
    
    def __init__(self, usar_otimizacao: bool = False, resolucao_minutos: int = 30, timeout_pl: int = 300):
        """
        Inicializa o sistema de produção.
        
        Args:
            usar_otimizacao: Se True, usa otimização PL. Se False, execução sequencial
            resolucao_minutos: Resolução temporal para otimização (30min recomendado)
            timeout_pl: Timeout em segundos para resolução PL (5min padrão)
        """
        # Componentes principais
        self.almoxarifado: Optional[Almoxarifado] = None
        self.gestor_almoxarifado: Optional[GestorAlmoxarifado] = None
        self.pedidos: List[PedidoDeProducao] = []
        
        # Configuração de execução
        self.usar_otimizacao = usar_otimizacao
        self.resolucao_minutos = resolucao_minutos
        self.timeout_pl = timeout_pl
        
        # Sistema de logging
        self.log_filename: Optional[str] = None
        
        # Otimizador (carregado sob demanda)
        self._otimizador = None
        
        # Estatísticas
        self.estatisticas_execucao: Dict[str, Any] = {}
        
        # Mapeamento de produtos (pode ser configurável futuramente)
        self.mapeamento_produtos = {
            "Pão Francês": 1001,
            "Pão Hambúrguer": 1002,
            "Pão de Forma": 1003,
            "Pão Baguete": 1004,
            "Pão Trança de Queijo finos": 1005
        }
    
    @property
    def otimizador(self):
        """Carrega otimizador sob demanda (usando otimizador)"""
        if self.usar_otimizacao and self._otimizador is None:
            try:
                from otimizador import ExecutorUnificadoPL
                self._otimizador = ExecutorUnificadoPL()
            except ImportError:
                print("⚠️ Otimizador v3 não disponível. Alternando para modo sequencial.")
                self.usar_otimizacao = False
        return self._otimizador
    
    # =============================================================================
    #                      CONFIGURAÇÃO DO SISTEMA
    # =============================================================================
    
    def configurar_log(self, prefixo: str = "execucao_pedidos") -> str:
        """
        Configura o sistema de logging com timestamp único.
        
        Args:
            prefixo: Prefixo para o nome do arquivo de log
            
        Returns:
            Caminho do arquivo de log criado
        """
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        modo = "otimizado" if self.usar_otimizacao else "sequencial"
        self.log_filename = f'logs/{prefixo}_{modo}_{timestamp}.log'
        return self.log_filename
    
    def inicializar_almoxarifado(self, limpar_dados_anteriores: bool = True) -> bool:
        """
        Carrega e inicializa o almoxarifado com todos os itens necessários.
        
        Args:
            limpar_dados_anteriores: Se True, limpa comandas e logs anteriores
            
        Returns:
            True se inicialização foi bem-sucedida
        """
        try:
            print("📄 Carregando itens do almoxarifado...")
            
            # Carrega itens do arquivo JSON
            itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
            
            # Limpa dados anteriores se solicitado
            if limpar_dados_anteriores:
                apagar_todas_as_comandas()
                limpar_todos_os_logs()
            
            # Inicializa almoxarifado
            self.almoxarifado = Almoxarifado()
            for item in itens:
                self.almoxarifado.adicionar_item(item)
            
            # Cria gestor
            self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)
            
            print("✅ Almoxarifado carregado com sucesso!")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar almoxarifado: {e}")
            return False
    
    def configurar_modo_execucao(self, usar_otimizacao: bool, resolucao_minutos: int = 30, timeout_pl: int = 300):
        """
        Configura o modo de execução do sistema.
        
        Args:
            usar_otimizacao: Se True, usa otimização PL
            resolucao_minutos: Resolução temporal para otimização
            timeout_pl: Timeout para resolução PL
        """
        self.usar_otimizacao = usar_otimizacao
        self.resolucao_minutos = resolucao_minutos
        self.timeout_pl = timeout_pl
        
        # Reset otimizador para recarregar com novas configurações
        self._otimizador = None
        
        modo = "OTIMIZADO" if usar_otimizacao else "SEQUENCIAL"
        print(f"⚙️ Modo configurado para: {modo}")
        if usar_otimizacao:
            print(f"   Resolução: {resolucao_minutos} minutos")
            print(f"   Timeout PL: {timeout_pl} segundos")
    
    # =============================================================================
    #                      GERENCIAMENTO DE PEDIDOS
    # =============================================================================
    
    def adicionar_pedidos(self, pedidos: List[PedidoDeProducao]):
        """
        Adiciona pedidos ao sistema.
        
        Args:
            pedidos: Lista de pedidos de produção
        """
        if not self.gestor_almoxarifado:
            raise RuntimeError("Almoxarifado deve ser inicializado antes de adicionar pedidos")
        
        # Garante que todos os pedidos têm gestor_almoxarifado
        for pedido in pedidos:
            if not hasattr(pedido, 'gestor_almoxarifado') or pedido.gestor_almoxarifado is None:
                pedido.gestor_almoxarifado = self.gestor_almoxarifado
        
        self.pedidos.extend(pedidos)
        print(f"📋 {len(pedidos)} pedido(s) adicionado(s). Total: {len(self.pedidos)}")
    
    def limpar_pedidos(self):
        """Remove todos os pedidos do sistema."""
        self.pedidos.clear()
        print("🗑️ Todos os pedidos foram removidos")
    
    def criar_pedido_padrao(self, produto: str, quantidade: int, hora_fim: int, data_base: datetime = None) -> Optional[PedidoDeProducao]:
        """
        Cria um pedido padrão com configurações automáticas.
        
        Args:
            produto: Nome do produto
            quantidade: Quantidade a produzir
            hora_fim: Hora limite para conclusão
            data_base: Data base para cálculos (hoje se None)
            
        Returns:
            Pedido criado ou None se erro
        """
        if not self.gestor_almoxarifado:
            raise RuntimeError("Almoxarifado deve ser inicializado antes de criar pedidos")
        
        try:
            # Data base
            if data_base is None:
                data_base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calcula datas
            fim_jornada = data_base.replace(hour=hora_fim, minute=0, second=0, microsecond=0)
            inicio_jornada = fim_jornada - timedelta(days=3)  # 3 dias de flexibilidade
            
            # Obtém ID do produto
            id_produto = self.mapeamento_produtos.get(produto)
            if id_produto is None:
                print(f"⚠️ Produto '{produto}' não encontrado no mapeamento!")
                return None
            
            # Gera ID único para o pedido
            id_pedido = len(self.pedidos) + 1
            
            # Cria pedido
            pedido = PedidoDeProducao(
                id_ordem=1,
                id_pedido=id_pedido,
                id_produto=id_produto,
                tipo_item=TipoItem.PRODUTO,
                quantidade=quantidade,
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada,
                gestor_almoxarifado=self.gestor_almoxarifado
            )
            
            pedido.montar_estrutura()
            return pedido
            
        except Exception as e:
            print(f"❌ Erro ao criar pedido: {e}")
            return None
    
    def ordenar_pedidos_por_prioridade(self):
        """Ordena pedidos baseado em restrições e prioridades."""
        if not self.usar_otimizacao:
            print("📄 Ordenando pedidos por restrições (modo sequencial)...")
            self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
            print(f"✅ {len(self.pedidos)} pedidos ordenados!")
        else:
            print("📄 Mantendo ordem original (otimização PL definirá execução)...")
        print()
    
    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================
    
    def executar_pedidos_sequencial(self) -> bool:
        """
        Executa todos os pedidos em ordem sequencial.
        
        Returns:
            True se execução foi bem-sucedida
        """
        print("📄 Executando pedidos em ordem sequencial...")
        
        if not self.pedidos:
            print("⚠️ Nenhum pedido para executar")
            return False
        
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
                
            except Exception as e:
                print(f"   ⚠️ Falha ao processar o pedido {pedido.id_pedido} ({nome_produto}): {e}")
                
            print()
        
        # Atualiza estatísticas
        self.estatisticas_execucao.update({
            'total_pedidos': len(self.pedidos),
            'pedidos_executados': pedidos_executados,
            'modo_execucao': 'sequencial',
            'taxa_sucesso': pedidos_executados / len(self.pedidos) if self.pedidos else 0
        })
        
        return pedidos_executados > 0
    
    def executar_pedidos_otimizado(self) -> bool:
        """
        Executa pedidos usando otimização PL.
        
        Returns:
            True se execução foi bem-sucedida
        """
        if not self.usar_otimizacao:
            print("❌ Sistema não configurado para otimização. Use executar_pedidos_sequencial().")
            return False
        
        if not self.pedidos:
            print("⚠️ Nenhum pedido para executar")
            return False
        
        print("🚀 Iniciando execução otimizada com Programação Linear...")
        
        try:
            # Carrega otimizador
            otimizador = self.otimizador
            if not otimizador:
                print("❌ Otimizador não disponível")
                return False
            
            # Delega execução para o otimizador
            sucesso = otimizador.executar_pedidos_otimizados(self.pedidos, self)
            
            # Coleta estatísticas do otimizador
            if sucesso:
                stats_otimizador = otimizador.obter_estatisticas()
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
            import traceback
            traceback.print_exc()
            return False
    
    def executar_pedidos(self) -> bool:
        """
        Executa pedidos usando o modo configurado (sequencial ou otimizado).
        
        Returns:
            True se execução foi bem-sucedida
        """
        if not self.pedidos:
            print("⚠️ Nenhum pedido para executar")
            return False
        
        # Ordena pedidos se necessário
        self.ordenar_pedidos_por_prioridade()
        
        # Executa baseado no modo configurado
        if self.usar_otimizacao:
            return self.executar_pedidos_otimizado()
        else:
            return self.executar_pedidos_sequencial()
    
    def _executar_pedido_individual(self, pedido: PedidoDeProducao):
        """
        Executa um pedido individual seguindo o fluxo padrão.
        
        Args:
            pedido: Pedido a ser executado
        """
        # Gera comanda de reserva
        gerar_comanda_reserva(
            id_ordem=pedido.id_ordem,
            id_pedido=pedido.id_pedido,
            ficha=pedido.ficha_tecnica_modular,
            gestor=self.gestor_almoxarifado,
            data_execucao=pedido.inicio_jornada
        )
        
        # Mostra estrutura da ficha técnica
        pedido.mostrar_estrutura()
        
        # Cria atividades modulares
        pedido.criar_atividades_modulares_necessarias()
        
        # Executa atividades em ordem
        pedido.executar_atividades_em_ordem()
    
    # =============================================================================
    #                      EXECUÇÃO COMPLETA COM LOGGING
    # =============================================================================
    
    def executar_sistema_completo(self, usar_logging_duplo: bool = True) -> bool:
        """
        Executa o sistema completo de produção.
        
        Args:
            usar_logging_duplo: Se True, salva log em arquivo além do terminal
            
        Returns:
            True se execução foi bem-sucedida
        """
        try:
            modo = "OTIMIZADA" if self.usar_otimizacao else "SEQUENCIAL"
            print(f"🥖 INICIANDO SISTEMA DE PRODUÇÃO - MODO {modo}")
            print()
            
            # Verifica se almoxarifado está inicializado
            if not self.gestor_almoxarifado:
                print("📦 Inicializando almoxarifado...")
                if not self.inicializar_almoxarifado():
                    return False
            
            # Verifica se há pedidos
            if not self.pedidos:
                print("⚠️ Nenhum pedido cadastrado no sistema")
                return False
            
            # Configura logging se necessário
            if usar_logging_duplo and not self.log_filename:
                self.configurar_log()
            
            # Executa com ou sem logging duplo
            if usar_logging_duplo and self.log_filename:
                return self._executar_com_logging_duplo()
            else:
                return self.executar_pedidos()
                
        except Exception as e:
            print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _executar_com_logging_duplo(self) -> bool:
        """Executa o sistema com logging duplo (terminal + arquivo)."""
        with open(self.log_filename, 'w', encoding='utf-8') as log_file:
            tee = TeeOutput(log_file)
            sys.stdout = tee
            
            try:
                # Escreve cabeçalho
                self.escrever_cabecalho_log()
                
                # Executa pedidos
                sucesso = self.executar_pedidos()
                
                # Escreve rodapé
                self.escrever_rodape_log(sucesso)
                
                return sucesso
                
            except Exception as e:
                print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
                import traceback
                traceback.print_exc()
                self.escrever_rodape_log(False)
                return False
            
            finally:
                # Restaura stdout original
                sys.stdout = tee.stdout
        
        return True
    
    # =============================================================================
    #                      SISTEMA DE LOGGING
    # =============================================================================
    
    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log."""
        print("=" * 80)
        print(f"LOG DE EXECUÇÃO - SISTEMA DE PRODUÇÃO PADARIA")
        modo = "OTIMIZADA (Programação Linear)" if self.usar_otimizacao else "SEQUENCIAL"
        print(f"Modo de execução: {modo}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if self.usar_otimizacao and self.otimizador:
            print(f"Configuração PL:")
            print(f"  - Resolução temporal: {self.resolucao_minutos} minutos")
            print(f"  - Timeout: {self.timeout_pl} segundos")
        
        print(f"Total de pedidos: {len(self.pedidos)}")
        print("=" * 80)
        print()
    
    def escrever_rodape_log(self, sucesso: bool = True):
        """Escreve rodapé final no log."""
        print("=" * 80)
        if sucesso:
            print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!")
            
            # Mostra estatísticas se disponíveis
            if self.estatisticas_execucao:
                self._imprimir_estatisticas_finais()
                
        else:
            print("❌ EXECUÇÃO FINALIZADA COM ERROS!")
        
        if self.log_filename:
            print(f"📄 Log salvo em: {self.log_filename}")
        print("=" * 80)
    
    def _imprimir_estatisticas_finais(self):
        """Imprime estatísticas finais da execução."""
        stats = self.estatisticas_execucao
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   Total de pedidos: {stats.get('total_pedidos', 'N/A')}")
        print(f"   Pedidos executados: {stats.get('pedidos_executados', 'N/A')}")
        print(f"   Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1%}")
        
        if self.usar_otimizacao and 'otimizacao' in stats:
            opt_stats = stats['otimizacao']
            print(f"   Taxa de atendimento PL: {opt_stats.get('taxa_atendimento', 0):.1%}")
            print(f"   Tempo otimização: {opt_stats.get('tempo_total_otimizacao', 0):.2f}s")
            print(f"   Status solver: {opt_stats.get('status_solver', 'N/A')}")
    
    # =============================================================================
    #                      MÉTODOS DE CONSULTA
    # =============================================================================
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da execução.
        
        Returns:
            Dicionário com estatísticas
        """
        return self.estatisticas_execucao.copy()
    
    def obter_cronograma_otimizado(self) -> Dict[str, Any]:
        """
        Retorna cronograma otimizado (se disponível).
        
        Returns:
            Dicionário com cronograma ou vazio se não disponível
        """
        if self.usar_otimizacao and self.otimizador:
            return self.otimizador.obter_cronograma_otimizado()
        return {}
    
    def obter_status_sistema(self) -> Dict[str, Any]:
        """
        Retorna status completo do sistema.
        
        Returns:
            Dicionário com status do sistema
        """
        return {
            'modo_execucao': 'otimizado' if self.usar_otimizacao else 'sequencial',
            'almoxarifado_inicializado': self.gestor_almoxarifado is not None,
            'total_pedidos': len(self.pedidos),
            'otimizador_disponivel': self.otimizador is not None if self.usar_otimizacao else False,
            'log_configurado': self.log_filename is not None,
            'configuracoes': {
                'resolucao_minutos': self.resolucao_minutos,
                'timeout_pl': self.timeout_pl
            }
        }
    
    def _obter_nome_produto_por_id(self, id_produto: int) -> str:
        """Obtém nome do produto pelo ID."""
        return next((nome for nome, id_prod in self.mapeamento_produtos.items() 
                    if id_prod == id_produto), f"Produto {id_produto}")
    
    # =============================================================================
    #                      MÉTODOS DE VALIDAÇÃO
    # =============================================================================
    
    def validar_sistema(self) -> Dict[str, bool]:
        """
        Valida se o sistema está pronto para execução.
        
        Returns:
            Dicionário com resultados da validação
        """
        resultados = {
            'almoxarifado_ok': self.gestor_almoxarifado is not None,
            'pedidos_ok': len(self.pedidos) > 0,
            'otimizador_ok': True
        }
        
        # Valida otimizador se necessário
        if self.usar_otimizacao:
            try:
                resultados['otimizador_ok'] = self.otimizador is not None
            except Exception:
                resultados['otimizador_ok'] = False
        
        return resultados
    
    def __repr__(self) -> str:
        modo = "Otimizado" if self.usar_otimizacao else "Sequencial"
        return f"SistemaDeProducao(modo={modo}, pedidos={len(self.pedidos)}, almoxarifado={'OK' if self.gestor_almoxarifado else 'Não inicializado'})"