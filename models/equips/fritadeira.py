from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger

# 🍟 Logger exclusivo da Fritadeira
logger = setup_logger('Fritadeira')


class Fritadeira(Equipamento):
    """
    🍟 Representa uma Fritadeira com controle por frações.
    ✔️ Valida capacidade mínima e máxima por atividade.
    ✔️ Controla temperatura e tempo de setup.
    ✔️ Permite múltiplas ocupações simultâneas com validação de janela de tempo.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        numero_fracoes: int,
        capacidade_min: int,
        capacidade_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
        setup_minutos: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.FRITADEIRA,
            status_ativo=True
        )

        self.numero_fracoes = numero_fracoes
        self.capacidade_min = capacidade_min
        self.capacidade_max = capacidade_max
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.setup_minutos = setup_minutos

        # 📦 Ocupações: (atividade_id, quantidade, inicio, fim, temperatura, setup)
        self.fracoes_ocupadas: List[Tuple[int, int, datetime, datetime, int, int]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def validar_quantidade(self, quantidade: int) -> bool:
        """
        ✅ Verifica se a quantidade está dentro da faixa permitida pela fritadeira.
        """
        return self.capacidade_min <= quantidade <= self.capacidade_max

    def validar_temperatura(self, temperatura: int) -> bool:
        """
        🌡️ Verifica se a temperatura solicitada está dentro da faixa permitida.
        """
        return self.faixa_temperatura_min <= temperatura <= self.faixa_temperatura_max

    # ==========================================================
    # 🔍 Verificar disponibilidade
    # ==========================================================
    def fracoes_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """
        🔍 Calcula quantas frações estão livres no intervalo solicitado.
        """
        ocupadas = sum(
            qtd for (aid, qtd, ini, f, temp, setup) in self.fracoes_ocupadas
            if not (fim <= ini or inicio >= f)
        )
        return self.numero_fracoes - ocupadas

    # ==========================================================
    # 🔐 Ocupação
    # ==========================================================
    def ocupar(
        self,
        atividade_id: int,
        quantidade_fracoes: int,
        inicio: datetime,
        fim: datetime,
        temperatura: int
    ) -> bool:
        """
        🔐 Tenta ocupar a fritadeira com base nas regras de capacidade, temperatura e frações disponíveis.
        """
        if not self.validar_quantidade(quantidade_fracoes):
            logger.warning(f"❌ Quantidade inválida: {quantidade_fracoes}g para a fritadeira {self.nome}.")
            return False

        if not self.validar_temperatura(temperatura):
            logger.warning(f"❌ Temperatura inválida: {temperatura}°C para a fritadeira {self.nome}.")
            return False

        if self.fracoes_disponiveis(inicio, fim) < quantidade_fracoes:
            logger.warning(
                f"❌ Frações insuficientes na fritadeira {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.fracoes_ocupadas.append(
            (atividade_id, quantidade_fracoes, inicio, fim, temperatura, self.setup_minutos)
        )

        logger.info(
            f"🍟 Fritadeira {self.nome} ocupada por atividade {atividade_id} "
            f"com {quantidade_fracoes} frações, temperatura {temperatura}°C "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (setup: {self.setup_minutos} min)."
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        """
        🧹 Libera todas as frações ocupadas associadas à atividade fornecida.
        """
        antes = len(self.fracoes_ocupadas)
        self.fracoes_ocupadas = [
            (aid, qtd, ini, fim, temp, setup)
            for (aid, qtd, ini, fim, temp, setup) in self.fracoes_ocupadas
            if aid != atividade_id
        ]
        liberadas = antes - len(self.fracoes_ocupadas)

        if liberadas > 0:
            logger.info(
                f"🟩 Liberou {liberadas} ocupações da fritadeira {self.nome} "
                f"relacionadas à atividade {atividade_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da fritadeira {self.nome} estava associada à atividade {atividade_id}."
            )

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        📅 Exibe todas as ocupações atuais da fritadeira.
        """
        logger.info("==============================================")
        logger.info(f"📅 Agenda da Fritadeira {self.nome}")
        logger.info("==============================================")

        if not self.fracoes_ocupadas:
            logger.info("🔹 Nenhuma ocupação.")
            return

        for (aid, qtd, inicio, fim, temp, setup) in self.fracoes_ocupadas:
            logger.info(
                f"🍟 Atividade {aid} | Frações: {qtd} | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                f"Temp: {temp}°C | Setup: {setup} min"
            )

    # ==========================================================
    # 📊 Representação
    # ==========================================================
    def __str__(self):
        return (
            f"\n🍟 Fritadeira: {self.nome} (ID: {self.id})"
            f"\nSetor: {self.setor.name} | Status: {'Ativa' if self.status_ativo else 'Inativa'}"
            f"\nFrações totais: {self.numero_fracoes} | Ocupações atuais: {len(self.fracoes_ocupadas)}"
        )
