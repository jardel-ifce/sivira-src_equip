from datetime import datetime, timedelta
from typing import List, Tuple, Set
from models.funcionarios.funcionario import Funcionario
from models.atividade_base import Atividade
from utils.data_utils import formatar_data_e_hora
from enums.tipo_profissional import TipoProfissional


def filtrar_funcionarios_por_tipos(
    funcionarios: List[Funcionario],
    tipos_permitidos: Set[TipoProfissional]
) -> List[Funcionario]:
    """
    🎯 Retorna apenas os funcionários cujo tipo está presente no conjunto informado.
    """
    return [
        f for f in funcionarios
        if f.tipo_profissional in tipos_permitidos
    ]


class GestorFuncionario:
    """
    👥 Gestor responsável por alocar funcionários disponíveis
    conforme perfil profissional, ordem de produção e menor FIP.
    """

    def __init__(self, funcionarios: List[Funcionario]):
        self.funcionarios = funcionarios

    def _ordenar_por_ordem_e_fip(self, candidatos: List[Funcionario], ordem_id: int) -> List[Funcionario]:
        """
        🔁 Prioriza funcionários já alocados na mesma ordem e depois por menor FIP.
        """
        mesma_ordem = [f for f in candidatos if any(oc[0] == ordem_id for oc in f.ocupacoes)]
        outras_ordens = [f for f in candidatos if f not in mesma_ordem]

        mesma_ordem.sort(key=lambda f: f.fip)
        outras_ordens.sort(key=lambda f: f.fip)

        return mesma_ordem + outras_ordens

    def alocar(
        self,
        atividade: Atividade,
        inicio: datetime,
        fim: datetime,
        quantidade_necessaria: int,
    ) -> Tuple[bool, List[Funcionario]]:
        """
        Tenta alocar os funcionários necessários para uma atividade,
        priorizando quem já está na mesma ordem.
        """
        duracao = fim - inicio

        # 🎯 Filtra profissionais compatíveis e disponíveis
        candidatos = [
            f for f in self.funcionarios
            if (
                f.tipo_profissional in atividade.tipos_profissionais_permitidos
                and f.esta_disponivel(inicio, duracao)
            )
        ]

        # 🎯 Ordena priorizando os da mesma ordem + FIP
        candidatos_ordenados = self._ordenar_por_ordem_e_fip(candidatos, atividade.ordem_id)

        alocados: List[Funcionario] = []

        for funcionario in candidatos_ordenados:
            funcionario.registrar_ocupacao(
                ordem_id=atividade.ordem_id,
                id_atividade_modular=atividade.id,
                id_atividade_json=atividade.id_atividade,
                inicio=inicio,
                fim=fim
            )
            alocados.append(funcionario)
            if len(alocados) == quantidade_necessaria:
                self._log_alocacao_sucesso(atividade, alocados, inicio, fim)
                return True, alocados

        # ❌ Falha — desfaz qualquer alocação parcial
        for f in alocados:
            f.desalocar(atividade.id, atividade.ordem_id)

        print(f"❌ Falha ao alocar funcionários para atividade #{atividade.id} ({atividade.nome})")
        return False, []

    def _log_alocacao_sucesso(self, atividade: Atividade, funcionarios: List[Funcionario], inicio: datetime, fim: datetime):
        """
        Imprime log detalhado da alocação de funcionários.
        """
        dia_pt, data_pt, hora_pt = formatar_data_e_hora(inicio)
        for f in funcionarios:
            print(f"✅ {atividade.nome} - {f.nome} | {dia_pt}, {data_pt} | {hora_pt} → {fim.strftime('%H:%M')}")

    def liberar_por_ordem(self, ordem_id: int):
        """
        🔁 Libera todas as ocupações associadas à ordem fornecida para todos os funcionários.
        """
        total_liberadas = 0

        for f in self.funcionarios:
            ocup_antes = len(f.ocupacoes)
            f.ocupacoes = [oc for oc in f.ocupacoes if oc[0] != ordem_id]
            ocup_depois = len(f.ocupacoes)
            liberadas = ocup_antes - ocup_depois

            if liberadas > 0:
                print(f"🗑️ {liberadas} ocupações removidas de {f.nome} para a ordem #{ordem_id}")
                total_liberadas += liberadas

        if total_liberadas == 0:
            print(f"ℹ️ Nenhuma ocupação encontrada para a ordem #{ordem_id}")
        else:
            print(f"✅ Total de {total_liberadas} ocupações liberadas para a ordem #{ordem_id}")

    def visualizar_agenda(self):
        """
        Exibe a agenda consolidada de todos os funcionários do gestor.
        """
        print(f"📋 Agenda Consolidada de Funcionários:")
        todas_atividades = []

        for f in self.funcionarios:
            for ordem_id, id_mod, id_json, inicio, fim in f.ocupacoes:
                todas_atividades.append((inicio, fim, ordem_id, id_mod, id_json, f.nome))

        todas_atividades.sort(key=lambda x: x[0])
        for inicio, fim, ordem_id, id_mod, id_json, func_nome in todas_atividades:
            dia_pt, data_pt, hora_pt = formatar_data_e_hora(inicio)
            print(f"👷 Ordem #{ordem_id} | Ativ. {id_mod}/{id_json} | {func_nome} | {dia_pt}, {data_pt} | {hora_pt} → {fim.strftime('%H:%M')}")
