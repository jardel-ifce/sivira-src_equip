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
            "Coxinha de Frango": 1055,
            "Coxinha de Carne de Sol": 1069,
            "Coxinha de Camarão": 1070,
            "Coxinha de Queijos Finos": 1071
        }
        
        # Estatísticas da execução
        self.estatisticas_execucao = {}
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        modo = "otimizado" if self.usar_otimizacao else "sequencial"
        self.log_filename = f'logs/execucao_coxinhas_sequencial_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print(f"LOG DE EXECUÇÃO - SISTEMA DE PRODUÇÃO COXINHAS")
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
        print("🔄 Criando pedidos de produção de coxinhas...")
        self.pedidos = []
        
        # Data base para os cálculos
        data_base = datetime(2025, 6, 26)
        
        # Configurações dos pedidos de coxinhas
        configuracoes_pedidos = [
           # CONJUNTO MATINAL 
            {"produto": "Coxinha de Frango", "quantidade": 36, "hora_fim": 8},
           # {"produto": "Coxinha de Carne de Sol", "quantidade": 10, "hora_fim": 8},
           # {"produto": "Coxinha de Camarão", "quantidade": 12, "hora_fim": 8},
           # {"produto": "Coxinha de Queijos Finos", "quantidade": 12, "hora_fim": 8},

          

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
        
        print(f"\n✅ Total de {len(self.pedidos)} pedidos criados para coxinhas!")
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
        print("🔄 Executando pedidos de coxinhas em ordem sequencial...")
        
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
        Executa o teste completo do sistema de produção de coxinhas.
        ATUALIZADO para escolher entre execução sequencial ou otimizada.
        """
        try:
            modo = "OTIMIZADA" if self.usar_otimizacao else "SEQUENCIAL"
            print(f"🥟 INICIANDO SISTEMA DE PRODUÇÃO DE COXINHAS - MODO {modo}")
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
    Função principal que coordena todo o teste de produção de coxinhas.
    ✅ CORRIGIDO com janela temporal adequada para otimizador PL.
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