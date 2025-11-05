"""
Validador de Consistência
==========================

Valida consistência geral da recuperação de estado.
"""

from typing import List, Dict
from utils.recuperacao.modelos.estado_equipamento_dto import EstadoEquipamentoDTO


class ValidadorConsistencia:
    """
    🔍 Validador de consistência geral

    Verifica:
    - Todos os equipamentos foram processados
    - Não há equipamentos duplicados
    - Estatísticas são consistentes
    """

    def __init__(self):
        """Inicializa validador"""
        self.erros: List[str] = []
        self.avisos: List[str] = []

    def validar_estados_equipamentos(
        self,
        estados: List[EstadoEquipamentoDTO]
    ) -> bool:
        """
        Valida lista de estados de equipamentos

        Args:
            estados: Lista de estados de equipamentos

        Returns:
            True se todos os estados são consistentes
        """
        self.limpar()

        if not estados:
            self.adicionar_erro("Nenhum estado de equipamento para validar")
            return False

        valido = True

        # Verificar duplicatas
        if not self.verificar_duplicatas(estados):
            valido = False

        # Verificar estados individuais
        for estado in estados:
            if not self.validar_estado_individual(estado):
                valido = False

        return valido

    def validar_estado_individual(self, estado: EstadoEquipamentoDTO) -> bool:
        """
        Valida um estado individual de equipamento

        Args:
            estado: Estado a validar

        Returns:
            True se estado é válido
        """
        valido = True

        # Verificar nome
        if not estado.nome_equipamento or not estado.nome_equipamento.strip():
            self.adicionar_erro(f"Estado sem nome de equipamento")
            valido = False

        # Verificar tipo
        if not estado.tipo_equipamento or not estado.tipo_equipamento.strip():
            self.adicionar_erro(f"Estado {estado.nome_equipamento} sem tipo de equipamento")
            valido = False

        # Verificar consistência de ocupações
        if estado.tem_ocupacoes and not estado.equipamento_restaurado:
            self.adicionar_aviso(
                f"{estado.nome_equipamento}: tem ocupações mas não foi restaurado"
            )

        # Verificar erros
        if estado.tem_erros and estado.equipamento_restaurado:
            self.adicionar_aviso(
                f"{estado.nome_equipamento}: foi restaurado mas tem erros registrados"
            )

        return valido

    def verificar_duplicatas(self, estados: List[EstadoEquipamentoDTO]) -> bool:
        """
        Verifica se há equipamentos duplicados

        Args:
            estados: Lista de estados

        Returns:
            True se não há duplicatas
        """
        nomes_vistos = set()
        duplicatas = []

        for estado in estados:
            nome = estado.nome_equipamento
            if nome in nomes_vistos:
                duplicatas.append(nome)
                self.adicionar_erro(f"Equipamento duplicado: {nome}")
            nomes_vistos.add(nome)

        return len(duplicatas) == 0

    def verificar_cobertura_tipos(
        self,
        estados: List[EstadoEquipamentoDTO],
        tipos_esperados: List[str]
    ) -> bool:
        """
        Verifica se todos os tipos esperados foram processados

        Args:
            estados: Lista de estados
            tipos_esperados: Lista de tipos que deveriam estar presentes

        Returns:
            True se todos os tipos estão presentes
        """
        tipos_encontrados = set(e.tipo_equipamento for e in estados)
        tipos_faltantes = set(tipos_esperados) - tipos_encontrados

        if tipos_faltantes:
            for tipo in tipos_faltantes:
                self.adicionar_aviso(f"Tipo de equipamento não encontrado: {tipo}")
            return False

        return True

    def gerar_estatisticas(
        self,
        estados: List[EstadoEquipamentoDTO]
    ) -> Dict[str, int]:
        """
        Gera estatísticas sobre os estados

        Args:
            estados: Lista de estados

        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_equipamentos': len(estados),
            'equipamentos_com_ocupacoes': sum(1 for e in estados if e.tem_ocupacoes),
            'equipamentos_restaurados': sum(1 for e in estados if e.equipamento_restaurado),
            'equipamentos_com_erros': sum(1 for e in estados if e.tem_erros),
            'total_ocupacoes': sum(e.total_ocupacoes for e in estados),
            'total_erros': sum(len(e.erros) for e in estados)
        }

        return stats

    def adicionar_erro(self, erro: str):
        """Adiciona erro à lista"""
        self.erros.append(erro)

    def adicionar_aviso(self, aviso: str):
        """Adiciona aviso à lista"""
        self.avisos.append(aviso)

    def obter_erros(self) -> List[str]:
        """Retorna lista de erros"""
        return self.erros.copy()

    def obter_avisos(self) -> List[str]:
        """Retorna lista de avisos"""
        return self.avisos.copy()

    def tem_erros(self) -> bool:
        """Verifica se há erros"""
        return len(self.erros) > 0

    def tem_avisos(self) -> bool:
        """Verifica se há avisos"""
        return len(self.avisos) > 0

    def limpar(self):
        """Limpa erros e avisos"""
        self.erros.clear()
        self.avisos.clear()

    def gerar_relatorio(self, estados: List[EstadoEquipamentoDTO]) -> str:
        """
        Gera relatório de consistência

        Args:
            estados: Lista de estados para analisar

        Returns:
            String com relatório formatado
        """
        linhas = []
        linhas.append("=" * 60)
        linhas.append("🔍 RELATÓRIO DE CONSISTÊNCIA")
        linhas.append("=" * 60)

        # Estatísticas
        stats = self.gerar_estatisticas(estados)
        linhas.append("\n📊 ESTATÍSTICAS:")
        for chave, valor in stats.items():
            linhas.append(f"   • {chave.replace('_', ' ').title()}: {valor}")

        # Erros e avisos
        if not self.tem_erros() and not self.tem_avisos():
            linhas.append("\n✅ Nenhum problema de consistência encontrado")
        else:
            if self.tem_erros():
                linhas.append(f"\n❌ ERROS ({len(self.erros)}):")
                for erro in self.erros:
                    linhas.append(f"   • {erro}")

            if self.tem_avisos():
                linhas.append(f"\n⚠️  AVISOS ({len(self.avisos)}):")
                for aviso in self.avisos:
                    linhas.append(f"   • {aviso}")

        linhas.append("\n" + "=" * 60)
        return "\n".join(linhas)
