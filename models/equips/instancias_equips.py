from .balanca_digital import BalancaDigital
from .masseira import Masseira
from .bancada import Bancada
from .batedeira_industrial import BatedeiraIndustrial
from .batedeira_planetaria import BatedeiraPlanetaria
from .hot_mix import HotMix
from .fogao import Fogao
from .camara_refrigerada import CamaraRefrigerada
from .freezer import Freezer
from .embaladora import Embaladora
from .modeladora import Modeladora
from .divisora_de_massas import DivisoraDeMassas
from enums.tipo_setor import TipoSetor
from enums.tipo_mistura import TipoMistura
from enums.velocidade import Velocidade
from enums.pressao_chama import PressaoChama
from enums.tipo_chama import TipoChama
from enums.tipo_embalagem import TipoEmbalagem
from enums.tipo_produto_modelado import TipoProdutoModelado



"""
Módulo utilizado para instanciar objetos referentes aos equipamentos.
"""
# Instanciando as balanças
balanca_1 = BalancaDigital(
    id=1,
    nome="Balança digital 1",
    setor=TipoSetor.PANIFICACAO,  
    capacidade_gramas_min=1,     
    capacidade_gramas_max=40000  
)

balanca_2 = BalancaDigital(
    id=2,
    nome="Balança digital 2",
    setor=TipoSetor.CONFEITARIA,  
    capacidade_gramas_min=1,     
    capacidade_gramas_max=40000  
)

balanca_3 = BalancaDigital(
    id=3,
    nome="Balança digital 3",
    setor=TipoSetor.ALMOXARIFADO,  
    capacidade_gramas_min=0.1,     
    capacidade_gramas_max=5000    
)

balanca_4 = BalancaDigital(
    id=4,
    nome="Balança digital 4",
    setor=TipoSetor.COZINHA,  
    capacidade_gramas_min=1,  
    capacidade_gramas_max=40000  
)

# Instanciando as masseiras
masseira_1 = Masseira(
    id=1,
    nome="Masseira 1",
    setor=TipoSetor.PANIFICACAO,
    capacidade_gramas_min=3000,
    capacidade_gramas_max=50000,
    ritmo_execucao=TipoMistura.SEMI_RAPIDA,
    velocidades_suportadas=[Velocidade.BAIXA, Velocidade.MEDIA],
    velocidade_atual=Velocidade.BAIXA
)

masseira_2 = Masseira(
    id=2,
    nome="Masseira 2",
    setor=TipoSetor.PANIFICACAO,
    capacidade_gramas_min=3000,
    capacidade_gramas_max=30000,
    ritmo_execucao=TipoMistura.RAPIDA,
    velocidades_suportadas=[Velocidade.ALTA],
    velocidade_atual=Velocidade.ALTA
)

masseira_3 = Masseira(
    id=3,
    nome="Masseira 3",
    setor=TipoSetor.CONFEITARIA,
    capacidade_gramas_min=3000,
    capacidade_gramas_max=20000,
    ritmo_execucao=TipoMistura.LENTA,
    velocidades_suportadas=[Velocidade.BAIXA],
    velocidade_atual=Velocidade.BAIXA
)

