from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Preparo_Armazenamento_Frango_Refogado')


class PreparoParaArmazenamentoDeFrangoRefogado(Atividade):
    """
    🍗 Atividade de preparo para armazenamento do frango refogado.
    ✔️ Equipamentos:
       - 🩵 Bancada (ocupação por frações, exclusiva no tempo por fração).
       - ⚖️ Balança Digital (registro de uso por peso, uso concorrente).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=10)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=20)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=30)
        else:
            logger.error(f"❌ Quantidade {q} fora das faixas válidas para esta atividade.")
            raise ValueError(
                f"❌ Quantidade {q} inválida para PreparoParaArmazenamentoDeFrangoRefogado."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de frango refogado."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 3
    ) -> bool:
        """
        🔁 Backward scheduling robusto:
        1️⃣ Aloca bancada (com controle de tempo e frações).
        2️⃣ Registra uso da balança (sem tempo, apenas valida peso).
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao

            sucesso_bancada, bancada, inicio_bancada_real, fim_bancada_real = gestor_bancadas.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                fracoes_necessarias=fracoes_necessarias
            )

            if not sucesso_bancada:
                logger.warning(
                    f"❌ Não foi possível alocar bancada para atividade {self.id} "
                    f"entre {horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}."
                )
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            sucesso_balanca, balanca = gestor_balancas.alocar(
                atividade=self,
                quantidade_gramas=self.quantidade_produto
            )

            if not sucesso_balanca:
                gestor_bancadas.liberar_por_atividade(self)
                logger.warning(
                    f"⚠️ Não foi possível registrar uso da balança para atividade {self.id}. "
                    f"Liberando bancada {bancada.nome} e tentando outro intervalo."
                )
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            self._registrar_sucesso(bancada, balanca, inicio_bancada_real, fim_bancada_real)
            return True

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def _registrar_sucesso(self, bancada, balanca, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.bancada_alocada = bancada
        self.balanca_alocada = balanca
        self.equipamento_alocado = [bancada, balanca]
        self.equipamentos_selecionados = [bancada, balanca]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🩵 Bancada: {bancada.nome} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}\n"
            f"⚖️ Balança: {balanca.nome} registrada com {self.quantidade_produto}g"
        )

    def iniciar(self):
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente "
            f"na bancada {self.bancada_alocada.nome} às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
