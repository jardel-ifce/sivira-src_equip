from copy import deepcopy
from models.atividades.pedido_de_producao import PedidoDeProducao
from typing import Tuple

def verificar_pedido_viavel(pedido: PedidoDeProducao) -> bool:
    """
    Verifica se um pedido pode ser executado isoladamente, sem afetar os objetos reais.
    Usa deepcopy para simular o ambiente.
    Retorna True se o pedido for viável, False caso contrário.
    """
    try:
        pedido_simulado = deepcopy(pedido)
        pedido_simulado.montar_estrutura()
        pedido_simulado.criar_atividades_modulares_necessarias()
        pedido_simulado.executar_atividades_em_ordem()
        return True
    except Exception as e:
        print(f"❌ Pedido {pedido.id_pedido} falhou na verificação: {e}")
        return False



def verificar_pedido_executavel_isoladamente(pedido: PedidoDeProducao) -> Tuple[bool, str]:
    """
    Verifica se o pedido pode ser executado isoladamente, sem sobreposição com outros.
    
    Retorna:
        (True, "") se executável;
        (False, mensagem de erro) se não executável.
    """
    copia = deepcopy(pedido)

    try:
        copia.montar_estrutura()
        copia.criar_atividades_modulares_necessarias()
        copia.executar_atividades_em_ordem()
        return True, ""
    except Exception as e:
        return False, str(e)
