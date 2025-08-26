import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import os

# Adicionar o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.consolidacao.consolidador_simples import ConsolidadorSimples
from enums.producao.tipo_item import TipoItem


class TestConsolidadorSimples(unittest.TestCase):
    """Testes para a classe ConsolidadorSimples"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        # Mock de PedidoDeProducao
        self.pedido1 = Mock()
        self.pedido1.id_pedido = 1001
        self.pedido1.consolidar_subprodutos = True
        self.pedido1.lotes_consolidados = {}
        
        self.pedido2 = Mock()
        self.pedido2.id_pedido = 1002
        self.pedido2.consolidar_subprodutos = True
        self.pedido2.lotes_consolidados = {}
        
        self.pedido3 = Mock()
        self.pedido3.id_pedido = 1003
        self.pedido3.consolidar_subprodutos = False
        self.pedido3.lotes_consolidados = {}
        
        # Mock de FichaTecnicaModular
        self.ficha_mock = Mock()
        self.pedido1.ficha_tecnica_modular = self.ficha_mock
        self.pedido2.ficha_tecnica_modular = self.ficha_mock
        self.pedido3.ficha_tecnica_modular = self.ficha_mock
    
    def test_processar_pedidos_lista_vazia(self):
        """Testa comportamento com lista vazia de pedidos"""
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            ConsolidadorSimples.processar_pedidos([])
            mock_logger.debug.assert_called_with("Lista de pedidos vazia. Nada a processar.")
    
    def test_processar_pedidos_sem_consolidacao(self):
        """Testa comportamento quando nenhum pedido quer consolidação"""
        # Configurar pedidos sem consolidação
        pedidos = [self.pedido3]  # pedido3.consolidar_subprodutos = False
        
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            ConsolidadorSimples.processar_pedidos(pedidos)
            mock_logger.debug.assert_called_with("Nenhum pedido configurado para consolidação.")
    
    def test_extrair_subprodutos_sucesso(self):
        """Testa extração de subprodutos de um pedido"""
        # Mock do retorno de calcular_quantidade_itens
        estimativas_mock = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 1000.0),
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2003}, 500.0),
            ({"tipo_item": "INSUMO", "id_ficha_tecnica": 3001}, 200.0)  # Não deve ser incluído
        ]
        self.ficha_mock.calcular_quantidade_itens.return_value = estimativas_mock
        
        resultado = ConsolidadorSimples._extrair_subprodutos(self.pedido1)
        
        expected = {2002: 1000.0, 2003: 500.0}
        self.assertEqual(resultado, expected)
    
    def test_extrair_subprodutos_sem_ficha_tecnica(self):
        """Testa extração quando pedido não tem ficha técnica"""
        pedido_sem_ficha = Mock()
        pedido_sem_ficha.id_pedido = 9999
        pedido_sem_ficha.ficha_tecnica_modular = None
        
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            resultado = ConsolidadorSimples._extrair_subprodutos(pedido_sem_ficha)
            
            self.assertEqual(resultado, {})
            mock_logger.warning.assert_called_with("Pedido 9999 sem ficha técnica montada")
    
    def test_mapear_demandas_subprodutos(self):
        """Testa mapeamento de demandas por subproduto"""
        # Configurar retornos de _extrair_subprodutos
        with patch.object(ConsolidadorSimples, '_extrair_subprodutos') as mock_extrair:
            mock_extrair.side_effect = [
                {2002: 1000.0, 2003: 300.0},  # pedido1
                {2002: 800.0, 2004: 200.0}    # pedido2
            ]
            
            pedidos = [self.pedido1, self.pedido2]
            resultado = ConsolidadorSimples._mapear_demandas_subprodutos(pedidos)
            
            expected = {
                2002: [(self.pedido1, 1000.0), (self.pedido2, 800.0)],
                2003: [(self.pedido1, 300.0)],
                2004: [(self.pedido2, 200.0)]
            }
            
            self.assertEqual(resultado, expected)
    
    def test_consolidar_subproduto_sucesso(self):
        """Testa consolidação de um subproduto entre dois pedidos"""
        demandas = [
            (self.pedido1, 1000.0),
            (self.pedido2, 800.0)
        ]
        
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            ConsolidadorSimples._consolidar_subproduto(2002, demandas)
            
            # Verificar se pedido1 se tornou mestre
            self.assertEqual(self.pedido1.lotes_consolidados[2002], 1800.0)
            
            # Verificar se pedido2 foi marcado como dependente
            self.assertEqual(self.pedido2.lotes_consolidados[2002], 0)
            
            # Verificar se log foi chamado
            self.assertTrue(mock_logger.info.called)
    
    def test_consolidar_subproduto_demandas_insuficientes(self):
        """Testa consolidação com menos de 2 demandas"""
        demandas = [(self.pedido1, 1000.0)]  # Apenas 1 demanda
        
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            ConsolidadorSimples._consolidar_subproduto(2002, demandas)
            
            # Não deve fazer nada
            self.assertEqual(len(self.pedido1.lotes_consolidados), 0)
            mock_logger.warning.assert_called()
    
    def test_consolidar_pedido_mestre_deterministico(self):
        """Testa que o pedido mestre é escolhido de forma determinística"""
        # Pedidos em ordem diferente
        demandas = [
            (self.pedido2, 800.0),  # ID maior
            (self.pedido1, 1000.0)  # ID menor
        ]
        
        ConsolidadorSimples._consolidar_subproduto(2002, demandas)
        
        # Pedido com menor ID deve ser mestre
        self.assertEqual(self.pedido1.lotes_consolidados[2002], 1800.0)
        self.assertEqual(self.pedido2.lotes_consolidados[2002], 0)
    
    def test_processar_pedidos_integracao_completa(self):
        """Teste de integração completo do processo de consolidação"""
        # Configurar estimativas das fichas técnicas
        estimativas_pedido1 = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 1000.0),
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2003}, 300.0)
        ]
        estimativas_pedido2 = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 800.0),
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2004}, 200.0)
        ]
        
        # Configurar mocks diferentes para cada pedido
        ficha_mock1 = Mock()
        ficha_mock1.calcular_quantidade_itens.return_value = estimativas_pedido1
        self.pedido1.ficha_tecnica_modular = ficha_mock1
        
        ficha_mock2 = Mock()
        ficha_mock2.calcular_quantidade_itens.return_value = estimativas_pedido2
        self.pedido2.ficha_tecnica_modular = ficha_mock2
        
        pedidos = [self.pedido1, self.pedido2]
        
        with patch('services.consolidacao.consolidador_simples.logger'):
            ConsolidadorSimples.processar_pedidos(pedidos)
        
        # Verificar consolidação do subproduto 2002 (presente em ambos)
        self.assertEqual(self.pedido1.lotes_consolidados[2002], 1800.0)  # Mestre
        self.assertEqual(self.pedido2.lotes_consolidados[2002], 0)       # Dependente
        
        # Verificar que subprodutos únicos não foram alterados
        self.assertNotIn(2003, self.pedido1.lotes_consolidados)  # Único do pedido1
        self.assertNotIn(2004, self.pedido2.lotes_consolidados)  # Único do pedido2
    
    def test_obter_resumo_consolidacoes(self):
        """Testa geração de resumo das consolidações"""
        # Configurar estado pós-consolidação
        self.pedido1.lotes_consolidados = {2002: 1800.0}  # Mestre
        self.pedido2.lotes_consolidados = {2002: 0}       # Dependente
        
        pedidos = [self.pedido1, self.pedido2]
        resumo = ConsolidadorSimples.obter_resumo_consolidacoes(pedidos)
        
        expected_keys = [
            'total_subprodutos_consolidados',
            'total_atividades_economizadas', 
            'detalhes_por_subproduto',
            'timestamp'
        ]
        
        for key in expected_keys:
            self.assertIn(key, resumo)
        
        self.assertEqual(resumo['total_subprodutos_consolidados'], 1)
        self.assertEqual(resumo['total_atividades_economizadas'], 1)
        self.assertIn(2002, resumo['detalhes_por_subproduto'])
    
    def test_processar_pedidos_com_excecao(self):
        """Testa comportamento quando há exceção durante processamento"""
        # Configurar mock para gerar exceção
        ficha_mock = Mock()
        ficha_mock.calcular_quantidade_itens.side_effect = Exception("Erro simulado")
        self.pedido1.ficha_tecnica_modular = ficha_mock
        
        pedidos = [self.pedido1]
        
        with patch('services.consolidacao.consolidador_simples.logger') as mock_logger:
            # Não deve gerar exceção, apenas log de erro
            ConsolidadorSimples.processar_pedidos(pedidos)
            mock_logger.error.assert_called()


class TestConsolidadorSimplesEdgeCases(unittest.TestCase):
    """Testes para casos extremos do ConsolidadorSimples"""
    
    def test_pedidos_mistos_consolidacao_habilitada_desabilitada(self):
        """Testa mistura de pedidos com e sem consolidação"""
        pedido_com_consolidacao = Mock()
        pedido_com_consolidacao.id_pedido = 1001
        pedido_com_consolidacao.consolidar_subprodutos = True
        pedido_com_consolidacao.lotes_consolidados = {}
        
        pedido_sem_consolidacao = Mock()
        pedido_sem_consolidacao.id_pedido = 1002
        pedido_sem_consolidacao.consolidar_subprodutos = False
        pedido_sem_consolidacao.lotes_consolidados = {}
        
        # Mock ficha técnica
        ficha_mock = Mock()
        ficha_mock.calcular_quantidade_itens.return_value = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 1000.0)
        ]
        pedido_com_consolidacao.ficha_tecnica_modular = ficha_mock
        pedido_sem_consolidacao.ficha_tecnica_modular = ficha_mock
        
        pedidos = [pedido_com_consolidacao, pedido_sem_consolidacao]
        
        with patch('services.consolidacao.consolidador_simples.logger'):
            ConsolidadorSimples.processar_pedidos(pedidos)
        
        # Apenas o pedido com consolidação habilitada deve ser processado
        # Como só há um pedido elegível, não há consolidação
        self.assertEqual(len(pedido_com_consolidacao.lotes_consolidados), 0)
        self.assertEqual(len(pedido_sem_consolidacao.lotes_consolidados), 0)
    
    def test_subprodutos_com_quantidade_zero(self):
        """Testa comportamento com subprodutos de quantidade zero"""
        estimativas = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 0.0),
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2003}, 100.0)
        ]
        
        ficha_mock = Mock()
        ficha_mock.calcular_quantidade_itens.return_value = estimativas
        
        pedido = Mock()
        pedido.id_pedido = 1001
        pedido.ficha_tecnica_modular = ficha_mock
        
        resultado = ConsolidadorSimples._extrair_subprodutos(pedido)
        
        # Deve incluir mesmo quantidades zero
        expected = {2002: 0.0, 2003: 100.0}
        self.assertEqual(resultado, expected)


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.getLogger('ConsolidadorSimples').setLevel(logging.CRITICAL)
    
    unittest.main()