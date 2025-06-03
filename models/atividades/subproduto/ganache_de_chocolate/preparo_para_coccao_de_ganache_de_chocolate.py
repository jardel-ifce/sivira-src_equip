from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Preparo_Coccao_Ganache_Chocolate')


class PreparoParaCoccaoDeGanacheDeChocolate(Atividade):
    """
    🍫 Atividade de preparo para cocção de ganache de chocolate.
    ✔️ Equipamentos:
       - 🪵 Bancada (frações exclusivas no tempo).
       - 🔥 Fogão (exclusivo no tempo, alocado com base em FIP).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.FOGOES: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto

        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=20)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=30)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=40)
        else:
            raise ValueError(
                f"❌ Quantidade {q} inválida para PreparoParaCoccaoDeGanacheDeChocolate."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de ganache de chocolate."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_fogoes,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 1
    ) -> bool:
        """
        🔁 Estrutura padronizada:
        1️⃣ Tenta alocar fogão (atividade principal).
        2️⃣ Tenta alocar bancada antes da cocção.
        3️⃣ Se falhar, recua 1 minuto e tenta novamente.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_fogao = horario_final_tentativa - self.duracao

            # 🔥 1. Tenta alocar fogão
            sucesso_fogao, fogao, inicio_fogao_real, fim_fogao_real = gestor_fogoes.alocar(
                inicio=horario_inicio_fogao,
                fim=horario_final_tentativa,
                atividade=self
            )

            if not sucesso_fogao:
                logger.warning(
                    f"❌ Falha na alocação do fogão entre {horario_inicio_fogao.strftime('%H:%M')} "
                    f"e {horario_final_tentativa.strftime('%H:%M')}."
                )
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # 🪵 2. Tenta alocar bancada antes do fogão
            inicio_bancada = inicio_fogao_real - self.duracao
            sucesso_bancada, bancada, inicio_bancada_real, fim_bancada_real = gestor_bancadas.alocar(
                inicio=inicio_bancada,
                fim=inicio_fogao_real,
                atividade=self,
                fracoes_necessarias=fracoes_necessarias
            )

            if not sucesso_bancada:
                gestor_fogoes.liberar_por_atividade(self)
                logger.warning(
                    f"⚠️ Falha na alocação da bancada antes de {inicio_fogao_real.strftime('%H:%M')}. "
                    f"Liberando fogão e tentando novo horário."
                )
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # ✅ Sucesso total
            self._registrar_sucesso(
                bancada=bancada,
                fogao=fogao,
                inicio_bancada=inicio_bancada_real,
                fim_fogao=fim_fogao_real
            )
            return True

        # ❌ Falha final
        logger.error(
            f"❌ Não foi possível alocar a atividade {self.id} na janela entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def _registrar_sucesso(self, bancada, fogao, inicio_bancada, fim_fogao):
        """
        ✅ Atualiza os atributos da atividade com sucesso de alocação.
        """
        self.inicio_real = inicio_bancada
        self.fim_real = fim_fogao
        self.bancada_alocada = bancada
        self.fogao_alocado = fogao
        self.equipamento_alocado = [bancada, fogao]
        self.equipamentos_selecionados = [bancada, fogao]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_bancada.strftime('%H:%M')} até {(inicio_bancada + self.duracao).strftime('%H:%M')}\n"
            f"🔥 Fogão: {fogao.nome} de {(fim_fogao - self.duracao).strftime('%H:%M')} até {fim_fogao.strftime('%H:%M')}."
        )

    def iniciar(self):
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente "
            f"na bancada {self.bancada_alocada.nome} e fogão {self.fogao_alocado.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome} e fogão {self.fogao_alocado.nome}."
        )
