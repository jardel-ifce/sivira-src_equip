import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs, limpar_logs_erros, limpar_logs_inicializacao
from services.gestores.comandas.gestor_comandas import gerar_comanda_reserva
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem

# IMPORTAÇÕES PARA AGRUPAMENTO
from services.consolidacao.consolidador_simples import ConsolidadorSimples
from models.atividades.agrupador_subprodutos import AgrupadorSubprodutos


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


class TesteSistemaProducaoAgrupado:
    """
    Sistema de produção de coxinhas COM AGRUPAMENTO DE SUBPRODUTOS.
    
    Funcionalidades principais:
    - Produção sequencial de coxinhas
    - AGRUPAMENTO/CONSOLIDAÇÃO de subprodutos (massa para frituras)
    - Economia de uso de equipamentos
    - Otimização de recursos entre pedidos
    
    🎯 FOCO: Consolidar "massa para frituras" quando múltiplas coxinhas precisam
    """
    
    def __init__(self, tipo_agrupamento="simples"):
        """
        Inicializa o sistema de produção com agrupamento.
        
        Args:
            tipo_agrupamento: "simples" ou "avancado"
                - simples: usa ConsolidadorSimples
                - avancado: usa AgrupadorSubprodutos
        """
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.log_filename = None
        self.tipo_agrupamento = tipo_agrupamento
        
        # Configurar agrupador baseado no tipo
        if tipo_agrupamento == "avancado":
            self.agrupador = AgrupadorSubprodutos(tolerancia_temporal=timedelta(minutes=30))
        else:
            self.agrupador = None  # ConsolidadorSimples é estático
        
        self.mapeamento_produtos = {
            "Coxinha de Frango": 1055,
            "Coxinha de Carne de Sol": 1069,
            "Coxinha de Camarão": 1070,
            "Coxinha de Queijos Finos": 1071
        }
        
        # Estatísticas da execução
        self.estatisticas_execucao = {}
        self.estatisticas_agrupamento = {}
        
    def configurar_log(self):
        """Configura o sistema de logging com timestamp único"""
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f'logs/execucao_coxinhas_agrupado_{self.tipo_agrupamento}_{timestamp}.log'
        return self.log_filename

    def escrever_cabecalho_log(self):
        """Escreve cabeçalho informativo no log"""
        print("=" * 80)
        print(f"LOG DE EXECUÇÃO - SISTEMA DE PRODUÇÃO COXINHAS COM AGRUPAMENTO")
        print(f"Tipo de agrupamento: {self.tipo_agrupamento.upper()}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        print()

    def escrever_rodape_log(self, sucesso=True):
        """Escreve rodapé final no log"""
        print("=" * 80)
        if sucesso:
            print("🎉 EXECUÇÃO COM AGRUPAMENTO CONCLUÍDA COM SUCESSO!")
            
            # Mostra estatísticas de agrupamento se disponíveis
            if self.estatisticas_agrupamento:
                self._imprimir_estatisticas_agrupamento()
                
        else:
            print("❌ EXECUÇÃO COM AGRUPAMENTO FINALIZADA COM ERROS!")
        
        print(f"📄 Log salvo em: {self.log_filename}")
        print("=" * 80)

    def _imprimir_estatisticas_agrupamento(self):
        """Imprime estatísticas do agrupamento"""
        stats = self.estatisticas_agrupamento
        
        print(f"\n📊 ESTATÍSTICAS DE AGRUPAMENTO ({self.tipo_agrupamento.upper()}):")
        print(f"   Consolidações realizadas: {stats.get('consolidacoes_realizadas', 0)}")
        print(f"   Economia de equipamentos: {stats.get('economia_equipamentos', 0)}")
        print(f"   Pedidos afetados: {len(stats.get('pedidos_afetados', []))}")
        
        if stats.get('detalhes'):
            print("   Detalhes das consolidações:")
            for detalhe in stats['detalhes']:
                print(f"     - {detalhe.get('item', 'Item')}: {detalhe.get('quantidade_total', 0)}g")

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
    #                       CRIAÇÃO DE PEDIDOS COM AGRUPAMENTO
    # =============================================================================

    def criar_pedidos_de_producao(self):
        """
        Cria pedidos de produção de coxinhas COM HABILITAÇÃO DE AGRUPAMENTO.
        
        🎯 DIFERENCIAL: Configura pedidos para permitir consolidação de subprodutos
        """
        print("🔄 Criando pedidos de produção de coxinhas COM AGRUPAMENTO...")
        self.pedidos = []
        
        # Data base para os cálculos
        data_base = datetime(2025, 6, 26)
        
        # Configurações dos pedidos de coxinhas (APENAS 2 PEDIDOS com janelas sincronizadas)
        configuracoes_pedidos = [
            # PEDIDOS SINCRONIZADOS - Janelas idênticas para garantir consolidação
            {"produto": "Coxinha de Frango", "quantidade": 15, "hora_fim": 8, "inicio_offset": 0},      # Janela: 23/06 08:00 → 26/06 08:00
            {"produto": "Coxinha de Carne de Sol", "quantidade": 10, "hora_fim": 8, "inicio_offset": 0}, # Janela: 23/06 08:00 → 26/06 08:00 (IGUAL)
        ]
        
        id_pedido_counter = 1
        
        for config in configuracoes_pedidos:
            print(f"   Processando pedido {id_pedido_counter}: {config['produto']} - {config['quantidade']} unidades...")
            
            try:
                # Calcular datas com offsets para criar sobreposições
                fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
                inicio_jornada = fim_jornada - timedelta(days=3) + timedelta(minutes=config['inicio_offset'])
                
                print(f"   📅 Configuração temporal (com offset para agrupamento):")
                print(f"      Deadline: {fim_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Início: {inicio_jornada.strftime('%d/%m %H:%M')}")
                print(f"      Offset: {config['inicio_offset']}min (para sobreposição)")
                
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
                
                # 🎯 CONFIGURAÇÃO CHAVE: Habilitar consolidação de subprodutos (propriedade dinâmica)
                pedido.consolidar_subprodutos = True
                
                # 🔧 INICIALIZAR: Atributo necessário para ConsolidadorSimples
                pedido.lotes_consolidados = {}
                
                pedido.montar_estrutura()
                self.pedidos.append(pedido)
                print(f"   ✅ Pedido {id_pedido_counter} criado: {config['produto']} ({config['quantidade']} uni) - AGRUPAMENTO HABILITADO")
                
                id_pedido_counter += 1
                
            except RuntimeError as e:
                print(f"   ⚠️ Falha ao montar estrutura do pedido {id_pedido_counter}: {e}")
                id_pedido_counter += 1
        
        print(f"\n✅ Total de {len(self.pedidos)} pedidos criados para coxinhas COM AGRUPAMENTO!")
        print(f"🔧 Pedidos configurados com janelas temporais sobrepostas para otimizar consolidação")
        print()

    # =============================================================================
    #                      AGRUPAMENTO DE SUBPRODUTOS
    # =============================================================================
    
    def executar_agrupamento_subprodutos(self):
        """
        Executa o agrupamento/consolidação de subprodutos antes da execução dos pedidos.
        
        🎯 FUNCIONALIDADE PRINCIPAL: Consolida "massa para frituras" entre diferentes pedidos
        """
        print(f"🔄 Executando agrupamento de subprodutos (método: {self.tipo_agrupamento})...")
        
        if not self.pedidos:
            print("   ⚠️ Nenhum pedido para agrupar!")
            return
        
        # Primeiro, criar atividades modulares para todos os pedidos
        print("   📋 Criando atividades modulares para análise...")
        for pedido in self.pedidos:
            pedido.criar_atividades_modulares_necessarias()
        
        # Executar agrupamento baseado no tipo configurado
        if self.tipo_agrupamento == "avancado":
            self._executar_agrupamento_avancado()
        else:
            self._executar_agrupamento_simples()
        
        print("✅ Agrupamento de subprodutos concluído!")
        
        # Salvar informação de consolidação para pós-processamento
        if hasattr(self.agrupador, 'consolidacoes_ativas') and self.agrupador.consolidacoes_ativas:
            self.consolidacoes_para_comandas = self.agrupador.consolidacoes_ativas
        else:
            self.consolidacoes_para_comandas = []
        
        print()

    def _executar_agrupamento_simples(self):
        """Executa agrupamento usando ConsolidadorSimples"""
        print("   🔧 Usando ConsolidadorSimples...")
        
        # Usar consolidador estático
        ConsolidadorSimples.processar_pedidos(self.pedidos)
        
        # Coletar estatísticas básicas
        subprodutos_consolidados = 0
        for pedido in self.pedidos:
            for atividade in pedido.atividades_modulares:
                if hasattr(atividade, '_consolidacao_info'):
                    subprodutos_consolidados += 1
                    break
        
        self.estatisticas_agrupamento = {
            'consolidacoes_realizadas': subprodutos_consolidados,
            'economia_equipamentos': subprodutos_consolidados,
            'pedidos_afetados': [p.id_pedido for p in self.pedidos if p.consolidar_subprodutos],
            'tipo': 'simples'
        }
        
        print(f"   📊 Resultado: {subprodutos_consolidados} consolidações realizadas")

    def _executar_agrupamento_avancado(self):
        """Executa agrupamento usando AgrupadorSubprodutos"""
        print("   🔧 Usando AgrupadorSubprodutos...")
        
        # 🔍 DEBUG: Ver quantas atividades modulares cada pedido tem
        print(f"   🔍 DEBUG: Analisando {len(self.pedidos)} pedidos:")
        for pedido in self.pedidos:
            subprodutos = [a for a in pedido.atividades_modulares if a.tipo_item.name == 'SUBPRODUTO']
            print(f"     Pedido {pedido.id_pedido}: {len(pedido.atividades_modulares)} atividades totais, {len(subprodutos)} subprodutos")
            for sub in subprodutos:
                print(f"       - ID {sub.id_atividade}: {sub.nome_item} ({sub.quantidade}g)")
        
        # Executar agrupamento automático
        resultado = self.agrupador.executar_agrupamento_automatico(self.pedidos)
        
        # Armazenar estatísticas
        self.estatisticas_agrupamento = {
            'consolidacoes_realizadas': resultado.get('consolidacoes_realizadas', 0),
            'economia_equipamentos': resultado.get('economia_equipamentos', 0),
            'pedidos_afetados': resultado.get('pedidos_afetados', []),
            'detalhes': resultado.get('detalhes', []),
            'tipo': 'avancado'
        }
        
        # Mostrar resultado detalhado
        consolidacoes = resultado.get('consolidacoes_realizadas', 0)
        if consolidacoes > 0:
            print(f"   📊 Resultado: {consolidacoes} consolidações realizadas")
            print(f"   💡 Economia: {resultado.get('economia_equipamentos', 0)} equipamentos")
            print(f"   🎯 Pedidos afetados: {len(resultado.get('pedidos_afetados', []))}")
            
            for detalhe in resultado.get('detalhes', []):
                print(f"     - {detalhe['item']}: {detalhe['quantidade_total']}g de {len(detalhe['pedidos'])} pedidos")
        else:
            motivo = resultado.get('motivo', resultado.get('erro', 'Motivo não especificado'))
            print(f"   ⚠️ Nenhuma consolidação realizada: {motivo}")

    # =============================================================================
    #                      EXECUÇÃO DOS PEDIDOS
    # =============================================================================

    def executar_pedidos_ordenados(self):
        """
        Executa todos os pedidos em ordem sequencial APÓS o agrupamento.
        """
        print("🔄 Executando pedidos de coxinhas (pós-agrupamento)...")
        
        pedidos_executados = 0
        
        for idx, pedido in enumerate(self.pedidos, 1):
            nome_produto = self._obter_nome_produto_por_id(pedido.id_produto)
            
            print(f"   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})...")
            print(f"   📋 {nome_produto} - {pedido.quantidade} unidades")
            print(f"   ⏰ Prazo: {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🔗 Consolidação: {'SIM' if pedido.consolidar_subprodutos else 'NÃO'}")
            
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
            'modo_execucao': 'sequencial_agrupado'
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
        Executa o teste completo do sistema de produção de coxinhas COM AGRUPAMENTO.
        """
        try:
            print(f"🥟 INICIANDO SISTEMA DE PRODUÇÃO DE COXINHAS - MODO AGRUPADO ({self.tipo_agrupamento.upper()})")
            print()
            
            # Fase 1: Configuração do ambiente
            self.inicializar_almoxarifado()
            
            # Fase 2: Criação dos pedidos (com configuração de agrupamento)
            self.criar_pedidos_de_producao()
            
            # Fase 3: AGRUPAMENTO DE SUBPRODUTOS (nova fase)
            self.executar_agrupamento_subprodutos()
            
            # Fase 4: Ordenação por prioridade
            self.pedidos = ordenar_pedidos_por_restricoes(self.pedidos)
            print(f"✅ {len(self.pedidos)} pedidos ordenados pós-agrupamento!")
            
            # Fase 5: Execução
            self.executar_pedidos_ordenados()
            
            # Fase 6: Atualização das comandas com informação de consolidação
            self._atualizar_comandas_pos_execucao()
            
            return True
            
        except Exception as e:
            print("=" * 80)
            print(f"❌ ERRO CRÍTICO NA EXECUÇÃO COM AGRUPAMENTO: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return False
    
    def _atualizar_comandas_pos_execucao(self):
        """Atualiza as comandas existentes com informação de consolidação"""
        if not hasattr(self, 'consolidacoes_para_comandas') or not self.consolidacoes_para_comandas:
            return
        
        print("📝 Atualizando comandas com informações de consolidação...")
        
        for plano in self.consolidacoes_para_comandas:
            try:
                # Atualizar comandas dos pedidos afetados
                for id_pedido in plano.pedidos_afetados:
                    self._atualizar_comanda_individual(id_pedido, plano)
                    
            except Exception as e:
                print(f"⚠️ Erro ao atualizar comandas: {e}")
    
    def _atualizar_comanda_individual(self, id_pedido: int, plano):
        """Atualiza uma comanda individual com informação de consolidação"""
        import json
        import os
        
        caminho_comanda = f"data/comandas/comanda_ordem_1_pedido_{id_pedido}.json"
        
        if not os.path.exists(caminho_comanda):
            print(f"   ⚠️ Comanda não encontrada: {caminho_comanda}")
            return
        
        try:
            # Carregar comanda
            with open(caminho_comanda, 'r', encoding='utf-8') as f:
                comanda = json.load(f)
            
            # Adicionar seção de consolidações
            if "consolidacoes" not in comanda:
                comanda["consolidacoes"] = []
            
            # Para cada oportunidade de consolidação
            for oportunidade in plano.oportunidades:
                # Verificar se este pedido está envolvido
                if id_pedido in oportunidade.pedidos_envolvidos:
                    # Encontrar quantidade original deste pedido
                    quantidade_original = None
                    for atividade in oportunidade.atividades:
                        if atividade.id_pedido == id_pedido:
                            quantidade_original = atividade.quantidade
                            break
                    
                    consolidacao_info = {
                        "subproduto_consolidado": "Massa para Frituras",
                        "id_subproduto": 2003,
                        "quantidade_original": quantidade_original,
                        "quantidade_total_consolidada": oportunidade.quantidade_total,
                        "pedidos_envolvidos": list(oportunidade.pedidos_envolvidos),
                        "economia_equipamentos": 1,
                        "observacao": "Subproduto consolidado - produção única para múltiplos pedidos"
                    }
                    comanda["consolidacoes"].append(consolidacao_info)
                    
                    # Atualizar item na estrutura da comanda
                    self._marcar_item_consolidado_na_comanda(comanda, oportunidade)
            
            # Salvar comanda atualizada
            with open(caminho_comanda, 'w', encoding='utf-8') as f:
                json.dump(comanda, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Comanda atualizada: {caminho_comanda}")
            
        except Exception as e:
            print(f"   ❌ Erro ao atualizar comanda {caminho_comanda}: {e}")
    
    def _marcar_item_consolidado_na_comanda(self, comanda, oportunidade):
        """Marca item como consolidado na estrutura da comanda"""
        
        def buscar_e_marcar(itens):
            for item in itens:
                if item.get("id_item") == 2003:  # ID da Massa para Frituras
                    item["consolidado"] = True
                    item["quantidade_total_consolidada"] = oportunidade.quantidade_total
                    item["observacao"] = "⚡ Consolidado com outros pedidos"
                    return True
                
                # Buscar recursivamente
                if "itens_necessarios" in item:
                    if buscar_e_marcar(item["itens_necessarios"]):
                        return True
            return False
        
        buscar_e_marcar(comanda["itens"])

    # =============================================================================
    #                       MÉTODOS DE APOIO
    # =============================================================================

    def obter_estatisticas(self):
        """Retorna estatísticas da execução"""
        stats = self.estatisticas_execucao.copy()
        stats['agrupamento'] = self.estatisticas_agrupamento
        return stats


def main():
    """
    Função principal que coordena todo o teste de coxinhas com agrupamento.
    """
    # Configuração do tipo de agrupamento
    TIPO_AGRUPAMENTO = "avancado"  # "simples" ou "avancado"
    
    print(f"=" * 80)
    print(f"INICIANDO TESTE DE PRODUÇÃO DE COXINHAS COM AGRUPAMENTO")
    print(f"Tipo: {TIPO_AGRUPAMENTO.upper()}")
    print(f"=" * 80)
    
    # Inicializar sistema de teste
    sistema = TesteSistemaProducaoAgrupado(tipo_agrupamento=TIPO_AGRUPAMENTO)
    
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
            print(f"\n📋 RELATÓRIO FINAL:")
            stats = sistema.obter_estatisticas()
            print(f"   Execução: {stats}")
            
            # Escrever rodapé
            sistema.escrever_rodape_log(sucesso)
            
        except Exception as e:
            sistema.escrever_rodape_log(False)
            raise
        
        finally:
            # Restaurar stdout original
            sys.stdout = tee.stdout
            print(f"\n📄 Log de execução com agrupamento salvo em: {log_filename}")


if __name__ == "__main__":
    main()