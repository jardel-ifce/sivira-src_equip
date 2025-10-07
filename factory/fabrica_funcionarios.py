"""
Factory de Funcionários - Versão com JSON.

Carrega funcionários a partir de arquivo JSON de configuração,
permitindo fácil manutenção sem modificar código.
"""

import sys
import os
import json
from typing import List, Dict, Any
from datetime import time, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.funcionarios.funcionario import Funcionario
from enums.funcionarios.tipo_profissional import TipoProfissional
from enums.funcionarios.tipo_folga import TipoFolga
from enums.producao.dia_semana import DiaSemana
from enums.producao.tipo_setor import TipoSetor
from utils.funcionarios.regras_folga import RegraFolga


class FabricaFuncionarios:
    """
    Factory para criação de funcionários a partir de arquivo JSON.

    ⚠️ SINGLETON: Garante que apenas uma instância da fábrica existe,
    mantendo os mesmos objetos Funcionario em memória durante toda a execução.

    Responsabilidades:
    - Carregar configuração de funcionários de arquivo JSON
    - Converter dados JSON para objetos Funcionario
    - Validar dados de entrada
    - Fornecer lista de funcionários disponíveis
    """

    _instance = None
    _funcionarios_carregados = False

    def __new__(cls, caminho_json: str = "data/funcionarios/funcionarios.json"):
        """
        Implementa o padrão Singleton.
        Garante que apenas uma instância da factory existe.
        """
        if cls._instance is None:
            cls._instance = super(FabricaFuncionarios, cls).__new__(cls)
        return cls._instance

    def __init__(self, caminho_json: str = "data/funcionarios/funcionarios.json"):
        """
        Inicializa a factory de funcionários.

        ⚠️ SINGLETON: Só inicializa uma vez, mesmo se __init__ for chamado múltiplas vezes.

        Args:
            caminho_json: Caminho para o arquivo JSON de configuração
        """
        # Evita reinicialização se já foi carregado
        if FabricaFuncionarios._funcionarios_carregados:
            return

        self.caminho_json = caminho_json
        self.funcionarios_disponiveis: List[Funcionario] = []

    def carregar_funcionarios(self) -> List[Funcionario]:
        """
        Carrega funcionários do arquivo JSON.

        ⚠️ SINGLETON: Se já foi carregado antes, retorna a mesma lista
        de funcionários (com ocupações preservadas).

        Returns:
            List[Funcionario]: Lista de funcionários carregados

        Raises:
            FileNotFoundError: Se o arquivo JSON não for encontrado
            ValueError: Se os dados JSON forem inválidos
        """
        # Se já foi carregado, retorna os funcionários existentes (com ocupações)
        if FabricaFuncionarios._funcionarios_carregados:
            return self.funcionarios_disponiveis

        if not os.path.exists(self.caminho_json):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho_json}")

        with open(self.caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        self.funcionarios_disponiveis = []

        for dados_func in dados.get('funcionarios', []):
            funcionario = self._criar_funcionario_de_dict(dados_func)
            self.funcionarios_disponiveis.append(funcionario)

        # Marca como carregado para evitar recarregar
        FabricaFuncionarios._funcionarios_carregados = True

        return self.funcionarios_disponiveis

    def _criar_funcionario_de_dict(self, dados: Dict[str, Any]) -> Funcionario:
        """
        Cria um objeto Funcionario a partir de um dicionário.

        Args:
            dados: Dicionário com dados do funcionário

        Returns:
            Funcionario: Objeto funcionário criado
        """
        # Converte setores
        setores = [TipoSetor[setor] for setor in dados['setores']]

        # Converte tipos profissionais
        tipos_profissionais = [
            TipoProfissional[tipo] for tipo in dados['tipos_profissionais']
        ]

        # Converte regras de folga
        regras_folga = [
            self._criar_regra_folga(regra) for regra in dados['regras_folga']
        ]

        # Converte horários
        horario_inicio = self._parse_time(dados['horario_inicio'])
        horario_final = self._parse_time(dados['horario_final'])

        # Converte intervalo
        intervalo_inicio = self._parse_time(dados['horario_intervalo']['inicio'])
        intervalo_duracao = timedelta(minutes=dados['horario_intervalo']['duracao_minutos'])

        return Funcionario(
            id=dados['id'],
            nome=dados['nome'],
            setor=setores,
            tipo_profissional=tipos_profissionais,
            regras_folga=regras_folga,
            ch_semanal=dados['ch_semanal'],
            horario_inicio=horario_inicio,
            horario_final=horario_final,
            horario_intervalo=(intervalo_inicio, intervalo_duracao),
            fip=dados['fip']
        )

    def _criar_regra_folga(self, dados: Dict[str, Any]) -> RegraFolga:
        """
        Cria uma regra de folga a partir de um dicionário.

        Args:
            dados: Dicionário com dados da regra de folga

        Returns:
            RegraFolga: Objeto regra de folga criado
        """
        tipo_folga = TipoFolga[dados['tipo']]

        if tipo_folga == TipoFolga.DIA_FIXO_SEMANA:
            dia_semana = DiaSemana[dados['dia_semana']]
            return RegraFolga(tipo_folga, dia_semana)

        elif tipo_folga == TipoFolga.DIA_FIXO_MES:
            dia_mes = dados['dia_mes']
            return RegraFolga(tipo_folga, dia_mes=dia_mes)

        elif tipo_folga == TipoFolga.N_DIA_SEMANA_DO_MES:
            dia_semana = DiaSemana[dados['dia_semana']]
            n_ocorrencia = dados['n_ocorrencia']
            return RegraFolga(tipo_folga, dia_semana=dia_semana, n_ocorrencia=n_ocorrencia)

        else:
            raise ValueError(f"Tipo de folga não suportado: {tipo_folga}")

    def _parse_time(self, time_str: str) -> time:
        """
        Converte string de horário para objeto time.

        Args:
            time_str: String no formato "HH:MM"

        Returns:
            time: Objeto time
        """
        horas, minutos = map(int, time_str.split(':'))
        return time(horas, minutos)

    def obter_funcionarios(self) -> List[Funcionario]:
        """
        Retorna lista de funcionários disponíveis.

        Se ainda não foram carregados, carrega do arquivo JSON.

        Returns:
            List[Funcionario]: Lista de funcionários
        """
        if not self.funcionarios_disponiveis:
            self.carregar_funcionarios()

        return self.funcionarios_disponiveis

    def obter_funcionario_por_id(self, id_funcionario: int) -> Funcionario:
        """
        Busca funcionário por ID.

        Args:
            id_funcionario: ID do funcionário

        Returns:
            Funcionario: Funcionário encontrado ou None
        """
        if not self.funcionarios_disponiveis:
            self.carregar_funcionarios()

        for funcionario in self.funcionarios_disponiveis:
            if funcionario.id == id_funcionario:
                return funcionario

        return None

    def obter_funcionarios_por_setor(self, setor: TipoSetor) -> List[Funcionario]:
        """
        Busca funcionários que trabalham em um setor específico.

        Args:
            setor: Setor desejado

        Returns:
            List[Funcionario]: Lista de funcionários do setor
        """
        if not self.funcionarios_disponiveis:
            self.carregar_funcionarios()

        return [
            func for func in self.funcionarios_disponiveis
            if setor in func.setor
        ]

    def obter_funcionarios_por_profissao(self, profissao: TipoProfissional) -> List[Funcionario]:
        """
        Busca funcionários com uma profissão específica.

        Args:
            profissao: Profissão desejada

        Returns:
            List[Funcionario]: Lista de funcionários com a profissão
        """
        if not self.funcionarios_disponiveis:
            self.carregar_funcionarios()

        return [
            func for func in self.funcionarios_disponiveis
            if profissao in func.tipo_profissional
        ]


# ============================================================================
# COMPATIBILIDADE COM VERSÃO ANTIGA
# ============================================================================

# Cria instância global da factory
_fabrica = FabricaFuncionarios()

# Carrega funcionários automaticamente
try:
    funcionarios_disponiveis = _fabrica.carregar_funcionarios()

    # Cria variáveis individuais para compatibilidade com código legado
    if len(funcionarios_disponiveis) >= 9:
        funcionario_1 = funcionarios_disponiveis[0]
        funcionario_2 = funcionarios_disponiveis[1]
        funcionario_3 = funcionarios_disponiveis[2]
        funcionario_4 = funcionarios_disponiveis[3]
        funcionario_5 = funcionarios_disponiveis[4]
        funcionario_6 = funcionarios_disponiveis[5]
        funcionario_7 = funcionarios_disponiveis[6]
        funcionario_8 = funcionarios_disponiveis[7]
        funcionario_9 = funcionarios_disponiveis[8]
    else:
        # Fallback se houver menos funcionários
        for i in range(9):
            if i < len(funcionarios_disponiveis):
                globals()[f'funcionario_{i+1}'] = funcionarios_disponiveis[i]
            else:
                globals()[f'funcionario_{i+1}'] = None

except Exception as e:
    print(f"⚠️ Erro ao carregar funcionários: {e}")
    funcionarios_disponiveis = []
    # Criar variáveis None para evitar erros de importação
    funcionario_1 = funcionario_2 = funcionario_3 = None
    funcionario_4 = funcionario_5 = funcionario_6 = None
    funcionario_7 = funcionario_8 = funcionario_9 = None


# ============================================================================
# TESTES
# ============================================================================

if __name__ == "__main__":
    print("🏭 FÁBRICA DE FUNCIONÁRIOS - VERSÃO JSON")
    print("=" * 60)

    try:
        fabrica = FabricaFuncionarios()
        funcionarios = fabrica.carregar_funcionarios()

        print(f"✅ {len(funcionarios)} funcionários carregados com sucesso!")
        print(f"📄 Arquivo: {fabrica.caminho_json}")
        print()

        for funcionario in funcionarios:
            tipos_str = ', '.join([t.name for t in funcionario.tipo_profissional])
            setores_str = ', '.join([s.name for s in funcionario.setor])

            print(f"👤 {funcionario.nome} (ID: {funcionario.id})")
            print(f"   💼 Profissões: {tipos_str}")
            print(f"   🏢 Setores: {setores_str}")
            print(f"   🕐 Turno: {funcionario.horario_inicio_turno} - {funcionario.horario_final_turno}")
            print(f"   📊 FIP: {funcionario.fip}")
            print(f"   📅 Folgas: {len(funcionario.regras_folga)} regra(s)")
            print()

        # Testa busca por setor
        print("=" * 60)
        print("🔍 TESTE: Funcionários da Panificação")
        print("-" * 60)
        panificacao = fabrica.obter_funcionarios_por_setor(TipoSetor.PANIFICACAO)
        for func in panificacao:
            print(f"  • {func.nome}")

        print()
        print("=" * 60)
        print("🔍 TESTE: Funcionários Padeiros")
        print("-" * 60)
        padeiros = fabrica.obter_funcionarios_por_profissao(TipoProfissional.PADEIRO)
        for func in padeiros:
            print(f"  • {func.nome}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
