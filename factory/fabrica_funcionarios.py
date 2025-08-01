from models.funcionarios.funcionario import Funcionario
from enums.funcionarios.tipo_profissional import TipoProfissional
from enums.funcionarios.tipo_folga import TipoFolga
from enums.producao.dia_semana import DiaSemana
from utils.funcionarios.regras_folga import RegraFolga
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
    tipo_profissional=TipoProfissional.AUXILIAR_DE_PADEIRO,
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
    tipo_profissional=TipoProfissional.PADEIRO,
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
    tipo_profissional=TipoProfissional.ALMOXARIFE,
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
    tipo_profissional=TipoProfissional.AUXILIAR_DE_CONFEITEIRO,
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
    tipo_profissional=TipoProfissional.COZINHEIRO,
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
    tipo_profissional=TipoProfissional.COZINHEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)
funcionario_10 = Funcionario(
    id=10,
    nome="Funcionário 10",
    tipo_profissional=TipoProfissional.COZINHEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)
funcionario_11 = Funcionario(
    id=11,
    nome="Funcionário 11",
    tipo_profissional=TipoProfissional.COZINHEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)
funcionario_12 = Funcionario(
    id=12,
    nome="Funcionário 12",
    tipo_profissional=TipoProfissional.COZINHEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)
funcionario_13 = Funcionario(
    id=13,
    nome="Funcionário 13",
    tipo_profissional=TipoProfissional.COZINHEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=1.0
)

funcionario_14 = Funcionario(
    id=14,
    nome="Funcionário 14",
    tipo_profissional=TipoProfissional.PADEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.SEXTA)
    ],
    ch_semanal=44,
    horario_inicio=time(8, 0),
    horario_final=time(18, 0),
    horario_intervalo=(time(11, 0), timedelta(minutes=60)),
    fip=3.0
)

funcionario_15 = Funcionario(
    id=15,
    nome="Funcionário 15",
    tipo_profissional=TipoProfissional.PADEIRO,
    regras_folga=[
        RegraFolga(TipoFolga.DIA_FIXO_SEMANA, DiaSemana.QUINTA),
    ],
    ch_semanal=44,
    horario_inicio=time(8,0),
    horario_final=time(18,0),
    horario_intervalo=(time(11,0), timedelta(minutes=60)),
    fip=2.0
)

funcionario_16 = Funcionario(
    id=16,
    nome="Funcionário 16",
    tipo_profissional=TipoProfissional.ALMOXARIFE,
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
                            funcionario_7, funcionario_8, funcionario_9,
                            funcionario_10, funcionario_11, funcionario_12,
                            funcionario_13, funcionario_14, funcionario_15,
                            funcionario_16
                           ]
