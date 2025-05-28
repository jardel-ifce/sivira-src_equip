from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from models.equips.armario_esqueleto import ArmarioEsqueleto
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class PreparoParaCoccaoDeMassasParaBoloBranco(Atividade):
    """
    Atividade que representa o preparo para cocção de massas para bolo branco.
    Utiliza uma bancada (conforme capacidade de fração) e um armário esqueleto
    (seguindo a lógica de 1000g = 1 nível de tela).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade com base na quantidade de massa.
        """
        q = self.quantidade_produto
        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=8)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=16)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=24)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas definidas para PREPARO PARA COCCÃO DE MASSAS PARA BOLO BRANCO."
            )

    def iniciar(self):
        """
        Executa os métodos específicos dos equipamentos selecionados,
        priorizando conforme o FIP dos equipamentos.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None
        armario_alocado = None

        # Ordenar equipamentos por FIP
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            # Ocupação da bancada
            if isinstance(equipamento, Bancada) and bancada_alocada is None:
                # Ocupa conforme a fração definida na bancada (o método já gerencia isso)
                sucesso = equipamento.ocupar(equipamento.capacidade_total)  

                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🧰 Bancada {equipamento.nome} ocupada para preparo de cocção "
                        f"na fração {equipamento.capacidade_total}."
                    )
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

            # Ocupação do Armário Esqueleto (1000g = 1 nível de tela)
            if isinstance(equipamento, ArmarioEsqueleto) and armario_alocado is None:
                sucesso = equipamento.ocupar(self.quantidade_produto)
                if sucesso:
                    armario_alocado = equipamento
                    print(
                        f"📦 Armário Esqueleto {equipamento.nome} ocupado com "
                        f"{self.quantidade_produto}g "
                        f"(equivalente a {(self.quantidade_produto + 999) // 1000} níveis de tela)."
                    )
                else:
                    print(
                        f"⚠️ Armário Esqueleto {equipamento.nome} não disponível. Buscando próximo..."
                    )

            if bancada_alocada and armario_alocado:
                print(
                    f"✅ Preparo para cocção de massas para bolo branco iniciado com "
                    f"Bancada {bancada_alocada.nome} e Armário {armario_alocado.nome}."
                )
                return True

        raise Exception(
            "❌ Não foi possível alocar todos os equipamentos necessários "
            "(Bancada e Armário Esqueleto)."
        )
