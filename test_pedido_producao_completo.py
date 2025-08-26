import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enums.producao.tipo_item import TipoItem


class TestPedidoDeProducaoConsolidacao(unittest.TestCase):
    """Testes para as modificações de consolidação no PedidoDeProducao"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        # Mock das dependências necessárias
        self.mock_funcionario = Mock()
        self.mock_gestor_almoxarifado = Mock()
        
        # Parâmetros base para criação do pedido
        self.pedido_params = {
            'id_ordem': 1001,
            'id_pedido': 2001,
            'id_produto': 1002,
            'tipo_item': TipoItem.PRODUTO,
            'quantidade': 100,
            'inicio_jornada': datetime(2024, 1, 15, 6, 0),
            'fim_jornada': datetime(2024, 1, 15, 18, 0),
            'todos_funcionarios': [self.mock_funcionario],
            'gestor_almoxarifado': self.mock_gestor_almoxarifado
        }
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_init_sem_consolidacao(self, mock_setup_logger, mock_logger):
        """Testa inicialização de pedido sem consolidação (comportamento padrão)"""
        mock_setup_logger.return_value = mock_logger
        
        # Importar dentro do teste para evitar problemas de import
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(**self.pedido_params)
        
        # Verificar propriedades de consolidação
        self.assertFalse(pedido.consolidar_subprodutos)
        self.assertEqual(pedido.lotes_consolidados, {})
        
        # Verificar que log foi chamado com status correto
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        self.assertIn("sem consolidação", log_call)
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_init_com_consolidacao(self, mock_setup_logger, mock_logger):
        """Testa inicialização de pedido com consolidação habilitada"""
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        
        # Verificar propriedades de consolidação
        self.assertTrue(pedido.consolidar_subprodutos)
        self.assertEqual(pedido.lotes_consolidados, {})
        
        # Verificar que log foi chamado com status correto
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        self.assertIn("COM consolidação", log_call)
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    @patch('models.atividades.pedido_de_producao.debug_atividades')
    @patch('models.atividades.pedido_de_producao.buscar_atividades_por_id_item')
    def test_criar_atividades_recursivas_subproduto_consolidado_skipado(
        self, 
        mock_buscar_atividades, 
        mock_debug, 
        mock_setup_logger, 
        mock_logger
    ):
        """Testa que subproduto já processado em lote é pulado"""
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        
        # Simular que subproduto 2002 já foi processado por outro pedido
        pedido.lotes_consolidados = {2002: 0}  # 0 = já processado
        
        # Mock da ficha técnica
        ficha_mock = Mock()
        ficha_mock.tipo_item = TipoItem.SUBPRODUTO
        ficha_mock.id_item = 2002
        ficha_mock.quantidade_requerida = 100
        
        pedido._criar_atividades_recursivas(ficha_mock)
        
        # Verificar que log correto foi chamado
        mock_logger.info.assert_called()
        calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("já processado em lote consolidado" in call for call in calls))
        
        # Verificar que buscar_atividades não foi chamado (pois foi pulado)
        mock_buscar_atividades.assert_not_called()
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    @patch('models.atividades.pedido_de_producao.debug_atividades')
    @patch('models.atividades.pedido_de_producao.buscar_atividades_por_id_item')
    def test_criar_atividades_recursivas_pedido_mestre_lote(
        self, 
        mock_buscar_atividades, 
        mock_debug, 
        mock_setup_logger, 
        mock_logger
    ):
        """Testa criação de atividades quando pedido é mestre do lote consolidado"""
        mock_setup_logger.return_value = mock_logger
        mock_buscar_atividades.return_value = []  # Sem atividades para simplificar
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        
        # Simular que este pedido é mestre do lote (quantidade maior que a original)
        pedido.lotes_consolidados = {2002: 500}  # Lote consolidado
        
        # Mock da ficha técnica
        ficha_mock = Mock()
        ficha_mock.tipo_item = TipoItem.SUBPRODUTO
        ficha_mock.id_item = 2002
        ficha_mock.quantidade_requerida = 100
        ficha_mock.dados_ficha_tecnica = {"mock": "data"}
        ficha_mock.peso_unitario = 65
        
        # Mock do método _criar_ficha_consolidada
        ficha_consolidada_mock = Mock()
        ficha_consolidada_mock.quantidade_requerida = 500
        ficha_consolidada_mock.tipo_item = TipoItem.SUBPRODUTO
        ficha_consolidada_mock.id_item = 2002
        
        with patch.object(pedido, '_criar_ficha_consolidada', return_value=ficha_consolidada_mock):
            with patch.object(pedido, '_verificar_estoque_suficiente', return_value=False):
                pedido._criar_atividades_recursivas(ficha_mock)
                
                # Verificar que método de criar ficha consolidada foi chamado
                pedido._criar_ficha_consolidada.assert_called_once_with(ficha_mock, 500)
                
                # Verificar log de lote mestre
                mock_logger.info.assert_called()
                calls = [call[0][0] for call in mock_logger.info.call_args_list]
                self.assertTrue(any("LOTE CONSOLIDADO" in call for call in calls))
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    @patch('models.atividades.pedido_de_producao.FichaTecnicaModular')
    def test_criar_ficha_consolidada(self, mock_ficha_tecnica, mock_setup_logger, mock_logger):
        """Testa criação de ficha técnica consolidada"""
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(**self.pedido_params)
        
        # Mock da ficha original
        ficha_original = Mock()
        ficha_original.id_item = 2002
        ficha_original.quantidade_requerida = 100
        ficha_original.dados_ficha_tecnica = {"test": "data"}
        ficha_original.nome = "massa_suave"
        ficha_original.descricao = "Massa Suave"
        
        # Mock da nova instância criada
        ficha_consolidada_mock = Mock()
        mock_ficha_tecnica.return_value = ficha_consolidada_mock
        
        resultado = pedido._criar_ficha_consolidada(ficha_original, 500)
        
        # Verificar que nova instância foi criada com quantidade correta
        mock_ficha_tecnica.assert_called_once_with(
            dados_ficha_tecnica={"test": "data"},
            quantidade_requerida=500
        )
        
        # Verificar que propriedades foram preservadas
        self.assertEqual(ficha_consolidada_mock.nome, "massa_suave")
        self.assertEqual(ficha_consolidada_mock.descricao, "Massa Suave")
        
        self.assertEqual(resultado, ficha_consolidada_mock)
    
    @patch('models.atividades.pedido_de_producao.logger')
    @patch('models.atividades.pedido_de_producao.setup_logger')
    @patch('models.atividades.pedido_de_producao.FichaTecnicaModular')
    def test_criar_ficha_consolidada_com_erro(self, mock_ficha_tecnica, mock_setup_logger, mock_logger):
        """Testa criação de ficha consolidada com erro (deve retornar original)"""
        mock_setup_logger.return_value = mock_logger
        mock_ficha_tecnica.side_effect = Exception("Erro teste")
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(**self.pedido_params)
        ficha_original = Mock()
        
        resultado = pedido._criar_ficha_consolidada(ficha_original, 500)
        
        # Deve retornar a ficha original em caso de erro
        self.assertEqual(resultado, ficha_original)
        
        # Deve ter logado o erro
        mock_logger.error.assert_called()
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_obter_pedidos_beneficiados(self, mock_setup_logger):
        """Testa obtenção de pedidos beneficiados por lote consolidado"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(**self.pedido_params)
        
        resultado = pedido._obter_pedidos_beneficiados(2002)
        
        # Por simplicidade, deve retornar apenas o pedido atual
        self.assertEqual(resultado, [pedido.id_pedido])
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_obter_resumo_pedido_com_consolidacao(self, mock_setup_logger):
        """Testa resumo do pedido incluindo informações de consolidação"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        
        # Simular estado pós-consolidação
        pedido.lotes_consolidados = {2002: 500, 2003: 0}  # Mestre de 2002, dependente de 2003
        
        # Mock de atividades com flag de consolidação
        atividade_consolidada = Mock()
        atividade_consolidada.alocada = True
        atividade_consolidada.eh_lote_consolidado = True
        atividade_consolidada.inicio_real = datetime(2024, 1, 15, 8, 0)
        atividade_consolidada.fim_real = datetime(2024, 1, 15, 10, 0)
        
        atividade_normal = Mock()
        atividade_normal.alocada = True
        atividade_normal.eh_lote_consolidado = False
        atividade_normal.inicio_real = datetime(2024, 1, 15, 11, 0)
        atividade_normal.fim_real = datetime(2024, 1, 15, 12, 0)
        
        pedido.atividades_modulares = [atividade_consolidada, atividade_normal]
        
        resumo = pedido.obter_resumo_pedido()
        
        # Verificar informações básicas
        self.assertTrue(resumo['consolidacao_habilitada'])
        self.assertEqual(resumo['lotes_consolidados'], {2002: 500, 2003: 0})
        self.assertEqual(resumo['atividades_consolidadas'], 1)
        self.assertTrue(resumo['eh_pedido_mestre'])  # Tem quantidade > 0
        self.assertTrue(resumo['eh_pedido_dependente'])  # Tem quantidade = 0
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_repr_com_consolidacao_mestre(self, mock_setup_logger):
        """Testa representação string do pedido mestre"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        pedido.lotes_consolidados = {2002: 500}  # Pedido mestre
        
        repr_str = repr(pedido)
        
        self.assertIn("[MESTRE]", repr_str)
        self.assertIn(f"PedidoDeProducao {pedido.id_pedido}", repr_str)
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_repr_com_consolidacao_dependente(self, mock_setup_logger):
        """Testa representação string do pedido dependente"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        pedido.lotes_consolidados = {2002: 0}  # Pedido dependente
        
        repr_str = repr(pedido)
        
        self.assertIn("[DEPENDENTE]", repr_str)
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_repr_com_consolidacao_habilitada_sem_lotes(self, mock_setup_logger):
        """Testa representação quando consolidação está habilitada mas não há lotes"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=True, **self.pedido_params)
        # lotes_consolidados vazio
        
        repr_str = repr(pedido)
        
        self.assertIn("[CONSOLIDAÇÃO]", repr_str)
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_repr_sem_consolidacao(self, mock_setup_logger):
        """Testa representação normal sem consolidação"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(consolidar_subprodutos=False, **self.pedido_params)
        
        repr_str = repr(pedido)
        
        # Não deve conter indicadores de consolidação
        self.assertNotIn("[MESTRE]", repr_str)
        self.assertNotIn("[DEPENDENTE]", repr_str)
        self.assertNotIn("[CONSOLIDAÇÃO]", repr_str)


class TestPedidoDeProducaoDuracaoConsolidada(unittest.TestCase):
    """Testes específicos para recálculo de duração em lotes consolidados"""
    
    def setUp(self):
        self.pedido_params = {
            'id_ordem': 1001,
            'id_pedido': 2001,
            'id_produto': 1002,
            'tipo_item': TipoItem.PRODUTO,
            'quantidade': 100,
            'inicio_jornada': datetime(2024, 1, 15, 6, 0),
            'fim_jornada': datetime(2024, 1, 15, 18, 0),
            'consolidar_subprodutos': True
        }
    
    @patch('models.atividades.pedido_de_producao.FichaTecnicaModular')
    def test_recalculo_duracao_lote_consolidado(self, mock_ficha_tecnica):
        """Testa se a duração é recalculada corretamente para lotes consolidados"""
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        pedido = PedidoDeProducao(**self.pedido_params)
        
        # Mock da ficha original (100 unidades)
        ficha_original = Mock()
        ficha_original.id_item = 2002
        ficha_original.quantidade_requerida = 100
        ficha_original.dados_ficha_tecnica = {
            "faixas": [
                {"quantidade_min": 1, "quantidade_max": 150, "duracao": "00:07:00"},
                {"quantidade_min": 151, "quantidade_max": 300, "duracao": "00:11:00"},
                {"quantidade_min": 301, "quantidade_max": 500, "duracao": "00:15:00"}
            ]
        }
        
        # Mock da ficha consolidada que será criada (500 unidades - muda de faixa!)
        ficha_consolidada_mock = Mock()
        ficha_consolidada_mock.quantidade_requerida = 500
        mock_ficha_tecnica.return_value = ficha_consolidada_mock
        
        resultado = pedido._criar_ficha_consolidada(ficha_original, 500)
        
        # Verificar que foi criada com nova quantidade (que deve recalcular duração)
        mock_ficha_tecnica.assert_called_once_with(
            dados_ficha_tecnica=ficha_original.dados_ficha_tecnica,
            quantidade_requerida=500  # Esta quantidade mudará a faixa de duração!
        )
        
        # Verificar que o resultado é a ficha consolidada
        self.assertEqual(resultado, ficha_consolidada_mock)
        
        # Verificar que propriedades foram preservadas se existirem
        if hasattr(ficha_original, 'nome'):
            self.assertEqual(ficha_consolidada_mock.nome, ficha_original.nome)
        if hasattr(ficha_original, 'descricao'):
            self.assertEqual(ficha_consolidada_mock.descricao, ficha_original.descricao)


class TestPedidoDeProducaoConsolidacaoIntegracao(unittest.TestCase):
    """Testes de integração para funcionalidades de consolidação"""
    
    def setUp(self):
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    @patch('services.consolidacao.consolidador_simples.logger')
    def test_fluxo_completo_consolidacao(self, mock_consolidador_logger, mock_setup_logger):
        """Testa fluxo completo de consolidação entre dois pedidos"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        mock_consolidador_logger.info = Mock()
        mock_consolidador_logger.debug = Mock()
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        from services.consolidacao.consolidador_simples import ConsolidadorSimples
        
        # Criar dois pedidos com consolidação habilitada
        pedido_params = {
            'id_ordem': 1001,
            'id_produto': 1002,
            'tipo_item': TipoItem.PRODUTO,
            'quantidade': 100,
            'inicio_jornada': datetime(2024, 1, 15, 6, 0),
            'fim_jornada': datetime(2024, 1, 15, 18, 0),
            'consolidar_subprodutos': True
        }
        
        pedido1 = PedidoDeProducao(id_pedido=2001, **pedido_params)
        pedido2 = PedidoDeProducao(id_pedido=2002, **pedido_params)
        
        # Mock das fichas técnicas
        ficha1 = Mock()
        ficha1.calcular_quantidade_itens.return_value = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 100)
        ]
        
        ficha2 = Mock()
        ficha2.calcular_quantidade_itens.return_value = [
            ({"tipo_item": "SUBPRODUTO", "id_ficha_tecnica": 2002}, 150)
        ]
        
        pedido1.ficha_tecnica_modular = ficha1
        pedido2.ficha_tecnica_modular = ficha2
        
        # Processar consolidação
        ConsolidadorSimples.processar_pedidos([pedido1, pedido2])
        
        # Verificar que consolidação foi aplicada
        self.assertEqual(pedido1.lotes_consolidados[2002], 250)  # Mestre (menor ID)
        self.assertEqual(pedido2.lotes_consolidados[2002], 0)    # Dependente


