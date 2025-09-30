import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.funcionarios.funcionario import Funcionario
from enums.funcionarios.tipo_profissional import TipoProfissional
from enums.funcionarios.tipo_folga import TipoFolga
from enums.producao.dia_semana import DiaSemana
from enums.producao.tipo_setor import TipoSetor
from utils.funcionarios.regras_folga import RegraFolga
from datetime import time, timedelta

funcionario_1 = Funcionario(
    id=1,
    nome="Funcionário 1",
    setor = [TipoSetor.PANIFICACAO, TipoSetor.CONFEITARIA],
    tipo_profissional= [TipoProfissional.PADEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA),
        RegraFolga(TipoFolga.N_DIA_SEMANA_DO_MES, dia_semana=DiaSemana.DOMINGO, n_ocorrencia=2)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=2.0
)

funcionario_2 = Funcionario(
    id=2,
    nome="Funcionário 2",
    setor = [TipoSetor.PANIFICACAO],
    tipo_profissional=[TipoProfissional.AUXILIAR_DE_PADEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)


funcionario_3 = Funcionario(
    id=3,
    nome="Funcionário 3",
    setor = [TipoSetor.PANIFICACAO, TipoSetor.CONFEITARIA],
    tipo_profissional=[TipoProfissional.AUXILIAR_DE_PADEIRO, TipoProfissional.AUXILIAR_DE_CONFEITEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=3.0
)

funcionario_4 = Funcionario(
    id=4,
    nome="Funcionário 4",
    setor = [TipoSetor.CONFEITARIA],
    tipo_profissional=[TipoProfissional.CONFEITEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.QUINTA),
    ],
    ch_semanal=44,
    horario_inicio=time(8,0),
    horario_final=time(18,0),
    horario_intervalo=(time(11,0), timedelta(minutes=60)),
    fip=2.0
)

funcionario_5 = Funcionario(
    id=5,
    nome="Funcionário 5",
    setor = [TipoSetor.CONFEITARIA],
    tipo_profissional=[TipoProfissional.AUXILIAR_DE_CONFEITEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA),
        RegraFolga(TipoFolga.N_DIA_SEMANA_DO_MES, dia_semana=DiaSemana.DOMINGO, n_ocorrencia=2)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=2.0
)

funcionario_6 = Funcionario(
    id=6,
    nome="Funcionário 6",
    setor = [TipoSetor.CONFEITARIA, TipoSetor.PANIFICACAO],
    tipo_profissional=[TipoProfissional.AUXILIAR_DE_CONFEITEIRO, TipoProfissional.AUXILIAR_DE_PADEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)

funcionario_7 = Funcionario(
    id=7,
    nome="Funcionário 7",
    setor = [TipoSetor.COZINHA],
    tipo_profissional=[TipoProfissional.COZINHEIRO],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)

funcionario_8 = Funcionario(
    id=8,
    nome="Funcionário 8",
    setor = [TipoSetor.ALMOXARIFADO],
    tipo_profissional=[TipoProfissional.ALMOXARIFE],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)
funcionario_9 = Funcionario(
    id=9,
    nome="Funcionário 9",
    setor = [TipoSetor.ALMOXARIFADO],
    tipo_profissional=[TipoProfissional.ALMOXARIFE],
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)

# Lista de todos os funcionários disponíveis
funcionarios_disponiveis = [
    funcionario_1, funcionario_2, funcionario_3, funcionario_4, funcionario_5,
    funcionario_6, funcionario_7, funcionario_8, funcionario_9
]

# Permite execução direta do arquivo para teste
if __name__ == "__main__":
    print("🏭 FÁBRICA DE FUNCIONÁRIOS")
    print("=" * 40)
    print(f"✅ {len(funcionarios_disponiveis)} funcionários carregados com sucesso!")
    print()

    for funcionario in funcionarios_disponiveis:
        tipos_str = ', '.join([t.name for t in funcionario.tipo_profissional])
        setores_str = ', '.join([s.name for s in funcionario.setor])
        print(f"👤 {funcionario.nome}")
        print(f"   💼 Tipos: {tipos_str}")
        print(f"   🏢 Setores: {setores_str}")
        print(f"   🕐 Turno: {funcionario.horario_inicio_turno} - {funcionario.horario_final_turno}")
        print(f"   📊 FIP: {funcionario.fip}")
        print()