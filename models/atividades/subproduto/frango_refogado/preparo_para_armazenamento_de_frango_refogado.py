from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from models.equips.balanca_digital import BalancaDigital
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class PreparoParaArmazenamentoDeFrangoRefogado(Atividade):
    """
    Atividade que representa o preparo para armazenamento do frango refogado.
    Utiliza uma bancada (ocupação fracionada em 3/6) e uma balança para pesagem.
    Duração variável conforme quantidade.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade com base na quantidade de produto.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=10)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=20)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=30)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para PREPARO PARA ARMAZENAMENTO DE FRANGO REFOGADO."
            )

    def iniciar(self):
        """
        Realiza a ocupação dos equipamentos: bancada e balança digital.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None
        balanca_alocada = None

        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            # 👉 Ocupação da bancada
            if isinstance(equipamento, Bancada) and bancada_alocada is None:
                sucesso = equipamento.ocupar((3, 6))  # ✅ Ocupa 3/6 da bancada
                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🪵 Bancada {equipamento.nome} ocupada na fração 3/6 "
                        f"para preparo de frango refogado."
                    )
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

            # 👉 Ocupação da balança
            if isinstance(equipamento, BalancaDigital) and balanca_alocada is None:
                if not equipamento.ocupar(self.quantidade_produto):
                    raise Exception(
                        f"❌ A quantidade ({self.quantidade_produto}g) não pode ser pesada na balança {equipamento.nome}. "
                        f"Capacidade mínima: {equipamento.capacidade_gramas_min}g | "
                        f"Capacidade máxima: {equipamento.capacidade_gramas_max}g."
                    )
                else:
                    balanca_alocada = equipamento
                    print(
                        f"⚖️ Balança {equipamento.nome} ocupada para pesagem de "
                        f"{self.quantidade_produto}g de frango refogado."
                    )

            if bancada_alocada and balanca_alocada:
                print(
                    f"✅ Preparo para armazenamento do frango refogado iniciado com "
                    f"Bancada {bancada_alocada.nome} e Balança {balanca_alocada.nome}."
                )
                return True

        raise Exception(
            "❌ Não foi possível alocar todos os equipamentos necessários "
            "(Bancada e Balança Digital)."
        )