class TestPedidoDeProducaoBackwardCompatibility(unittest.TestCase):
    """Testes de compatibilidade com sistema existente"""
    
    @patch('models.atividades.pedido_de_producao.setup_logger')
    def test_comportamento_identico_sem_consolidacao(self, mock_setup_logger):
        """Testa que pedidos sem consolidação funcionam exatamente como antes"""
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        from models.atividades.pedido_de_producao import PedidoDeProducao
        
        # Parâmetros idênticos ao sistema antigo (sem consolidar_subprodutos)
        pedido_params = {
            'id_ordem': 1001,
            'id_pedido': 2001,
            'id_produto': 1002,
            'tipo_item': TipoItem.PRODUTO,
            'quantidade': 100,
            'inicio_jornada': datetime(2024, 1, 15, 6, 0),
            'fim_jornada': datetime(2024, 1, 15, 18, 0)
        }
        
        pedido = PedidoDeProducao(**pedido_params)
        
        # Deve funcionar exatamente como antes
        self.assertFalse(pedido.consolidar_subprodutos)
        self.assertEqual(pedido.lotes_consolidados, {})
        
        # Resumo não deve conter flags de consolidação ativas
        resumo = pedido.obter_resumo_pedido()
        self.assertFalse(resumo['consolidacao_habilitada'])
        self.assertFalse(resumo['eh_pedido_mestre'])
        self.assertFalse(resumo['eh_pedido_dependente'])


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    unittest.main()