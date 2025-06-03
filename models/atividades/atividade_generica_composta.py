
import json
from typing import Optional, Dict, Any
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_coccao import TipoCoccao
from enums.tipo_profissional import TipoProfissional
from enums.tipo_atividade import TipoAtividade
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from utils.consultar_duracao_por_ids import consultar_duracao_por_ids
from models.atividade_base import Atividade
from factory import fabrica_equipamentos

logger = setup_logger('Atividade_Generica_Composta')

# ==========================================
# 📦 DADOS LOCAIS PARA A ATIVIDADE
# ==========================================
DADOS_ATIVIDADES = [
    {
        "id_produto": 1,
        "nome_produto": "Carne de Sol Refogada",
        "atividades": [
            {
                "id_atividade": 1,
                "nome": "Armazenamento sob temperatura para Carne de Sol Refogada",
                "tipo_atividade": "ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CARNE_DE_SOL_REFOGADA",
                "faixa_temperatura_armazenamento": -18,
                "tipo_equipamento": {"REFRIGERACAO_CONGELAMENTO": 1},
                "equipamentos_elegiveis": ["camara_refrigerada_2"],
                "fips_equipamentos": {
                    "camara_refrigerada_2": 1
                },
                "tipos_profissionais_permitidos": ["COZINHEIRO"],
                "quantidade_funcionarios": 1,
                "faixas": [
                    {"quantidade": "3000–20000", "duracao": "0:03:00"},
                    {"quantidade": "20001–40000", "duracao": "0:05:00"},
                    {"quantidade": "40001–60000", "duracao": "0:07:00"}
                ]
            },
            {
                "id_atividade": 2,
                "nome": "Preparo para armazenamento de Carne de Sol Refogada",
                "tipo_atividade": "PREPARO_PARA_ARMAZENAMENTO_DE_CARNE_DE_SOL_REFOGADA",
                "tipo_equipamento": {
                    "BANCADAS": 1,
                    "BALANCAS": 1
                },
                "equipamentos_elegiveis": [
                    "bancada_7",
                    "balanca_digital_4",
                    "balanca_digital_2"
                ],
                "fips_equipamentos": {
                    "bancada_7": 1,
                    "balanca_digital_4": 1,
                    "balanca_digital_2": 2
                },
                "tipos_profissionais_permitidos": ["COZINHEIRO"],
                "quantidade_funcionarios": 1,
                "fracoes_necessarias": 4,
                "faixas": [
                    {"quantidade": "3000–20000", "duracao": "0:05:00"},
                    {"quantidade": "20001–40000", "duracao": "0:07:00"},
                    {"quantidade": "40001–60000", "duracao": "0:10:00"}
                ]
            }
        ]
    }
]

def buscar_dados_por_id_atividade(id_atividade: int):
    for produto in DADOS_ATIVIDADES:
        for atividade in produto["atividades"]:
            if atividade["id_atividade"] == id_atividade:
                return produto, atividade
    raise ValueError(f"❌ Atividade com id_atividade={id_atividade} não encontrada.")

