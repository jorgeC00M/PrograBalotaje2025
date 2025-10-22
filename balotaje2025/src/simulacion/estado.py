# -*- coding: utf-8 -*-
class EstadoIndividuo:
    """Representa el estado (clase de voto) y su firmeza asociada."""
    def __init__(self, clase: str, firmeza: float = 0.0):
        self.clase = clase
        self.firmeza = firmeza  # 0..5
