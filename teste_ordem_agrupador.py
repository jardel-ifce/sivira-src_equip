import sys
import os
import json
import glob
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger

logger = setup_logger('MenuSistemaProducao')


class MenuSistemaProducao:
    """
    Menu principal para gerenciar o sistema de produção de alimentos.
    Interface amigável para todas as funcionalidades do sistema.
    """
    
    def __init__(self):
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos: List[PedidoDeProducao] = []
        self.sistema_inicializado = False
        
        # Caminhos para produtos e subprodutos
        self.caminho_produtos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades/"
        self.caminho_subprodutos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/subprodutos/atividades/"
        
        # Cache dos produtos e subprodutos disponíveis
        self.produtos_disponiveis: Dict[int, Dict] = {}
        self.subprodutos_disponiveis: Dict[int, Dict] = {}
        
        # Configurações padrão - Baseadas no fim desejado da jornada  
        # Por padrão: fim amanhã às 18:00, início 72h antes
        self.fim_jornada_padrao = (datetime.now() + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        self.inicio_jornada_padrao = self.fim_jornada_padrao - timedelta(hours=72)  # 72h antes do fim desejado
        
        print(f"🔧 DEBUG INICIAL - Horários configurados:")
        print(f"   Início: {self.inicio_jornada_padrao}")
        print(f"   Fim: {self.fim_jornada_padrao}")
        print(f"   Duração: {self.fim_jornada_padrao - self.inicio_jornada_padrao}")
        
        # Carregar produtos e subprodutos ao inicializar
        self._carregar_produtos_e_subprodutos()
        
    def _carregar_produtos_e_subprodutos(self):
        """Carrega produtos e subprodutos das pastas especificadas"""
        print("🔄 Carregando produtos e subprodutos disponíveis...")
        
        # Carregar produtos
        self.produtos_disponiveis = self._carregar_itens_da_pasta(
            self.caminho_produtos, "produtos"
        )
        
        # Carregar subprodutos
        self.subprodutos_disponiveis = self._carregar_itens_da_pasta(
            self.caminho_subprodutos, "subprodutos"
        )
        
        print(f"✅ {len(self.produtos_disponiveis)} produtos carregados")
        print(f"✅ {len(self.subprodutos_disponiveis)} subprodutos carregados")
    
    def _carregar_itens_da_pasta(self, caminho: str, tipo: str) -> Dict[int, Dict]:
        """Carrega itens de uma pasta específica"""
        itens = {}
        
        if not os.path.exists(caminho):
            print(f"⚠️ Pasta {tipo} não encontrada: {caminho}")
            return itens
        
        # Buscar arquivos JSON na pasta
        arquivos_json = glob.glob(os.path.join(caminho, "*.json"))
        
        for arquivo in arquivos_json:
            try:
                nome_arquivo = os.path.basename(arquivo)
                
                # Extrair ID do nome do arquivo (formato: 1001_pao_frances.json)
                if '_' in nome_arquivo:
                    id_str = nome_arquivo.split('_')[0]
                    try:
                        item_id = int(id_str)
                    except ValueError:
                        print(f"⚠️ ID inválido no arquivo {nome_arquivo}")
                        continue
                    
                    # Extrair nome amigável
                    nome_sem_extensao = nome_arquivo.replace('.json', '')
                    nome_amigavel = nome_sem_extensao.replace('_', ' ').title()
                    
                    # Tentar carregar o conteúdo do JSON para obter mais informações
                    nome_detalhado = nome_amigavel
                    try:
                        with open(arquivo, 'r', encoding='utf-8') as f:
                            dados_json = json.load(f)
                            # Tentar obter um nome mais descritivo do JSON
                            if isinstance(dados_json, dict):
                                nome_detalhado = dados_json.get('nome', dados_json.get('descricao', nome_amigavel))
                    except:
                        # Se não conseguir ler o JSON, usar o nome extraído do arquivo
                        pass
                    
                    itens[item_id] = {
                        'id': item_id,
                        'nome': nome_detalhado,
                        'arquivo': arquivo,
                        'nome_arquivo': nome_arquivo,
                        'tipo': tipo
                    }
                
            except Exception as e:
                print(f"❌ Erro ao processar arquivo {arquivo}: {e}")
                continue
        
        return itens
    
    def limpar_tela(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def pausar(self):
        """Pausa e espera input do usuário"""
        input("\n⏸️  Pressione ENTER para continuar...")
    
    def exibir_cabecalho(self):
        """Exibe o cabeçalho do sistema"""
        print("=" * 80)
        print("🏭 SISTEMA DE PRODUÇÃO DE ALIMENTOS")
        print("📅 " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        print("=" * 80)
        
        # Status do sistema
        if self.sistema_inicializado:
            print(f"✅ Sistema inicializado | 📦 {len(self.almoxarifado.itens) if self.almoxarifado else 0} itens no almoxarifado | 📋 {len(self.pedidos)} pedidos")
        else:
            print("⚠️  Sistema não inicializado - Execute a opção 1 primeiro")
        
        # Mostrar produtos e subprodutos disponíveis
        print(f"🍞 {len(self.produtos_disponiveis)} produtos disponíveis | 🥖 {len(self.subprodutos_disponiveis)} subprodutos disponíveis")
        
        # Mostrar configuração de horários de forma amigável
        if hasattr(self, 'fim_jornada_padrao') and hasattr(self, 'inicio_jornada_padrao'):
            duracao = self.fim_jornada_padrao - self.inicio_jornada_padrao
            dias = duracao.days
            horas = duracao.seconds // 3600
            
            print(f"🎯 Meta: Produção deve terminar até {self.fim_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
            if dias > 0:
                print(f"⏰ Janela de busca: {dias} dias e {horas}h (desde {self.inicio_jornada_padrao.strftime('%d/%m/%Y %H:%M')})")
            else:
                print(f"⏰ Janela de busca: {horas}h (desde {self.inicio_jornada_padrao.strftime('%d/%m/%Y %H:%M')})")
        print()

    def menu_principal(self):
        """Exibe o menu principal e gerencia navegação"""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("📋 MENU PRINCIPAL:")
            print("-" * 40)
            print("1️⃣  Inicializar Sistema")
            print("2️⃣  Gerenciar Almoxarifado")
            print("3️⃣  Gerenciar Pedidos")
            print("4️⃣  Executar Produção")
            print("5️⃣  Relatórios e Consultas")
            print("6️⃣  Configurações")
            print("7️⃣  Recarregar Produtos/Subprodutos")
            print("0️⃣  Sair")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            try:
                if opcao == "1":
                    self.inicializar_sistema()
                elif opcao == "2":
                    if self._verificar_sistema_inicializado():
                        self.menu_almoxarifado()
                elif opcao == "3":
                    if self._verificar_sistema_inicializado():
                        self.menu_pedidos()
                elif opcao == "4":
                    if self._verificar_sistema_inicializado():
                        self.menu_producao()
                elif opcao == "5":
                    if self._verificar_sistema_inicializado():
                        self.menu_relatorios()
                elif opcao == "6":
                    self.menu_configuracoes()
                elif opcao == "7":
                    self._carregar_produtos_e_subprodutos()
                    print("✅ Produtos e subprodutos recarregados!")
                    self.pausar()
                elif opcao == "0":
                    if self._confirmar_saida():
                        break
                else:
                    print("❌ Opção inválida! Tente novamente.")
                    self.pausar()
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ Operação interrompida pelo usuário.")
                if self._confirmar_saida():
                    break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                logger.error(f"Erro no menu principal: {e}")
                self.pausar()

    def _verificar_sistema_inicializado(self) -> bool:
        """Verifica se o sistema está inicializado"""
        if not self.sistema_inicializado:
            print("⚠️ Sistema não inicializado! Execute a opção 1 primeiro.")
            self.pausar()
            return False
        return True
    
    def _confirmar_saida(self) -> bool:
        """Confirma se o usuário deseja sair"""
        resposta = input("\n🤔 Tem certeza que deseja sair? (s/N): ").strip().lower()
        return resposta in ['s', 'sim', 'y', 'yes']

    # =============================================================================
    #                         1. INICIALIZAÇÃO DO SISTEMA
    # =============================================================================
    
    def inicializar_sistema(self):
        """Inicializa o sistema completo"""
        self.limpar_tela()
        print("🔄 INICIALIZANDO SISTEMA DE PRODUÇÃO")
        print("=" * 50)
        
        try:
            print("📦 Carregando almoxarifado...")
            
            # Carregar itens do almoxarifado
            itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
            print(f"✅ {len(itens)} itens carregados do arquivo")
            
            # Limpar dados anteriores
            print("🧹 Limpando dados anteriores...")
            apagar_todas_as_comandas()
            limpar_todos_os_logs()
            
            # Inicializar almoxarifado
            print("🏗️ Configurando almoxarifado...")
            self.almoxarifado = Almoxarifado()
            
            for item in itens:
                self.almoxarifado.adicionar_item(item)
            
            # Criar gestor
            self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)
            
            # Validar integridade
            problemas = self.gestor_almoxarifado.validar_almoxarifado()
            if problemas:
                print(f"⚠️ {len(problemas)} problemas encontrados (não críticos)")
            
            # Configurar estoque de teste (opcional)
            if self._perguntar_estoque_teste():
                self._configurar_estoque_teste()
            
            self.sistema_inicializado = True
            print("\n🎉 Sistema inicializado com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Erro na inicialização: {e}")
            logger.error(f"Erro na inicialização: {e}")
            self.sistema_inicializado = False
        
        self.pausar()
    
    def _perguntar_estoque_teste(self) -> bool:
        """Pergunta se deve configurar estoque de teste"""
        resposta = input("\n🧪 Configurar estoque de teste? (S/n): ").strip().lower()
        return resposta in ['', 's', 'sim', 'y', 'yes']
    
    def _configurar_estoque_teste(self):
        """Configura estoque de teste para demonstração"""
        print("🔄 Configurando estoque de teste...")
        
        itens_teste = [
            {"id_item": 2001, "quantidade": 0, "nome": "massa_crocante"},
            {"id_item": 1, "quantidade": 25000, "nome": "acucar_refinado"},
            {"id_item": 16, "quantidade": 80000, "nome": "farinha_de_trigo_s_ferm"},
            {"id_item": 33, "quantidade": 12000, "nome": "ovo_de_galinha"},
        ]
        
        for item_teste in itens_teste:
            item = self.gestor_almoxarifado.obter_item_por_id(item_teste["id_item"])
            if item:
                valor_antes = item.estoque_atual
                item.estoque_atual = item_teste["quantidade"]
                valor_depois = item.estoque_atual
                
                print(f"   ✅ {item.descricao}: {valor_depois}")
                
                if item_teste["id_item"] == 2001:
                    print(f"       🔍 Debug massa_crocante:")
                    print(f"           Valor antes: {valor_antes}")
                    print(f"           Valor desejado: {item_teste['quantidade']}")
                    print(f"           Valor depois: {valor_depois}")
                    print(f"           Valor no objeto: {item.estoque_atual}")
                    print(f"           Objeto ID: {id(item)}")
            else:
                print(f"   ❌ Item {item_teste['id_item']} ({item_teste['nome']}) não encontrado!")
        
        print("✅ Estoque de teste configurado!")
        
        print("\n🔍 Verificação final (valores reais dos objetos):")
        for item_teste in itens_teste:
            item = self.gestor_almoxarifado.obter_item_por_id(item_teste["id_item"])
            if item:
                valor_real = item.estoque_atual
                status = "✅" if valor_real == item_teste["quantidade"] else "❌"
                print(f"   {status} ID {item_teste['id_item']}: {valor_real} (esperado: {item_teste['quantidade']})")
                
                if valor_real != item_teste["quantidade"]:
                    print(f"       🚨 INCONSISTÊNCIA DETECTADA!")
                    print(f"           Valor no objeto: {item.estoque_atual}")
                    print(f"           Tipo do valor: {type(item.estoque_atual)}")
                    print(f"           Valor esperado: {item_teste['quantidade']}")
                    print(f"           Tipo esperado: {type(item_teste['quantidade'])}")

    # =============================================================================
    #                         2. MENU ALMOXARIFADO
    # =============================================================================
    
    def menu_almoxarifado(self):
        """Menu para gerenciar almoxarifado"""
        while True:
            self.limpar_tela()
            print("📦 GERENCIAMENTO DE ALMOXARIFADO")
            print("=" * 40)
            print("1️⃣  Ver Resumo Geral")
            print("2️⃣  Consultar Item Específico")
            print("3️⃣  Ver Itens Críticos")
            print("4️⃣  Buscar Itens")
            print("5️⃣  Atualizar Estoque")
            print("6️⃣  Relatório por Data")
            print("0️⃣  Voltar ao Menu Principal")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.ver_resumo_almoxarifado()
            elif opcao == "2":
                self.consultar_item_especifico()
            elif opcao == "3":
                self.ver_itens_criticos()
            elif opcao == "4":
                self.buscar_itens()
            elif opcao == "5":
                self.atualizar_estoque()
            elif opcao == "6":
                self.relatorio_por_data()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida!")
                self.pausar()
    
    def ver_resumo_almoxarifado(self):
        """Exibe resumo geral do almoxarifado"""
        self.limpar_tela()
        print("📊 RESUMO GERAL DO ALMOXARIFADO")
        print("=" * 50)
        
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
        
        self.pausar()
    
    def consultar_item_especifico(self):
        """Consulta um item específico"""
        self.limpar_tela()
        print("🔍 CONSULTAR ITEM ESPECÍFICO")
        print("=" * 40)
        
        try:
            id_item = int(input("Digite o ID do item: "))
            item = self.gestor_almoxarifado.obter_item_por_id(id_item)
            
            if item:
                resumo = item.resumo_estoque()
                print(f"\n📋 INFORMAÇÕES DO ITEM {id_item}:")
                print("-" * 40)
                print(f"Nome: {resumo['nome']}")
                print(f"Descrição: {resumo['descricao']}")
                print(f"Estoque atual: {resumo['estoque_atual']} {resumo['unidade_medida']}")
                print(f"Estoque mín/máx: {resumo['estoque_min']}/{resumo['estoque_max']}")
                print(f"Percentual: {resumo['percentual_estoque']:.1f}%")
                print(f"Política: {resumo['politica_producao']}")
                print(f"Status: {'❌ Crítico' if resumo['abaixo_do_minimo'] else '✅ Normal'}")
                
                if resumo['dias_restantes']:
                    print(f"Dias restantes: {resumo['dias_restantes']:.1f}")
            else:
                print("❌ Item não encontrado!")
        
        except ValueError:
            print("❌ ID inválido! Digite apenas números.")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        self.pausar()
    
    def ver_itens_criticos(self):
        """Exibe itens críticos"""
        self.limpar_tela()
        print("⚠️ ITENS CRÍTICOS")
        print("=" * 30)
        
        itens_criticos = self.gestor_almoxarifado.verificar_estoque_minimo()
        
        if itens_criticos:
            print(f"📊 {len(itens_criticos)} itens precisam de atenção:\n")
            
            for i, item in enumerate(itens_criticos, 1):
                print(f"{i:2d}. {item['descricao']}")
                print(f"    ID: {item['id_item']} | Atual: {item['estoque_atual']} | Mín: {item['estoque_min']}")
                print(f"    Falta: {item['falta']} {item['unidade']}")
                print()
        else:
            print("✅ Nenhum item crítico encontrado!")
        
        self.pausar()
    
    def buscar_itens(self):
        """Busca itens por critérios"""
        self.limpar_tela()
        print("🔍 BUSCAR ITENS")
        print("=" * 20)
        
        termo = input("Digite um termo para buscar (nome/descrição): ").strip()
        
        if termo:
            resultados = self.gestor_almoxarifado.buscar_itens_por_criterio(nome_parcial=termo)
            
            if resultados:
                print(f"\n📊 {len(resultados)} itens encontrados:\n")
                
                for item in resultados[:10]:
                    print(f"ID {item.id_item}: {item.descricao}")
                    print(f"   Estoque: {item.estoque_atual} {item.unidade_medida.value}")
                    print()
                
                if len(resultados) > 10:
                    print(f"... e mais {len(resultados) - 10} itens")
            else:
                print("❌ Nenhum item encontrado!")
        else:
            print("❌ Digite um termo para buscar!")
        
        self.pausar()
    
    def atualizar_estoque(self):
        """Atualiza estoque de um item"""
        self.limpar_tela()
        print("📝 ATUALIZAR ESTOQUE")
        print("=" * 30)
        
        try:
            id_item = int(input("Digite o ID do item: "))
            item = self.gestor_almoxarifado.obter_item_por_id(id_item)
            
            if item:
                print(f"\nItem: {item.descricao}")
                print(f"Estoque atual: {item.estoque_atual} {item.unidade_medida.value}")
                
                novo_estoque = float(input("\nDigite o novo estoque: "))
                
                if novo_estoque >= 0:
                    item.estoque_atual = novo_estoque
                    print(f"✅ Estoque atualizado para {novo_estoque} {item.unidade_medida.value}")
                else:
                    print("❌ Estoque não pode ser negativo!")
            else:
                print("❌ Item não encontrado!")
        
        except ValueError:
            print("❌ Valor inválido!")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        self.pausar()
    
    def relatorio_por_data(self):
        """Gera relatório para uma data específica"""
        self.limpar_tela()
        print("📅 RELATÓRIO POR DATA")
        print("=" * 30)
        
        try:
            data_str = input("Digite a data (DD/MM/AAAA) ou ENTER para hoje: ").strip()
            
            if data_str:
                data = datetime.strptime(data_str, "%d/%m/%Y").date()
            else:
                data = datetime.now().date()
            
            self.gestor_almoxarifado.resumir_estoque_projetado(data)
        
        except ValueError:
            print("❌ Formato de data inválido! Use DD/MM/AAAA")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        self.pausar()

    # =============================================================================
    #                         3. MENU PEDIDOS - VERSÃO MELHORADA
    # =============================================================================
    
    def menu_pedidos(self):
        """Menu para gerenciar pedidos"""
        while True:
            self.limpar_tela()
            print("📋 GERENCIAMENTO DE PEDIDOS")
            print("=" * 40)
            print(f"📊 Pedidos atuais: {len(self.pedidos)}")
            print()
            print("1️⃣  Criar Novo Pedido")
            print("2️⃣  Listar Pedidos")
            print("3️⃣  Ver Detalhes de Pedido")
            print("4️⃣  Remover Pedido")
            print("5️⃣  Limpar Todos os Pedidos")
            print("6️⃣  Ver Produtos/Subprodutos Disponíveis")
            print("0️⃣  Voltar ao Menu Principal")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.criar_novo_pedido()
            elif opcao == "2":
                self.listar_pedidos()
            elif opcao == "3":
                self.ver_detalhes_pedido()
            elif opcao == "4":
                self.remover_pedido()
            elif opcao == "5":
                self.limpar_pedidos()
            elif opcao == "6":
                self.ver_produtos_subprodutos_disponiveis()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida!")
                self.pausar()
    
    def ver_produtos_subprodutos_disponiveis(self):
        """Mostra todos os produtos e subprodutos disponíveis"""
        self.limpar_tela()
        print("📋 PRODUTOS E SUBPRODUTOS DISPONÍVEIS")
        print("=" * 50)
        
        # Mostrar produtos
        if self.produtos_disponiveis:
            print("🍞 PRODUTOS:")
            print("-" * 20)
            for produto_id in sorted(self.produtos_disponiveis.keys()):
                produto = self.produtos_disponiveis[produto_id]
                print(f"   {produto_id:4d} - {produto['nome']}")
                print(f"        📁 {produto['nome_arquivo']}")
            print()
        else:
            print("❌ Nenhum produto encontrado!")
        
        # Mostrar subprodutos
        if self.subprodutos_disponiveis:
            print("🥖 SUBPRODUTOS:")
            print("-" * 20)
            for subproduto_id in sorted(self.subprodutos_disponiveis.keys()):
                subproduto = self.subprodutos_disponiveis[subproduto_id]
                print(f"   {subproduto_id:4d} - {subproduto['nome']}")
                print(f"        📁 {subproduto['nome_arquivo']}")
            print()
        else:
            print("❌ Nenhum subproduto encontrado!")
        
        print(f"📊 Total: {len(self.produtos_disponiveis)} produtos + {len(self.subprodutos_disponiveis)} subprodutos")
        self.pausar()
    
    def criar_novo_pedido(self):
        """Cria um novo pedido com produtos/subprodutos carregados dinamicamente"""
        self.limpar_tela()
        print("➕ CRIAR NOVO PEDIDO")
        print("=" * 30)
        
        if not self.produtos_disponiveis and not self.subprodutos_disponiveis:
            print("❌ Nenhum produto ou subproduto disponível!")
            print("ℹ️ Verifique se os arquivos existem nas pastas:")
            print(f"   📁 {self.caminho_produtos}")
            print(f"   📁 {self.caminho_subprodutos}")
            self.pausar()
            return
        
        try:
            # =====================================================================
            # CONFIGURAÇÃO DE HORÁRIOS - FLUXO ESPECÍFICO SOLICITADO
            # =====================================================================
            
            # 1. Capturar data atual e sugerir fim_jornada para daqui a 3 dias às 18:00
            data_atual = datetime.now()
            fim_sugerido = (data_atual + timedelta(days=3)).replace(hour=18, minute=0, second=0, microsecond=0)
            
            print("⏰ CONFIGURAÇÃO DE HORÁRIOS PARA ESTE PEDIDO:")
            print(f"📅 Data atual do sistema: {data_atual.strftime('%d/%m/%Y %H:%M')}")
            print(f"🎯 Sugestão de prazo: {fim_sugerido.strftime('%d/%m/%Y %H:%M')} (daqui a 3 dias)")
            
            # 2. Perguntar se pode usar a data sugerida
            usar_fim_sugerido = input(f"\nPosso usar {fim_sugerido.strftime('%d/%m/%Y %H:%M')} como prazo final? (S/n): ").strip().lower()
            
            if usar_fim_sugerido in ['', 's', 'sim']:
                fim_jornada = fim_sugerido
                print(f"✅ Prazo final configurado: {fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            else:
                # Se não aceitar, pedir data e hora específica
                while True:
                    try:
                        fim_especifico = input("Digite o prazo final desejado (DD/MM/AAAA HH:MM): ").strip()
                        fim_jornada = datetime.strptime(fim_especifico, '%d/%m/%Y %H:%M')
                        print(f"✅ Prazo final configurado: {fim_jornada.strftime('%d/%m/%Y %H:%M')}")
                        break
                    except ValueError:
                        print("❌ Formato inválido! Use DD/MM/AAAA HH:MM")
            
            # 3. Calcular início_jornada 72h antes e perguntar se pode usar
            inicio_sugerido = fim_jornada - timedelta(hours=72)
            
            print(f"\n🔍 Para o prazo {fim_jornada.strftime('%d/%m/%Y %H:%M')}:")
            print(f"💡 Sugestão de início da busca: {inicio_sugerido.strftime('%d/%m/%Y %H:%M')} (72h antes)")
            print(f"⏰ Isso dará uma janela de 3 dias para encontrar os melhores horários")
            
            usar_inicio_sugerido = input(f"\nPosso usar {inicio_sugerido.strftime('%d/%m/%Y %H:%M')} como início da busca? (S/n): ").strip().lower()
            
            if usar_inicio_sugerido in ['', 's', 'sim']:
                inicio_jornada = inicio_sugerido
                print(f"✅ Início da busca configurado: {inicio_jornada.strftime('%d/%m/%Y %H:%M')}")
            else:
                # Se não aceitar, pedir data e hora específica de início
                while True:
                    try:
                        inicio_especifico = input("Digite o início da busca desejado (DD/MM/AAAA HH:MM): ").strip()
                        inicio_jornada = datetime.strptime(inicio_especifico, '%d/%m/%Y %H:%M')
                        
                        # Validar se início é antes do fim
                        if inicio_jornada >= fim_jornada:
                            print("❌ Início deve ser anterior ao fim! Tente novamente.")
                            continue
                            
                        print(f"✅ Início da busca configurado: {inicio_jornada.strftime('%d/%m/%Y %H:%M')}")
                        break
                    except ValueError:
                        print("❌ Formato inválido! Use DD/MM/AAAA HH:MM")
            
            # 4. Mostrar resumo final da configuração
            janela_total = fim_jornada - inicio_jornada
            dias_janela = janela_total.days
            horas_janela = janela_total.seconds // 3600
            
            print(f"\n" + "="*60)
            print(f"📋 CONFIGURAÇÃO FINAL DO PEDIDO:")
            print(f"   🎯 Prazo final: {fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🔍 Início da busca: {inicio_jornada.strftime('%d/%m/%Y %H:%M')}")
            print(f"   ⏰ Janela total: {dias_janela} dias e {horas_janela}h")
            print(f"   📊 Total de horas: {janela_total.total_seconds()/3600:.0f}h")
            print("="*60)
            
            # Escolher tipo
            print("\n🎯 TIPO DE ITEM:")
            print("1️⃣  Produto")
            print("2️⃣  Subproduto")
            print()
            
            tipo_opcao = input("Escolha o tipo (1-2): ").strip()
            
            if tipo_opcao == "1":
                # Produtos
                if not self.produtos_disponiveis:
                    print("❌ Nenhum produto disponível!")
                    self.pausar()
                    return
                
                print("\n🍞 PRODUTOS DISPONÍVEIS:")
                print("-" * 30)
                
                # Mostrar produtos em formato compacto
                produtos_ordenados = sorted(self.produtos_disponiveis.keys())
                for i, produto_id in enumerate(produtos_ordenados):
                    produto = self.produtos_disponiveis[produto_id]
                    print(f"   {produto_id:4d} - {produto['nome']}")
                    
                    # Quebrar linha a cada 5 itens para melhor visualização
                    if (i + 1) % 5 == 0 and i < len(produtos_ordenados) - 1:
                        print()
                
                print()
                id_produto = int(input("Digite o ID do produto: "))
                
                if id_produto not in self.produtos_disponiveis:
                    print("❌ Produto não encontrado!")
                    self.pausar()
                    return
                
                item_escolhido = self.produtos_disponiveis[id_produto]
                tipo_item = TipoItem.PRODUTO
                
            elif tipo_opcao == "2":
                # Subprodutos
                if not self.subprodutos_disponiveis:
                    print("❌ Nenhum subproduto disponível!")
                    self.pausar()
                    return
                
                print("\n🥖 SUBPRODUTOS DISPONÍVEIS:")
                print("-" * 30)
                
                # Mostrar subprodutos em formato compacto
                subprodutos_ordenados = sorted(self.subprodutos_disponiveis.keys())
                for i, subproduto_id in enumerate(subprodutos_ordenados):
                    subproduto = self.subprodutos_disponiveis[subproduto_id]
                    print(f"   {subproduto_id:4d} - {subproduto['nome']}")
                    
                    # Quebrar linha a cada 5 itens para melhor visualização
                    if (i + 1) % 5 == 0 and i < len(subprodutos_ordenados) - 1:
                        print()
                
                print()
                id_produto = int(input("Digite o ID do subproduto: "))
                
                if id_produto not in self.subprodutos_disponiveis:
                    print("❌ Subproduto não encontrado!")
                    self.pausar()
                    return
                
                item_escolhido = self.subprodutos_disponiveis[id_produto]
                tipo_item = TipoItem.SUBPRODUTO
                
            else:
                print("❌ Opção inválida!")
                self.pausar()
                return
            
            # Solicitar quantidade
            print(f"\n📋 Item selecionado: {item_escolhido['nome']}")
            quantidade = int(input("Digite a quantidade: "))
            
            if quantidade <= 0:
                print("❌ Quantidade deve ser positiva!")
                self.pausar()
                return
            
            # Gerar IDs únicos para o pedido - CORREÇÃO: usar timestamp para evitar duplicatas
            import time
            timestamp = int(time.time())
            id_pedido = len(self.pedidos) + 1 + timestamp % 1000  # Mais único
            id_ordem = 1  # Fixo por simplicidade
            
            # Criar pedido
            print(f"\n🔄 Criando pedido {id_pedido} para {quantidade}x {item_escolhido['nome']}...")
            
            pedido = PedidoDeProducao(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_produto=id_produto,
                tipo_item=tipo_item,
                quantidade=quantidade,
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada,
                todos_funcionarios=funcionarios_disponiveis,
                gestor_almoxarifado=self.gestor_almoxarifado
            )
            
            # Montar estrutura
            print("🏗️ Montando estrutura da ficha técnica...")
            pedido.montar_estrutura()
            
            self.pedidos.append(pedido)
            
            print(f"\n✅ Pedido {id_pedido} criado com sucesso!")
            print(f"   📋 Item: {item_escolhido['nome']} ({item_escolhido['tipo']})")
            print(f"   📊 Quantidade: {quantidade}")
            print(f"   🆔 ID do item: {id_produto}")
            print(f"   📁 Arquivo: {item_escolhido['nome_arquivo']}")
            print(f"   ⏰ Prazo: até {fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            
            # Mostrar resumo rápido da estrutura
            resumo = pedido.obter_resumo_pedido()
            print(f"   🔧 Atividades criadas: {resumo['total_atividades']}")
            print(f"   👥 Funcionários elegíveis: {resumo['funcionarios_elegiveis']}")
            
        except ValueError:
            print("❌ Valor inválido! Digite apenas números.")
        except Exception as e:
            print(f"❌ Erro ao criar pedido: {e}")
            logger.error(f"Erro ao criar pedido: {e}")
        
        self.pausar()
    
    def listar_pedidos(self):
        """Lista todos os pedidos"""
        self.limpar_tela()
        print("📋 LISTA DE PEDIDOS")
        print("=" * 30)
        
        if not self.pedidos:
            print("ℹ️ Nenhum pedido cadastrado.")
        else:
            print(f"📊 Total: {len(self.pedidos)} pedidos\n")
            
            for pedido in self.pedidos:
                resumo = pedido.obter_resumo_pedido()
                status = f"{resumo['atividades_alocadas']}/{resumo['total_atividades']} atividades"
                
                # Determinar se é produto ou subproduto
                tipo_str = "🍞 Produto" if pedido.tipo_item == TipoItem.PRODUTO else "🥖 Subproduto"
                
                # Buscar nome do item
                nome_item = "Desconhecido"
                if pedido.tipo_item == TipoItem.PRODUTO and pedido.id_produto in self.produtos_disponiveis:
                    nome_item = self.produtos_disponiveis[pedido.id_produto]['nome']
                elif pedido.tipo_item == TipoItem.SUBPRODUTO and pedido.id_produto in self.subprodutos_disponiveis:
                    nome_item = self.subprodutos_disponiveis[pedido.id_produto]['nome']
                
                print(f"🔸 Pedido {resumo['id_pedido']}")
                print(f"   {tipo_str}: {nome_item} (ID: {resumo['id_produto']})")
                print(f"   📊 Quantidade: {resumo['quantidade']}")
                print(f"   ⚙️ Status: {status}")
                print()
        
        self.pausar()
    
    def ver_detalhes_pedido(self):
        """Mostra detalhes de um pedido específico"""
        if not self.pedidos:
            print("ℹ️ Nenhum pedido cadastrado.")
            self.pausar()
            return
        
        self.limpar_tela()
        print("🔍 DETALHES DO PEDIDO")
        print("=" * 30)
        
        try:
            id_pedido = int(input("Digite o ID do pedido: "))
            
            pedido = next((p for p in self.pedidos if p.id_pedido == id_pedido), None)
            
            if pedido:
                resumo = pedido.obter_resumo_pedido()
                
                # Buscar informações do item
                tipo_str = "🍞 Produto" if pedido.tipo_item == TipoItem.PRODUTO else "🥖 Subproduto"
                nome_item = "Desconhecido"
                arquivo_item = "N/A"
                
                if pedido.tipo_item == TipoItem.PRODUTO and pedido.id_produto in self.produtos_disponiveis:
                    item_info = self.produtos_disponiveis[pedido.id_produto]
                    nome_item = item_info['nome']
                    arquivo_item = item_info['nome_arquivo']
                elif pedido.tipo_item == TipoItem.SUBPRODUTO and pedido.id_produto in self.subprodutos_disponiveis:
                    item_info = self.subprodutos_disponiveis[pedido.id_produto]
                    nome_item = item_info['nome']
                    arquivo_item = item_info['nome_arquivo']
                
                print(f"\n📋 PEDIDO {resumo['id_pedido']}:")
                print("-" * 40)
                print(f"Tipo: {tipo_str}")
                print(f"Item: {nome_item}")
                print(f"ID do item: {resumo['id_produto']}")
                print(f"Arquivo: {arquivo_item}")
                print(f"Quantidade: {resumo['quantidade']}")
                print(f"Atividades: {resumo['total_atividades']} criadas, {resumo['atividades_alocadas']} alocadas")
                print(f"Funcionários elegíveis: {resumo['funcionarios_elegiveis']}")
                print(f"Jornada: {datetime.fromisoformat(resumo['inicio_jornada']).strftime('%H:%M')} - {datetime.fromisoformat(resumo['fim_jornada']).strftime('%H:%M')}")
                
                if resumo['inicio_real']:
                    inicio_real = datetime.fromisoformat(resumo['inicio_real'])
                    fim_real = datetime.fromisoformat(resumo['fim_real'])
                    print(f"Execução real: {inicio_real.strftime('%H:%M')} - {fim_real.strftime('%H:%M')}")
                
                # Mostrar estrutura da ficha técnica
                print("\n📊 Estrutura da ficha técnica:")
                pedido.mostrar_estrutura()
                
            else:
                print("❌ Pedido não encontrado!")
        
        except ValueError:
            print("❌ ID inválido!")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        self.pausar()
    
    def remover_pedido(self):
        """Remove um pedido"""
        if not self.pedidos:
            print("ℹ️ Nenhum pedido cadastrado.")
            self.pausar()
            return
        
        self.limpar_tela()
        print("🗑️ REMOVER PEDIDO")
        print("=" * 20)
        
        self.listar_pedidos()
        
        try:
            id_pedido = int(input("Digite o ID do pedido para remover: "))
            
            pedido = next((p for p in self.pedidos if p.id_pedido == id_pedido), None)
            
            if pedido:
                # Fazer rollback se necessário
                if pedido.atividades_modulares:
                    pedido.rollback_pedido()
                
                self.pedidos.remove(pedido)
                print(f"✅ Pedido {id_pedido} removido com sucesso!")
            else:
                print("❌ Pedido não encontrado!")
        
        except ValueError:
            print("❌ ID inválido!")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        self.pausar()
    
    def limpar_pedidos(self):
        """Remove todos os pedidos"""
        if not self.pedidos:
            print("ℹ️ Nenhum pedido cadastrado.")
            self.pausar()
            return
        
        resposta = input(f"⚠️ Confirma remoção de {len(self.pedidos)} pedidos? (s/N): ").strip().lower()
        
        if resposta in ['s', 'sim']:
            # Fazer rollback de todos os pedidos
            for pedido in self.pedidos:
                if pedido.atividades_modulares:
                    pedido.rollback_pedido()
            
            self.pedidos.clear()
            print("✅ Todos os pedidos foram removidos!")
        else:
            print("❌ Operação cancelada.")
        
        self.pausar()

    # =============================================================================
    #                         4. MENU PRODUÇÃO
    # =============================================================================
    
    def menu_producao(self):
        """Menu para executar produção"""
        while True:
            self.limpar_tela()
            print("⚙️ EXECUÇÃO DE PRODUÇÃO")
            print("=" * 40)
            print(f"📊 Pedidos prontos: {len(self.pedidos)}")
            print()
            print("1️⃣  Executar Todos os Pedidos")
            print("2️⃣  Executar Pedido Específico")
            print("3️⃣  Simular Execução (Dry Run)")
            print("4️⃣  Ver Histórico de Execuções")
            print("0️⃣  Voltar ao Menu Principal")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.executar_todos_pedidos()
            elif opcao == "2":
                self.executar_pedido_especifico()
            elif opcao == "3":
                self.simular_execucao()
            elif opcao == "4":
                self.ver_historico_execucoes()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida!")
                self.pausar()
    
    def executar_todos_pedidos(self):
        """Executa todos os pedidos na ordem"""
        if not self.pedidos:
            print("ℹ️ Nenhum pedido para executar.")
            self.pausar()
            return
        
        self.limpar_tela()
        print("🚀 EXECUTANDO TODOS OS PEDIDOS")
        print("=" * 40)
        
        try:
            # O ordenamento é responsabilidade do sistema de produção, não do menu
            pedidos_ordenados = ordenar_pedidos_por_restricoes(self.pedidos.copy())
            
            print(f"📋 Executando {len(pedidos_ordenados)} pedidos:")
            for i, pedido in enumerate(pedidos_ordenados, 1):
                nome_item = self._obter_nome_item(pedido)
                tipo_str = "Produto" if pedido.tipo_item == TipoItem.PRODUTO else "Subproduto"
                print(f"   {i}. Pedido {pedido.id_pedido} - {tipo_str}: {nome_item}")
            
            print("\n🔄 Iniciando execução...")
            
            sucessos = 0
            erros = 0
            
            for pedido in pedidos_ordenados:
                try:
                    nome_item = self._obter_nome_item(pedido)
                    print(f"\n📋 Executando pedido {pedido.id_pedido} ({nome_item})...")
                    
                    # Delegar toda a lógica de execução para a classe PedidoDeProducao
                    self._executar_pedido_individual(pedido)
                    
                    print(f"✅ Pedido {pedido.id_pedido} executado com sucesso!")
                    sucessos += 1
                    
                except Exception as e:
                    print(f"❌ Erro no pedido {pedido.id_pedido}: {e}")
                    logger.error(f"Erro detalhado no pedido {pedido.id_pedido}: {e}")
                    erros += 1
                    continue
            
            print(f"\n📊 RESUMO DA EXECUÇÃO:")
            print(f"✅ Sucessos: {sucessos}")
            print(f"❌ Erros: {erros}")
            print(f"📋 Total: {len(pedidos_ordenados)}")
            
        except Exception as e:
            print(f"❌ Erro geral na execução: {e}")
            logger.error(f"Erro na execução: {e}")
        
        self.pausar()
    
    def _obter_nome_item(self, pedido):
        """Obtém o nome amigável do item do pedido"""
        if pedido.tipo_item == TipoItem.PRODUTO and pedido.id_produto in self.produtos_disponiveis:
            return self.produtos_disponiveis[pedido.id_produto]['nome']
        elif pedido.tipo_item == TipoItem.SUBPRODUTO and pedido.id_produto in self.subprodutos_disponiveis:
            return self.subprodutos_disponiveis[pedido.id_produto]['nome']
        return "Desconhecido"
    
    def _executar_pedido_individual(self, pedido):
        """Executa um pedido individual - delega toda a lógica para as classes de negócio"""
        # DIAGNÓSTICO: Verificar horários antes da execução
        print(f"🔍 DIAGNÓSTICO DO PEDIDO {pedido.id_pedido}:")
        print(f"   📅 Início jornada: {pedido.inicio_jornada}")
        print(f"   📅 Fim jornada: {pedido.fim_jornada}")
        
        duracao_jornada = pedido.fim_jornada - pedido.inicio_jornada
        print(f"   ⏰ Duração total: {duracao_jornada}")
        print(f"   🧮 Minutos totais: {duracao_jornada.total_seconds() / 60}")
        
        # CORREÇÃO: Garantir janela temporal adequada
        if duracao_jornada.total_seconds() < 3600:  # Menos de 1 hora
            print(f"   ⚠️ PROBLEMA: Janela muito pequena! Corrigindo...")
            
            # Usar configuração padrão do sistema
            pedido.inicio_jornada = self.inicio_jornada_padrao
            pedido.fim_jornada = self.fim_jornada_padrao
            
            nova_duracao = pedido.fim_jornada - pedido.inicio_jornada
            print(f"   ✅ CORRIGIDO: Nova duração: {nova_duracao}")
        
        # A classe PedidoDeProducao deve saber como se executar
        # O menu apenas coordena, não implementa regras de negócio
        
        # Verificar se já tem atividades criadas
        if not pedido.atividades_modulares:
            pedido.gerar_comanda_de_reserva(pedido.inicio_jornada)
            pedido.criar_atividades_modulares_necessarias()
        
        # Executar se há atividades
        if pedido.atividades_modulares:
            pedido.executar_atividades_em_ordem()
        else:
            print(f"ℹ️ Pedido não precisou de produção (estoque suficiente)")
    
    def executar_pedido_especifico(self):
        """Executa um pedido específico"""
        if not self.pedidos:
            print("ℹ️ Nenhum pedido para executar.")
            self.pausar()
            return
        
        self.limpar_tela()
        print("🎯 EXECUTAR PEDIDO ESPECÍFICO")
        print("=" * 40)
        
        self.listar_pedidos()
        
        try:
            id_pedido = int(input("\nDigite o ID do pedido para executar: "))
            
            pedido = next((p for p in self.pedidos if p.id_pedido == id_pedido), None)
            
            if pedido:
                nome_item = self._obter_nome_item(pedido)
                print(f"\n🔄 Executando pedido {id_pedido} ({nome_item})...")
                
                # Mostrar estrutura se solicitado
                resposta = input("Deseja ver a estrutura da ficha técnica? (s/N): ").strip().lower()
                if resposta in ['s', 'sim']:
                    print("\n📊 Estrutura da ficha técnica:")
                    pedido.mostrar_estrutura()
                
                # Delegar execução para a classe de negócio
                self._executar_pedido_individual(pedido)
                
                print(f"\n✅ Pedido {id_pedido} executado com sucesso!")
                
                # Mostrar resumo opcional
                resumo = pedido.obter_resumo_pedido()
                if resumo.get('inicio_real'):
                    inicio = datetime.fromisoformat(resumo['inicio_real'])
                    fim = datetime.fromisoformat(resumo['fim_real'])
                    print(f"⏰ Período: {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}")
                
            else:
                print("❌ Pedido não encontrado!")
        
        except ValueError:
            print("❌ ID inválido!")
        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            logger.error(f"Erro na execução: {e}")
        
        self.pausar()
    
    def simular_execucao(self):
        """Simula execução sem alocar recursos"""
        print("🧪 SIMULAÇÃO DE EXECUÇÃO")
        print("=" * 30)
        print("ℹ️ Funcionalidade em desenvolvimento...")
        self.pausar()
    
    def ver_historico_execucoes(self):
        """Mostra histórico de execuções"""
        print("📚 HISTÓRICO DE EXECUÇÕES")
        print("=" * 30)
        print("ℹ️ Funcionalidade em desenvolvimento...")
        self.pausar()

    # =============================================================================
    #                         5. MENU RELATÓRIOS
    # =============================================================================
    
    def menu_relatorios(self):
        """Menu de relatórios e consultas"""
        while True:
            self.limpar_tela()
            print("📊 RELATÓRIOS E CONSULTAS")
            print("=" * 40)
            print("1️⃣  Relatório Completo do Almoxarifado")
            print("2️⃣  Análise de Pedidos")
            print("3️⃣  Logs de Equipamentos")
            print("4️⃣  Estatísticas de Produção")
            print("0️⃣  Voltar ao Menu Principal")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.relatorio_completo_almoxarifado()
            elif opcao == "2":
                self.analise_pedidos()
            elif opcao == "3":
                self.logs_equipamentos()
            elif opcao == "4":
                self.estatisticas_producao()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida!")
                self.pausar()
    
    def relatorio_completo_almoxarifado(self):
        """Gera relatório completo do almoxarifado"""
        self.limpar_tela()
        print("📋 RELATÓRIO COMPLETO DO ALMOXARIFADO")
        print("=" * 50)
        
        relatorio = self.gestor_almoxarifado.gerar_relatorio_estoque_completo()
        
        print("📊 ESTATÍSTICAS GERAIS:")
        stats = relatorio['estatisticas_gerais']
        print(f"   Total de itens: {stats['total_itens']}")
        print(f"   Itens críticos: {stats['itens_abaixo_minimo']} ({relatorio['percentual_itens_criticos']:.1f}%)")
        print(f"   Itens sem estoque: {stats['itens_sem_estoque']}")
        
        if relatorio['itens_criticos']:
            print(f"\n⚠️ ITENS CRÍTICOS ({len(relatorio['itens_criticos'])}):")
            for item in relatorio['itens_criticos'][:5]:
                print(f"   - {item['descricao']}: {item['estoque_atual']}/{item['estoque_min']}")
            if len(relatorio['itens_criticos']) > 5:
                print(f"   ... e mais {len(relatorio['itens_criticos']) - 5} itens")
        
        self.pausar()
    
    def analise_pedidos(self):
        """Análise detalhada dos pedidos"""
        self.limpar_tela()
        print("📈 ANÁLISE DE PEDIDOS")
        print("=" * 30)
        
        if not self.pedidos:
            print("ℹ️ Nenhum pedido para analisar.")
        else:
            total_atividades = sum(len(p.atividades_modulares) for p in self.pedidos)
            atividades_alocadas = sum(
                len([a for a in p.atividades_modulares if a.alocada]) 
                for p in self.pedidos
            )
            
            print(f"📊 Resumo geral:")
            print(f"   Total de pedidos: {len(self.pedidos)}")
            print(f"   Total de atividades: {total_atividades}")
            print(f"   Atividades alocadas: {atividades_alocadas}")
            print(f"   Taxa de sucesso: {(atividades_alocadas/total_atividades*100):.1f}%" if total_atividades > 0 else "   Taxa de sucesso: 0%")
            
            # Análise por tipo
            produtos_count = sum(1 for p in self.pedidos if p.tipo_item == TipoItem.PRODUTO)
            subprodutos_count = len(self.pedidos) - produtos_count
            
            print(f"\n📋 Distribuição por tipo:")
            print(f"   🍞 Produtos: {produtos_count}")
            print(f"   🥖 Subprodutos: {subprodutos_count}")
            
            print(f"\n📋 Detalhes por pedido:")
            for pedido in self.pedidos:
                resumo = pedido.obter_resumo_pedido()
                tipo_str = "🍞" if pedido.tipo_item == TipoItem.PRODUTO else "🥖"
                print(f"   {tipo_str} Pedido {resumo['id_pedido']}: {resumo['atividades_alocadas']}/{resumo['total_atividades']} atividades")
        
        self.pausar()
    
    def logs_equipamentos(self):
        """Mostra logs de equipamentos"""
        self.limpar_tela()
        print("🛠️ LOGS DE EQUIPAMENTOS")
        print("=" * 30)
        
        # Procurar por arquivos de log
        log_dir = "logs/equipamentos"
        if os.path.exists(log_dir):
            arquivos = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            
            if arquivos:
                print(f"📄 {len(arquivos)} arquivo(s) de log encontrado(s):")
                for arquivo in arquivos:
                    print(f"   - {arquivo}")
                
                arquivo_escolhido = input("\nDigite o nome do arquivo para visualizar (ou ENTER para sair): ").strip()
                
                if arquivo_escolhido and arquivo_escolhido in arquivos:
                    try:
                        with open(os.path.join(log_dir, arquivo_escolhido), 'r', encoding='utf-8') as f:
                            print(f"\n📋 Conteúdo de {arquivo_escolhido}:")
                            print("-" * 50)
                            print(f.read())
                    except Exception as e:
                        print(f"❌ Erro ao ler arquivo: {e}")
            else:
                print("ℹ️ Nenhum log de equipamentos encontrado.")
        else:
            print("ℹ️ Diretório de logs não encontrado.")
        
        self.pausar()
    
    def estatisticas_producao(self):
        """Estatísticas de produção"""
        self.limpar_tela()
        print("📈 ESTATÍSTICAS DE PRODUÇÃO")
        print("=" * 40)
        print("ℹ️ Funcionalidade em desenvolvimento...")
        print("📊 Em breve: métricas de eficiência, tempo médio por produto, utilização de equipamentos...")
        self.pausar()

    # =============================================================================
    #                         6. MENU CONFIGURAÇÕES
    # =============================================================================
    
    def menu_configuracoes(self):
        """Menu de configurações do sistema"""
        while True:
            self.limpar_tela()
            print("⚙️ CONFIGURAÇÕES")
            print("=" * 30)
            print("1️⃣  Horários de Produção")  # Nome mais descritivo
            print("2️⃣  Configurar Estoque de Teste")
            print("3️⃣  Caminhos dos Arquivos")
            print("4️⃣  Limpar Logs")
            print("5️⃣  Sobre o Sistema")
            print("0️⃣  Voltar ao Menu Principal")
            print()
            
            opcao = input("🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.configurar_horarios()
            elif opcao == "2":
                if self.sistema_inicializado:
                    self._configurar_estoque_teste()
                    print("✅ Estoque de teste configurado!")
                    self.pausar()
                else:
                    print("⚠️ Sistema não inicializado!")
                    self.pausar()
            elif opcao == "3":
                self.configurar_caminhos()
            elif opcao == "4":
                self.limpar_logs()
            elif opcao == "5":
                self.sobre_sistema()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida!")
                self.pausar()
    
    def configurar_horarios(self):
        """Configura horários padrão do sistema - usuário define fim desejado, início calculado automaticamente"""
        self.limpar_tela()
        print("⏰ CONFIGURAR HORÁRIOS DE PRODUÇÃO")
        print("=" * 50)
        
        duracao_atual = self.fim_jornada_padrao - self.inicio_jornada_padrao
        print(f"📅 Configuração atual:")
        print(f"   🎯 Fim desejado: {self.fim_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
        print(f"   🔍 Início da busca: {self.inicio_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
        print(f"   ⏰ Janela total: {int(duracao_atual.total_seconds()/3600)} horas")
        
        print(f"\n💡 COMO FUNCIONA:")
        print(f"   🎯 Você define: QUANDO quer que a produção termine")
        print(f"   🔍 Sistema calcula: Janela de busca (72h antes por padrão)")
        print(f"   ⚙️ Algoritmo: Aloca atividades na melhor ordem dentro da janela")
        
        try:
            print(f"\n" + "="*50)
            print(f"📝 CONFIGURAÇÃO")
            
            # 1. Configurar fim desejado - SIMPLIFICADO
            novo_fim = input(f"\n🎯 Quando você quer que a produção termine?\n   Digite (DD/MM/AAAA HH:MM) ou ENTER para manter atual: ").strip()
            if novo_fim:
                try:
                    self.fim_jornada_padrao = datetime.strptime(novo_fim, '%d/%m/%Y %H:%M')
                    print(f"   ✅ Fim configurado para: {self.fim_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
                except ValueError:
                    print(f"   ❌ Formato inválido! Use DD/MM/AAAA HH:MM. Mantendo valor atual.")
            
            # 2. Configurar janela de busca - SIMPLIFICADO
            print(f"\n🔍 Quantas horas antes do fim quer iniciar a busca?")
            print(f"   💡 Recomendado: 72 horas (3 dias)")
            
            horas_input = input(f"   Digite número de horas (ou ENTER para 72h): ").strip()
            
            horas_janela = 72  # Valor padrão
            if horas_input:
                try:
                    horas_janela = int(horas_input)
                    if horas_janela < 1:
                        print(f"   ❌ Deve ser pelo menos 1 hora. Usando 72h.")
                        horas_janela = 72
                except ValueError:
                    print(f"   ❌ Valor inválido. Usando 72h.")
                    horas_janela = 72
            
            # 3. Calcular início automaticamente
            self.inicio_jornada_padrao = self.fim_jornada_padrao - timedelta(hours=horas_janela)
            
            # 4. Mostrar resultado final
            print(f"\n" + "="*50)
            print(f"✅ CONFIGURAÇÃO FINALIZADA")
            print(f"   🎯 Fim da produção: {self.fim_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🔍 Início da busca: {self.inicio_jornada_padrao.strftime('%d/%m/%Y %H:%M')}")
            print(f"   ⏰ Janela total: {horas_janela} horas")
            
            # 5. Atualizar pedidos existentes com novos horários
            if self.pedidos:
                print(f"\n🔄 Atualizando {len(self.pedidos)} pedidos existentes...")
                for pedido in self.pedidos:
                    pedido.inicio_jornada = self.inicio_jornada_padrao
                    pedido.fim_jornada = self.fim_jornada_padrao
                print(f"   ✅ Pedidos atualizados com novos horários")
        
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            print(f"🔄 Mantendo configuração anterior.")
        
        self.pausar()
    
    def configurar_caminhos(self):
        """Configura caminhos dos arquivos"""
        self.limpar_tela()
        print("📁 CONFIGURAR CAMINHOS DOS ARQUIVOS")
        print("=" * 40)
        
        print(f"Caminho atual dos produtos:")
        print(f"   📁 {self.caminho_produtos}")
        print(f"   {'✅ Existe' if os.path.exists(self.caminho_produtos) else '❌ Não existe'}")
        
        print(f"\nCaminho atual dos subprodutos:")
        print(f"   📁 {self.caminho_subprodutos}")
        print(f"   {'✅ Existe' if os.path.exists(self.caminho_subprodutos) else '❌ Não existe'}")
        
        print(f"\n📊 Produtos encontrados: {len(self.produtos_disponiveis)}")
        print(f"📊 Subprodutos encontrados: {len(self.subprodutos_disponiveis)}")
        
        resposta = input("\n🔄 Deseja alterar os caminhos? (s/N): ").strip().lower()
        
        if resposta in ['s', 'sim']:
            novo_caminho_produtos = input(f"\nNovo caminho para produtos (ENTER para manter atual):\n").strip()
            if novo_caminho_produtos:
                self.caminho_produtos = novo_caminho_produtos
            
            novo_caminho_subprodutos = input(f"\nNovo caminho para subprodutos (ENTER para manter atual):\n").strip()
            if novo_caminho_subprodutos:
                self.caminho_subprodutos = novo_caminho_subprodutos
            
            print("\n🔄 Recarregando produtos e subprodutos...")
            self._carregar_produtos_e_subprodutos()
            
            print("✅ Caminhos atualizados e itens recarregados!")
        
        self.pausar()
    
    def limpar_logs(self):
        """Limpa todos os logs do sistema"""
        resposta = input("⚠️ Confirma limpeza de todos os logs? (s/N): ").strip().lower()
        
        if resposta in ['s', 'sim']:
            try:
                limpar_todos_os_logs()
                apagar_todas_as_comandas()
                print("✅ Logs limpos com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao limpar logs: {e}")
        else:
            print("❌ Operação cancelada.")
        
        self.pausar()
    
    def sobre_sistema(self):
        """Informações sobre o sistema"""
        self.limpar_tela()
        print("ℹ️ SOBRE O SISTEMA")
        print("=" * 30)
        print("🏭 Sistema de Produção de Alimentos")
        print("📅 Versão: 2.0.0 - Versão Melhorada")
        print("👨‍💻 Desenvolvido com Python")
        print()
        print("🚀 Funcionalidades:")
        print("   ✅ Gestão completa de almoxarifado")
        print("   ✅ Carregamento automático de produtos/subprodutos")
        print("   ✅ Criação e execução de pedidos dinâmicos")
        print("   ✅ Otimização automática de estoque")
        print("   ✅ Alocação inteligente de equipamentos")
        print("   ✅ Logs detalhados e rastreabilidade")
        print("   ✅ Relatórios e análises")
        print("   ✅ Interface amigável e intuitiva")
        print()
        print("🆕 Novidades desta versão:")
        print("   🔹 Carregamento automático de arquivos JSON")
        print("   🔹 Suporte dinâmico para produtos e subprodutos")  
        print("   🔹 Interface melhorada para seleção de itens")
        print("   🔹 Configuração flexível de caminhos")
        print("   🔹 Sistema de janela de busca inteligente (72h padrão)")
        print("   🔹 Usuário define fim desejado, sistema calcula início")
        print("   🔹 Melhor organização e visualização")
        print()
        print(f"📁 Caminhos configurados:")
        print(f"   Produtos: {self.caminho_produtos}")
        print(f"   Subprodutos: {self.caminho_subprodutos}")
        print()
        print(f"📊 Itens carregados:")
        print(f"   🍞 {len(self.produtos_disponiveis)} produtos")
        print(f"   🥖 {len(self.subprodutos_disponiveis)} subprodutos")
        print()
        print("🎯 Sistema totalmente funcional e otimizado!")
        self.pausar()


def main():
    """Função principal que inicia o menu do sistema"""
    try:
        print("🚀 Iniciando Sistema de Produção de Alimentos v2.0")
        print("=" * 50)
        
        menu = MenuSistemaProducao()
        menu.menu_principal()
        
        print("\n👋 Obrigado por usar o Sistema de Produção de Alimentos!")
        print("🎯 Até a próxima!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Sistema encerrado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        logger.error(f"Erro crítico no menu: {e}")


if __name__ == "__main__":
    main()