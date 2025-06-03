from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from utils.conversores_ocupacao import gramas_para_niveis_tela

# 🔥 Logger específico para esta atividade
logger = setup_logger('AtividadeCoccaoMassaBrownie')


class CoccaoDeMassasParaBrownie(Atividade):
    """
    🔥🍫 Cocção da massa de brownie.
    ✅ Utiliza fornos com controle de:
    - Ocupação por níveis
    - Temperatura (180°C)
    - Vaporização (se aplicável)
    - Velocidade (se aplicável)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "NIVEIS_TELA"
        self.niveis_necessarios = 0
        self.forno_alocado = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FORNOS: self.niveis_necessarios,
        }

    def calcular_duracao(self):
        """
        ✅ Duração fixa de 15 minutos para qualquer quantidade entre 1000g e 20000g.
        """
        q = self.quantidade_produto

        if 1000 <= q <= 20000:
            self.duracao = timedelta(minutes=15)
        else:
            logger.error(f"❌ Quantidade {q} fora da faixa válida para cocção de massa de brownie.")
            raise ValueError(f"❌ Quantidade {q} fora da faixa válida para cocção de massa de brownie.")

        self.niveis_necessarios = gramas_para_niveis_tela(q)

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa de brownie. "
            f"Níveis necessários: {self.niveis_necessarios}"
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_fornos,
        inicio_janela: datetime,
        horario_limite: datetime,
        temperatura_desejada: int = 180,
        vaporizacao_desejada: int = None,
        velocidade_desejada: int = None
    ) -> bool:
        """
        🔥 Tenta alocar backward em forno com controle de temperatura e recursos.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g | níveis: {self.niveis_necessarios}) "
            f"entre {inicio_janela.strftime('%H:%M')} e {horario_limite.strftime('%H:%M')}."
        )

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

        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.forno_alocado = forno
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🔥 Forno: {forno.nome} | "
            f"Período: {inicio_real.strftime('%H:%M')} - {fim_real.strftime('%H:%M')} | "
            f"Temp: {temperatura_desejada}°C | "
            f"Vapor: {vaporizacao_desejada if vaporizacao_desejada is not None else 'N/A'}s | "
            f"Velocidade: {velocidade_desejada if velocidade_desejada is not None else 'N/A'} m/s"
        )

        print(
            f"✅ Atividade {self.id} alocada no forno {forno.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )

        return True

    def iniciar(self):
        """
        🟢 Inicia oficialmente a atividade no forno.
        """
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar.")
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Cocção da massa de brownie iniciada no forno {self.forno_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada no forno {self.forno_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
