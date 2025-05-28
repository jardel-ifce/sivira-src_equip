from models.atividade_base import Atividade
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class MisturaDeMassasParaBrownie(Atividade):
    """
    Atividade que representa a mistura de massas para brownie.
    Utiliza batedeiras priorizando via FIP, sempre na velocidade 5.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BATEDEIRAS: 1,
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
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE MASSAS PARA BROWNIE."
            )

    def iniciar(self):
        """
        Executa os métodos específicos das batedeiras selecionadas,
        priorizando conforme o FIP dos equipamentos.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        # Ordena batedeiras pela prioridade (FIP)
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, (BatedeiraIndustrial, BatedeiraPlanetaria)):
                equipamento.selecionar_velocidade(5)  # ✅ Velocidade 5 sempre
                sucesso = equipamento.ocupar(self.quantidade_produto)

                if sucesso:
                    print(
                        f"🌀 Mistura de massas para brownie iniciada na batedeira {equipamento.nome} "
                        f"para {self.quantidade_produto}g de massa na velocidade 5."
                    )
                    return True
                else:
                    print(
                        f"⚠️ Não foi possível ocupar a batedeira {equipamento.nome}. "
                        "Tentando a próxima na ordem de prioridade..."
                    )

        raise Exception("❌ Nenhuma batedeira disponível para a mistura de massas para brownie.")
