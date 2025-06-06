
import json
import os
from typing import Optional, Dict, Any
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_coccao import TipoCoccao
from enums.tipo_profissional import TipoProfissional
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividade_base import Atividade
from parser.leitor_json_subprodutos import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama

logger = setup_logger('Atividade_Generica_Composta')

dados, dados_atividade = buscar_dados_por_id_atividade(3)
nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]


id_atividade = dados_atividade["id_atividade"]
nome = dados_atividade["nome"]
tipo_atividade = dados_atividade["tipo_atividade"]
tipo_equipamento = dados_atividade["tipo_equipamento"]
equipamentos_elegiveis = dados_atividade["equipamentos_elegiveis"]
fips_equipamentos = dados_atividade["fips_equipamentos"]
configuracoes_equipamentos = dados_atividade["configuracoes_equipamentos"]
tipos_profissionais_permitidos = dados_atividade["tipos_profissionais_permitidos"]
quantidade_funcionarios = dados_atividade["quantidade_funcionarios"]
faixas = dados_atividade["faixas"]

print(type(configuracoes_equipamentos))

print(configuracoes_equipamentos.get("Fogão 1").get("tipo_chama"))
