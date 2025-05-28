from models.atividade_base import Atividade
from models.equips.forno import Forno
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class CoccaoDeMassasParaBoloBranco(Atividade):
    """
    Atividade que representa a cocção de massas para bolo branco.
    Utiliza fornos, priorizando via FIP.
    Ocupação feita por níveis de tela (1000g = 1 nível) com temperatura fixa de 160°C.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FORNOS: 1
        }

    def calcular_duracao(self):
        """
        Define a duração da cocção com base na quantidade de massa.
        NÃO inclui o tempo de setup.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=40)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=50)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=60)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para COCCAO DE MASSA DE BOLO DE CHOCOLATE."
            )
        
    def iniciar(self):
        """
        Executa os métodos específicos dos fornos selecionados,
        priorizando conforme o FIP dos equipamentos.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        forno_alocado = None

        # Ordenar os equipamentos por FIP
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, Forno):
                equipamento.selecionar_faixa_temperatura(160)  # 🔥 Temperatura fixa

                sucesso = equipamento.ocupar_nivel_tela(
                    (self.quantidade_produto + 999) // 1000  # 1000g = 1 nível
                )

                if sucesso:
                    forno_alocado = equipamento
                    print(
                        f"🔥 Cocção de massas para bolo branco iniciada no forno {equipamento.nome} "
                        f"para {self.quantidade_produto}g "
                        f"(ocupa {(self.quantidade_produto + 999) // 1000} níveis) "
                        f"a 160°C."
                    )
                    return True
                else:
                    print(
                        f"⚠️ Forno {equipamento.nome} não possui níveis disponíveis. Buscando próximo..."
                    )

        raise Exception(
            "❌ Nenhum forno disponível para a cocção de massas para bolo branco."
        )
