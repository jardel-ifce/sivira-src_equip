from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class PreparoParaCoccaoDeCremeDeQueijo(Atividade):
    """
    Atividade que representa o preparo para cocção do creme de queijo.
    Utiliza bancada, ocupando 1/6 da capacidade total.
    Duração variável conforme quantidade.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade conforme a quantidade.
        Faixa de tempo oficial:
        - 3000–20000g → 8 minutos
        - 20001–40000g → 16 minutos
        - 40001–60000g → 24 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=8)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=16)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=24)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para PREPARO PARA COCCAO DE CREME DE QUEIJO."
            )

    def iniciar(self):
        """
        Realiza a ocupação da bancada, considerando a fração de 1/6.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None

        # 🔥 Ordena os equipamentos pelo menor FIP
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados, 
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, Bancada):
                sucesso = equipamento.ocupar((1, 6))  # ✅ Ocupa 1/6 da bancada

                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🪵 Bancada {equipamento.nome} ocupada na fração 1/6 "
                        f"para preparo do creme de queijo."
                    )
                    break
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

        if bancada_alocada:
            print(
                f"✅ Preparo para cocção do creme de queijo iniciado na "
                f"Bancada {bancada_alocada.nome}."
            )
            return True

        raise Exception(
            "❌ Não foi possível alocar uma bancada para o preparo do creme de queijo."
        )
