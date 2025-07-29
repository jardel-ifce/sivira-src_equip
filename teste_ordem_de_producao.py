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
for i in range(1, 3):  # ou qualquer número de pedidos
    pedido = PedidoDeProducao(
        id_ordem=1,
        id_pedido=i,
        id_produto=2003,
        tipo_item=TipoItem.SUBPRODUTO,
        quantidade=10000,
        inicio_jornada=datetime(2025, 6, 23, 8, 0),
        fim_jornada=datetime(2025, 6, 24, 18, 0),
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
            id_ordem=pedido.id_ordem,
            id_pedido=pedido.id_pedido,
            ficha=pedido.ficha_tecnica_modular,
            gestor=gestor,
            data_execucao=pedido.inicio_jornada
        )
        pedido.mostrar_estrutura()
        pedido.criar_atividades_modulares_necessarias()
        pedido.executar_atividades_em_ordem()
        pedido.exibir_historico_de_funcionarios()
    except RuntimeError as e:
        print(f"⚠️ Falha ao processar a ordem: {e}")