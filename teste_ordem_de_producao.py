from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.itens.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.gerenciador_logs import limpar_todos_os_logs
from modules.modulo_comandas import gerar_comanda_reserva
from utils.limpador_comandas import apagar_todas_as_comandas

# 1. Carregar os itens do almoxarifado
itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
apagar_todas_as_comandas()
almox = Almoxarifado()
for item in itens:
    almox.adicionar_item(item) 

gestor = GestorAlmoxarifado(almox)
gestor.exibir_itens_estoque()
limpar_todos_os_logs()

# 2. Criar pedido de produção
for i in range(1, 2):
    pedido = PedidoDeProducao(
        ordem_id=1,
        pedido_id=i,
        id_produto=1,  # pão francês
        quantidade=240,
        inicio_jornada=datetime(2025, 6, 24, 8, 0),
        fim_jornada=datetime(2025, 6, 24, 18, 0),
        todos_funcionarios=funcionarios_disponiveis
    )

    try:
        # 3. Montar ficha técnica
        pedido.montar_estrutura()

        # 4. Gerar comanda de reserva (módulo externo)
        gerar_comanda_reserva(
            ordem_id=pedido.ordem_id,
            pedido_id=pedido.pedido_id,
            ficha=pedido.ficha_tecnica_modular,
            gestor=gestor,
            data_execucao=pedido.inicio_jornada
        )

        # 5. Criar e executar atividades normalmente
        pedido.mostrar_estrutura()
        pedido.criar_atividades_modulares_necessarias()
        pedido.executar_atividades_em_ordem()
        pedido.exibir_historico_de_funcionarios()

    except RuntimeError as e:
        print(f"⚠️ Falha ao processar a ordem: {e}")
