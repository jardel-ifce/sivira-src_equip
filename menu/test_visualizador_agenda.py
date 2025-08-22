"""
Testes para VisualizadorAgenda com Navegação Hierárquica
======================================================

Testa todas as funcionalidades do módulo de visualização de agenda
com tipos hardcoded e instâncias dinâmicas.

Cobertura de testes:
- Navegação hierárquica por tipos
- Descoberta dinâmica de equipamentos
- Submenu por tipo de equipamento
- Agenda geral vs específica
- Integração com múltiplos gestores
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import os

# Adiciona o caminho do módulo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.visualizador_agenda import VisualizadorAgenda


class TestVisualizadorAgendaHierarquico(unittest.TestCase):
    """Testes para a nova versão hierárquica do VisualizadorAgenda"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.visualizador = VisualizadorAgenda()
        
        # Mock do GestorProducao com múltiplos gestores
        self.mock_gestor_producao = Mock()
        
        # Mock de equipamentos para masseiras
        self.mock_masseira = Mock()
        self.mock_masseira.nome = "Masseira 1"
        self.mock_masseira.ocupacoes = []
        self.mock_masseira.mostrar_agenda = Mock()
        
        # Mock de equipamentos para batedeiras
        self.mock_batedeira = Mock()
        self.mock_batedeira.nome = "Batedeira Planetária 1"
        self.mock_batedeira.ocupacoes = []
        self.mock_batedeira.mostrar_agenda = Mock()
        
        # Mock dos gestores
        self.mock_gestor_masseiras = Mock()
        self.mock_gestor_masseiras.masseiras = [self.mock_masseira]
        self.mock_gestor_masseiras.mostrar_agenda = Mock()
        
        self.mock_gestor_batedeiras = Mock()
        self.mock_gestor_batedeiras.batedeiras = [self.mock_batedeira]
        self.mock_gestor_batedeiras.mostrar_agenda = Mock()
        
        # Configura o gestor de produção com múltiplos gestores
        self.mock_gestor_producao.gestor_misturadoras = self.mock_gestor_masseiras
        self.mock_gestor_batedeiras = self.mock_gestor_batedeiras
    
    def test_tipos_equipamentos_constantes(self):
        """Testa se as constantes de tipos de equipamentos estão definidas"""
        tipos = VisualizadorAgenda.TIPOS_EQUIPAMENTOS
        
        self.assertIn("MISTURADORAS", tipos)
        self.assertIn("BATEDEIRAS", tipos)
        self.assertIn("FORNOS", tipos)
        
        # Testa estrutura de cada tipo
        tipo_masseiras = tipos["MISTURADORAS"]
        self.assertIn("nome_display", tipo_masseiras)
        self.assertIn("gestor_attr", tipo_masseiras)
        self.assertIn("equipamentos_attr", tipo_masseiras)
        
        self.assertEqual(tipo_masseiras["nome_display"], "Misturadoras")
        self.assertEqual(tipo_masseiras["gestor_attr"], "gestor_misturadoras")
        self.assertEqual(tipo_masseiras["equipamentos_attr"], "masseiras")
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_obter_tipos_disponiveis(self, mock_gestor_class):
        """Testa obtenção de tipos disponíveis baseado em gestores ativos"""
        # Configura mock - apenas gestor de masseiras disponível
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        tipos_disponiveis = self.visualizador._obter_tipos_disponiveis()
        
        self.assertIn("MISTURADORAS", tipos_disponiveis)
        self.assertEqual(tipos_disponiveis["MISTURADORAS"]["nome_display"], "Misturadoras")
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_obter_tipos_disponiveis_sem_gestores(self, mock_gestor_class):
        """Testa quando nenhum gestor está disponível"""
        # Gestor sem atributos de gestores específicos
        gestor_vazio = Mock()
        mock_gestor_class.return_value = gestor_vazio
        self.visualizador._inicializar_gestor_producao()
        
        tipos_disponiveis = self.visualizador._obter_tipos_disponiveis()
        
        self.assertEqual(tipos_disponiveis, {})
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_obter_equipamentos_tipo_sucesso(self, mock_gestor_class):
        """Testa obtenção de equipamentos de um tipo específico"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        equipamentos = self.visualizador._obter_equipamentos_tipo("MISTURADORAS")
        
        self.assertEqual(len(equipamentos), 1)
        self.assertEqual(equipamentos[0], self.mock_masseira)
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_obter_equipamentos_tipo_inexistente(self, mock_gestor_class):
        """Testa obtenção de equipamentos para tipo que não existe"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        equipamentos = self.visualizador._obter_equipamentos_tipo("TIPO_INEXISTENTE")
        
        self.assertEqual(equipamentos, [])
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_menu_agenda_com_tipos(self, mock_gestor_class, mock_print):
        """Testa exibição do menu principal com tipos disponíveis"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        
        self.visualizador.mostrar_menu_agenda()
        
        # Verifica se mostrou o cabeçalho
        mock_print.assert_any_call("📅 AGENDA DE EQUIPAMENTOS")
        # Verifica se mostrou pelo menos um tipo
        mock_print.assert_any_call("1️⃣  Misturadoras")
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_menu_agenda_sem_tipos(self, mock_gestor_class, mock_print):
        """Testa exibição quando não há tipos disponíveis"""
        # Gestor sem gestores específicos
        gestor_vazio = Mock()
        mock_gestor_class.return_value = gestor_vazio
        
        self.visualizador.mostrar_menu_agenda()
        
        mock_print.assert_any_call("❌ Nenhum tipo de equipamento disponível")
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_processar_opcao_agenda_valida(self, mock_gestor_class):
        """Testa processamento de opção válida do menu"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        with patch.object(self.visualizador, '_mostrar_submenu_tipo_equipamento', return_value=True) as mock_submenu:
            resultado = self.visualizador.processar_opcao_agenda("1")
        
        self.assertTrue(resultado)
        mock_submenu.assert_called_once_with("MISTURADORAS")
    
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_processar_opcao_agenda_sair(self, mock_gestor_class):
        """Testa opção de sair (0)"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        resultado = self.visualizador.processar_opcao_agenda("0")
        
        self.assertFalse(resultado)
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_processar_opcao_agenda_invalida(self, mock_gestor_class, mock_print):
        """Testa processamento de opção inválida"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        resultado = self.visualizador.processar_opcao_agenda("999")
        
        self.assertTrue(resultado)
        mock_print.assert_any_call("❌ Opção '999' inválida!")
    
    @patch('builtins.input')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_submenu_tipo_equipamento(self, mock_gestor_class, mock_input):
        """Testa submenu para tipo específico de equipamento"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        # Simula escolha da opção "voltar"
        mock_input.return_value = "0"
        
        with patch.object(self.visualizador.utils, 'limpar_tela'):
            with patch('builtins.print') as mock_print:
                resultado = self.visualizador._mostrar_submenu_tipo_equipamento("MISTURADORAS")
        
        self.assertTrue(resultado)
        mock_print.assert_any_call("📋 Tipo: Misturadoras")
        mock_print.assert_any_call("1️⃣  Mostrar agenda de todos os equipamentos")
        mock_print.assert_any_call("2️⃣  Escolher equipamento específico")
    
    @patch('builtins.input')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_submenu_opcao_agenda_todos(self, mock_gestor_class, mock_input):
        """Testa opção de mostrar agenda de todos os equipamentos"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        # Simula escolha da opção "1" e depois "0" para voltar
        mock_input.side_effect = ["1", "0"]
        
        with patch.object(self.visualizador.utils, 'limpar_tela'):
            with patch.object(self.visualizador, '_mostrar_agenda_todos_equipamentos') as mock_agenda:
                resultado = self.visualizador._mostrar_submenu_tipo_equipamento("MISTURADORAS")
        
        mock_agenda.assert_called_once_with("MISTURADORAS")
    
    @patch('builtins.input')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_submenu_opcao_equipamento_especifico(self, mock_gestor_class, mock_input):
        """Testa opção de escolher equipamento específico"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        # Simula escolha da opção "2" e depois "0" para voltar
        mock_input.side_effect = ["2", "0"]
        
        with patch.object(self.visualizador.utils, 'limpar_tela'):
            with patch.object(self.visualizador, '_mostrar_submenu_equipamento_especifico') as mock_especifico:
                resultado = self.visualizador._mostrar_submenu_tipo_equipamento("MISTURADORAS")
        
        mock_especifico.assert_called_once_with("MISTURADORAS")
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_agenda_todos_equipamentos(self, mock_gestor_class, mock_print):
        """Testa exibição da agenda de todos os equipamentos de um tipo"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        self.visualizador._mostrar_agenda_todos_equipamentos("MISTURADORAS")
        
        mock_print.assert_any_call("📅 AGENDA DE TODOS OS MISTURADORAS")
        self.mock_gestor_masseiras.mostrar_agenda.assert_called_once()
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_agenda_todos_sem_metodo(self, mock_gestor_class, mock_print):
        """Testa quando gestor não tem método mostrar_agenda"""
        # Remove método mostrar_agenda do mock
        del self.mock_gestor_masseiras.mostrar_agenda
        
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        self.visualizador._mostrar_agenda_todos_equipamentos("MISTURADORAS")
        
        mock_print.assert_any_call("❌ Método mostrar_agenda não disponível para Misturadoras")
    
    @patch('builtins.input')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_submenu_equipamento_especifico(self, mock_gestor_class, mock_input):
        """Testa submenu para seleção de equipamento específico"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        # Simula escolha do primeiro equipamento e depois voltar
        mock_input.side_effect = ["1", "0"]
        
        with patch.object(self.visualizador.utils, 'limpar_tela'):
            with patch.object(self.visualizador, '_mostrar_agenda_equipamento_individual') as mock_individual:
                with patch('builtins.print') as mock_print:
                    self.visualizador._mostrar_submenu_equipamento_especifico("MISTURADORAS")
        
        mock_print.assert_any_call("📋 Selecione o equipamento:")
        mock_print.assert_any_call("1️⃣  Masseira 1 (0 ocupação(ões))")
        mock_individual.assert_called_once_with(self.mock_masseira)
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_agenda_equipamento_individual_com_metodo(self, mock_gestor_class, mock_print):
        """Testa exibição de agenda individual quando equipamento tem método próprio"""
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        self.visualizador._mostrar_agenda_equipamento_individual(self.mock_masseira)
        
        mock_print.assert_any_call("📅 AGENDA: Masseira 1")
        self.mock_masseira.mostrar_agenda.assert_called_once()
    
    @patch('builtins.print')
    @patch('menu.visualizador_agenda.GestorProducao')
    def test_mostrar_agenda_equipamento_individual_sem_metodo(self, mock_gestor_class, mock_print):
        """Testa exibição de agenda individual quando equipamento não tem método próprio"""
        # Remove método mostrar_agenda do equipamento
        del self.mock_masseira.mostrar_agenda
        
        mock_gestor_class.return_value = self.mock_gestor_producao
        self.visualizador._inicializar_gestor_producao()
        
        self.visualizador._mostrar_agenda_equipamento_individual(self.mock_masseira)
        
        mock_print.assert_any_call("📅 AGENDA: Masseira 1")
        # Deve chamar _mostrar_agenda_manual porque tem ocupacoes
        mock_print.assert_any_call("🔧 Masseira 1")
    
    @patch('builtins.print')
    def test_mostrar_agenda_manual(self, mock_print):
        """Testa exibição manual de agenda"""
        # Equipamento com ocupação
        ocupacao = (1, 1, 1, 1001, 2000.0, [], None, 
                   datetime(2025, 8, 20, 10, 0), 
                   datetime(2025, 8, 20, 12, 0))
        self.mock_masseira.ocupacoes = [ocupacao]
        self.mock_masseira.capacidade_gramas_min = 3000
        self.mock_masseira.capacidade_gramas_max = 50000
        
        self.visualizador._mostrar_agenda_manual(self.mock_masseira)
        
        mock_print.assert_any_call("🔧 Masseira 1")
        mock_print.assert_any_call("📊 Capacidade: 3000g - 50000g")
        mock_print.assert_any_call("📋 Ocupações ativas: 1")
        mock_print.assert_any_call("   • Ordem 1 | Pedido 1 | Item 1001")
        mock_print.assert_any_call("     2000.0g | 10:00 → 12:00")
    
    @patch('builtins.print')
    def test_mostrar_agenda_manual_sem_ocupacoes(self, mock_print):
        """Testa exibição manual quando não há ocupações"""
        self.mock_masseira.ocupacoes = []
        
        self.visualizador._mostrar_agenda_manual(self.mock_masseira)
        
        mock_print.assert_any_call("🔧 Masseira 1")
        mock_print.assert_any_call("   📭 Nenhuma ocupação")
    
    def test_buscar_ocupacoes_periodo_tipo(self):
        """Testa busca de ocupações por período em um tipo específico"""
        # Adiciona ocupação à masseira
        inicio_oc = datetime(2025, 8, 20, 10, 0)
        fim_oc = datetime(2025, 8, 20, 12, 0)
        ocupacao = (1, 1, 1, 1001, 2000.0, [], None, inicio_oc, fim_oc)
        
        self.mock_masseira.ocupacoes = [ocupacao]
        self.mock_masseira.obter_ocupacoes_periodo = Mock(return_value=[ocupacao])
        
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        # Busca no período que inclui a ocupação
        inicio_busca = datetime(2025, 8, 20, 9, 0)
        fim_busca = datetime(2025, 8, 20, 13, 0)
        
        resultado = self.visualizador._buscar_ocupacoes_periodo_tipo("MISTURADORAS", inicio_busca, fim_busca)
        
        self.assertEqual(len(resultado), 1)
        self.assertIn("Masseira 1", resultado[0])
        self.assertIn("Ordem 1", resultado[0])
    
    def test_buscar_ocupacoes_item_tipo(self):
        """Testa busca de ocupações por item em um tipo específico"""
        # Adiciona ocupação do item 1001
        ocupacao = (1, 1, 1, 1001, 2000.0, [], None, 
                   datetime(2025, 8, 20, 10, 0), 
                   datetime(2025, 8, 20, 12, 0))
        self.mock_masseira.ocupacoes = [ocupacao]
        
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        resultado = self.visualizador._buscar_ocupacoes_item_tipo("MISTURADORAS", 1001)
        
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['quantidade'], 2000.0)
        self.assertIn("Masseira 1", resultado[0]['descricao'])
    
    def test_calcular_estatisticas_tipo(self):
        """Testa cálculo de estatísticas para um tipo específico"""
        # Adiciona ocupação e capacidade
        self.mock_masseira.ocupacoes = [Mock()]  # Uma ocupação
        self.mock_masseira.capacidade_gramas_max = 50000
        
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        resultado = self.visualizador._calcular_estatisticas_tipo("MISTURADORAS")
        
        self.assertIn('Total de equipamentos', resultado)
        self.assertIn('Total de ocupações ativas', resultado)
        self.assertIn('Capacidade total máxima', resultado)
        
        self.assertEqual(resultado['Total de equipamentos'], '1')
        self.assertEqual(resultado['Total de ocupações ativas'], '1')
        self.assertEqual(resultado['Capacidade total máxima'], '50000g')
    
    def test_obter_status_tipo_livre(self):
        """Testa obtenção de status quando equipamento está livre"""
        self.mock_masseira.ocupacoes = []
        self.mock_masseira.obter_proxima_liberacao = Mock(return_value=None)
        
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        agora = datetime.now()
        resultado = self.visualizador._obter_status_tipo("MISTURADORAS", agora)
        
        self.assertIn("Masseira 1", resultado)
        self.assertEqual(resultado["Masseira 1"], "Livre")
    
    def test_obter_status_tipo_ocupado(self):
        """Testa obtenção de status quando equipamento está ocupado"""
        # Ocupação ativa (agora está dentro do período)
        agora = datetime.now()
        inicio = agora - timedelta(hours=1)
        fim = agora + timedelta(hours=1)
        ocupacao = (1, 1, 1, 1001, 2000.0, [], None, inicio, fim)
        self.mock_masseira.ocupacoes = [ocupacao]
        
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        resultado = self.visualizador._obter_status_tipo("MISTURADORAS", agora)
        
        self.assertIn("Masseira 1", resultado)
        self.assertIn("Ocupado", resultado["Masseira 1"])
    
    def test_verificar_disponibilidade_tipo_disponivel(self):
        """Testa verificação de disponibilidade quando equipamento está disponível"""
        self.mock_masseira.esta_disponivel = Mock(return_value=True)
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        inicio = datetime.now()
        fim = inicio + timedelta(hours=2)
        
        resultado = self.visualizador._verificar_disponibilidade_tipo("MISTURADORAS", inicio, fim)
        
        self.assertIn("Masseira 1", resultado)
        self.assertEqual(resultado["Masseira 1"], "Disponível")
    
    def test_verificar_disponibilidade_tipo_ocupado(self):
        """Testa verificação quando equipamento está ocupado"""
        self.mock_masseira.esta_disponivel = Mock(return_value=False)
        self.visualizador.gestor_producao = self.mock_gestor_producao
        
        inicio = datetime.now()
        fim = inicio + timedelta(hours=2)
        
        resultado = self.visualizador._verificar_disponibilidade_tipo("MISTURADORAS", inicio, fim)
        
        self.assertIn("Masseira 1", resultado)
        self.assertEqual(resultado["Masseira 1"], "Ocupado")


class TestVisualizadorAgendaCompatibilidade(unittest.TestCase):
    """Testes para métodos de compatibilidade com versão anterior"""
    
    def setUp(self):
        """Setup para testes de compatibilidade"""
        self.visualizador = VisualizadorAgenda()
        
        # Setup básico com gestor de masseiras
        self.mock_gestor_producao = Mock()
        self.mock_masseira = Mock()
        self.mock_masseira.nome = "Masseira Test"
        self.mock_masseira.ocupacoes = []
        
        self.mock_gestor_masseiras = Mock()
        self.mock_gestor_masseiras.masseiras = [self.mock_masseira]
        self.mock_gestor_masseiras.mostrar_agenda = Mock()
        
        self.mock_gestor_producao.gestor_misturadoras = self.mock_gestor_masseiras
    