class AtividadeGenericaComposta(Atividade):
    def __init__(self, id_atividade: int, quantidade_produto: int, *args, **kwargs):
        dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade)
        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]

        super().__init__(
            id=id_atividade,
            id_atividade=id_atividade,
            tipo_atividade=TipoAtividade[dados_atividade["tipo_atividade"]],
            tipos_profissionais_permitidos=[TipoProfissional[nome] for nome in dados_atividade.get("tipos_profissionais_permitidos", [])],
            quantidade_funcionarios=dados_atividade.get("quantidade_funcionarios", 1),
            equipamentos_elegiveis=equipamentos_elegiveis,
            id_produto_gerado=dados_gerais["id_produto"],
            quantidade_produto=quantidade_produto
        )

        self.nome_produto = dados_gerais.get("nome_produto")
        self.faixa_temperatura_desejada_armazenamento = dados_atividade.get("faixa_temperatura_armazenamento")
        self.tipo_ocupacao = kwargs.get("tipo_ocupacao", "CAIXAS")
        self.fracoes_necessarias = dados_atividade.get("fracoes_necessarias")
        self.faixa_temperatura_desejada_coccao = kwargs.get("faixa_temperatura_desejada_coccao")
        self.vaporizacao_seg_desejada = kwargs.get("vaporizacao_seg_desejada")
        self.velocidade_mps_desejada = kwargs.get("velocidade_mps_desejada")
        self.tipo_coccao = kwargs.get("tipo_coccao")
        self.pressao_chama = kwargs.get("pressao_chama")
        self.tipo_mistura = kwargs.get("tipo_mistura")
        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }
        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }
        self.duracao = self._consultar_duracao_por_faixas(dados_atividade)

    def _consultar_duracao_por_faixas(self, dados_atividade: Dict[str, Any]) -> timedelta:
        faixas = dados_atividade.get("faixas", [])
        qtd = self.quantidade_produto

        for faixa in faixas:
            quantidade_range = faixa["quantidade"].replace("–", "-").split("-")
            if len(quantidade_range) != 2:
                raise ValueError(f"❌ Faixa inválida: {faixa['quantidade']}")

            min_qtd, max_qtd = map(int, quantidade_range)
            if min_qtd <= qtd <= max_qtd:
                h, m, s = map(int, faixa["duracao"].split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)

        raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {qtd}g.")

    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        """
        🔧 Cria instâncias dos gestores adequados com base nos tipos de equipamento utilizados pela atividade.
        """
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}")

            gestor_cls = MAPA_GESTOR[tipo_equipamento]

            # Filtra os equipamentos da atividade que correspondem a este tipo
            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} associado à atividade.")

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)

        return gestores_por_tipo

    def calcular_duracao(self):
        return super().calcular_duracao()

    def iniciar(self):
        return super().iniciar()


    def tentar_alocar_e_iniciar(
        self,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int = None,
        fracoes_necessarias: int = None,
        velocidade_mps_desejada: int = None,
        vaporizacao_seg_desejada: int = None,
        pressao_chama=None,
        tipo_mistura: str = None
    ) -> bool:
        self.calcular_duracao()
        horario_final = fim_jornada
        equipamentos_alocados = []

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao
            sucesso = True
            equipamentos_alocados.clear()

            for tipo_eqp, quantidade in self._quantidade_por_tipo_equipamento.items():
                equipamentos = [
                    eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp
                ]

                if not equipamentos:
                    logger.warning(f"⚠️ Nenhum equipamento do tipo {tipo_eqp} disponível.")
                    sucesso = False
                    break

                classe_gestor = MAPA_GESTOR.get(tipo_eqp)
                if not classe_gestor:
                    logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp}")
                    sucesso = False
                    break

                gestor = classe_gestor(equipamentos)
                metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)

                try:
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=horario_inicio,
                        fim=horario_final,
                        temperatura_desejada=temperatura_desejada,
                        fracoes_necessarias=self.fracoes_necessarias,
                        velocidade_mps_desejada=velocidade_mps_desejada,
                        vaporizacao_seg_desejada=vaporizacao_seg_desejada,
                        pressao_chama=pressao_chama,
                        tipo_mistura=tipo_mistura
                    )
                    if not resultado[0]:
                        sucesso = False
                        break
                    equipamentos_alocados.append(resultado)
                except Exception as e:
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    sucesso = False
                    break

            if sucesso:
                self._registrar_sucesso(equipamentos_alocados, horario_inicio, horario_final)
                return True

            horario_final -= timedelta(minutes=1)

        logger.warning(f"⚠️ Falha na alocação da atividade {self.id_atividade}")
        return False

    def _registrar_sucesso(self, equipamentos_alocados, inicio: datetime, fim: datetime):
        """
        ✅ Registra os equipamentos alocados e define horários reais da atividade.
        """
        self.equipamentos_selecionados = [dados[1] for dados in equipamentos_alocados]
        self.equipamento_alocado = self.equipamentos_selecionados
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for sucesso, equipamento, i, f in equipamentos_alocados:
            if i and f:
                logger.info(f"🔧 {equipamento.nome} alocado de {i.strftime('%H:%M')} até {f.strftime('%H:%M')}")
            else:
                logger.info(f"🔧 {equipamento.nome} alocado (sem janela de tempo)")

    


    def _resolver_metodo_alocacao(self, tipo_equipamento):
        if tipo_equipamento == TipoEquipamento.REFRIGERACAO_CONGELAMENTO:
            return self._alocar_camara
        elif tipo_equipamento == TipoEquipamento.BANCADAS:
            return self._alocar_bancada
        elif tipo_equipamento == TipoEquipamento.FOGOES:
            return self._alocar_fogao
        elif tipo_equipamento == TipoEquipamento.BATEDEIRAS:
            return self._alocar_batedeira
        elif tipo_equipamento == TipoEquipamento.BALANCAS:
            return self._alocar_balanca
        elif tipo_equipamento == TipoEquipamento.FORNOS:
            return self._alocar_forno
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS:
            return self._alocar_misturadora
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS_COM_COCCAO:
            return self._alocar_misturadora_com_coccao
        elif tipo_equipamento == TipoEquipamento.ARMARIOS_PARA_FERMENTACAO:
            return self._alocar_armario_fermentacao
        else:
            raise ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")


    def _alocar_camara(self, gestor, inicio, fim, temperatura_desejada=-18, **kwargs):
        return gestor.alocar(inicio, fim, self, temperatura_desejada)

    def _alocar_bancada(self, gestor, inicio, fim, fracoes_necessarias=1, **kwargs):
        return gestor.alocar(inicio, fim, self, fracoes_necessarias)

    def _alocar_fogao(self, gestor, inicio, fim, quantidade_gramas=0, **kwargs):
        return gestor.alocar(inicio, fim, self, quantidade_gramas)

    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)

    def _alocar_balanca(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_forno(self, gestor, inicio, fim, temperatura=180, vapor=False, velocidade=None, **kwargs):
        return gestor.alocar(inicio, fim, self, temperatura, vapor, velocidade)

    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)

    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, chama=None, pressao=None, velocidade=None, **kwargs):
        return gestor.alocar(inicio, fim, self, chama, pressao, velocidade)

    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)


    # def tentar_alocar_e_iniciar(
    #     self,
    #     inicio_jornada: datetime,
    #     fim_jornada: datetime,
    #     gestores: Dict[TipoEquipamento, Any],  # Ex: {TipoEquipamento.BANCADAS: gestor_bancadas}
    #     ordem_equipamentos: list,
    #     parametros_adicionais: Optional[Dict[str, Any]] = None
    # ) -> bool:
    #     """
    #     ordem_equipamentos: ordem em que os equipamentos devem ser alocados (TipoEquipamento).
    #     parametros_adicionais: parâmetros específicos, como {"fracoes_necessarias": 2, "quantidade_gramas": 5000}
    #     """
    #     horario_final = fim_jornada
    #     parametros_adicionais = parametros_adicionais or {}

    #     while horario_final - self.duracao >= inicio_jornada:
    #         horario_inicio = horario_final - self.duracao
    #         equipamentos_alocados = []
    #         sucesso = True

    #         for tipo_eqp in ordem_equipamentos:
    #             gestor = gestores.get(tipo_eqp)
    #             if gestor is None:
    #                 logger.warning(f"⚠️ Nenhum gestor informado para {tipo_eqp}")
    #                 sucesso = False
    #                 break

    #             metodo = self._resolver_metodo_alocacao(tipo_eqp)
    #             resultado = metodo(
    #                 gestor=gestor,
    #                 inicio=horario_inicio,
    #                 fim=horario_final,
    #                 **parametros_adicionais
    #             )

    #             if not resultado[0]:
    #                 sucesso = False
    #                 break

    #             equipamentos_alocados.append(resultado)

    #         if sucesso:
    #             self._registrar_sucesso(equipamentos_alocados, horario_inicio, horario_final)
    #             return True

    #         horario_final -= timedelta(minutes=1)

    #     return False

    # def _resolver_metodo_alocacao(self, tipo_equipamento):
    #     if tipo_equipamento == TipoEquipamento.BANCADAS:
    #         return self._alocar_bancada
    #     elif tipo_equipamento == TipoEquipamento.BALANCAS:
    #         return self._alocar_balanca
    #     elif tipo_equipamento == TipoEquipamento.REFRIGERACAO_CONGELAMENTO:
    #         return self._alocar_camara
    #     else:
    #         raise ValueError(f"❌ Tipo de equipamento não suportado: {tipo_equipamento}")

    # def _alocar_bancada(self, gestor, inicio, fim, fracoes_necessarias=1, **kwargs):
    #     return gestor.alocar(inicio, fim, self, fracoes_necessarias)

    # def _alocar_balanca(self, gestor, inicio, fim, quantidade_gramas=0, **kwargs):
    #     return gestor.alocar(inicio, fim, self, quantidade_gramas)

    # def _alocar_camara(self, gestor, inicio, fim, temperatura_desejada=-18, **kwargs):
    #     return gestor.alocar(inicio, fim, self, temperatura_desejada)

    # def _registrar_sucesso(self, alocados, inicio, fim):
    #     self.inicio_real = inicio
    #     self.fim_real = fim
    #     self.equipamento_alocado = [eq[1] for eq in alocados]
    #     self.equipamentos_selecionados = self.equipamento_alocado
    #     self.alocada = True

    #     logger.info(f"✅ Atividade {self.id} alocada com sucesso:")
    #     for sucesso, eqp, *_ in alocados:
    #         logger.info(f"🔧 {eqp.nome}")