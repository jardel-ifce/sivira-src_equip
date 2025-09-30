#!/usr/bin/env python3
"""
🔍 ANALISADOR DE CONFLITOS DE OCUPAÇÕES
======================================

Módulo para analisar e explicar falhas na alocação de funcionários,
mostrando conflitos temporais e sugestões de reagendamento.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from models.funcionarios.funcionario import Funcionario
from enums.funcionarios.tipo_profissional import TipoProfissional


class TipoConflito(Enum):
    """Tipos de conflitos possíveis."""
    OCUPADO_OUTRO_PEDIDO = "ocupado_outro_pedido"
    OCUPADO_MESMA_ATIVIDADE = "ocupado_mesma_atividade"
    FOLGA = "folga"
    FORA_TURNO = "fora_turno"
    INTERVALO = "intervalo"
    SEM_FUNCIONARIO_TIPO = "sem_funcionario_tipo"


@dataclass
class ConflitoDeTempo:
    """Representa um conflito temporal específico."""
    funcionario: Funcionario
    tipo_conflito: TipoConflito
    inicio_conflito: datetime
    fim_conflito: datetime
    atividade_conflitante: Optional[str] = None
    ordem_conflitante: Optional[int] = None
    pedido_conflitante: Optional[int] = None
    detalhes: Optional[str] = None


@dataclass
class AnaliseConflito:
    """Resultado da análise de um conflito."""
    id_atividade: int
    nome_atividade: str
    tipos_necessarios: List[TipoProfissional]
    quantidade_necessaria: int
    horario_inicio: datetime
    horario_fim: datetime
    funcionarios_elegiveis: List[Funcionario]
    conflitos: List[ConflitoDeTempo]
    funcionarios_disponiveis: List[Funcionario]
    sugestoes_reagendamento: List[str]


class AnalisadorConflitos:
    """
    🔍 Analisa conflitos de alocação de funcionários e gera relatórios detalhados.
    """

    def __init__(self, funcionarios: List[Funcionario]):
        self.funcionarios = funcionarios

    def analisar_falha_alocacao(
        self,
        id_atividade: int,
        nome_atividade: str,
        tipos_necessarios: List[TipoProfissional],
        quantidade_necessaria: int,
        inicio: datetime,
        fim: datetime
    ) -> AnaliseConflito:
        """
        Analisa por que uma alocação falhou.

        Args:
            id_atividade: ID da atividade
            nome_atividade: Nome da atividade
            tipos_necessarios: Tipos profissionais necessários
            quantidade_necessaria: Quantidade de funcionários necessários
            inicio: Horário de início
            fim: Horário de fim

        Returns:
            AnaliseConflito com detalhes da falha
        """
        # 1. Encontrar funcionários elegíveis por tipo
        funcionarios_elegiveis = self._filtrar_funcionarios_elegiveis(tipos_necessarios)

        # 2. Analisar conflitos para cada funcionário elegível
        conflitos = []
        funcionarios_disponiveis = []

        for funcionario in funcionarios_elegiveis:
            conflito = self._analisar_conflito_funcionario(funcionario, inicio, fim)
            if conflito:
                conflitos.append(conflito)
            else:
                funcionarios_disponiveis.append(funcionario)

        # 3. Gerar sugestões de reagendamento
        sugestoes = self._gerar_sugestoes_reagendamento(
            funcionarios_elegiveis, inicio, fim, quantidade_necessaria
        )

        return AnaliseConflito(
            id_atividade=id_atividade,
            nome_atividade=nome_atividade,
            tipos_necessarios=tipos_necessarios,
            quantidade_necessaria=quantidade_necessaria,
            horario_inicio=inicio,
            horario_fim=fim,
            funcionarios_elegiveis=funcionarios_elegiveis,
            conflitos=conflitos,
            funcionarios_disponiveis=funcionarios_disponiveis,
            sugestoes_reagendamento=sugestoes
        )

    def _filtrar_funcionarios_elegiveis(self, tipos_necessarios: List[TipoProfissional]) -> List[Funcionario]:
        """Filtra funcionários que têm os tipos profissionais necessários."""
        funcionarios_elegiveis = []

        for funcionario in self.funcionarios:
            # Verificar se há interseção entre tipos do funcionário e tipos necessários
            tipos_funcionario = set(funcionario.tipo_profissional)
            tipos_requeridos = set(tipos_necessarios)

            if tipos_funcionario.intersection(tipos_requeridos):
                funcionarios_elegiveis.append(funcionario)

        return funcionarios_elegiveis

    def _analisar_conflito_funcionario(
        self,
        funcionario: Funcionario,
        inicio: datetime,
        fim: datetime
    ) -> Optional[ConflitoDeTempo]:
        """Analisa se um funcionário tem conflito no horário especificado."""

        # 1. Verificar folga
        if funcionario.esta_de_folga(inicio) or funcionario.esta_de_folga(fim):
            return ConflitoDeTempo(
                funcionario=funcionario,
                tipo_conflito=TipoConflito.FOLGA,
                inicio_conflito=inicio,
                fim_conflito=fim,
                detalhes=f"Funcionário está de folga"
            )

        # 2. Verificar turno de trabalho
        inicio_turno = datetime.combine(inicio.date(), funcionario.horario_inicio_turno)
        fim_turno = datetime.combine(inicio.date(), funcionario.horario_final_turno)

        if inicio < inicio_turno or fim > fim_turno:
            return ConflitoDeTempo(
                funcionario=funcionario,
                tipo_conflito=TipoConflito.FORA_TURNO,
                inicio_conflito=inicio,
                fim_conflito=fim,
                detalhes=f"Fora do turno {funcionario.horario_inicio_turno}-{funcionario.horario_final_turno}"
            )

        # 3. Verificar intervalo
        inicio_intv, duracao_intv = funcionario.horario_intervalo
        inicio_intervalo = datetime.combine(inicio.date(), inicio_intv)
        fim_intervalo = inicio_intervalo + duracao_intv

        if not (fim <= inicio_intervalo or inicio >= fim_intervalo):
            return ConflitoDeTempo(
                funcionario=funcionario,
                tipo_conflito=TipoConflito.INTERVALO,
                inicio_conflito=inicio_intervalo,
                fim_conflito=fim_intervalo,
                detalhes=f"Conflito com intervalo {inicio_intv}-{fim_intervalo.time()}"
            )

        # 4. Verificar ocupações existentes
        for ocupacao in funcionario.ocupacoes:
            ordem_oc, pedido_oc, ativ_oc, nome_oc, inicio_oc, fim_oc = ocupacao

            # Verificar sobreposição temporal
            if not (fim <= inicio_oc or inicio >= fim_oc):
                return ConflitoDeTempo(
                    funcionario=funcionario,
                    tipo_conflito=TipoConflito.OCUPADO_OUTRO_PEDIDO,
                    inicio_conflito=inicio_oc,
                    fim_conflito=fim_oc,
                    atividade_conflitante=nome_oc,
                    ordem_conflitante=ordem_oc,
                    pedido_conflitante=pedido_oc,
                    detalhes=f"Ocupado com '{nome_oc}' (O:{ordem_oc} P:{pedido_oc})"
                )

        return None  # Sem conflito

    def _gerar_sugestoes_reagendamento(
        self,
        funcionarios_elegiveis: List[Funcionario],
        inicio: datetime,
        fim: datetime,
        quantidade_necessaria: int
    ) -> List[str]:
        """Gera sugestões para reagendar a atividade."""
        sugestoes = []
        duracao = fim - inicio

        # 1. Verificar slots livres no mesmo dia
        slots_livres = self._encontrar_slots_livres_mesmo_dia(
            funcionarios_elegiveis, inicio.date(), duracao, quantidade_necessaria
        )

        for slot in slots_livres:
            sugestoes.append(
                f"📅 Reagendar para {slot['inicio'].strftime('%H:%M')}-{slot['fim'].strftime('%H:%M')} "
                f"(mesmo dia, {len(slot['funcionarios'])} funcionários disponíveis)"
            )

        # 2. Verificar próximos dias
        for dias_adiante in [1, 2, 3]:
            nova_data = inicio.date() + timedelta(days=dias_adiante)
            slots_proximos_dias = self._encontrar_slots_livres_mesmo_dia(
                funcionarios_elegiveis, nova_data, duracao, quantidade_necessaria
            )

            if slots_proximos_dias:
                slot = slots_proximos_dias[0]  # Primeiro slot disponível
                sugestoes.append(
                    f"📅 Reagendar para {nova_data.strftime('%d/%m')} "
                    f"{slot['inicio'].strftime('%H:%M')}-{slot['fim'].strftime('%H:%M')} "
                    f"({len(slot['funcionarios'])} funcionários disponíveis)"
                )
                break

        # 3. Sugestões de otimização
        if not sugestoes:
            sugestoes.append("⚠️ Considere contratar mais funcionários deste tipo")
            sugestoes.append("🔄 Revisar sequenciamento de atividades de outros pedidos")

        return sugestoes

    def _encontrar_slots_livres_mesmo_dia(
        self,
        funcionarios: List[Funcionario],
        data: datetime.date,
        duracao: timedelta,
        quantidade_necessaria: int
    ) -> List[Dict]:
        """Encontra slots livres no mesmo dia para os funcionários."""
        slots_livres = []

        # Horários de trabalho padrão (6h às 20h em intervalos de 15 min)
        inicio_busca = datetime.combine(data, datetime.min.time().replace(hour=6))
        fim_busca = datetime.combine(data, datetime.min.time().replace(hour=20))

        atual = inicio_busca
        while atual + duracao <= fim_busca:
            funcionarios_disponiveis = []

            for funcionario in funcionarios:
                if funcionario.esta_disponivel(atual, duracao):
                    funcionarios_disponiveis.append(funcionario)

            if len(funcionarios_disponiveis) >= quantidade_necessaria:
                slots_livres.append({
                    'inicio': atual,
                    'fim': atual + duracao,
                    'funcionarios': funcionarios_disponiveis[:quantidade_necessaria]
                })

            atual += timedelta(minutes=15)  # Incremento de 15 minutos

        return slots_livres

    def gerar_relatorio_conflito(self, analise: AnaliseConflito) -> str:
        """Gera um relatório detalhado do conflito."""
        relatorio = []

        # Cabeçalho
        relatorio.append("=" * 80)
        relatorio.append("🔍 ANÁLISE DE CONFLITO DE ALOCAÇÃO")
        relatorio.append("=" * 80)
        relatorio.append(f"🎯 Atividade: {analise.nome_atividade} (ID: {analise.id_atividade})")
        relatorio.append(f"⏰ Horário: {analise.horario_inicio.strftime('%H:%M')} - {analise.horario_fim.strftime('%H:%M')}")
        relatorio.append(f"👥 Necessário: {analise.quantidade_necessaria} funcionários")

        tipos_str = ", ".join([tipo.name for tipo in analise.tipos_necessarios])
        relatorio.append(f"💼 Tipos: {tipos_str}")
        relatorio.append("")

        # Funcionários elegíveis
        relatorio.append(f"👤 FUNCIONÁRIOS ELEGÍVEIS ({len(analise.funcionarios_elegiveis)}):")
        for funcionario in analise.funcionarios_elegiveis:
            tipos_func = ", ".join([t.name for t in funcionario.tipo_profissional])
            relatorio.append(f"   • {funcionario.nome} ({tipos_func})")
        relatorio.append("")

        # Análise de conflitos
        if analise.conflitos:
            relatorio.append("❌ CONFLITOS IDENTIFICADOS:")
            for conflito in analise.conflitos:
                relatorio.append(f"   🚫 {conflito.funcionario.nome}:")
                relatorio.append(f"      Motivo: {conflito.detalhes}")
                relatorio.append(f"      Período: {conflito.inicio_conflito.strftime('%H:%M')} - {conflito.fim_conflito.strftime('%H:%M')}")
                relatorio.append("")

        # Funcionários disponíveis
        if analise.funcionarios_disponiveis:
            relatorio.append("✅ FUNCIONÁRIOS DISPONÍVEIS:")
            for funcionario in analise.funcionarios_disponiveis:
                relatorio.append(f"   • {funcionario.nome}")
            relatorio.append("")

        # Sugestões
        if analise.sugestoes_reagendamento:
            relatorio.append("💡 SUGESTÕES DE REAGENDAMENTO:")
            for sugestao in analise.sugestoes_reagendamento:
                relatorio.append(f"   {sugestao}")
            relatorio.append("")

        # Resumo
        disponiveis = len(analise.funcionarios_disponiveis)
        necessarios = analise.quantidade_necessaria

        if disponiveis >= necessarios:
            relatorio.append(f"✅ RESULTADO: {disponiveis}/{necessarios} funcionários disponíveis - ALOCAÇÃO POSSÍVEL")
        else:
            relatorio.append(f"❌ RESULTADO: {disponiveis}/{necessarios} funcionários disponíveis - ALOCAÇÃO IMPOSSÍVEL")

        relatorio.append("=" * 80)

        return "\n".join(relatorio)