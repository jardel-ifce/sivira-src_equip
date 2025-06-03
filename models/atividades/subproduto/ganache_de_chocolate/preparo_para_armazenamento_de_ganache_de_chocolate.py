from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🍫 Logger específico
logger = setup_logger('Atividade_Preparo_Armazenamento_Ganache_De_Chocolate')


class PreparoParaArmazenamentoDeGanacheDeChocolate(Atividade):
    """
    🍫 Atividade de preparo para armazenamento da ganache de chocolate.
    ✔️ Equipamentos:
       - 🪵 Bancada (ocupação por frações, exclusiva no tempo por fração).
       - ⚖️ Balança Digital (registro de uso por peso, uso concorrente).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bancada_alocada = None
        self.balanca_alocada = None
        self.fim_bancada_real = None  # ✅ Rastreia o fim real da bancada

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto

        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=3)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=5)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(f"❌ Quantidade {q}g inválida para esta atividade.")
            raise ValueError(
                f"❌ Quantidade {q}g inválida para PreparoParaArmazenamentoDeGanacheDeChocolate."
            )

        logger.info(f"🕒 Duração calculada: {self.duracao} para {q}g de ganache de chocolate.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int
    ) -> bool:
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} ({self.quantidade_produto}g) entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}"
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao

            # 🔹 Tentar alocar bancada
            sucesso_bancada, bancada, i_real, f_real = gestor_bancadas.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                fracoes_necessarias=fracoes_necessarias
            )

            if not sucesso_bancada:
                logger.warning(
                    f"❌ Bancada não disponível entre "
                    f"{horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}."
                )
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # 🔹 Tentar registrar uso da balança
            sucesso_balanca, balanca = gestor_balancas.alocar(
                atividade=self,
                quantidade_gramas=self.quantidade_produto
            )

            if not sucesso_balanca:
                gestor_bancadas.liberar_por_atividade(self)
                logger.warning(
                    f"⚠️ Balança indisponível para atividade {self.id}. Liberando bancada e tentando novo intervalo."
                )
                continue

            # ✅ Sucesso total
            self._registrar_sucesso(bancada, balanca, i_real, f_real)
            return True

        # ❌ Falha final
        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def _registrar_sucesso(self, bancada, balanca, inicio_bancada, fim_bancada):
        self.bancada_alocada = bancada
        self.balanca_alocada = balanca
        self.equipamento_alocado = [bancada, balanca]
        self.equipamentos_selecionados = [bancada, balanca]

        self.inicio_real = inicio_bancada
        self.fim_bancada_real = fim_bancada
        self.fim_real = fim_bancada
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_bancada.strftime('%H:%M')} até {fim_bancada.strftime('%H:%M')}\n"
            f"⚖️ Balança: {balanca.nome} registrada com {self.quantidade_produto}g"
        )

    def iniciar(self):
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada. Não é possível iniciar.")
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada na bancada {self.bancada_alocada.nome} às {self.inicio_real.strftime('%H:%M')}"
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} na bancada {self.bancada_alocada.nome}."
        )
