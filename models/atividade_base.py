from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from models.equips.equipamento import Equipamento


class Atividade(ABC):
    """
    Classe abstrata base para todas as atividades de produção.
    """

    def __init__(
        self,
        id: int,
        tipo_atividade: TipoAtividade,
        tipos_profissionais_permitidos: List[TipoProfissional],
        quantidade_funcionarios: int,
        equipamentos_elegiveis: List[Equipamento],
        quantidade_produto: float,
        fips_equipamentos: Optional[Dict[Equipamento, int]] = None
    ):
        # ===========================
        # 🎯 Atributos principais
        # ===========================
        self.id = id
        self.tipo_atividade = tipo_atividade
        self.tipos_profissionais_permitidos = tipos_profissionais_permitidos
        self.quantidade_funcionarios = max(1, quantidade_funcionarios)  # não aceita zero
        self.equipamentos_elegiveis = equipamentos_elegiveis
        self.equipamentos_selecionados: List[Equipamento] = []

        # ===========================
        # 📦 Produto e alocação
        # ===========================
        self.quantidade_produto = quantidade_produto
        self.funcionarios_alocados: List = []
        self.alocada = False

        # ===========================
        # ⏳ Tempo da atividade
        # ===========================
        self.duracao: timedelta = timedelta(0)
        self.inicio_previsto: Optional[datetime] = None
        self.fim_previsto: Optional[datetime] = None

        # ===========================
        # ⚙️ FIP dos equipamentos
        # ===========================
        self.fips_equipamentos: Dict[Equipamento, int] = fips_equipamentos or {}

        # ===========================
        # 🧠 Cálculo de duração
        # ===========================
        self.calcular_duracao()

    # ============================================
    # ⏳ Agenda
    # ============================================

    def definir_agenda(self, inicio: datetime):
        self.inicio_previsto = inicio
        self.fim_previsto = inicio + self.duracao

    # ============================================
    # 🔧 Métodos abstratos
    # ============================================

    @abstractmethod
    def calcular_duracao(self):
        """
        Subclasse implementa: calcula a duração da atividade.
        """
        pass

    @abstractmethod
    def iniciar(self):
        """
        Subclasse implementa: executa a lógica da atividade.
        """
        pass

    # ============================================
    # 🔍 Visualização e Status
    # ============================================

    def __str__(self):
        return (
            f"\n🆔 Atividade: {self.tipo_atividade.name} (ID: {self.id})"
            f"\n📦 Quantidade Produto: {self.quantidade_produto}"
            f"\n👥 Funcionários necessários: {self.quantidade_funcionarios}"
            f"\n👷‍♂️ Funcionários alocados: {len(self.funcionarios_alocados)}"
            f"\n🛠️ Equipamentos elegíveis: {[e.nome for e in self.equipamentos_elegiveis]}"
            f"\n🔧 Equipamentos selecionados: {[e.nome for e in self.equipamentos_selecionados]}"
            f"\n🧠 Alocada: {self.alocada}"
            f"\n⏳ Duração: {self.duracao}"
            f"\n🕐 Início previsto: {self.inicio_previsto}"
            f"\n🕔 Fim previsto: {self.fim_previsto}\n"
        )

    def resumo(self):
        """
        Retorna um resumo simples da atividade para logs rápidos.
        """
        return (
            f"[{self.tipo_atividade.name} ID {self.id}] "
            f"{self.inicio_previsto.strftime('%H:%M') if self.inicio_previsto else '??:??'} - "
            f"{self.fim_previsto.strftime('%H:%M') if self.fim_previsto else '??:??'} | "
            f"{'Alocada' if self.alocada else 'Não Alocada'}"
        )
