from models.funcionarios.funcionario import Funcionario
from enums.tipo_profissional import TipoProfissional
from enums.tipo_folga import TipoFolga
from enums.dia_semana import DiaSemana
from utils.regras_folga import RegraFolga
from datetime import time, timedelta

funcionario_1 = Funcionario(
    id=1,
    nome="Funcionário 1",
    tipo_profissional=TipoProfissional.PADEIRO,
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
    tipo_profissional=TipoProfissional.PADEIRO,
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
    tipo_profissional=TipoProfissional.AUXILIAR_DE_PADEIRO,
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
    tipo_profissional=TipoProfissional.AUXILIAR_DE_PADEIRO,
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
    tipo_profissional=TipoProfissional.PADEIRO,
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
    tipo_profissional=TipoProfissional.PADEIRO,
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
    tipo_profissional=TipoProfissional.AUXILIAR_DE_PADEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=3.0
)

funcionario_8 = Funcionario(
    id=8,
    nome="Funcionário 8",
    tipo_profissional=TipoProfissional.AUXILIAR_DE_PADEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.QUINTA),
    ],
    ch_semanal=44,
    horario_inicio=time(8,0),
    horario_final=time(18,0),
    horario_intervalo=(time(11,0), timedelta(minutes=60)),
    fip=2.0
)


funcionarios_disponiveis = [funcionario_1, funcionario_2, funcionario_3, 
                            funcionario_4, funcionario_5, funcionario_6, 
                            funcionario_7, funcionario_8]
