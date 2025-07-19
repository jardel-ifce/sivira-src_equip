from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem
from datetime import timedelta

# 1. Carregar os itens do almoxarifado
itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
apagar_todas_as_comandas()
almox = Almoxarifado()
for item in itens:
    almox.adicionar_item(item) 

gestor = GestorAlmoxarifado(almox)
#gestor.exibir_itens_estoque()
limpar_todos_os_logs()

# 2. Criar pedidos de produção
pedidos = []

dados_pedidos = [
    (1001, 450, "07:00"),
    (1002, 120, "07:00"),
    (1003, 20,  "07:00"),
    (1004, 20,  "07:00"),
    (1005, 10,  "07:00"),
    (1001, 300, "09:00"),
    (1004, 10,  "09:00"),
    (1005, 10,  "09:00"),
    (1001, 450, "15:00"),
    (1002,  60, "15:00"),
    (1003,  10, "15:00"),
    (1004,  20, "15:00"),
    (1005,  10, "15:00"),
    (1001, 300, "17:00"),
    (1004,  30, "17:00"),
    (1005,  10, "17:00"),
]

for i, (id_produto, quantidade, hora_str) in enumerate(dados_pedidos, start=1):
    hora, minuto = map(int, hora_str.split(":"))
    fim = datetime(2025, 7, 20, hora, minuto)
    inicio = fim - timedelta(hours=72)

    pedido = PedidoDeProducao(
        ordem_id=1,
        pedido_id=i,
        id_produto=id_produto,
        tipo_item=TipoItem.PRODUTO,
        quantidade=quantidade,
        inicio_jornada=inicio,
        fim_jornada=fim,
        todos_funcionarios=funcionarios_disponiveis
    )
    try:
        pedido.montar_estrutura()
        pedidos.append(pedido)
    except RuntimeError as e:
        print(f"⚠️ Falha ao montar estrutura do pedido {i}: {e}")

# 🧠 Ordenar os pedidos com base nas restrições
pedidos_ordenados = ordenar_pedidos_por_restricoes(pedidos)

# 3. Executar cada pedido em ordem de prioridade
for pedido in pedidos_ordenados:
    try:
        gerar_comanda_reserva(
            ordem_id=pedido.ordem_id,
            pedido_id=pedido.pedido_id,
            ficha=pedido.ficha_tecnica_modular,
            gestor=gestor,
            data_execucao=pedido.inicio_jornada
        )
        pedido.mostrar_estrutura()
        pedido.criar_atividades_modulares_necessarias()
        pedido.executar_atividades_em_ordem()
        #pedido.exibir_historico_de_funcionarios()
    except RuntimeError as e:
        print(f"⚠️ Falha ao processar a ordem: {e}")