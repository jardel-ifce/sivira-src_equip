import sys
import os
from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva
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
        self.file.flush()  # Garante escrita imediata no arquivo
        
    def flush(self):
        self.stdout.flush()
        self.file.flush()


class TesteSistemaProducao:
    """
    Classe principal para teste do sistema de produção.
    Coordena todo o fluxo de execução desde o carregamento do almoxarifado 
    até a execução completa dos pedidos.
    """
    
    def __init__(self):
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.log_filename = None
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f'logs/execucao_pedidos_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print(f"LOG DE EXECUÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        print()

    def escrever_rodape_log(self, sucesso=True):
        """Escreve rodapé final no log"""
        print("=" * 80)
        if sucesso:
            print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("❌ EXECUÇÃO FINALIZADA COM ERROS!")
        print(f"📄 Log salvo em: {self.log_filename}")
        print("=" * 80)

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
        Cria os pedidos de produção conforme configuração.
        Atualmente configurado para 1 pedido de teste.
        """
        print("🔄 Criando pedidos de produção...")
        self.pedidos = []
        
        # Configurações do pedido (podem ser parametrizadas futuramente)
        configuracoes_pedidos = [
            {
                'id_pedido': 1,
                'id_produto': 1002,
                'quantidade': 50,
            }
        ]
        
        for config in configuracoes_pedidos:
            print(f"   Processando pedido {config['id_pedido']}...")
            
            try:
                pedido = PedidoDeProducao(
                    id_ordem=1,  # Fixo para testes
                    id_pedido=config['id_pedido'],
                    id_produto=config['id_produto'],
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=config['quantidade'],
                    inicio_jornada=datetime(2025, 6, 23, 8, 0),
                    fim_jornada=datetime(2025, 6, 24, 18, 0),
                    todos_funcionarios=funcionarios_disponiveis
                )
                
                pedido.montar_estrutura()
                self.pedidos.append(pedido)
                print(f"   ✅ Pedido {config['id_pedido']} criado com sucesso!")
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao montar estrutura do pedido {config['id_pedido']}: {e}")
        
        print()

    def ordenar_pedidos_por_prioridade(self):
        """Ordena pedidos baseado em restrições e prioridades"""
        print("🔄 Ordenando pedidos por restrições...")
        self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
        print(f"✅ {len(self.pedidos)} pedidos ordenados!")
        print()

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_ordenados(self):
        """
        Executa todos os pedidos em ordem de prioridade.
        Para cada pedido: gera comanda, mostra estrutura, cria atividades e executa.
        """
        print("🔄 Executando pedidos em ordem de prioridade...")
        
        for idx, pedido in enumerate(self.pedidos, 1):
            print(f"   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})...")
            
            try:
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
                
                # Exibir histórico (opcional - pode ser comentado para logs mais limpos)
                # pedido.exibir_historico_de_funcionarios()
                
                print(f"   ✅ Pedido {pedido.id_pedido} executado com sucesso!")
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao processar o pedido {pedido.id_pedido}: {e}")
                # Continue com próximos pedidos mesmo se um falhar
                
            print()

    # =============================================================================
    #                       FLUXO PRINCIPAL
    # =============================================================================

    def executar_teste_completo(self):
        """
        Executa o teste completo do sistema de produção.
        Fluxo: Almoxarifado → Pedidos → Ordenação → Execução
        """
        try:
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Criação dos pedidos
            self.criar_pedidos_de_producao()
            
            # Fase 3: Ordenação por prioridade
            self.ordenar_pedidos_por_prioridade()
            
            # Fase 4: Execução
            self.executar_pedidos_ordenados()
            
            return True
            
        except Exception as e:
            print("=" * 80)
            print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Função principal que coordena todo o teste.
    Configura logging e executa o sistema completo.
    """
    # Inicializar sistema de teste
    sistema = TesteSistemaProducao()
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
            
            # Escrever rodapé
            sistema.escrever_rodape_log(sucesso)
            
        except Exception as e:
            sistema.escrever_rodape_log(False)
            raise
        
        finally:
            # Restaurar stdout original
            sys.stdout = tee.stdout
            print(f"\n📄 Log de execução salvo em: {log_filename}")


if __name__ == "__main__":
    main()