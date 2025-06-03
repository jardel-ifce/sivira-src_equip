import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import json
from models.atividades.atividade_generica_composta import AtividadeGenericaComposta
from enums.tipo_profissional import TipoProfissional
from factory.fabrica_equipamentos import camara_refrigerada_2
from datetime import datetime



quantidade = 10000

atividade1 = AtividadeGenericaComposta(id_atividade=2, quantidade_produto=10000)
atividade2 = AtividadeGenericaComposta(id_atividade=2, quantidade_produto=5000)

# ⏰ Janela de jornada
inicio_jornada = datetime(2025, 6, 3, 8, 0)
fim_jornada = datetime(2025, 6, 3, 18, 0)

# 🚀 Executa a tentativa de alocação com base na temperatura desejada (do JSON)
atividade1.tentar_alocar_e_iniciar(
    inicio_jornada=inicio_jornada,
    fim_jornada=fim_jornada,
)
atividade2.tentar_alocar_e_iniciar(
    inicio_jornada=inicio_jornada,
    fim_jornada=fim_jornada,
)