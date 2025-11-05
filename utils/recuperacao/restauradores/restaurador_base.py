"""
Classe Base para Restauradores de Equipamentos
===============================================

Define interface comum para todos os restauradores de estado.
"""

from abc import ABC, abstractmethod
from typing import List, Any
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class RestauradorBase(ABC):
    """
    🔧 Classe base abstrata para restauradores de equipamentos

    Cada restaurador específico deve:
    1. Herdar desta classe
    2. Implementar o método restaurar()
    3. Modificar o objeto equipamento passado, adicionando ocupações

    O restaurador é responsável por:
    - Receber lista de OcupacaoDTO (saída do parser)
    - Localizar ou validar o equipamento correto
    - Restaurar as estruturas internas do equipamento:
      * fracoes_ocupacoes (Bancada)
      * ocupacoes_por_boca (Fogão)
      * niveis_ocupacoes (Câmara)
      * ocupacoes (Masseira, Batedeira, etc.)
    - Reportar erros encontrados
    """

    def __init__(self):
        """Inicializa restaurador base"""
        self.erros: List[str] = []

    @abstractmethod
    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Any) -> bool:
        """
        Método abstrato que deve ser implementado por cada restaurador específico

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto equipamento onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        pass

    # ==========================================================
    # 🔧 UTILITÁRIOS DE VALIDAÇÃO
    # ==========================================================

    def validar_tipo_equipamento(self, equipamento: Any, tipo_esperado: type) -> bool:
        """
        Valida se o equipamento é do tipo esperado

        Args:
            equipamento: Objeto equipamento
            tipo_esperado: Tipo/classe esperado(a)

        Returns:
            True se for do tipo correto
        """
        if not isinstance(equipamento, tipo_esperado):
            erro = f"Equipamento deve ser do tipo {tipo_esperado.__name__}, mas é {type(equipamento).__name__}"
            self.adicionar_erro(erro)
            return False
        return True

    def validar_ocupacoes_nao_vazias(self, ocupacoes: List[OcupacaoDTO]) -> bool:
        """
        Valida se há ocupações para restaurar

        Args:
            ocupacoes: Lista de ocupações

        Returns:
            True se há ocupações
        """
        if not ocupacoes:
            self.adicionar_erro("Lista de ocupações está vazia")
            return False
        return True

    def validar_indice_valido(self, indice: int, tamanho_maximo: int, nome_estrutura: str) -> bool:
        """
        Valida se índice está dentro dos limites

        Args:
            indice: Índice a validar
            tamanho_maximo: Tamanho máximo permitido
            nome_estrutura: Nome da estrutura (para mensagem de erro)

        Returns:
            True se índice é válido
        """
        if indice < 0 or indice >= tamanho_maximo:
            erro = f"Índice {indice} inválido para {nome_estrutura} (máximo: {tamanho_maximo - 1})"
            self.adicionar_erro(erro)
            return False
        return True

    # ==========================================================
    # 🔧 UTILITÁRIOS DE CONVERSÃO
    # ==========================================================

    def converter_ocupacao_para_tupla_basica(self, ocupacao: OcupacaoDTO) -> tuple:
        """
        Converte OcupacaoDTO para tupla básica (comum a muitos equipamentos)

        Format: (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)

        Args:
            ocupacao: OcupacaoDTO

        Returns:
            Tupla com dados básicos
        """
        return (
            ocupacao.id_ordem,
            ocupacao.id_pedido,
            ocupacao.id_atividade,
            ocupacao.id_item,
            ocupacao.inicio,
            ocupacao.fim
        )

    # ==========================================================
    # 🔧 GERENCIAMENTO DE ERROS
    # ==========================================================

    def adicionar_erro(self, erro: str):
        """Adiciona erro à lista de erros"""
        self.erros.append(erro)

    def obter_erros(self) -> List[str]:
        """Retorna lista de erros encontrados"""
        return self.erros.copy()

    def limpar_erros(self):
        """Limpa lista de erros"""
        self.erros.clear()

    def tem_erros(self) -> bool:
        """Verifica se há erros"""
        return len(self.erros) > 0

    # ==========================================================
    # 🔧 UTILITÁRIOS DE LOG
    # ==========================================================

    def log_restauracao_inicio(self, equipamento: Any, total_ocupacoes: int):
        """Log de início de restauração"""
        nome = getattr(equipamento, 'nome', 'Equipamento desconhecido')
        print(f"🔧 Restaurando {nome}: {total_ocupacoes} ocupação(ões)")

    def log_restauracao_sucesso(self, equipamento: Any, total_restauradas: int):
        """Log de sucesso na restauração"""
        nome = getattr(equipamento, 'nome', 'Equipamento desconhecido')
        print(f"✅ {nome}: {total_restauradas} ocupação(ões) restauradas")

    def log_restauracao_erro(self, equipamento: Any, erro: str):
        """Log de erro na restauração"""
        nome = getattr(equipamento, 'nome', 'Equipamento desconhecido')
        print(f"❌ {nome}: {erro}")

    # ==========================================================
    # 🔧 UTILITÁRIOS DE BACKUP (para rollback futuro)
    # ==========================================================

    def criar_backup_ocupacoes(self, equipamento: Any) -> Any:
        """
        Cria backup do estado atual de ocupações do equipamento

        Args:
            equipamento: Objeto equipamento

        Returns:
            Estrutura com backup (varia por tipo de equipamento)
        """
        # Implementação específica em cada subclasse se necessário
        # Por padrão, retorna None
        return None

    def restaurar_backup_ocupacoes(self, equipamento: Any, backup: Any):
        """
        Restaura ocupações a partir de backup

        Args:
            equipamento: Objeto equipamento
            backup: Estrutura de backup

        Útil para rollback em caso de erro durante restauração
        """
        # Implementação específica em cada subclasse se necessário
        pass
