from parser.parser_json_comandas import ler_comandas_em_pasta
from parser.gerenciador_reservas import registrar_reservas_em_itens_almoxarifado, descontar_estoque_por_reservas
from pprint import pprint
from datetime import date


# reservas = ler_comandas_em_pasta()
# pprint(reservas)
# registrar_reservas_em_itens_almoxarifado(reservas)

descontar_estoque_por_reservas()

# from datetime import date
# from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
# from models.itens.almoxarifado import Almoxarifado
# from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado

# def main():
#     caminho_json = "data/almoxarifado/itens_almoxarifado.json"  # ajuste se necessário
#     itens = carregar_itens_almoxarifado(caminho_json)

#     almoxarifado = Almoxarifado()
#     for item in itens:
#         almoxarifado.adicionar_item(item)

#     gestor = GestorAlmoxarifado(almoxarifado)

#     # Data desejada para projeção
#     data_projecao = date(2025, 6, 24)

#     print(f"📅 Estoque projetado para {data_projecao.strftime('%Y-%m-%d')}:\n")

#     for item in almoxarifado.listar_itens():
#         estoque_atual = item.estoque_atual
#         reservado = item.quantidade_reservada_em(data_projecao)
#         projetado = item.estoque_projetado_em(data_projecao)

#         print(f"🔹 ID: {item.id_item} | {item.descricao}")
#         print(f"   Estoque atual: {estoque_atual:.2f} {item.unidade_medida.value}")
#         print(f"   Reservado para {data_projecao.strftime('%Y-%m-%d')}: {reservado:.2f}")
#         print(f"   📉 Estoque projetado: {projetado:.2f} {item.unidade_medida.value}\n")

# if __name__ == "__main__":
#     main()
