"""
Validador de Ocupações
=======================

Valida ocupações recuperadas para garantir integridade.
"""

from typing import List, Tuple, Optional
from datetime import datetime
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ValidadorOcupacoes:
    """
    ✅ Validador de ocupações recuperadas

    Verifica:
    - Sobreposições temporais indevidas
    - Horários válidos
    - IDs válidos
    - Consistência dos dados
    """

    def __init__(self):
        """Inicializa validador"""
        self.erros: List[str] = []
        self.avisos: List[str] = []

    def validar_lista_ocupacoes(self, ocupacoes: List[OcupacaoDTO]) -> bool:
        """
        Valida uma lista de ocupações

        Args:
            ocupacoes: Lista de ocupações a validar

        Returns:
            True se todas as ocupações são válidas
        """
        self.limpar()

        if not ocupacoes:
            self.adicionar_aviso("Lista de ocupações está vazia")
            return True

        valido = True

        for i, ocupacao in enumerate(ocupacoes):
            if not self.validar_ocupacao_individual(ocupacao, i):
                valido = False

        return valido

    def validar_ocupacao_individual(self, ocupacao: OcupacaoDTO, indice: int = 0) -> bool:
        """
        Valida uma ocupação individual

        Args:
            ocupacao: Ocupação a validar
            indice: Índice na lista (para mensagens de erro)

        Returns:
            True se ocupação é válida
        """
        valido = True

        # Validar IDs
        if ocupacao.id_ordem <= 0:
            self.adicionar_erro(f"Ocupação {indice}: id_ordem inválido ({ocupacao.id_ordem})")
            valido = False

        if ocupacao.id_pedido <= 0:
            self.adicionar_erro(f"Ocupação {indice}: id_pedido inválido ({ocupacao.id_pedido})")
            valido = False

        if ocupacao.id_atividade <= 0:
            self.adicionar_erro(f"Ocupação {indice}: id_atividade inválido ({ocupacao.id_atividade})")
            valido = False

        if ocupacao.id_item < 0:  # Item pode ser 0 em alguns casos
            self.adicionar_erro(f"Ocupação {indice}: id_item inválido ({ocupacao.id_item})")
            valido = False

        # Validar horários
        if ocupacao.fim <= ocupacao.inicio:
            self.adicionar_erro(
                f"Ocupação {indice}: fim ({ocupacao.fim}) deve ser posterior ao início ({ocupacao.inicio})"
            )
            valido = False

        # Validar duração razoável (não mais de 24 horas)
        if ocupacao.duracao_minutos > 1440:  # 24 horas
            self.adicionar_aviso(
                f"Ocupação {indice}: duração muito longa ({ocupacao.duracao_minutos} minutos)"
            )

        # Validar duração mínima (pelo menos 1 minuto)
        if ocupacao.duracao_minutos < 1:
            self.adicionar_aviso(
                f"Ocupação {indice}: duração muito curta ({ocupacao.duracao_minutos} minutos)"
            )

        return valido

    def validar_sobreposicoes_por_recurso(
        self,
        ocupacoes: List[OcupacaoDTO],
        chave_recurso: str
    ) -> List[Tuple[OcupacaoDTO, OcupacaoDTO]]:
        """
        Detecta sobreposições temporais para o mesmo recurso

        Args:
            ocupacoes: Lista de ocupações
            chave_recurso: Chave do detalhe que identifica o recurso
                          (ex: "fracao_numero", "boca_numero")

        Returns:
            Lista de pares de ocupações que se sobrepõem
        """
        sobreposicoes = []

        # Agrupar por recurso
        recursos = {}
        for ocupacao in ocupacoes:
            recurso_id = ocupacao.obter_detalhe(chave_recurso)
            if recurso_id is None:
                continue

            if recurso_id not in recursos:
                recursos[recurso_id] = []
            recursos[recurso_id].append(ocupacao)

        # Verificar sobreposições dentro de cada recurso
        for recurso_id, ocupacoes_recurso in recursos.items():
            for i, ocupacao1 in enumerate(ocupacoes_recurso):
                for ocupacao2 in ocupacoes_recurso[i+1:]:
                    if self._tem_sobreposicao_temporal(
                        ocupacao1.inicio, ocupacao1.fim,
                        ocupacao2.inicio, ocupacao2.fim
                    ):
                        sobreposicoes.append((ocupacao1, ocupacao2))
                        self.adicionar_erro(
                            f"Sobreposição no recurso {recurso_id}: "
                            f"{ocupacao1} sobrepõe {ocupacao2}"
                        )

        return sobreposicoes

    def _tem_sobreposicao_temporal(
        self,
        inicio1: datetime,
        fim1: datetime,
        inicio2: datetime,
        fim2: datetime
    ) -> bool:
        """
        Verifica se dois períodos têm sobreposição temporal

        Args:
            inicio1, fim1: Primeiro período
            inicio2, fim2: Segundo período

        Returns:
            True se há sobreposição
        """
        return not (fim1 <= inicio2 or inicio1 >= fim2)

    def validar_ordem_cronologica(self, ocupacoes: List[OcupacaoDTO]) -> bool:
        """
        Valida se ocupações estão em ordem cronológica

        Args:
            ocupacoes: Lista de ocupações

        Returns:
            True se estão em ordem
        """
        if len(ocupacoes) <= 1:
            return True

        valido = True
        for i in range(len(ocupacoes) - 1):
            if ocupacoes[i].inicio > ocupacoes[i+1].inicio:
                self.adicionar_aviso(
                    f"Ocupações fora de ordem cronológica: "
                    f"índice {i} ({ocupacoes[i].inicio}) > índice {i+1} ({ocupacoes[i+1].inicio})"
                )
                valido = False

        return valido

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

    def gerar_relatorio(self) -> str:
        """Gera relatório de validação"""
        linhas = []
        linhas.append("=" * 60)
        linhas.append("📋 RELATÓRIO DE VALIDAÇÃO DE OCUPAÇÕES")
        linhas.append("=" * 60)

        if not self.tem_erros() and not self.tem_avisos():
            linhas.append("✅ Nenhum erro ou aviso encontrado")
        else:
            if self.tem_erros():
                linhas.append(f"\n❌ ERROS ({len(self.erros)}):")
                for erro in self.erros:
                    linhas.append(f"   • {erro}")

            if self.tem_avisos():
                linhas.append(f"\n⚠️  AVISOS ({len(self.avisos)}):")
                for aviso in self.avisos:
                    linhas.append(f"   • {aviso}")

        linhas.append("=" * 60)
        return "\n".join(linhas)
