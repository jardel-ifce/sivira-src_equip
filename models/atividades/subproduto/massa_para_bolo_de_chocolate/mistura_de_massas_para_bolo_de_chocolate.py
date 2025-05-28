from models.atividade_base import Atividade
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class MisturaDeMassasParaBoloDeChocolate(Atividade):
    """
    Atividade que representa a mistura de massas para bolo de chocolate.
    Utiliza batedeiras planetárias ou industriais conforme a quantidade,
    priorizando via FIP.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BATEDEIRAS: 1
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade com base na quantidade de massa.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=5)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=7)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=9)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas definidas para MISTURA DE MASSAS PARA BOLO DE CHOCOLATE."
            )

    def iniciar(self):
        """
        Executa os métodos específicos dos equipamentos selecionados,
        priorizando conforme o FIP dos equipamentos.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        batedeira_alocada = None

        # Ordenar os equipamentos por FIP
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, (BatedeiraPlanetaria, BatedeiraIndustrial)):
                sucesso = equipamento.ocupar(self.quantidade_produto)

                if sucesso:
                    equipamento.selecionar_velocidade(5)
                    batedeira_alocada = equipamento
                    print(
                        f"✅ Mistura de massas para bolo de chocolate iniciada na batedeira {equipamento.nome} "
                        f"com {self.quantidade_produto}g na velocidade 5."
                    )
                    return True
                else:
                    print(
                        f"⚠️ Batedeira {equipamento.nome} não disponível ou sem capacidade. Buscando próxima..."
                    )

        raise Exception(
            "❌ Nenhuma batedeira disponível para a mistura de massas para bolo de chocolate."
        )
