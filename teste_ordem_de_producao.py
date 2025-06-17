from models.atividades.ordem_de_producao import OrdemDeProducao
from datetime import datetime
from utils.relatorios import exibir_ocupacoes_funcionarios_ordenadas_por_ordem
from factory.fabrica_funcionarios import funcionarios_disponiveis

import logging
logging.basicConfig(level=logging.DEBUG)


ordem = []
for i in range(1,3):
    ordem = OrdemDeProducao(
        ordem_id=i,
        id_produto=1,
        quantidade=240,
        inicio_jornada=datetime(2025, 6, 17, 8, 0),
        fim_jornada=datetime(2025, 6, 17, 18, 0),
        )
    ordem.montar_estrutura()
    ordem.mostrar_estrutura()
    ordem.criar_atividades_modulares_necessarias()
    ordem.executar_atividades_em_ordem()


exibir_ocupacoes_funcionarios_ordenadas_por_ordem(funcionarios_disponiveis)

   
