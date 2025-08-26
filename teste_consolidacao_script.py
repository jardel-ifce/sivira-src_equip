import sys
import os
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from services.consolidacao.consolidador_simples import ConsolidadorSimples
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


class TesteConsolidacaoSubprodutos:
    """
    Classe para testar especificamente o sistema de consolidação de subprodutos.
    Usa apenas Pão Hambúrguer e Pão de Forma que compartilham o subproduto massa_suave.
    """
    
    def __init__(self, usar_consolidacao=True):
        self.usar_consolidacao = usar_consolidacao
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.log_filename = None
        self.mapeamento_produtos = {
            "Pão Hambúrguer": 1002,
            "Pão de Forma": 1003
        }
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        consolidacao_status = "COM_CONSOLIDACAO" if self.usar_consolidacao else "SEM_CONSOLIDACAO"
        self.log_filename = f'logs/teste_consolidacao_{consolidacao_status}_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print("TESTE DE CONSOLIDAÇÃO DE SUBPRODUTOS - MASSA SUAVE")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Modo: {'COM CONSOLIDAÇÃO' if self.usar_consolidacao else 'SEM CONSOLIDAÇÃO'}")
        print("Produtos testados: Pão Hambúrguer + Pão de Forma")
        print("Subproduto compartilhado: massa_suave (ID: 2002)")
        print("=" * 80)
        print()

    def escrever_rodape_log(self, sucesso=True):
        """Escreve rodapé final no log"""
        print("=" * 80)
        if sucesso:
            print("EXECUÇÃO CONCLUÍDA COM SUCESSO!")
            if self.usar_consolidacao:
                print("Verifique os logs para confirmar a consolidação da massa_suave")
            else:
                print("Massa_suave foi produzida separadamente para cada pedido")
        else:
            print("EXECUÇÃO FINALIZADA COM ERROS!")
        print(f"Log salvo em: {self.log_filename}")
        print("=" * 80)

    # =============================================================================
    #                      CONFIGURAÇÃO DO AMBIENTE
    # =============================================================================

    def inicializar_almoxarifado(self):
        """Carrega e inicializa o almoxarifado"""
        print("Carregando itens do almoxarifado...")
        
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
        
        print("Almoxarifado carregado com sucesso!")
        print()

    # =============================================================================
    #                       CRIAÇÃO DE PEDIDOS PARA TESTE
    # =============================================================================

    def criar_pedidos_teste_consolidacao(self):
        """
        Cria pedidos específicos para testar consolidação de massa_suave.
        Pedidos com quantidades que resultam em diferentes necessidades de massa_suave.
        """
        print("Criando pedidos para teste de consolidação...")
        
        status_consolidacao = "COM" if self.usar_consolidacao else "SEM"
        print(f"Modo: {status_consolidacao} consolidação de subprodutos")
        
        self.pedidos = []
        
        # Data base para os cálculos
        data_base = datetime(2025, 6, 26, 12, 0)  # Meio-dia como prazo
        
        # Configurações dos pedidos de teste
        # Essas quantidades irão gerar diferentes quantidades de massa_suave
        configuracoes_pedidos = [
            {"produto": "Pão de Forma", "quantidade": 60, "hora_fim": 12, "id_pedido": 101},
            {"produto": "Pão Hambúrguer", "quantidade": 60, "hora_fim": 12, "id_pedido": 102},
        ]
        
        for config in configuracoes_pedidos:
            print(f"   Criando pedido {config['id_pedido']}: {config['produto']} - {config['quantidade']} unidades...")
            
            try:
                # Calcular datas de início e fim da jornada
                fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
                inicio_jornada = fim_jornada - timedelta(days=3)  # 1 dia de janela para teste
                
                # Obter ID do produto
                id_produto = self.mapeamento_produtos.get(config['produto'])
                if id_produto is None:
                    print(f"   Produto '{config['produto']}' não encontrado no mapeamento!")
                    continue
                
                # Criar pedido COM OU SEM consolidação baseado no parâmetro
                pedido = PedidoDeProducao(
                    id_ordem=1,
                    id_pedido=config['id_pedido'],
                    id_produto=id_produto,
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=config['quantidade'],
                    inicio_jornada=inicio_jornada,
                    fim_jornada=fim_jornada,
                    todos_funcionarios=funcionarios_disponiveis,
                    gestor_almoxarifado=self.gestor_almoxarifado,
                    consolidar_subprodutos=self.usar_consolidacao  # PARÂMETRO CHAVE
                )
                
                pedido.montar_estrutura()
                self.pedidos.append(pedido)
                
                # Calcular massa_suave necessária para este pedido (estimativa)
                if pedido.ficha_tecnica_modular:
                    estimativas = pedido.ficha_tecnica_modular.calcular_quantidade_itens()
                    massa_suave_necessaria = 0
                    for item_dict, quantidade in estimativas:
                        if (item_dict.get("tipo_item") == "SUBPRODUTO" and 
                            item_dict.get("id_ficha_tecnica") == 2002):
                            massa_suave_necessaria = quantidade
                            break
                    
                    print(f"   Pedido {config['id_pedido']} criado: {config['produto']} ({config['quantidade']} uni)")
                    print(f"   Massa_suave necessária: {massa_suave_necessaria:.1f}g")
                    print(f"   Consolidação: {'HABILITADA' if self.usar_consolidacao else 'DESABILITADA'}")
                
            except RuntimeError as e:
                print(f"   Falha ao criar pedido {config['id_pedido']}: {e}")
        
        print(f"\nTotal de {len(self.pedidos)} pedidos criados para teste!")
        
        # Calcular total de massa_suave se NÃO houver consolidação
        total_massa_suave = 0
        for pedido in self.pedidos:
            if pedido.ficha_tecnica_modular:
                estimativas = pedido.ficha_tecnica_modular.calcular_quantidade_itens()
                for item_dict, quantidade in estimativas:
                    if (item_dict.get("tipo_item") == "SUBPRODUTO" and 
                        item_dict.get("id_ficha_tecnica") == 2002):
                        total_massa_suave += quantidade
        
        print(f"Total massa_suave necessária (individual): {total_massa_suave:.1f}g")
        if self.usar_consolidacao:
            print("Com consolidação: será produzida apenas UMA VEZ em quantidade total")
        else:
            print("Sem consolidação: será produzida SEPARADAMENTE para cada pedido")
        print()

    def aplicar_consolidacao_se_habilitada(self):
        """Aplica consolidação de subprodutos se estiver habilitada"""
        if not self.usar_consolidacao:
            print("Consolidação DESABILITADA - pulando esta etapa")
            print()
            return
        
        print("Aplicando consolidação de subprodutos...")
        
        # Verificar pedidos elegíveis para consolidação
        pedidos_com_consolidacao = [p for p in self.pedidos if p.consolidar_subprodutos]
        print(f"Pedidos elegíveis para consolidação: {len(pedidos_com_consolidacao)}")
        
        # Processar consolidação
        ConsolidadorSimples.processar_pedidos(self.pedidos)
        
        # Verificar resultados da consolidação
        for pedido in self.pedidos:
            if pedido.lotes_consolidados:
                print(f"   Pedido {pedido.id_pedido}: {pedido.lotes_consolidados}")
        
        # Obter e exibir resumo
        resumo = ConsolidadorSimples.obter_resumo_consolidacoes(self.pedidos)
        print(f"\nResumo da consolidação:")
        print(f"   Subprodutos consolidados: {resumo['total_subprodutos_consolidados']}")
        print(f"   Atividades economizadas: {resumo['total_atividades_economizadas']}")
        print(f"   Detalhes: {resumo['detalhes_por_subproduto']}")
        print()

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_teste(self):
        """Executa os pedidos de teste"""
        print("Executando pedidos de teste...")
        
        for idx, pedido in enumerate(self.pedidos, 1):
            # Identificar nome do produto
            nome_produto = next((nome for nome, id_prod in self.mapeamento_produtos.items() 
                               if id_prod == pedido.id_produto), f"Produto {pedido.id_produto}")
            
            print(f"   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})")
            print(f"   {nome_produto} - {pedido.quantidade} unidades")
            
            # Mostrar status de consolidação
            if hasattr(pedido, 'lotes_consolidados') and pedido.lotes_consolidados:
                for id_sub, qtd in pedido.lotes_consolidados.items():
                    if qtd > 0:
                        print(f"   PEDIDO MESTRE: produzirá {qtd}g de subproduto {id_sub}")
                    elif qtd == 0:
                        print(f"   PEDIDO DEPENDENTE: usará subproduto {id_sub} já produzido")
            
            try:
                # Gerar comanda de reserva
                gerar_comanda_reserva(
                    id_ordem=pedido.id_ordem,
                    id_pedido=pedido.id_pedido,
                    ficha=pedido.ficha_tecnica_modular,
                    gestor=self.gestor_almoxarifado,
                    data_execucao=pedido.inicio_jornada
                )
                
                # Criar atividades modulares
                pedido.criar_atividades_modulares_necessarias()
                
                # Mostrar atividades criadas
                print(f"   Atividades criadas: {len(pedido.atividades_modulares)}")
                
                # Contar atividades de massa_suave
                atividades_massa_suave = 0
                for atividade in pedido.atividades_modulares:
                    if (hasattr(atividade, 'nome_item') and 
                        'massa_suave' in atividade.nome_item.lower()):
                        atividades_massa_suave += 1
                        if hasattr(atividade, 'eh_lote_consolidado') and atividade.eh_lote_consolidado:
                            print(f"   LOTE CONSOLIDADO: {atividade.nome_atividade} ({atividade.quantidade}g)")
                        else:
                            print(f"   Atividade individual: {atividade.nome_atividade} ({atividade.quantidade}g)")
                
                if atividades_massa_suave == 0:
                    print(f"   Nenhuma atividade de massa_suave (já processada por outro pedido)")
                
                # Executar atividades em ordem
                pedido.executar_atividades_em_ordem()
                
                print(f"   Pedido {pedido.id_pedido} ({nome_produto}) executado com sucesso!")
                
            except RuntimeError as e:
                print(f"   Falha ao processar o pedido {pedido.id_pedido} ({nome_produto}): {e}")
                
            print()

    def analisar_resultados_consolidacao(self):
        """Analisa e exibe os resultados da consolidação"""
        print("=" * 60)
        print("ANÁLISE DOS RESULTADOS")
        print("=" * 60)
        
        if not self.usar_consolidacao:
            print("Modo SEM consolidação:")
            print("- Cada pedido produziu sua própria massa_suave")
            print("- Atividades de massa_suave foram executadas separadamente")
            total_atividades_massa = sum(1 for pedido in self.pedidos 
                                       for atividade in pedido.atividades_modulares
                                       if hasattr(atividade, 'nome_item') and 
                                       'massa_suave' in atividade.nome_item.lower())
            print(f"- Total de atividades de massa_suave: {total_atividades_massa}")
        else:
            print("Modo COM consolidação:")
            
            # Contar pedidos mestres e dependentes
            pedidos_mestre = 0
            pedidos_dependentes = 0
            total_consolidado = 0
            
            for pedido in self.pedidos:
                resumo = pedido.obter_resumo_pedido()
                if resumo.get('eh_pedido_mestre'):
                    pedidos_mestre += 1
                if resumo.get('eh_pedido_dependente'):
                    pedidos_dependentes += 1
                    
                if hasattr(pedido, 'lotes_consolidados'):
                    for qtd in pedido.lotes_consolidados.values():
                        if qtd > 0:
                            total_consolidado += qtd
            
            print(f"- Pedidos mestres (produzem lote): {pedidos_mestre}")
            print(f"- Pedidos dependentes (usam lote): {pedidos_dependentes}")
            print(f"- Quantidade total consolidada: {total_consolidado}g")
            
            # Contar atividades de massa_suave realmente executadas
            atividades_executadas = 0
            for pedido in self.pedidos:
                for atividade in pedido.atividades_modulares:
                    if (hasattr(atividade, 'nome_item') and 
                        'massa_suave' in atividade.nome_item.lower()):
                        atividades_executadas += 1
            
            print(f"- Atividades de massa_suave executadas: {atividades_executadas}")
            
            if atividades_executadas == 1:
                print("✅ CONSOLIDAÇÃO BEM-SUCEDIDA: Apenas 1 atividade de massa_suave foi executada!")
            else:
                print("❌ Possível falha na consolidação: múltiplas atividades executadas")
        
        print()

    # =============================================================================
    #                       FLUXO PRINCIPAL
    # =============================================================================

    def executar_teste_completo(self):
        """Executa o teste completo de consolidação"""
        try:
            print(f"INICIANDO TESTE DE CONSOLIDAÇÃO DE SUBPRODUTOS")
            print(f"Modo: {'COM' if self.usar_consolidacao else 'SEM'} consolidação")
            print()
            
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Criação dos pedidos de teste
            self.criar_pedidos_teste_consolidacao()
            
            # Fase 3: Aplicar consolidação (se habilitada)
            self.aplicar_consolidacao_se_habilitada()
            
            # Fase 4: Execução
            self.executar_pedidos_teste()
            
            # Fase 5: Análise dos resultados
            self.analisar_resultados_consolidacao()
            
            return True
            
        except Exception as e:
            print("=" * 80)
            print(f"ERRO CRÍTICO NA EXECUÇÃO: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Função principal que executa testes COM e SEM consolidação para comparação.
    """
    # Teste 1: SEM consolidação
    print("🔵 EXECUTANDO TESTE SEM CONSOLIDAÇÃO")
    sistema_sem = TesteConsolidacaoSubprodutos(usar_consolidacao=False)
    log_sem = sistema_sem.configurar_log()
    
    with open(log_sem, 'w', encoding='utf-8') as log_file:
        tee = TeeOutput(log_file)
        sys.stdout = tee
        
        sistema_sem.escrever_cabecalho_log()
        try:
            sucesso_sem = sistema_sem.executar_teste_completo()
            sistema_sem.escrever_rodape_log(sucesso_sem)
        finally:
            sys.stdout = tee.stdout
    
    print(f"Log SEM consolidação salvo em: {log_sem}")
    print()
    
    # Teste 2: COM consolidação  
    print("🟢 EXECUTANDO TESTE COM CONSOLIDAÇÃO")
    sistema_com = TesteConsolidacaoSubprodutos(usar_consolidacao=True)
    log_com = sistema_com.configurar_log()
    
    with open(log_com, 'w', encoding='utf-8') as log_file:
        tee = TeeOutput(log_file)
        sys.stdout = tee
        
        sistema_com.escrever_cabecalho_log()
        try:
            sucesso_com = sistema_com.executar_teste_completo()
            sistema_com.escrever_rodape_log(sucesso_com)
        finally:
            sys.stdout = tee.stdout
    
    print(f"Log COM consolidação salvo em: {log_com}")
    print()
    
    # Resumo final
    print("=" * 80)
    print("RESUMO COMPARATIVO")
    print("=" * 80)
    print(f"Teste SEM consolidação: {'✅ SUCESSO' if sucesso_sem else '❌ FALHA'}")
    print(f"Teste COM consolidação: {'✅ SUCESSO' if sucesso_com else '❌ FALHA'}")
    print()
    print("Compare os logs para verificar:")
    print("- SEM: Atividades de massa_suave criadas em ambos os pedidos")  
    print("- COM: Atividade de massa_suave criada apenas no pedido mestre")
    print()
    print(f"Log SEM consolidação: {log_sem}")
    print(f"Log COM consolidação: {log_com}")


if __name__ == "__main__":
    main()