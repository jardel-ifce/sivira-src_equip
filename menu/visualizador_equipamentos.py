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
        from models.equipamentos.balanca_digital import BalancaDigital

        # Define tipos de equipamentos
        tipos_equipamentos = [
            ('Câmaras Refrigeradas', CamaraRefrigerada),
            ('Fogões', Fogao),
            ('Balanças Digitais', BalancaDigital),
            ('Bancadas', Bancada),
            ('Batedeiras Planetárias', BatedeiraPlanetaria),
            ('Batedeiras Industriais', BatedeiraIndustrial),
            ('Masseiras', Masseira),
            ('HotMix', HotMix),
            ('Freezers', Freezer),
            ('Fritadeiras', Fritadeira),
            ('Armários Esqueleto', ArmarioEsqueleto),
            ('Armários Fermentadores', ArmarioFermentador),
            ('Divisoras de Massas', DivisoraDeMassas),
            ('Modeladoras de Pães', ModeladoraDePaes),
            ('Modeladoras de Salgados', ModeladoraDeSalgados),
            ('Embaladoras', Embaladora),
            ('Fornos', Forno)
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
                    self._exibir_detalhes_ocupacoes(equip)
                else:
                    print(f"  • ID: {equip.id:3d} | Nome: {equip.nome}")

    def _exibir_detalhes_ocupacoes(self, equip: Any) -> None:
        """
        Exibe detalhes de todas as ocupações de um equipamento.

        Args:
            equip: Equipamento com ocupações
        """
        ocupacoes_formatadas = []

        # Formato 1: lista de ocupações simples
        if hasattr(equip, 'ocupacoes') and equip.ocupacoes:
            for ocupacao in equip.ocupacoes:
                ocupacoes_formatadas.append(self._formatar_ocupacao_simples(ocupacao))

        # Formato 2: lista de listas por níveis (Forno, Câmara, Armário)
        elif hasattr(equip, 'niveis_ocupacoes') and equip.niveis_ocupacoes:
            for nivel_idx, nivel in enumerate(equip.niveis_ocupacoes):
                for ocupacao in nivel:
                    ocupacoes_formatadas.append(self._formatar_ocupacao_nivel(ocupacao, nivel_idx, equip))

        # Formato 3: lista de listas por frações (Bancada)
        elif hasattr(equip, 'fracoes_ocupacoes') and equip.fracoes_ocupacoes:
            for fracao_idx, fracao in enumerate(equip.fracoes_ocupacoes):
                for ocupacao in fracao:
                    ocupacoes_formatadas.append(self._formatar_ocupacao_fracao(ocupacao, fracao_idx))

        # Formato 4: lista de listas por boca (Fogão)
        elif hasattr(equip, 'ocupacoes_por_boca') and equip.ocupacoes_por_boca:
            for boca_idx, boca in enumerate(equip.ocupacoes_por_boca):
                for ocupacao in boca:
                    ocupacoes_formatadas.append(self._formatar_ocupacao_boca(ocupacao, boca_idx))

        # Formato 5: lista de listas por fração (Fritadeira)
        elif hasattr(equip, 'ocupacoes_por_fracao') and equip.ocupacoes_por_fracao:
            for fracao_idx, fracao in enumerate(equip.ocupacoes_por_fracao):
                for ocupacao in fracao:
                    ocupacoes_formatadas.append(self._formatar_ocupacao_simples(ocupacao))

        # Exibe todas as ocupações
        for ocupacao_str in ocupacoes_formatadas:
            print(f"    {ocupacao_str}")

    def _formatar_ocupacao_simples(self, ocupacao: tuple) -> str:
        """Formata ocupação no formato simples."""
        try:
            # Formato com 9 campos (Masseira): (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidades, tipo_mistura, inicio, fim)
            if len(ocupacao) >= 9 and isinstance(ocupacao[5], list):
                id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidades, tipo_mistura, inicio, fim = ocupacao[:9]
                vel_str = ", ".join([v.name for v in velocidades]) if velocidades else "Nenhuma"
                return (
                    f"🗂️ Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                    f"Item {id_item} | {quantidade:.2f}g | Velocidades: {vel_str} | Tipo: {tipo_mistura.value if hasattr(tipo_mistura, 'value') else tipo_mistura} | "
                    f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
                )
            # Formato com 8 campos (Divisora): (id_ordem, id_pedido, id_atividade, id_item, quantidade, usa_boleadora, inicio, fim)
            elif len(ocupacao) >= 8 and isinstance(ocupacao[5], bool):
                id_ordem, id_pedido, id_atividade, id_item, quantidade, usa_boleadora, inicio, fim = ocupacao[:8]
                return (
                    f"🗂️ Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                    f"Item {id_item} | {quantidade:.2f}g | Boleadora: {'Sim' if usa_boleadora else 'Não'} | "
                    f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
                )
            # Formato padrão com 7 campos: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
            else:
                id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim = ocupacao[:7]
                return (
                    f"🗂️ Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                    f"Item {id_item} | {quantidade:.2f} unidades | "
                    f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
                )
        except (IndexError, AttributeError, ValueError) as e:
            return f"⚠️ Ocupação com formato inválido: {e}"

    def _formatar_ocupacao_nivel(self, ocupacao: tuple, nivel_idx: int, equip: Any) -> str:
        """Formata ocupação com indicação de nível."""
        try:
            id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim = ocupacao[:7]

            # Tentar obter informação específica do nível
            nivel_info = f"Nível {nivel_idx + 1}"
            if hasattr(equip, 'obter_andar_e_nivel_por_indice'):
                try:
                    andar, nivel = equip.obter_andar_e_nivel_por_indice(nivel_idx)
                    nivel_info = f"Andar {andar}, Nível {nivel}"
                except:
                    pass

            return (
                f"🗂️ {nivel_info} | Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                f"Item {id_item} | {quantidade:.2f} unidades | "
                f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
            )
        except (IndexError, AttributeError, ValueError):
            return "⚠️ Ocupação com formato inválido"

    def _formatar_ocupacao_fracao(self, ocupacao: tuple, fracao_idx: int) -> str:
        """Formata ocupação com indicação de fração."""
        try:
            id_ordem, id_pedido, id_atividade, id_item, inicio, fim = ocupacao[:6]
            return (
                f"🗂️ Fração {fracao_idx + 1} | Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                f"Item {id_item} | "
                f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
            )
        except (IndexError, AttributeError, ValueError):
            return "⚠️ Ocupação com formato inválido"

    def _formatar_ocupacao_boca(self, ocupacao: tuple, boca_idx: int) -> str:
        """Formata ocupação com indicação de boca (Fogão tem 9 campos)."""
        try:
            # Fogão: (id_ordem, id_pedido, id_atividade, id_item, quantidade, tipo_chama, pressoes_chama, inicio, fim)
            id_ordem, id_pedido, id_atividade, id_item, quantidade, tipo_chama, pressoes_chama, inicio, fim = ocupacao[:9]
            pressoes_str = ", ".join([p.value for p in pressoes_chama]) if pressoes_chama else "Nenhuma"
            return (
                f"🗂️ Boca {boca_idx + 1} | Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                f"Item {id_item} | {quantidade:.2f}g | Chama: {tipo_chama.value if hasattr(tipo_chama, 'value') else tipo_chama} | Pressões: {pressoes_str} | "
                f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
            )
        except (IndexError, AttributeError, ValueError) as e:
            return f"⚠️ Ocupação com formato inválido: {e}"

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
