#!/usr/bin/env python3
"""
🍟 Script de Produção: Sistema de Produção de Coxinhas de Frango
===============================================================

Baseado no producao_paes.py, adaptado para produção de coxinhas com sistema de bateladas.
Modo de execução: SEQUENCIAL (sem otimização PL).
"""

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
from enums.equipamentos.tipo_equipamento import TipoEquipamento


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


class SistemaProducaoCoxinhas:
    """
    Classe principal para teste do sistema de produção de coxinhas.
    Coordena todo o fluxo de execução desde o carregamento do almoxarifado 
    até a execução completa dos pedidos de coxinhas.
    
    🍟 ESPECIALIZADO: Produção de coxinhas com sistema de bateladas
    """
    
    def __init__(self):
        """Inicializa o sistema de produção de coxinhas."""
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.log_filename = None
        
        # Mapeamento específico para coxinhas e folhados
        self.mapeamento_produtos = {
            "Coxinha de Frango": 1055,
            "Coxinha de Carne de sol": 1069,
  
            "Coxinha de Queijos finos": 1071,
            "Folhado de Frango": 1072,
            "Folhado de Carne de sol": 1059,
            "Folhado de Camarão": 1073,
            "Folhado de Queijos finos": 1074
        }
        
        # Estatísticas da execução
        self.estatisticas_execucao = {}
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f'logs/execucao_coxinhas_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print(f"🍟 LOG DE EXECUÇÃO - SISTEMA DE PRODUÇÃO DE CONFEITARIA")
        print(f"Modo de execução: SEQUENCIAL")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
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
        print(f"   Total de itens produzidos: {stats.get('total_itens', 'N/A')}")

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
        Cria pedidos de produção de coxinhas com diferentes quantidades para testar o sistema de bateladas.
        """
        print("🔄 Criando pedidos de produção de coxinhas...")
        self.pedidos = []
        
        # Data base para os cálculos
        data_base = datetime(2025, 9, 9)  # Data atual
        
        # Configurações dos pedidos para confeitaria
        configuracoes_pedidos = [
            # PEDIDOS MATUTINOS - 08:00
            {"produto": "Coxinha de Carne de sol", "quantidade": 8, "hora_fim": 8},
            {"produto": "Coxinha de Camarão", "quantidade": 8, "hora_fim": 8},
            {"produto": "Coxinha de Queijos finos", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Frango", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Carne de sol", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Camarão", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Queijos finos", "quantidade": 5, "hora_fim": 8},
        ]
        
        id_pedido_counter = 1
        
        for config in configuracoes_pedidos:
            print(f"   Processando pedido {id_pedido_counter}: {config['produto']} - {config['quantidade']} unidades...")
            
            try:
                # Calcular datas de início e fim da jornada
                fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
                
                # Janela de 3 dias para flexibilidade de alocação
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
                
                # Configurar bypass para HotMix e Fogões (capacidade mínima)
                bypass_tipos = {TipoEquipamento.MISTURADORAS_COM_COCCAO, TipoEquipamento.FOGOES}
                pedido.configurar_bypass_capacidade(bypass_tipos)
                
                self.pedidos.append(pedido)
                print(f"   ✅ Pedido {id_pedido_counter} criado: {config['produto']} ({config['quantidade']} uni)")
                
                id_pedido_counter += 1
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao montar estrutura do pedido {id_pedido_counter}: {e}")
                id_pedido_counter += 1
        
        print(f"\n✅ Total de {len(self.pedidos)} pedidos criados para confeitaria!")
        print(f"🔧 Pedidos configurados com janela de 3 dias para execução sequencial")
        print()

    def ordenar_pedidos_por_prioridade(self):
        """Ordena pedidos baseado em restrições e prioridades."""
        print("🔄 Ordenando pedidos por restrições (modo sequencial)...")
        self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
        print(f"✅ {len(self.pedidos)} pedidos ordenados!")
        print()

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_ordenados(self):
        """Executa todos os pedidos em ordem sequencial."""
        print("🔄 Executando pedidos de confeitaria em ordem sequencial...")
        
        pedidos_executados = 0
        total_itens = 0
        
        for idx, pedido in enumerate(self.pedidos, 1):
            nome_produto = self._obter_nome_produto_por_id(pedido.id_produto)
            
            print(f"   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})...")
            print(f"   📋 {nome_produto} - {pedido.quantidade} unidades")
            print(f"   ⏰ Prazo: {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            
            try:
                self._executar_pedido_individual(pedido)
                print(f"   ✅ Pedido {pedido.id_pedido} ({nome_produto}) executado com sucesso!")
                pedidos_executados += 1
                total_itens += pedido.quantidade
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao processar o pedido {pedido.id_pedido} ({nome_produto}): {e}")
                
            print()
        
        self.estatisticas_execucao.update({
            'total_pedidos': len(self.pedidos),
            'pedidos_executados': pedidos_executados,
            'total_itens': total_itens,
            'modo_execucao': 'sequencial'
        })

    def _executar_pedido_individual(self, pedido):
        """
        Executa um pedido individual seguindo o fluxo padrão.
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
        
        # Executar atividades em ordem (incluindo a fritadeira com sistema de bateladas)
        pedido.executar_atividades_em_ordem()

    def _obter_nome_produto_por_id(self, id_produto):
        """Obtém nome do produto pelo ID"""
        return next((nome for nome, id_prod in self.mapeamento_produtos.items() 
                    if id_prod == id_produto), f"Produto {id_produto}")

    # =============================================================================
    #                       FLUXO PRINCIPAL
    # =============================================================================

    def executar_teste_completo(self):
        """Executa o teste completo do sistema de produção de coxinhas."""
        try:
            print(f"🍟 INICIANDO SISTEMA DE PRODUÇÃO DE CONFEITARIA - MODO SEQUENCIAL")
            print()
            
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Criação dos pedidos
            self.criar_pedidos_de_producao()
            
            # Fase 3: Ordenação por prioridade
            self.ordenar_pedidos_por_prioridade()
            
            # Fase 4: Execução sequencial
            self.executar_pedidos_ordenados()
            
            return True
            
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


