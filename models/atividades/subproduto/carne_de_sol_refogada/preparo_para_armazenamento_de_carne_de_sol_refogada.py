from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Preparo_Armazenamento_Carne_Sol')


class PreparoParaArmazenamentoDeCarneDeSolRefogada(Atividade):
    """
    🥩 Atividade de preparo para armazenamento da carne de sol refogada.
    ✔️ Equipamentos:
       - 🪵 Bancada (ocupação por frações, exclusiva no tempo por fração).
       - ⚖️ Balança Digital (ocupação exclusiva no tempo).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        """
        Calcula a duração da atividade conforme a quantidade de produto.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=3)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=5)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(
                f"❌ Quantidade {q} inválida para esta atividade."
            )
            raise ValueError(
                f"❌ Quantidade {q} inválida para PreparoParaArmazenamentoDeCarneDeSolRefogada."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de carne de sol refogada."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 2
    ) -> bool:
        """
        🔥 Backward scheduling robusto:
        1️⃣ Aloca balança (ocupação exclusiva no tempo).
        2️⃣ Aloca bancada (ocupação fracionada no tempo).
        🔄 Se falhar, faz rollback e tenta outro intervalo.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_balanca = horario_final_tentativa - self.duracao

            # 🔸 1. Tentativa de alocar balança
            sucesso_balanca, balanca, inicio_balanca, fim_balanca = gestor_balancas.alocar(
                inicio=horario_inicio_balanca,
                fim=horario_final_tentativa,
                atividade=self,
                quantidade_gramas=self.quantidade_produto
            )

            if not sucesso_balanca:
                horario_final_tentativa -= timedelta(minutes=5)
                continue

            # 🔸 2. Tentativa de alocar bancada (antes da balança)
            fim_bancada = inicio_balanca
            inicio_bancada = fim_bancada - self.duracao

            sucesso_bancada, bancada, inicio_bancada_real, fim_bancada_real = gestor_bancadas.alocar(
                inicio=inicio_bancada,
                fim=fim_bancada,
                atividade=self,
                fracoes_necessarias=fracoes_necessarias
            )

            if sucesso_bancada:
                # ✅ Sucesso total
                self.inicio_real = inicio_bancada_real
                self.fim_real = fim_balanca
                self.bancada_alocada = bancada
                self.balanca_alocada = balanca
                self.equipamento_alocado = [bancada, balanca]
                self.equipamentos_selecionados = [bancada, balanca]
                self.alocada = True

                logger.info(
                    f"✅ Atividade {self.id} alocada com sucesso!\n"
                    f"🪵 Bancada: {bancada.nome} de {inicio_bancada_real.strftime('%H:%M')} até {fim_bancada_real.strftime('%H:%M')}\n"
                    f"⚖️ Balança: {balanca.nome} de {inicio_balanca.strftime('%H:%M')} até {fim_balanca.strftime('%H:%M')}"
                )
                return True

            # 🔥 Rollback automático: libera balança
            gestor_balancas.liberar_por_atividade(self)

            logger.warning(
                f"⚠️ Falha na alocação da bancada para atividade {self.id} "
                f"no intervalo {inicio_bancada.strftime('%H:%M')} até {fim_bancada.strftime('%H:%M')}.\n"
                f"Liberando balança {balanca.nome} e retrocedendo no tempo."
            )

            horario_final_tentativa -= timedelta(minutes=5)

        # ❌ Não conseguiu alocar
        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def iniciar(self):
        """
        🟢 Marca oficialmente o início da atividade.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente "
            f"na bancada {self.bancada_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
