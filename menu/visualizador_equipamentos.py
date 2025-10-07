"""
Módulo para visualização de equipamentos em memória.

Permite listar todos os equipamentos carregados no sistema com suas ocupações.
"""

import gc
from datetime import datetime
from typing import Dict, List, Type, Any


class VisualizadorEquipamentos:
    """
    Visualizador de equipamentos em memória.

    Responsabilidades:
    - Coletar equipamentos da memória usando garbage collector
    - Organizar equipamentos por tipo
    - Exibir listagem formatada
    """

    def __init__(self):
        """Inicializa o visualizador de equipamentos."""
        self.equipamentos_por_tipo: Dict[str, List[Any]] = {}
        self.total_equipamentos = 0

    def coletar_equipamentos(self) -> bool:
        """
        Coleta todos os equipamentos da memória.

        Returns:
            bool: True se encontrou equipamentos, False caso contrário
        """
        # Importa os módulos de equipamentos
        from models.equipamentos.forno import Forno
        from models.equipamentos.fogao import Fogao
        from models.equipamentos.batedeira_industrial import BatedeiraIndustrial
        from models.equipamentos.batedeira_planetaria import BatedeiraPlanetaria
        from models.equipamentos.masseira import Masseira
        from models.equipamentos.hot_mix import HotMix
        from models.equipamentos.modeladora_de_paes import ModeladoraDePaes
        from models.equipamentos.modeladora_de_salgados import ModeladoraDeSalgados
        from models.equipamentos.divisora_de_massas import DivisoraDeMassas
        from models.equipamentos.armario_fermentador import ArmarioFermentador
        from models.equipamentos.armario_esqueleto import ArmarioEsqueleto
        from models.equipamentos.bancada import Bancada
        from models.equipamentos.embaladora import Embaladora
        from models.equipamentos.fritadeira import Fritadeira
        from models.equipamentos.camara_refrigerada import CamaraRefrigerada
        from models.equipamentos.freezer import Freezer

        # Define tipos de equipamentos
        tipos_equipamentos = [
            ('Fornos', Forno),
            ('Fogões', Fogao),
            ('Batedeiras Industriais', BatedeiraIndustrial),
            ('Batedeiras Planetárias', BatedeiraPlanetaria),
            ('Masseiras', Masseira),
            ('HotMix', HotMix),
            ('Modeladoras de Pães', ModeladoraDePaes),
            ('Modeladoras de Salgados', ModeladoraDeSalgados),
            ('Divisoras de Massas', DivisoraDeMassas),
            ('Armários Fermentadores', ArmarioFermentador),
            ('Armários Esqueleto', ArmarioEsqueleto),
            ('Bancadas', Bancada),
            ('Embaladoras', Embaladora),
            ('Fritadeiras', Fritadeira),
            ('Câmaras Refrigeradas', CamaraRefrigerada),
            ('Freezers', Freezer)
        ]

        self.equipamentos_por_tipo = {}
        self.total_equipamentos = 0

        # Coleta equipamentos usando garbage collector
        for nome_tipo, classe in tipos_equipamentos:
            objetos = [obj for obj in gc.get_objects() if isinstance(obj, classe)]
            if objetos:
                self.equipamentos_por_tipo[nome_tipo] = objetos
                self.total_equipamentos += len(objetos)

        return self.total_equipamentos > 0

    def exibir_equipamentos(self) -> None:
        """Exibe a listagem formatada de equipamentos."""
        if self.total_equipamentos == 0:
            print("\n⚠️ Nenhum equipamento encontrado na memória")
            print("💡 Execute um pedido primeiro para carregar os equipamentos")
            return

        print(f"\n📊 Total de equipamentos em memória: {self.total_equipamentos}")
        print("\n" + "─" * 60)

        for nome_tipo, equipamentos in sorted(self.equipamentos_por_tipo.items()):
            print(f"\n🔧 {nome_tipo}: {len(equipamentos)} unidade(s)")
            print("─" * 60)

            for equip in sorted(equipamentos, key=lambda x: x.id):
                # Conta ocupações (diferentes formatos possíveis)
                num_ocupacoes = 0

                # Formato 1: lista de ocupações simples
                # Usado por: HotMix, Embaladora, Modeladora de Pães/Salgados, Balança Digital,
                #            Batedeira Planetária/Industrial, Masseira, Divisora de Massas
                if hasattr(equip, 'ocupacoes') and equip.ocupacoes:
                    num_ocupacoes = len(equip.ocupacoes)

                # Formato 2: lista de listas por níveis
                # Usado por: Forno, Câmara Refrigerada, Armário Fermentador, Armário Esqueleto
                elif hasattr(equip, 'niveis_ocupacoes') and equip.niveis_ocupacoes:
                    num_ocupacoes = sum(len(nivel) for nivel in equip.niveis_ocupacoes)

                # Formato 3: lista de listas por frações
                # Usado por: Bancada
                elif hasattr(equip, 'fracoes_ocupacoes') and equip.fracoes_ocupacoes:
                    num_ocupacoes = sum(len(fracao) for fracao in equip.fracoes_ocupacoes)

                # Formato 4: lista de listas por boca
                # Usado por: Fogão
                elif hasattr(equip, 'ocupacoes_por_boca') and equip.ocupacoes_por_boca:
                    num_ocupacoes = sum(len(boca) for boca in equip.ocupacoes_por_boca)

                # Formato 5: lista de listas por fração (diferente de bancada)
                # Usado por: Fritadeira
                elif hasattr(equip, 'ocupacoes_por_fracao') and equip.ocupacoes_por_fracao:
                    num_ocupacoes = sum(len(fracao) for fracao in equip.ocupacoes_por_fracao)

                # Exibe com ou sem ocupações
                if num_ocupacoes > 0:
                    print(f"  • ID: {equip.id:3d} | Nome: {equip.nome} | 📅 {num_ocupacoes} ocupação(ões)")
                else:
                    print(f"  • ID: {equip.id:3d} | Nome: {equip.nome}")

    def visualizar(self) -> None:
        """
        Método principal para visualizar equipamentos.

        Coleta e exibe os equipamentos em uma única chamada.
        """
        if self.coletar_equipamentos():
            self.exibir_equipamentos()
        else:
            print("\n⚠️ Nenhum equipamento encontrado na memória")
            print("💡 Execute um pedido primeiro para carregar os equipamentos")
