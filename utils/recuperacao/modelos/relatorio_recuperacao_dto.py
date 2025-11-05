"""
DTO para Relatório de Recuperação
==================================

Representa o resultado completo de uma operação de recuperação.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
from .estado_equipamento_dto import EstadoEquipamentoDTO


@dataclass
class RelatorioRecuperacaoDTO:
    """
    📊 DTO que representa o relatório completo de recuperação

    Contém:
    - caminho_log: Caminho do arquivo de log usado
    - data_recuperacao: Data/hora da recuperação
    - equipamentos: Lista de estados de equipamentos
    - sucesso: Se a recuperação foi bem-sucedida
    - mensagens: Mensagens informativas
    - erros_globais: Erros que afetaram toda a recuperação
    """

    caminho_log: str
    data_recuperacao: datetime = field(default_factory=datetime.now)
    equipamentos: List[EstadoEquipamentoDTO] = field(default_factory=list)
    sucesso: bool = False
    mensagens: List[str] = field(default_factory=list)
    erros_globais: List[str] = field(default_factory=list)

    @property
    def total_equipamentos(self) -> int:
        """Total de equipamentos processados"""
        return len(self.equipamentos)

    @property
    def equipamentos_com_ocupacoes(self) -> int:
        """Equipamentos que tinham ocupações"""
        return sum(1 for e in self.equipamentos if e.tem_ocupacoes)

    @property
    def equipamentos_restaurados(self) -> int:
        """Equipamentos restaurados com sucesso"""
        return sum(1 for e in self.equipamentos if e.equipamento_restaurado)

    @property
    def total_ocupacoes_recuperadas(self) -> int:
        """Total de ocupações recuperadas"""
        return sum(e.total_ocupacoes for e in self.equipamentos)

    @property
    def total_erros(self) -> int:
        """Total de erros encontrados"""
        erros_equipamentos = sum(len(e.erros) for e in self.equipamentos)
        return len(self.erros_globais) + erros_equipamentos

    @property
    def tem_erros(self) -> bool:
        """Verifica se houve erros"""
        return self.total_erros > 0

    def adicionar_equipamento(self, estado: EstadoEquipamentoDTO):
        """Adiciona estado de equipamento"""
        self.equipamentos.append(estado)

    def adicionar_mensagem(self, mensagem: str):
        """Adiciona mensagem informativa"""
        self.mensagens.append(mensagem)

    def adicionar_erro_global(self, erro: str):
        """Adiciona erro global"""
        self.erros_globais.append(erro)

    def estatisticas_por_tipo(self) -> Dict[str, int]:
        """Retorna estatísticas de ocupações por tipo de equipamento"""
        stats = {}
        for equipamento in self.equipamentos:
            tipo = equipamento.tipo_equipamento
            if tipo not in stats:
                stats[tipo] = 0
            stats[tipo] += equipamento.total_ocupacoes
        return stats

    def gerar_resumo(self) -> str:
        """Gera resumo textual da recuperação"""
        linhas = []
        linhas.append("=" * 80)
        linhas.append("📊 RELATÓRIO DE RECUPERAÇÃO DE ESTADO")
        linhas.append("=" * 80)
        linhas.append(f"📄 Log: {self.caminho_log}")
        linhas.append(f"🕒 Data: {self.data_recuperacao.strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"✅ Status: {'SUCESSO' if self.sucesso else 'FALHA'}")
        linhas.append("=" * 80)
        linhas.append("")

        linhas.append("📈 ESTATÍSTICAS:")
        linhas.append(f"   • Total de equipamentos: {self.total_equipamentos}")
        linhas.append(f"   • Equipamentos com ocupações: {self.equipamentos_com_ocupacoes}")
        linhas.append(f"   • Equipamentos restaurados: {self.equipamentos_restaurados}")
        linhas.append(f"   • Total de ocupações recuperadas: {self.total_ocupacoes_recuperadas}")
        linhas.append(f"   • Total de erros: {self.total_erros}")
        linhas.append("")

        if self.mensagens:
            linhas.append("💬 MENSAGENS:")
            for msg in self.mensagens:
                linhas.append(f"   • {msg}")
            linhas.append("")

        if self.erros_globais:
            linhas.append("❌ ERROS GLOBAIS:")
            for erro in self.erros_globais:
                linhas.append(f"   • {erro}")
            linhas.append("")

        # Estatísticas por tipo
        stats = self.estatisticas_por_tipo()
        if stats:
            linhas.append("🏷️ OCUPAÇÕES POR TIPO:")
            for tipo, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                linhas.append(f"   • {tipo}: {count} ocupação(ões)")
            linhas.append("")

        # Equipamentos com erro
        equipamentos_com_erro = [e for e in self.equipamentos if e.tem_erros]
        if equipamentos_com_erro:
            linhas.append("⚠️ EQUIPAMENTOS COM ERROS:")
            for eq in equipamentos_com_erro:
                linhas.append(f"   • {eq.nome_equipamento}:")
                for erro in eq.erros:
                    linhas.append(f"      - {erro}")
            linhas.append("")

        linhas.append("=" * 80)
        return "\n".join(linhas)

    def __repr__(self) -> str:
        """Representação legível"""
        status = "✅ SUCESSO" if self.sucesso else "❌ FALHA"
        return (
            f"RelatorioRecuperacaoDTO("
            f"{self.total_equipamentos} equipamentos, "
            f"{self.total_ocupacoes_recuperadas} ocupações, "
            f"status={status}"
            f")"
        )
