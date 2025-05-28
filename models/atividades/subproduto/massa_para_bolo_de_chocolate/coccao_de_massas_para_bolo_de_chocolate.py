from models.atividade_base import Atividade
from models.equips.forno import Forno
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class CoccaoDeMassaParaBoloDeChocolate(Atividade):
    """
    Atividade que representa a cocção da massa para bolo de chocolate.
    Utiliza fornos, ocupando níveis de tela (4 níveis por forno).
    Considera tempo de setup e faixa de temperatura.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FORNOS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da cocção com base em uma regra fixa.
        Aqui vamos assumir, como exemplo, que o tempo de cocção é de 40 minutos.
        O setup de 20 minutos é adicionado automaticamente.
        """
        tempo_coccao = timedelta(minutes=40)  # Definir conforme sua ficha técnica real
        tempo_setup = timedelta(minutes=20)
        self.duracao = tempo_setup + tempo_coccao

    def iniciar(self):
        """
        Realiza ocupação dos fornos selecionados, considerando níveis de tela.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        forno_alocado = None

        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, Forno) and forno_alocado is None:
                niveis_necessarios = (self.quantidade_produto + 999) // 1000  # Cada 1000g ocupa 1 nível

                sucesso = equipamento.ocupar_niveis(niveis_necessarios)

                if sucesso:
                    forno_alocado = equipamento
                    equipamento.ajustar_temperatura(160)  # Ajusta temperatura
                    print(
                        f"🔥 Forno {equipamento.nome} ocupado com {niveis_necessarios} níveis "
                        f"para cocção de {self.quantidade_produto}g a 160°C."
                    )
                else:
                    print(
                        f"⚠️ Forno {equipamento.nome} não disponível. Buscando próximo..."
                    )

            if forno_alocado:
                print(
                    f"✅ Cocção de massa para bolo de chocolate iniciada no Forno {forno_alocado.nome}."
                )
                return True

        raise Exception(
            "❌ Não foi possível alocar forno disponível para cocção de massa de bolo de chocolate."
        )
