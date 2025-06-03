# utils/gerador_ocupacao_id.py
from datetime import date

class GeradorDeOcupacaoID:
    def __init__(self):
        self.data_atual = date.today()
        self.contador = 0

    def gerar_id(self) -> int:
        if self.data_atual != date.today():
            self.data_atual = date.today()
            self.contador = 0
        self.contador += 1
        return self.contador
    
    def resetar(self):
        self.data_atual = date.today()
        self.contador = 0