import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# =========================================
# 📦 Imports dos Equipamentos
# =========================================
from models.equips.camara_refrigerada import CamaraRefrigerada
from models.equips.freezer import Freezer
from models.equips.fogao import Fogao
from models.equips.balanca_digital import BalancaDigital
from models.equips.bancada import Bancada
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from models.equips.masseira import Masseira
from models.equips.hot_mix import HotMix
from models.equips.forno import Forno
from models.equips.armario_esqueleto import ArmarioEsqueleto
from models.equips.divisora_de_massas import DivisoraDeMassas
from models.equips.modeladora_de_paes import ModeladoraDePaes
from models.equips.armario_fermentador import ArmarioFermentador
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from enums.tipo_mistura import TipoMistura
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_coccao import TipoCoccao


class FabricaEquipamentos:
    """
    🏭 Fábrica responsável pela criação dos equipamentos.
    """

    # =======================
    # 🧊 Câmaras Refrigeradas
    # =======================
    @staticmethod
    def criar_camara_refrigerada_1():
        return CamaraRefrigerada(
            id=1,
            nome="Câmara Refrigerada 1",
            setor=TipoSetor.ALMOXARIFADO,
            capacidade_niveis_tela=25,
            capacidade_caixa_30kg=200,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4,
        )

    @staticmethod
    def criar_camara_refrigerada_2():
        return CamaraRefrigerada(
            id=2,
            nome="Câmara Refrigerada 2",
            setor=TipoSetor.ALMOXARIFADO,
            capacidade_niveis_tela=25,
            capacidade_caixa_30kg=20,
            faixa_temperatura_min=-18,
            faixa_temperatura_max=-7,
        )

    # =======================
    # 🔥 Fogões
    # =======================
    @staticmethod
    def criar_fogao_1():
        return Fogao(
            id=3,
            nome="Fogão 1",
            setor=TipoSetor.COZINHA,
            numero_operadores=1,
            chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
            capacidade_por_boca_gramas_min=2000,
            capacidade_por_boca_gramas_max=30000,
            numero_bocas=6,
            pressao_chamas_suportadas=[TipoPressaoChama.ALTA_PRESSAO, TipoPressaoChama.CHAMA_DUPLA]
        )

    @staticmethod
    def criar_fogao_2():
        return Fogao(
            id=4,
            nome="Fogão 2",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
            capacidade_por_boca_gramas_min=2000,
            capacidade_por_boca_gramas_max=30000,
            numero_bocas=4,
            pressao_chamas_suportadas=[TipoPressaoChama.BAIXA_PRESSAO, TipoPressaoChama.CHAMA_UNICA]
        )

    # =======================
    # ⚖️ Balanças Digitais
    # =======================
    @staticmethod
    def criar_balanca_digital_1():
        return BalancaDigital(5, "Balança Digital 1", TipoSetor.PANIFICACAO, 1, 40000)

    @staticmethod
    def criar_balanca_digital_2():
        return BalancaDigital(6, "Balança Digital 2", TipoSetor.CONFEITARIA, 1, 40000)

    @staticmethod
    def criar_balanca_digital_3():
        return BalancaDigital(7, "Balança Digital 3", TipoSetor.ALMOXARIFADO, 0.1, 5000)

    @staticmethod
    def criar_balanca_digital_4():
        return BalancaDigital(8, "Balança Digital 4", TipoSetor.COZINHA, 1, 40000)

    # ============================================
    # 🪵 Criação das Bancadas (atualizado)
    # ============================================
    @staticmethod
    def criar_bancada_1():
        return Bancada(
            id=9,
            nome="Bancada 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=4,
            numero_fracoes=4
        )

    @staticmethod
    def criar_bancada_2():
        return Bancada(
            id=10,
            nome="Bancada 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=4,
            numero_fracoes=4
        )

    @staticmethod
    def criar_bancada_3():
        return Bancada(
            id=11,
            nome="Bancada 3",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=4,
            numero_fracoes=4
        )

    @staticmethod
    def criar_bancada_4():
        return Bancada(
            id=12,
            nome="Bancada 4",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=4,
            numero_fracoes=4
        )

    @staticmethod
    def criar_bancada_5():
        return Bancada(
            id=13,
            nome="Bancada 5",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=4,
            numero_fracoes=4
        )

    @staticmethod
    def criar_bancada_6():
        return Bancada(
            id=14,
            nome="Bancada 6",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=6,
            numero_fracoes=6
        )

    @staticmethod
    def criar_bancada_7():
        return Bancada(
            id=15,
            nome="Bancada 7",
            setor=TipoSetor.COZINHA,
            numero_operadores=6,
            numero_fracoes=6
        )

    @staticmethod
    def criar_bancada_8():
        return Bancada(
            id=16,
            nome="Bancada 8",
            setor=TipoSetor.ALMOXARIFADO,
            numero_operadores=4,
            numero_fracoes=4
        )



    # =======================
    # 🍥 Batedeiras
    # =======================
    @staticmethod
    def criar_batedeira_planetaria_1():
        return BatedeiraPlanetaria(
            id=17,
            nome="Batedeira Planetária 1",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            velocidade_min=1,
            velocidade_max=12,
            capacidade_gramas_min=500,
            capacidade_gramas_max=5000
        )

    @staticmethod
    def criar_batedeira_planetaria_2():
        return BatedeiraPlanetaria(
            id=18,
            nome="Batedeira Planetária 2",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            velocidade_min=1,
            velocidade_max=12,
            capacidade_gramas_min=500,
            capacidade_gramas_max=5000
        )

    @staticmethod
    def criar_batedeira_industrial_1():
        return BatedeiraIndustrial(
            id=19,
            nome="Batedeira Industrial 1",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            velocidade_min=1,
            velocidade_max=5,
            capacidade_gramas_min=2000,
            capacidade_gramas_max=20000
        )

    # =======================
    # 🌀 Masseiras
    # =======================
    @staticmethod
    def criar_masseira_1():
        return Masseira(
            id=20,
            nome="Masseira 1",
            setor=TipoSetor.PANIFICACAO,
            capacidade_gramas_min=3000,
            capacidade_gramas_max=50000,
            tipos_de_mistura_suportados=[TipoMistura.SEMI_RAPIDA],
            velocidades_suportadas=[
                TipoVelocidade.BAIXA,
                TipoVelocidade.MEDIA
            ],
        )

    @staticmethod
    def criar_masseira_2():
        return Masseira(
            id=21,
            nome="Masseira 2",
            setor=TipoSetor.PANIFICACAO,
            capacidade_gramas_min=3000,
            capacidade_gramas_max=30000,
            tipos_de_mistura_suportados=[TipoMistura.RAPIDA],
            velocidades_suportadas=[
                TipoVelocidade.ALTA
            ],
        )

    @staticmethod
    def criar_masseira_3():
        return Masseira(
            id=22,
            nome="Masseira 3",
            setor=TipoSetor.CONFEITARIA,
            capacidade_gramas_min=3000,
            capacidade_gramas_max=20000,
            tipos_de_mistura_suportados=TipoMistura.LENTA,
            velocidades_suportadas=[
                TipoVelocidade.BAIXA
            ],
        )

    # =======================
    # 🍳 HotMix (Misturadoras com Cocção)
    # =======================

    @staticmethod
    def criar_hotmix_1():
        return HotMix(
            id=23,
            nome="HotMix 1",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            capacidade_gramas_min=2000,
            capacidade_gramas_max=30000,
            velocidades_suportadas=[
                TipoVelocidade.BAIXA,
                TipoVelocidade.MEDIA,
                TipoVelocidade.ALTA
            ],
            chamas_suportadas=[
                TipoChama.BAIXA,
                TipoChama.MEDIA,
                TipoChama.ALTA
            ],
            pressao_chamas_suportadas=[
                TipoPressaoChama.ALTA_PRESSAO,
                TipoPressaoChama.CHAMA_DUPLA
            ]
        )


    @staticmethod
    def criar_hotmix_2():
        return HotMix(
            id=24,
            nome="HotMix 2",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            capacidade_gramas_min=2000,
            capacidade_gramas_max=30000,
            velocidades_suportadas=[
                TipoVelocidade.BAIXA,
                TipoVelocidade.MEDIA,
                TipoVelocidade.ALTA
            ],
            chamas_suportadas=[
                TipoChama.BAIXA,
                TipoChama.MEDIA,
                TipoChama.ALTA
            ],
            pressao_chamas_suportadas=[
                TipoPressaoChama.ALTA_PRESSAO,
                TipoPressaoChama.CHAMA_DUPLA
            ]
        )
    # =======================
    # 🧊 Freezers
    # =======================
    @staticmethod
    def criar_freezer_1():
        return Freezer(
            id=25,
            nome="Freezer 1",
            setor=TipoSetor.PANIFICACAO,
            capacidade_caixa_30kg=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    @staticmethod
    def criar_freezer_2():
        return Freezer(
            id=26,
            nome="Freezer 2",
            setor=TipoSetor.CONFEITARIA,
            capacidade_caixa_30kg=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    @staticmethod
    def criar_freezer_3():
        return Freezer(
            id=27,
            nome="Freezer 3",
            setor=TipoSetor.COZINHA,
            capacidade_caixa_30kg=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    # =======================
    # 🔥 Fornos
    # =======================

    @staticmethod
    def criar_forno_1():
        return Forno(
            id=101,
            nome="Forno 1",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=1,
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=15,
            tipo_coccao=TipoCoccao.TURBO,
            vaporizacao_seg_min=1,
            vaporizacao_seg_max=5,
            velocidade_mps_min=None,
            velocidade_mps_max=None
        )


    @staticmethod
    def criar_forno_2():
        return Forno(
            id=102,
            nome="Forno 2",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=2,
            faixa_temperatura_min=120,
            faixa_temperatura_max=200,
            setup_min=20,
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=1,
            vaporizacao_seg_max=5,
            velocidade_mps_min=None,
            velocidade_mps_max=None
        )


    @staticmethod
    def criar_forno_3():
        return Forno(
            id=103,
            nome="Forno 3",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=4,
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=20,
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=1,
            vaporizacao_seg_max=10,
            velocidade_mps_min=2,
            velocidade_mps_max=5
        )


    @staticmethod
    def criar_forno_4():
        return Forno(
            id=104,
            nome="Forno 4",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=4,
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=20,
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=None,
            vaporizacao_seg_max=None,
            velocidade_mps_min=1,
            velocidade_mps_max=4
        )
    # =========================================
    # 🗄️ Armário Esqueleto
    # =========================================
    @staticmethod
    def criar_armario_esqueleto_1():
        return ArmarioEsqueleto(
            id=105,
            nome="Armário Esqueleto 1",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=25
        )
    
    @staticmethod
    def criar_armario_esqueleto_2():
        return ArmarioEsqueleto(
            id=105,
            nome="Armário Esqueleto 2",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=25
        )


    # =========================================
    # 🗄️ Divisoras de Massas
    # =========================================

    def criar_divisora_de_massas_1():
        return DivisoraDeMassas(
            id=106,
            nome="Divisoras de Massas 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_boleamento_unidades_por_segundo=100,
            capacidade_divisao_unidades_por_segundo=100,
            capacidade_gramas_max=30000,
            capacidade_gramas_min=100,
            boleadora=False
        )
    
    def criar_divisora_de_massas_2():
        return DivisoraDeMassas(
            id=107,
            nome="Divisoras de Massas 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_boleamento_unidades_por_segundo=100,
            capacidade_divisao_unidades_por_segundo=100,
            capacidade_gramas_max=30000,
            capacidade_gramas_min=100,
            boleadora=True
        )
    # =========================================
    # 🧁 Modeladora de Pães Divisoras de Massas
    # =========================================
    @staticmethod 
    def criar_modeladora_de_paes_1():
        return ModeladoraDePaes(
            id=108,
            nome="Modeladora de Pães 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_min_unidades_por_minuto=60,
            capacidade_max_unidades_por_minuto=120 
        )
    @staticmethod 
    def criar_modeladora_de_paes_2():
        return ModeladoraDePaes(
            id=109,
            nome="Modeladora de Pães 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_min_unidades_por_minuto=60,
            capacidade_max_unidades_por_minuto=120 
        )
    # =========================================
    # 🗄️ Armário Fermentador
    # =========================================

    @staticmethod
    def criar_armario_fermentador_1():
        return ArmarioFermentador(
            id=110,
            nome="Armário Fermentador 1",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25
        )
    
    @staticmethod
    def criar_armario_fermentador_2():
        return ArmarioFermentador(
            id=111,
            nome="Armário Fermentador 2",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25
        )

    @staticmethod
    def criar_armario_fermentador_3():
        return ArmarioFermentador(
            id=112,
            nome="Armário Fermentador 3",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25
        )
    @staticmethod
    def criar_armario_fermentador_4():
        return ArmarioFermentador(
            id=113,
            nome="Armário Fermentador 4",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25
        )
        
        

# ✅ Instâncias prontas para importação
camara_refrigerada_1 = FabricaEquipamentos.criar_camara_refrigerada_1()
camara_refrigerada_2 = FabricaEquipamentos.criar_camara_refrigerada_2()

fogao_1 = FabricaEquipamentos.criar_fogao_1()
fogao_2 = FabricaEquipamentos.criar_fogao_2()

balanca_digital_1 = FabricaEquipamentos.criar_balanca_digital_1()
balanca_digital_2 = FabricaEquipamentos.criar_balanca_digital_2()
balanca_digital_3 = FabricaEquipamentos.criar_balanca_digital_3()
balanca_digital_4 = FabricaEquipamentos.criar_balanca_digital_4()

bancada_1 = FabricaEquipamentos.criar_bancada_1()
bancada_2 = FabricaEquipamentos.criar_bancada_2()
bancada_3 = FabricaEquipamentos.criar_bancada_3()
bancada_4 = FabricaEquipamentos.criar_bancada_4()
bancada_5 = FabricaEquipamentos.criar_bancada_5()
bancada_6 = FabricaEquipamentos.criar_bancada_6()
bancada_7 = FabricaEquipamentos.criar_bancada_7()
bancada_8 = FabricaEquipamentos.criar_bancada_8()

batedeira_planetaria_1 = FabricaEquipamentos.criar_batedeira_planetaria_1()
batedeira_planetaria_2 = FabricaEquipamentos.criar_batedeira_planetaria_2()
batedeira_industrial_1 = FabricaEquipamentos.criar_batedeira_industrial_1()

masseira_1 = FabricaEquipamentos.criar_masseira_1()
masseira_2 = FabricaEquipamentos.criar_masseira_2()
masseira_3 = FabricaEquipamentos.criar_masseira_3()

hotmix_1 = FabricaEquipamentos.criar_hotmix_1()
hotmix_2 = FabricaEquipamentos.criar_hotmix_2()

freezer_1 = FabricaEquipamentos.criar_freezer_1()
freezer_2 = FabricaEquipamentos.criar_freezer_2()
freezer_3 = FabricaEquipamentos.criar_freezer_3()

forno_1 = FabricaEquipamentos.criar_forno_1()
forno_2 = FabricaEquipamentos.criar_forno_2()
forno_3 = FabricaEquipamentos.criar_forno_3()
forno_4 = FabricaEquipamentos.criar_forno_4()

armario_esqueleto_1 = FabricaEquipamentos.criar_armario_esqueleto_1()
armario_esqueleto_2 = FabricaEquipamentos.criar_armario_esqueleto_2()

armario_fermentador_1 = FabricaEquipamentos.criar_armario_fermentador_1()
armario_fermentador_2 = FabricaEquipamentos.criar_armario_fermentador_2()
armario_fermentador_3 = FabricaEquipamentos.criar_armario_fermentador_3()
armario_fermentador_4 = FabricaEquipamentos.criar_armario_fermentador_4()

divisora_de_massas_1 = FabricaEquipamentos.criar_divisora_de_massas_1()
divisora_de_massas_2 = FabricaEquipamentos.criar_divisora_de_massas_2()

modeladora_de_paes_1 = FabricaEquipamentos.criar_modeladora_de_paes_1()
modeladora_de_paes_2 = FabricaEquipamentos.criar_modeladora_de_paes_2()

equipamentos_por_nome = {
    "Bancada 7": bancada_7,
    "Balança Digital 1": balanca_digital_1,
    "Balança Digital 2": balanca_digital_2,
}

equipamentos_disponiveis = [
    camara_refrigerada_1,
    camara_refrigerada_2,
    fogao_1,
    fogao_2,
    balanca_digital_1,
    balanca_digital_2,
    balanca_digital_3,
    balanca_digital_4,
    bancada_1,
    bancada_2,
    bancada_3,
    bancada_4,
    bancada_5,
    bancada_6,
    bancada_7,
    bancada_8,
    batedeira_planetaria_1,
    batedeira_planetaria_2,
    batedeira_industrial_1,
    masseira_1,
    masseira_2,
    masseira_3,
    hotmix_1,
    hotmix_2,
    freezer_1,
    freezer_2,
    freezer_3,
    forno_1,
    forno_2,
    forno_3,
    forno_4,
    armario_esqueleto_1,
    armario_esqueleto_2,
    armario_fermentador_1,
    armario_fermentador_2,
    armario_fermentador_3,
    armario_fermentador_4,
    divisora_de_massas_1,
    divisora_de_massas_2,
    modeladora_de_paes_1,
    modeladora_de_paes_2,
]
