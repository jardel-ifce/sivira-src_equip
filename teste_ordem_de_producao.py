from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.gerenciador_logs import limpar_todos_os_logs

# 1. Carregar os itens do almoxarifado
itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
gestor = GestorAlmoxarifado(itens)
gestor.exibir_itens()
limpar_todos_os_logs()
# 2. Criar pedido de produção
for i in range(1, 3):
    pedido = PedidoDeProducao(
        ordem_id=1,
        pedido_id=i,
        id_produto=1,  # pão francês
        quantidade=240,
        inicio_jornada=datetime(2025, 6, 24, 8, 0),
        fim_jornada=datetime(2025, 6, 24, 18, 0),
        todos_funcionarios=funcionarios_disponiveis
    )

    # 3. Verificar estoque e montar estrutura
    try:
        pedido.montar_estrutura()
        #pedido.verificar_disponibilidade_estoque(gestor, pedido.inicio_jornada)
        pedido.criar_atividades_modulares_necessarias()
        pedido.executar_atividades_em_ordem()
        pedido.exibir_historico_de_funcionarios()

    except RuntimeError as e:
        print(f"⚠️ Falha ao processar a ordem: {e}")
