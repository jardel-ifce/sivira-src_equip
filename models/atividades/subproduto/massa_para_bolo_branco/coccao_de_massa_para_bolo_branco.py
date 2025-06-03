from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from utils.conversores_ocupacao import gramas_para_niveis_tela

# 🔥 Logger específico para esta atividade
logger = setup_logger('AtividadeCoccaoMassaBoloBranco')


class CoccaoDeMassaParaBoloBranco(Atividade):
    """
    🔥🎂 Cocção da massa de bolo branco.
    ✅ Utiliza fornos com controle de:
    - Ocupação por níveis
    - Temperatura (160°C)
    - Vaporização (opcional)
    - Velocidade (opcional)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "NIVEIS_TELA"
        self.forno_alocado = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FORNOS: 1
        }

    def calcular_duracao(self):
        q = self.quantidade_produto
        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=40)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=50)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=60)
        else:
            logger.error(f"❌ Quantidade {q} fora das faixas.")
            raise ValueError(f"❌ Quantidade {q} fora das faixas.")
        self.niveis_necessarios = gramas_para_niveis_tela(q)
        logger.info(f"🕒 Duração: {self.duracao} | Níveis: {self.niveis_necessarios}")

    def tentar_alocar_e_iniciar(self, gestor_fornos, inicio_janela, horario_limite, temperatura_desejada=160, vaporizacao_desejada=None, velocidade_desejada=None):
        self.calcular_duracao()
        logger.info(f"🚀 Tentando alocar atividade {self.id}.")
        sucesso, forno, inicio_real, fim_real = gestor_fornos.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self,
            temperatura_desejada=temperatura_desejada,
            vaporizacao_desejada=vaporizacao_desejada,
            velocidade_desejada=velocidade_desejada
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação do forno para a atividade {self.id}.")
            return False

        self._registrar_sucesso(forno, inicio_real, fim_real)
        return True

    def _registrar_sucesso(self, forno, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.forno_alocado = forno
        self.equipamento_alocado = forno
        self.equipamentos_selecionados = [forno]
        self.alocada = True
        logger.info(f"✅ Cocção {self.id} alocada no forno {forno.nome} das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}.")

    def iniciar(self):
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada.")
            raise Exception("❌ Atividade não alocada.")
        logger.info(f"🚀 Iniciada no forno {self.forno_alocado.nome} das {self.inicio_real.strftime('%H:%M')} às {self.fim_real.strftime('%H:%M')}.")
