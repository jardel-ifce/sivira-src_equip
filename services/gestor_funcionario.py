from datetime import datetime, timedelta
from typing import List, Tuple
from models.funcionarios.funcionario import Funcionario
from models.atividade_base import Atividade
from utils.data_utils import formatar_data_e_hora


class GestorFuncionario:
    """
    👥 Gestor responsável por alocar funcionários disponíveis
    conforme perfil profissional e menor FIP.
    """

    def __init__(self, funcionarios: List[Funcionario]):
        self.funcionarios = funcionarios

    def alocar(
        self,
        atividade: Atividade,
        inicio: datetime,
        fim: datetime,
        quantidade_necessaria: int,
    ) -> Tuple[bool, List[Funcionario]]:
        """
        Tenta alocar os funcionários necessários para uma atividade.

        Retorna:
        - sucesso (bool)
        - lista de funcionários alocados
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

        # 🧮 Ordena por menor FIP
        candidatos_ordenados = sorted(candidatos, key=lambda f: f.fip)

        alocados: List[Funcionario] = []

        for funcionario in candidatos_ordenados:
            funcionario.registrar_ocupacao(inicio, fim, atividade.id)
            alocados.append(funcionario)
            if len(alocados) == quantidade_necessaria:
                self._log_alocacao_sucesso(atividade, alocados, inicio, fim)
                return True, alocados

        # ❌ Falha — desfaz qualquer alocação parcial
        for f in alocados:
            f.desalocar(atividade.id)

        print(f"❌ Falha ao alocar funcionários para atividade #{atividade.id} ({atividade.nome})")
        return False, []

    def _log_alocacao_sucesso(self, atividade: Atividade, funcionarios: List[Funcionario], inicio: datetime, fim: datetime):
        """
        Imprime log detalhado da alocação de funcionários.
        """
        dia_pt, data_pt, hora_pt = formatar_data_e_hora(inicio)
        for f in funcionarios:
            print(f"✅ {atividade.nome} - {f.nome} | {dia_pt}, {data_pt} | {hora_pt} → {fim.strftime('%H:%M')}")

    def visualizar_agenda(self):
        """
        Exibe a agenda consolidada de todos os funcionários do gestor.
        """
        print(f"📋 Agenda Consolidada de Funcionários:")
        todas_atividades = []

        for f in self.funcionarios:
            for id_atividade, inicio, fim in f.ocupacoes:
                todas_atividades.append((inicio, fim, id_atividade, f.nome))

        todas_atividades.sort(key=lambda x: x[0])
        for inicio, fim, atividade_id, func_nome in todas_atividades:
            dia_pt, data_pt, hora_pt = formatar_data_e_hora(inicio)
            print(f"👷 Atividade #{atividade_id} | {func_nome} | {dia_pt}, {data_pt} | {hora_pt} → {fim.strftime('%H:%M')}")
