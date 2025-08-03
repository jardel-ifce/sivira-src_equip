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
from utils.logs.logger_factory import setup_logger

# Logger para o teste
logger = setup_logger('TesteSistemaProducao')


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
        print(f"🚀 LOG DE EXECUÇÃO DO SISTEMA DE PRODUÇÃO")
        print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        print()

    def escrever_rodape_log(self, sucesso=True):
        """Escreve rodapé final no log"""
        print("=" * 80)
        if sucesso:
            print("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("❌ EXECUÇÃO FINALIZADA COM ERROS!")
        print(f"📄 Log completo salvo em: {self.log_filename}")
        print("=" * 80)

    # =============================================================================
    #                      CONFIGURAÇÃO DO AMBIENTE
    # =============================================================================

    def inicializar_almoxarifado(self):
        """
        Carrega e inicializa o almoxarifado com todos os itens necessários.
        Limpa comandas e logs anteriores.
        """
        logger.info("🔄 Iniciando carregamento do almoxarifado...")
        print("🔄 Carregando itens do almoxarifado...")
        
        try:
            # Carregar itens do arquivo JSON
            itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
            logger.info(f"📦 {len(itens)} itens carregados do arquivo JSON")
            
            # Limpar dados anteriores
            print("🧹 Limpando dados anteriores...")
            apagar_todas_as_comandas()
            limpar_todos_os_logs()
            logger.info("🧹 Limpeza de dados concluída")
            
            # Inicializar almoxarifado
            self.almoxarifado = Almoxarifado()
            itens_adicionados = 0
            
            for item in itens:
                try:
                    self.almoxarifado.adicionar_item(item)
                    itens_adicionados += 1
                except Exception as e:
                    logger.error(f"❌ Erro ao adicionar item {item.id_item}: {e}")
                    continue
            
            # Criar gestor
            self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)
            
            # Validar integridade
            problemas = self.gestor_almoxarifado.validar_almoxarifado()
            if problemas:
                logger.warning(f"⚠️ {len(problemas)} problemas encontrados no almoxarifado")
            
            logger.info(f"✅ Almoxarifado inicializado: {itens_adicionados} itens carregados")
            print(f"✅ Almoxarifado carregado com sucesso! ({itens_adicionados} itens)")
            print()
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar almoxarifado: {e}")
            raise

    def adicionar_estoque_de_teste(self):
        """
        Adiciona estoque de teste para alguns itens para demonstrar 
        a funcionalidade de verificação de estoque.
        """
        logger.info("🔄 Adicionando estoque de teste...")
        print("🔄 Adicionando estoque de teste...")
        
        try:
            # Adicionar estoque para alguns SUBPRODUTOS e INSUMOS para teste
            itens_com_estoque = [
                # SUBPRODUTOS com estoque SUFICIENTE para demonstrar otimização
                {"id_item": 2001, "quantidade": 0, "descricao": "massa_crocante"},  # Estoque abundante
                {"id_item": 2002, "quantidade": 5000, "descricao": "massa_suave"},  
                {"id_item": 2006, "quantidade": 20000, "descricao": "carne_de_sol_refogada"},
                {"id_item": 2013, "quantidade": 15000, "descricao": "creme_chantilly"},
                
                # INSUMOS básicos
                {"id_item": 1, "quantidade": 25000, "descricao": "acucar_refinado"},
                {"id_item": 2, "quantidade": 30000, "descricao": "agua"},
                {"id_item": 16, "quantidade": 80000, "descricao": "farinha_de_trigo_s_ferm"},
                {"id_item": 17, "quantidade": 2000, "descricao": "fermento_biologico_seco"},
                {"id_item": 25, "quantidade": 15000, "descricao": "manteiga_s_sal"},
                {"id_item": 33, "quantidade": 12000, "descricao": "ovo_de_galinha"},
                {"id_item": 39, "quantidade": 2000, "descricao": "sal_refinado"},
            ]
            
            itens_atualizados = 0
            
            for item_estoque in itens_com_estoque:
                item = self.gestor_almoxarifado.obter_item_por_id(item_estoque["id_item"])
                if item:
                    # Usar o estoque atual + adicionar mais para simular reabastecimento
                    item.estoque_atual = item_estoque["quantidade"]
                    itens_atualizados += 1
                    
                    logger.debug(
                        f"📦 Estoque atualizado: {item.descricao} = {item_estoque['quantidade']} "
                        f"(Política: {item.politica_producao.value})"
                    )
                    print(f"   ✅ {item.descricao}: {item_estoque['quantidade']} unidades")
                else:
                    logger.warning(f"⚠️ Item {item_estoque['id_item']} não encontrado")
            
            logger.info(f"✅ Estoque de teste adicionado: {itens_atualizados} itens atualizados")
            print(f"✅ Estoque de teste configurado para {itens_atualizados} itens!")
            print()
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar estoque de teste: {e}")
            raise

    def exibir_resumo_almoxarifado(self):
        """Exibe um resumo do estado atual do almoxarifado"""
        try:
            print("📊 RESUMO DO ALMOXARIFADO:")
            print("-" * 50)
            
            # Obter estatísticas gerais
            stats = self.almoxarifado.estatisticas_almoxarifado()
            
            print(f"📦 Total de itens: {stats['total_itens']}")
            print(f"⚠️ Itens abaixo do mínimo: {stats['itens_abaixo_minimo']}")
            print(f"🚨 Itens sem estoque: {stats['itens_sem_estoque']}")
            print(f"📈 Percentual crítico: {stats['percentual_critico']:.1f}%")
            
            print("\n📋 Distribuição por tipo:")
            for tipo, qtd in stats['distribuicao_por_tipo'].items():
                print(f"   {tipo}: {qtd} itens")
            
            print("\n🏷️ Distribuição por política:")
            for politica, qtd in stats['distribuicao_por_politica'].items():
                print(f"   {politica}: {qtd} itens")
            
            # Verificar itens críticos
            itens_criticos = self.gestor_almoxarifado.verificar_estoque_minimo()
            if itens_criticos:
                print(f"\n⚠️ ITENS CRÍTICOS ({len(itens_criticos)}):")
                for item in itens_criticos[:5]:  # Mostrar apenas os primeiros 5
                    print(f"   - {item['descricao']}: {item['estoque_atual']}/{item['estoque_min']} {item['unidade']}")
                if len(itens_criticos) > 5:
                    print(f"   ... e mais {len(itens_criticos) - 5} itens")
            
            print()
            
        except Exception as e:
            logger.error(f"❌ Erro ao exibir resumo do almoxarifado: {e}")

    # =============================================================================
    #                       CRIAÇÃO DE PEDIDOS
    # =============================================================================

    def criar_pedidos_de_producao(self):
        """
        Cria os pedidos de produção conforme configuração.
        Configuração expandida para melhor demonstração.
        """
        logger.info("🔄 Iniciando criação de pedidos de produção...")
        print("🔄 Criando pedidos de produção...")
        
        self.pedidos = []
        
        # Configurações dos pedidos (expandidas para demonstração)
        configuracoes_pedidos = [
            {
                'id_pedido': 1,
                'id_produto': 1001,  # pao_frances
                'quantidade': 450,
                'descricao': 'Pão francês'
            },
            # Adicione mais pedidos aqui para testes mais complexos
            # {
            #     'id_pedido': 2,
            #     'id_produto': 1063,  # tartelete_de_morango
            #     'quantidade': 24,
            #     'descricao': 'Tartelete de morango'
            # },
        ]
        
        pedidos_criados = 0
        
        for config in configuracoes_pedidos:
            logger.info(f"🔄 Processando pedido {config['id_pedido']} ({config['descricao']})...")
            print(f"   📋 Processando pedido {config['id_pedido']}: {config['descricao']} (qtd: {config['quantidade']})...")
            
            try:
                # Validar gestor de almoxarifado
                if not self.gestor_almoxarifado:
                    raise ValueError("Gestor de almoxarifado não inicializado")
                
                pedido = PedidoDeProducao(
                    id_ordem=1,  # Fixo para testes
                    id_pedido=config['id_pedido'],
                    id_produto=config['id_produto'],
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=config['quantidade'],
                    inicio_jornada=datetime(2025, 6, 23, 8, 0),
                    fim_jornada=datetime(2025, 6, 24, 18, 0),
                    todos_funcionarios=funcionarios_disponiveis,
                    gestor_almoxarifado=self.gestor_almoxarifado  # Passar gestor otimizado
                )
                
                # Montar estrutura com validação
                pedido.montar_estrutura()
                
                # Verificar disponibilidade de estoque
                try:
                    pedido.verificar_disponibilidade_estoque(pedido.inicio_jornada)
                    logger.info(f"✅ Estoque verificado para pedido {config['id_pedido']}")
                except Exception as e:
                    logger.warning(f"⚠️ Problemas de estoque no pedido {config['id_pedido']}: {e}")
                    # Continuar mesmo com problemas de estoque para demonstração
                
                self.pedidos.append(pedido)
                pedidos_criados += 1
                
                logger.info(f"✅ Pedido {config['id_pedido']} criado com sucesso!")
                print(f"   ✅ Pedido {config['id_pedido']} criado com sucesso!")
                
            except Exception as e:
                logger.error(f"❌ Falha ao criar pedido {config['id_pedido']}: {e}")
                print(f"   ❌ Falha ao criar pedido {config['id_pedido']}: {e}")
                continue
        
        logger.info(f"✅ Criação concluída: {pedidos_criados}/{len(configuracoes_pedidos)} pedidos criados")
        print(f"✅ Total: {pedidos_criados}/{len(configuracoes_pedidos)} pedidos criados com sucesso!")
        print()

    def ordenar_pedidos_por_prioridade(self):
        """Ordena pedidos baseado em restrições e prioridades"""
        logger.info("🔄 Ordenando pedidos por restrições...")
        print("🔄 Ordenando pedidos por restrições...")
        
        try:
            pedidos_antes = len(self.pedidos)
            self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
            pedidos_depois = len(self.pedidos)
            
            if pedidos_antes != pedidos_depois:
                logger.warning(f"⚠️ Número de pedidos mudou durante ordenação: {pedidos_antes} → {pedidos_depois}")
            
            logger.info(f"✅ {pedidos_depois} pedidos ordenados com sucesso!")
            print(f"✅ {pedidos_depois} pedidos ordenados!")
            
            # Exibir ordem dos pedidos
            if self.pedidos:
                print("📋 Ordem de execução:")
                for i, pedido in enumerate(self.pedidos, 1):
                    resumo = pedido.obter_resumo_pedido()
                    print(f"   {i}. Pedido {pedido.id_pedido} - Produto {pedido.id_produto} (qtd: {pedido.quantidade})")
            
            print()
            
        except Exception as e:
            logger.error(f"❌ Erro ao ordenar pedidos: {e}")
            raise

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_ordenados(self):
        """
        Executa todos os pedidos em ordem de prioridade.
        Para cada pedido: gera comanda, mostra estrutura, cria atividades e executa.
        """
        total_pedidos = len(self.pedidos)
        logger.info(f"🚀 Iniciando execução de {total_pedidos} pedidos...")
        print(f"🚀 Executando {total_pedidos} pedidos em ordem de prioridade...")
        print()
        
        pedidos_executados = 0
        pedidos_com_erro = 0
        
        for idx, pedido in enumerate(self.pedidos, 1):
            print(f"📋 EXECUTANDO PEDIDO {idx}/{total_pedidos} (ID: {pedido.id_pedido})")
            print("-" * 60)
            
            logger.info(f"🔄 Iniciando execução do pedido {pedido.id_pedido} ({idx}/{total_pedidos})")
            
            try:
                # 1. Gerar comanda de reserva
                print("📋 Gerando comanda de reserva...")
                pedido.gerar_comanda_de_reserva(pedido.inicio_jornada)
                logger.info(f"✅ Comanda gerada para pedido {pedido.id_pedido}")
                
                # 2. Mostrar estrutura da ficha técnica
                print("📊 Exibindo estrutura da ficha técnica...")
                pedido.mostrar_estrutura()
                
                # 3. Criar atividades modulares (com verificação de estoque otimizada)
                print("🔧 Criando atividades modulares...")
                pedido.criar_atividades_modulares_necessarias()
                
                total_atividades = len(pedido.atividades_modulares)
                logger.info(f"🔧 {total_atividades} atividades criadas para pedido {pedido.id_pedido}")
                print(f"   ✅ {total_atividades} atividades criadas")
                
                # 4. Executar atividades em ordem
                if total_atividades > 0:
                    print("⚙️ Executando atividades em ordem...")
                    pedido.executar_atividades_em_ordem()
                    
                    # Obter resumo da execução
                    resumo = pedido.obter_resumo_pedido()
                    atividades_alocadas = resumo['atividades_alocadas']
                    
                    print(f"   ✅ {atividades_alocadas}/{total_atividades} atividades alocadas com sucesso")
                    
                    if resumo['inicio_real'] and resumo['fim_real']:
                        inicio = datetime.fromisoformat(resumo['inicio_real'])
                        fim = datetime.fromisoformat(resumo['fim_real'])
                        print(f"   ⏰ Período real: {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}")
                else:
                    print("   ℹ️ Nenhuma atividade necessária (estoque suficiente)")
                
                # 5. Exibir histórico (opcional - comentado para logs mais limpos)
                # print("📊 Exibindo histórico de funcionários...")
                # pedido.exibir_historico_de_funcionarios()
                
                pedidos_executados += 1
                logger.info(f"✅ Pedido {pedido.id_pedido} executado com sucesso!")
                print(f"✅ Pedido {pedido.id_pedido} executado com sucesso!")
                
            except Exception as e:
                pedidos_com_erro += 1
                logger.error(f"❌ Falha ao processar pedido {pedido.id_pedido}: {e}")
                print(f"❌ Falha ao processar pedido {pedido.id_pedido}: {e}")
                
                # Tentar rollback
                try:
                    pedido.rollback_pedido()
                    logger.info(f"🔄 Rollback executado para pedido {pedido.id_pedido}")
                except Exception as rollback_error:
                    logger.error(f"❌ Erro no rollback do pedido {pedido.id_pedido}: {rollback_error}")
                
                # Continuar com próximos pedidos
                
            print()

        # Resumo final da execução
        print("=" * 60)
        print("📊 RESUMO DA EXECUÇÃO:")
        print(f"✅ Pedidos executados com sucesso: {pedidos_executados}")
        print(f"❌ Pedidos com erro: {pedidos_com_erro}")
        print(f"📋 Total processado: {pedidos_executados + pedidos_com_erro}/{total_pedidos}")
        
        if pedidos_com_erro == 0:
            print("🎉 Todos os pedidos foram executados com sucesso!")
        
        logger.info(
            f"📊 Execução concluída: {pedidos_executados} sucessos, {pedidos_com_erro} erros"
        )

    # =============================================================================
    #                       FLUXO PRINCIPAL
    # =============================================================================

    def executar_teste_completo(self):
        """
        Executa o teste completo do sistema de produção.
        Fluxo: Almoxarifado → Estoque Teste → Resumo → Pedidos → Ordenação → Execução
        """
        try:
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Adicionar estoque de teste
            self.adicionar_estoque_de_teste()
            
            # Fase 3: Exibir resumo do almoxarifado
            self.exibir_resumo_almoxarifado()
            
            # Fase 4: Criação dos pedidos
            self.criar_pedidos_de_producao()
            
            # Fase 5: Ordenação por prioridade
            self.ordenar_pedidos_por_prioridade()
            
            # Fase 6: Execução
            self.executar_pedidos_ordenados()
            
            logger.info("🎉 Teste completo executado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
            print("=" * 80)
            print(f"❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")
            print("=" * 80)
            
            import traceback
            traceback.print_exc()
            return False

    def executar_diagnosticos_pos_execucao(self):
        """Executa diagnósticos após a execução para análise"""
        try:
            print("\n🔍 EXECUTANDO DIAGNÓSTICOS PÓS-EXECUÇÃO:")
            print("-" * 50)
            
            # 1. Validar integridade do almoxarifado
            problemas = self.gestor_almoxarifado.validar_almoxarifado()
            if problemas:
                print(f"⚠️ {len(problemas)} problemas de integridade encontrados:")
                for problema in problemas[:3]:  # Mostrar apenas os primeiros 3
                    print(f"   - {problema}")
                if len(problemas) > 3:
                    print(f"   ... e mais {len(problemas) - 3} problemas")
            else:
                print("✅ Integridade do almoxarifado validada")
            
            # 2. Resumo dos pedidos
            print(f"\n📋 RESUMO DOS PEDIDOS:")
            for pedido in self.pedidos:
                resumo = pedido.obter_resumo_pedido()
                status = f"{resumo['atividades_alocadas']}/{resumo['total_atividades']} atividades"
                print(f"   Pedido {resumo['id_pedido']}: {status}")
            
            # 3. Estatísticas finais do almoxarifado
            stats = self.almoxarifado.estatisticas_almoxarifado()
            print(f"\n📊 ESTATÍSTICAS FINAIS:")
            print(f"   Itens críticos: {stats['itens_abaixo_minimo']}")
            print(f"   Percentual crítico: {stats['percentual_critico']:.1f}%")
            
            logger.info("🔍 Diagnósticos pós-execução concluídos")
            
        except Exception as e:
            logger.error(f"❌ Erro nos diagnósticos: {e}")


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
            
            # Executar diagnósticos
            if sucesso:
                sistema.executar_diagnosticos_pos_execucao()
            
            # Escrever rodapé
            sistema.escrever_rodape_log(sucesso)
            
        except KeyboardInterrupt:
            print("\n⚠️ Execução interrompida pelo usuário")
            sistema.escrever_rodape_log(False)
        except Exception as e:
            logger.error(f"❌ Erro não tratado: {e}")
            sistema.escrever_rodape_log(False)
            raise
        
        finally:
            # Restaurar stdout original
            sys.stdout = tee.stdout
            print(f"\n📄 Log completo de execução salvo em: {log_filename}")


if __name__ == "__main__":
    main()