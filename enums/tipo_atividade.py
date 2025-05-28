from enum import Enum


class TipoAtividade(Enum):
    # ============================================
    # 🥟 Atividades de Massas
    # ============================================
    FABRICACAO_MASSAS = "Fabricação de Massas"
    MISTURA_DE_MASSAS_CROCANTES = "Mistura de Massas Crocantes"
    MISTURA_DE_MASSAS_SUAVES = "Mistura de Massas Suaves"
    MISTURA_DE_MASSAS_PARA_FRITURAS = "Mistura de Massas para Frituras"
    MISTURA_DE_MASSAS_PARA_FOLHADOS = "Mistura de Massas para Folhados"
    LAMINACAO_1_DE_MASSAS_PARA_FOLHADOS = "Laminação 1 de Massas para Folhados"
    LAMINACAO_2_DE_MASSAS_PARA_FOLHADOS = "Laminação 2 de Massas para Folhados"
    DESCANSO_DE_MASSAS_PARA_FOLHADOS = "Descanso de Massas para Folhados"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_MASSAS_FOLHADAS = "Armazenamento Sob Temperatura para Massas Folhadas"
    FABRICACAO_DE_RECHEIOS = "Fabricação de Recheios"
    MODELAGEM_DE_SALGADOS_DE_FORNO = "Modelagem de Salgados de Forno"
    MODELAGEM_DE_SALGADOS_DE_FRITURA = "Modelagem de Salgados de Fritura"
    ASSAMENTO_DE_SALGADOS = "Assamento de Salgados"
    FRITURA_DE_SALGADOS = "Fritura de Salgados"
    CONTAGEM_DE_SALGADOS = "Contagem de Salgados"
    CONTAGEM_PORCOES_DE_RECHEIOS = "Contagem de Porções de Recheios"

    # ============================================
    # 🍗 Atividades para Frango Refogado
    # ============================================
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_FRANGO_REFOGADO = "Armazenamento Sob Temperatura para Frango Refogado"
    PREPARO_PARA_COCCAO_DE_FRANGO_COZIDO_PRONTO = "Preparo para Cocção de Frango Cozido Pronto"

    # ============================================
    # 🥩 Atividades para Carne de Sol
    # ============================================
    COCCAO_DE_CARNE_DE_SOL_COZIDA_PRONTA = "Cocção de Carne de Sol Cozida Pronta"
    PREPARO_PARA_ARMAZENAMENTO_DE_CARNE_DE_SOL_REFOGADA = "Preparo para Armazenamento de Carne de Sol Refogada"
    PREPARO_PARA_COCCAO_DE_CARNE_DE_SOL_REFOGADA = "Preparo para Cocção de Carne de Sol Refogada"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CARNE_DE_SOL_REFOGADA = "Armazenamento Sob Temperatura para Carne de Sol Refogada"

    # ============================================
    # 🦐 Atividades para Creme de Camarão
    # ============================================
    COCCAO_DE_CREME_DE_CAMARAO = "Cocção de Creme de Camarão"
    PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_CAMARAO = "Preparo para Armazenamento de Creme de Camarão"
    PREPARO_PARA_COCCAO_DE_CREME_DE_CAMARAO = "Preparo para Cocção de Creme de Camarão"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_DE_CAMARAO = "Armazenamento Sob Temperatura para Creme de Camarão"

    # ============================================
    # 🍗 Atividades para Creme de Frango
    # ============================================
    COCCAO_DE_CREME_DE_FRANGO = "Cocção de Creme de Frango"
    PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_FRANGO = "Preparo para Armazenamento de Creme de Frango"
    PREPARO_PARA_COCCAO_DE_CREME_DE_FRANGO = "Preparo para Cocção de Creme de Frango"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_DE_FRANGO = "Armazenamento Sob Temperatura para Creme de Frango"

    # ============================================
    # 🍋 Atividades para Creme de Limão
    # ============================================
    PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_LIMAO = "Preparo para Armazenamento de Creme de Limão"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_DE_LIMAO = "Armazenamento Sob Temperatura para Creme de Limão"
    MISTURA_DE_CREME_DE_LIMAO = "Mistura de Creme de Limão"

    # ============================================
    # 🍶 Atividades para Creme de Chantilly
    # ============================================
    MISTURA_DE_CREME_CHANTILLY = "Mistura de Creme Chantilly"
    PREPARO_PARA_ARMAZENAMENTO_DE_CREME_CHANTILLY = "Preparo para Armazenamento de Creme Chantilly"
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_CHANTILLY = "Armazenamento Sob Temperatura para Creme Chantilly"

    # ============================================
    # 🧀 Atividades para Creme de Queijo
    # ============================================
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_DE_QUEIJO = "Armazenamento Sob Temperatura para Creme de Queijo"
    COCCAO_DE_CREME_DE_QUEIJO = "Cocção de Creme de Queijo"
    PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_QUEIJO = "Preparo para Armazenamento de Creme de Queijo"
    PREPARO_PARA_COCCAO_DE_CREME_DE_QUEIJO = "Preparo para Cocção de Creme de Queijo"

    # ============================================
    # 🍰 Atividades de Confeitaria e Sobremesas
    # ============================================
    MODELAGEM_DE_SOBREMESAS = "Modelagem de Sobremesas"
    MODELAGEM_DE_MASSAS = "Modelagem de Massas"
    ASSAMENTO_DE_MASSAS = "Assamento de Massas"
    FINALIZACAO_DE_SOBREMESAS = "Finalização de Sobremesas"
    CONTAGEM_DE_SOBREMESAS = "Contagem de Sobremesas"
    PESAGEM_DE_MASSAS = "Pesagem de Massas"

    # ============================================
    # 🍰 Atividades de Bolo Branco
    # ============================================
    ARMAZENAMENTO_SOB_TEMPERATURA_PARA_MASSA_PARA_BOLO_BRANCO = "Armazenamento Sob Temperatura para Massa para Bolo Branco"


    # ============================================
    # 🍰 Atividades de Massa para Brownie
    # ============================================
    COCCAO_DE_MASSAS_PARA_BROWNIE = "Cocção de Massas para Brownie"
    
    # ============================================
    # 🏭 Atividades Gerais
    # ============================================
    LIMPEZA_DA_AREA_DE_PRODUCAO = "Limpeza da Área de Produção"
    SUPERVISAO_DA_QUALIDADE_DE_PRODUCAO_DOS_SALGADOS = "Supervisão da Qualidade da Produção dos Salgados"
    SUPERVISAO_DA_QUALIDADE_DE_PRODUCAO_DE_CONFEITARIA = "Supervisão da Qualidade da Produção de Confeitaria"