def main():
    """
    Função principal que coordena todo o teste de produção de coxinhas.
    """
    
    # Inicializar sistema de teste
    sistema = SistemaProducaoCoxinhas()
    
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
            
            # Mostrar estatísticas finais
            if sucesso:
                print(f"\n📋 RELATÓRIO FINAL:")
                stats = sistema.obter_estatisticas()
                print(f"   Estatísticas: {stats}")
            
            # Escrever rodapé
            sistema.escrever_rodape_log(sucesso)
            
        except Exception as e:
            sistema.escrever_rodape_log(False)
            raise
        
        finally:
            # Restaurar stdout original
            sys.stdout = tee.stdout
            print(f"\n📄 Log de execução salvo em: {log_filename}")


def exemplo_diferentes_quantidades():
    """
    Exemplo que demonstra o sistema de bateladas com diferentes quantidades.
    """
    print("=" * 60)
    print("🍟 EXEMPLO: DEMONSTRAÇÃO DO SISTEMA DE BATELADAS")
    print("=" * 60)
    
    # Simular diferentes quantidades
    quantidades_teste = [9, 18, 30, 40, 45, 60]
    
    print("Simulação de bateladas para diferentes quantidades:")
    print("(9 unidades por cesta, 4 cestas disponíveis)")
    print()
    
    for quantidade in quantidades_teste:
        bateladas = quantidade // 36  # Quantas bateladas de 36 (4 cestas × 9)
        restante = quantidade % 36
        
        if restante > 0:
            bateladas += 1
            
        print(f"   {quantidade:2d} coxinhas → {bateladas} bateladas")
        
        # Detalhar bateladas
        unidades_processadas = 0
        for i in range(1, bateladas + 1):
            if i < bateladas:
                unidades_batelada = 36
            else:
                unidades_batelada = quantidade - unidades_processadas
            
            cestas_usadas = min(4, (unidades_batelada + 8) // 9)  # Arredonda para cima
            print(f"      Batelada {i}: {unidades_batelada} unidades em {cestas_usadas} cestas")
            unidades_processadas += unidades_batelada
        
        print()


if __name__ == "__main__":
    main()
    
    # Para demonstrar sistema de bateladas, descomente:
    # exemplo_diferentes_quantidades()