bancada_1 = Bancada(
    id=1,
    nome="Bancada 1",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

bancada_2 = Bancada(
    id=2,
    nome="Bancada 2",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

bancada_3 = Bancada(
    id=3,
    nome="Bancada 3",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

bancada_4 = Bancada(
    id=4,
    nome="Bancada 4",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

bancada_5 = Bancada(
    id=5,
    nome="Bancada 5",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

bancada_6 = Bancada(
    id=6,
    nome="Bancada 6",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(6, 6),
    numero_operadores=4
)

bancada_7 = Bancada(
    id=7,
    nome="Bancada 7",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(6, 6),
    numero_operadores=4
)

bancada_8 = Bancada(
    id=8,
    nome="Bancada 8",
    setor=TipoSetor.PANIFICACAO,
    capacidade_fracionamento=(4, 4),
    numero_operadores=4
)

# Batedeira Planetária 1
batedeira_planetaria_1 = BatedeiraPlanetaria(
    id=1,
    nome="Batedeira Planetária 1",
    setor=TipoSetor.CONFEITARIA,
    numero_operadores= 1,
    velocidade_min=0,
    velocidade_max=12,
    capacidade_gramas_min=500,
    capacidade_gramas_max=5000
)

# Batedeira Planetária 2
batedeira_planetaria_2 = BatedeiraPlanetaria(
    id=2,
    nome="Batedeira Planetária 2",
    setor=TipoSetor.CONFEITARIA,
    numero_operadores=1,
    velocidade_min=0,
    velocidade_max=12,
    capacidade_gramas_min=500,
    capacidade_gramas_max=5000
)

# Batedeira Industrial
batedeira_industrial = BatedeiraIndustrial(
    id=3,
    nome="Batedeira Industrial",
    setor=TipoSetor.CONFEITARIA,
    numero_operadores=1,
    velocidade_min=0,
    velocidade_max=5,
    capacidade_gramas_min=2000,
    capacidade_gramas_max=20000
)

hotmix_1 = HotMix(
    id=1,
    nome="Hot Mix 1",
    setor=TipoSetor.CONFEITARIA,
    velocidades_suportadas=[Velocidade.BAIXA, Velocidade.MEDIA, Velocidade.ALTA],
    pressao_chama_suportadas=[PressaoChama.ALTA_PRESSAO, PressaoChama.CHAMA_DUPLA],
    capacidade_gramas_min=2000,
    capacidade_gramas_max=30000
)

# HotMix 2
hotmix_2 = HotMix(
    id=2,
    nome="Hot Mix 2",
    setor=TipoSetor.CONFEITARIA,
    velocidades_suportadas=[Velocidade.BAIXA, Velocidade.MEDIA, Velocidade.ALTA],
    pressao_chama_suportadas=[PressaoChama.ALTA_PRESSAO, PressaoChama.CHAMA_DUPLA],
    capacidade_gramas_min=2000,
    capacidade_gramas_max=30000
)

fogao_1 = Fogao(
    id=1,
    nome="Fogão 1",
    setor=TipoSetor.COZINHA,
    chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
    capacidade_por_bocas_gramas=20,
    numero_bocas=6,
    numero_operadores=6,
    pressao_chamas_suportadas=[PressaoChama.ALTA_PRESSAO, PressaoChama.CHAMA_DUPLA]
)

fogao_1 = Fogao(
    id=2,
    nome="Fogão 2",
    setor=TipoSetor.CONFEITARIA,
    chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
    capacidade_por_bocas_gramas=20,
    numero_bocas=4,
    numero_operadores=4,
    pressao_chamas_suportadas=[PressaoChama.BAIXA_PRESSAO, PressaoChama.CHAMA_UNICA]
)

camara_refrigerada_1 = CamaraRefrigerada(
    id=1,
    nome="Camara refrigerada 1",
    setor=TipoSetor.ALMOXARIFADO,
    capacidade_caixa_30kg=200,
    nivel_tela=25,
    capacidade_niveis=1,
    faixa_temperatura_min=0,
    faixa_temperatura_max=4
)

camara_refrigerada_2 = CamaraRefrigerada(
    id=2,
    nome="Camara refrigerada 2",
    setor=TipoSetor.ALMOXARIFADO,
    capacidade_caixa_30kg=200,
    nivel_tela=25,
    capacidade_niveis=1,
    faixa_temperatura_min=-18,
    faixa_temperatura_max=-7
)

freezer_1 = Freezer(
    id=1,
    nome="Freezer 1",
    setor=TipoSetor.PANIFICACAO,
    capacidade_caixa_30kg=6,
    faixa_temperatura_min=0,
    faixa_temperatura_max=4
)

freezer_2 = Freezer(
    id=2,
    nome="Freezer 2",
    setor=TipoSetor.COZINHA,
    capacidade_caixa_30kg=6,
    faixa_temperatura_min=0,
    faixa_temperatura_max=4
)

freezer_2 = Freezer(
    id=2,
    nome="Freezer 2",
    setor=TipoSetor.CONFEITARIA,
    capacidade_caixa_30kg=6,
    faixa_temperatura_min=0,
    faixa_temperatura_max=4
)

embaladora_1 = Embaladora(
    id=1,
    nome="Embaladora 1",
    setor=TipoSetor.PANIFICACAO,
    capacidade_gramas=1000,
    lista_tipo_embalagem=[TipoEmbalagem.SIMPLES, TipoEmbalagem.SELADORA],
    numero_operadores=1
)

embaladora_2 = Embaladora(
    id=2,
    nome="Embaladora 2",
    setor=TipoSetor.CONFEITARIA,
    capacidade_gramas=1000,
    lista_tipo_embalagem=[TipoEmbalagem.VACUO, TipoEmbalagem.SELADORA],
    numero_operadores=1
)

modeladora_1 = Modeladora(
    id=1,
    nome="Modeladora de pães",
    setor=TipoSetor.PANIFICACAO,
    tipo_produto_modelado=TipoProdutoModelado.PAES,
    capacidade_min_unidades_por_min=30,
    capacidade_max_unidades_por_min=35,
    numero_operadores=2
)

modeladora_2 = Modeladora(
    id=2,
    nome="Modeladora de salgados",
    setor=TipoSetor.CONFEITARIA,
    tipo_produto_modelado=TipoProdutoModelado.SALGADOS,
    capacidade_min_unidades_por_min=9,
    capacidade_max_unidades_por_min=83,
    numero_operadores=3
)

divisora_1 = DivisoraDeMassas(
    id=1,
    nome="Divisora de massas 1",
    setor=TipoSetor.PANIFICACAO,
    capacidade_gramas_min=0,
    capacidade_gramas_max=30000,
    boleadora=False,
    capacidade_divisao_unidades_por_segundo=10,
    capacidade_boleamento_unidades_por_segundo=10,
    numero_operadores=2
)

divisora_2 = DivisoraDeMassas(
    id=2,
    nome="Divisora de massas 2",
    setor=TipoSetor.PANIFICACAO,
    capacidade_gramas_min=0,
    capacidade_gramas_max=30000,
    boleadora=True,
    capacidade_divisao_unidades_por_segundo=10,
    capacidade_boleamento_unidades_por_segundo=10,
    numero_operadores=2
)


