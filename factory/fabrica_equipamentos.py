# =========================================
# 📦 Imports dos Equipamentos
# =========================================
from models.equipamentos.camara_refrigerada import CamaraRefrigerada
from models.equipamentos.freezer import Freezer
from models.equipamentos.fogao import Fogao
from models.equipamentos.balanca_digital import BalancaDigital
from models.equipamentos.bancada import Bancada
from models.equipamentos.batedeira_industrial import BatedeiraIndustrial
from models.equipamentos.batedeira_planetaria import BatedeiraPlanetaria
from models.equipamentos.masseira import Masseira
from models.equipamentos.hot_mix import HotMix
from models.equipamentos.forno import Forno
from models.equipamentos.fritadeira import Fritadeira
from models.equipamentos.armario_esqueleto import ArmarioEsqueleto
from models.equipamentos.divisora_de_massas import DivisoraDeMassas
from models.equipamentos.modeladora_de_paes import ModeladoraDePaes
from models.equipamentos.modeladora_de_salgados import ModeladoraDeSalgados  
from models.equipamentos.armario_fermentador import ArmarioFermentador
from models.equipamentos.embaladora import Embaladora
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from enums.equipamentos.tipo_mistura import TipoMistura
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_coccao import TipoCoccao
from enums.equipamentos.tipo_embalagem import TipoEmbalagem


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
            capacidade_caixa_min=1,
            capacidade_caixa_max=200,  # CORRIGIDO: 20 → 200
            nivel_tela=25,
            capacidade_niveis_min=1,
            capacidade_niveis_max=25,  # CORRIGIDO: 1 → 25
            faixa_temperatura_min=0,   # CORRIGIDO: -18 → 0
            faixa_temperatura_max=4,
        )

    @staticmethod
    def criar_camara_refrigerada_2():
        return CamaraRefrigerada(
            id=2,
            nome="Câmara Refrigerada 2",
            setor=TipoSetor.ALMOXARIFADO,
            capacidade_caixa_min=1,
            capacidade_caixa_max=200,  # CORRIGIDO: 20 → 200
            nivel_tela=25,
            capacidade_niveis_min=1,
            capacidade_niveis_max=1,
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
            numero_operadores=6,  # CORRIGIDO: 1 → 6
            chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
            capacidade_por_boca_gramas_min=1,  # CORRIGIDO: 2000 → 500 (permite batches pequenos)
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
            numero_operadores=4,  # CORRIGIDO: 1 → 4
            chamas_suportadas=[TipoChama.BAIXA, TipoChama.MEDIA, TipoChama.ALTA],
            capacidade_por_boca_gramas_min=1,  # CORRIGIDO: 2000 → 500 (permite batches pequenos)
            capacidade_por_boca_gramas_max=30000,
            numero_bocas=4,  # CORRIGIDO: 6 → 4
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
    # 🪵 Criação das Bancadas (corrigido)
    # ============================================
    @staticmethod
    def criar_bancada_1():
        return Bancada(
            id=9,
            nome="Bancada 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=4,
            numero_fracoes=4  # Ajustado para consistência
        )

    @staticmethod
    def criar_bancada_2():
        return Bancada(
            id=10,
            nome="Bancada 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=4,
            numero_fracoes=4  # Ajustado para consistência
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
            numero_operadores=6,  # CORRIGIDO: 3 → 6
            numero_fracoes=6      # CORRIGIDO: 3 → 6
        )

    @staticmethod
    def criar_bancada_7():
        return Bancada(
            id=15,
            nome="Bancada 7",
            setor=TipoSetor.COZINHA,
            numero_operadores=6,  # CORRIGIDO: 3 → 6
            numero_fracoes=6      # CORRIGIDO: 3 → 6
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
            capacidade_gramas_min=1,
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
            numero_operadores=1,
            capacidade_gramas_min=1,
            capacidade_gramas_max=50000,  # CORRIGIDO: 5000 → 50000
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
            capacidade_gramas_min=1,
            capacidade_gramas_max=30000,
            numero_operadores=1,
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
            capacidade_gramas_min=1,
            capacidade_gramas_max=20000,
            numero_operadores=1,
            tipos_de_mistura_suportados=[TipoMistura.LENTA],  # CORRIGIDO: formato lista
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
            capacidade_gramas_min=1000,
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
            capacidade_gramas_min=1000,
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
            capacidade_caixa_min=1,
            capacidade_caixa_max=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    @staticmethod
    def criar_freezer_2():
        return Freezer(
            id=26,
            nome="Freezer 2",
            setor=TipoSetor.CONFEITARIA,
            capacidade_caixa_min=1,
            capacidade_caixa_max=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    @staticmethod
    def criar_freezer_3():
        return Freezer(
            id=27,
            nome="Freezer 3",
            setor=TipoSetor.COZINHA,
            capacidade_caixa_min=1,
            capacidade_caixa_max=6,
            faixa_temperatura_min=0,
            faixa_temperatura_max=4
        )

    # =======================
    # 🔥 Fornos
    # =======================

    @staticmethod
    def criar_forno_1():
        return Forno(
            id=28,
            nome="Forno 1",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=1,
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=15,
            capacidade_niveis_min=1,
            capacidade_niveis_max=15,
            tipo_coccao=TipoCoccao.TURBO,
            vaporizacao_seg_min=1,
            vaporizacao_seg_max=5,
            velocidade_mps_min=None,
            velocidade_mps_max=None
        )


    @staticmethod
    def criar_forno_2():
        return Forno(
            id=29,
            nome="Forno 2",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=2,
            faixa_temperatura_min=120,
            faixa_temperatura_max=200,
            setup_min=20,
            capacidade_niveis_min=1,
            capacidade_niveis_max=2,
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=1,
            vaporizacao_seg_max=5,
            velocidade_mps_min=None,
            velocidade_mps_max=None
        )


    @staticmethod
    def criar_forno_3():
        return Forno(
            id=30,
            nome="Forno 3",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=4,  # CORRIGIDO: 2 → 4
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=20,
            capacidade_niveis_min=1,
            capacidade_niveis_max=4,  # CORRIGIDO: 10 → 4
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=None,  # CORRIGIDO: 1 → None
            vaporizacao_seg_max=None,  # CORRIGIDO: 10 → None
            velocidade_mps_min=None,   # CORRIGIDO: 1 → None
            velocidade_mps_max=None    # CORRIGIDO: 4 → None
        )


    @staticmethod
    def criar_forno_4():
        return Forno(
            id=31,
            nome="Forno 4",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=4,  # CORRIGIDO: 2 → 4
            faixa_temperatura_min=120,
            faixa_temperatura_max=300,
            setup_min=20,
            capacidade_niveis_min=1,
            capacidade_niveis_max=4,  # CORRIGIDO: 10 → 4
            tipo_coccao=TipoCoccao.LASTRO,
            vaporizacao_seg_min=None,  # CORRIGIDO: 1 → None
            vaporizacao_seg_max=None,  # CORRIGIDO: 10 → None
            velocidade_mps_min=None,   # CORRIGIDO: 1 → None
            velocidade_mps_max=None    # CORRIGIDO: 4 → None
        )
        
    # =========================================
    # 🍟 Fritadeiras
    # =========================================
    @staticmethod
    def criar_fritadeira_1():
        return Fritadeira(
            id=32,
            nome="Fritadeira 1",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=4,  # CORRIGIDO: 1 → 4
            capacidade_gramas_min=1000,
            capacidade_gramas_max=5000,
            numero_fracoes=4,
            faixa_temperatura_min=120,  # CORRIGIDO: 150 → 120
            faixa_temperatura_max=250,
            setup_minutos=10
        )
    
    
    # =========================================
    # 🗄️ Armário Esqueleto
    # =========================================
    @staticmethod
    def criar_armario_esqueleto_1():
        return ArmarioEsqueleto(
            id=33,
            nome="Armário Esqueleto 1",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=25,
            capacidade_niveis=1
        )
    
    @staticmethod
    def criar_armario_esqueleto_2():
        return ArmarioEsqueleto(
            id=34,
            nome="Armário Esqueleto 2",
            setor=TipoSetor.CONFEITARIA,
            nivel_tela_min=1,
            nivel_tela_max=25,
            capacidade_niveis=1
        )


    # =========================================
    # 🗄️ Divisoras de Massas
    # =========================================

    @staticmethod
    def criar_divisora_de_massas_1():
        return DivisoraDeMassas(
            id=35,
            nome="Divisoras de Massas 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=2,  # Ajustado conforme PDF
            capacidade_boleamento_unidades_por_segundo=100,
            capacidade_divisao_unidades_por_segundo=100,
            capacidade_gramas_max=30000,
            capacidade_gramas_min=100,
            boleadora=False
        )
    
    @staticmethod
    def criar_divisora_de_massas_2():
        return DivisoraDeMassas(
            id=36,
            nome="Divisoras de Massas 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=2,  # Ajustado conforme PDF
            capacidade_boleamento_unidades_por_segundo=100,
            capacidade_divisao_unidades_por_segundo=100,
            capacidade_gramas_max=30000,
            capacidade_gramas_min=100,
            boleadora=True
        )
    # =========================================
    # 🧁 Modeladora de Pães
    # =========================================
    @staticmethod 
    def criar_modeladora_de_paes_1():
        return ModeladoraDePaes(
            id=37,
            nome="Modeladora de Pães 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=2,  # Ajustado conforme PDF
            capacidade_min_unidades_por_minuto=30,  # CORRIGIDO: 60 → 30
            capacidade_max_unidades_por_minuto=35   # CORRIGIDO: 120 → 35
        )
    @staticmethod 
    def criar_modeladora_de_paes_2():
        return ModeladoraDePaes(
            id=38,
            nome="Modeladora de Pães 2",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_min_unidades_por_minuto=60,
            capacidade_max_unidades_por_minuto=120 
        )
    
    # =========================================
    # 🥟 Modeladora de Salgados (NOVO EQUIPAMENTO)
    # =========================================
    @staticmethod
    def criar_modeladora_de_salgados_1():
        return ModeladoraDeSalgados(
            id=39,
            nome="Modeladora de salgados",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=3,
            capacidade_min_unidades_por_minuto=9,
            capacidade_max_unidades_por_minuto=83
        )
    
    # =========================================
    # 🗄️ Armário Fermentador
    # =========================================
    @staticmethod
    def criar_armario_fermentador_1():
        return ArmarioFermentador(
            id=40,
            nome="Armário Fermentador 1",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25,  # Mantido conforme PDF
            capacidade_niveis=1
        )
    
    @staticmethod
    def criar_armario_fermentador_2():
        return ArmarioFermentador(
            id=41,
            nome="Armário Fermentador 2",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25,  # Mantido conforme PDF
            capacidade_niveis=1
        )

    @staticmethod
    def criar_armario_fermentador_3():
        return ArmarioFermentador(
            id=42,
            nome="Armário Fermentador 3",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25,  # CORRIGIDO: 15 → 25
            capacidade_niveis=1
        )
    @staticmethod
    def criar_armario_fermentador_4():
        return ArmarioFermentador(
            id=43,
            nome="Armário Fermentador 4",
            setor=TipoSetor.PANIFICACAO,
            nivel_tela_min=1,
            nivel_tela_max=25,  # CORRIGIDO: 15 → 25
            capacidade_niveis=1
        )
        
    # =========================================
    # ✉️ Embaladoras
    # =========================================       
    @staticmethod
    def criar_embaladora_1():
        """
        🚀 ATUALIZADO: Embaladora 1 com capacidades min/max adequadas para 1100g+
        """
        return Embaladora(
            id=44,
            nome="Embaladora 1",
            setor=TipoSetor.PANIFICACAO,
            numero_operadores=1,
            capacidade_gramas_min=1,
            capacidade_gramas_max=1000,
            lista_tipo_embalagem=[TipoEmbalagem.SIMPLES, TipoEmbalagem.SELADORA]
        )

    @staticmethod
    def criar_embaladora_2():
        """
        🚀 ATUALIZADO: Embaladora 2 com capacidades min/max adequadas para 1100g+
        """
        return Embaladora(
            id=45,
            nome="Embaladora 2",
            setor=TipoSetor.CONFEITARIA,
            numero_operadores=1,
            capacidade_gramas_min=1,     
            capacidade_gramas_max=1000,   
            lista_tipo_embalagem=[TipoEmbalagem.VACUO, TipoEmbalagem.SELADORA]
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

fritadeira_1 = FabricaEquipamentos.criar_fritadeira_1()

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

# NOVO EQUIPAMENTO
modeladora_de_salgados_1 = FabricaEquipamentos.criar_modeladora_de_salgados_1()

embaladora_1 = FabricaEquipamentos.criar_embaladora_1()  
embaladora_2 = FabricaEquipamentos.criar_embaladora_2()

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
    fritadeira_1,
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
    modeladora_de_salgados_1,  # NOVO EQUIPAMENTO ADICIONADO
    embaladora_1,
    embaladora_2
]