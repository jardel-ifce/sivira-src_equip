import sys
import os
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import unittest
from datetime import timedelta
from models.atividades.mistura_de_massas_crocantes import MisturaDeMassasCrocantes
from models.equips.masseira import Masseira
from enums.tipo_profissional import TipoProfissional
from enums.tipo_equipamento import TipoEquipamento

class TestMisturaDeMassasCrocantes(unittest.TestCase):

    def setUp(self):
        # Cria um mock simples da Masseira
        self.masseira = Masseira(
            id=1,
            descricao="Masseira Industrial A",
            setor="Produção",
            fatorDeImportancia=1,
            capacidade_valor_maximo=720,
            capacidade_valor_minimo=30,
            capacidade_unidade="unidade",
            tipo_armazenamento=None
        )

        # Simula equipamentos elegíveis
        self.equipamentos = [self.masseira]

        # Cria atividade
        self.atividade = MisturaDeMassasCrocantes(
            id=101,
            tipos_profissionais_permitidos=[TipoProfissional.PADEIRO],
            quantidade_funcionarios=1,
            equipamentos_elegiveis=self.equipamentos,
            quantidade_produto=300
        )

    def test_quantidade_por_tipo_equipamento(self):
        esperado = {TipoEquipamento.MISTURADORAS: 1}
        self.assertEqual(self.atividade.quantidade_por_tipo_equipamento, esperado)

    def test_calcular_duracao(self):
        self.atividade.calcular_duracao()
        self.assertEqual(self.atividade.duracao, timedelta(minutes=6))

    def test_iniciar_sem_alocacao(self):
        with self.assertRaises(Exception) as context:
            self.atividade.iniciar()
        self.assertIn("Atividade não alocada", str(context.exception))

    def test_iniciar_com_alocacao(self):
        # Força o cenário como se tivesse sido alocada
        self.atividade.alocada = True
        self.atividade.equipamentos_selecionados = [self.masseira]

        # Cria flag para verificar se o método ocupar foi chamado
        chamada = {"foi_chamado": False}

        def mock_ocupar(quantidade):
            chamada["foi_chamado"] = True
            self.assertEqual(quantidade, 300)

        # Substitui o método ocupar da masseira pelo mock
        self.masseira.ocupar = mock_ocupar

        # Testa iniciar
        self.atividade.iniciar()
        self.assertTrue(chamada["foi_chamado"])

if __name__ == '__main__':
    unittest.main()
