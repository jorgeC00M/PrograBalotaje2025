# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class IteradorConfig:
    T: int = 20
    R: int = 50
    seed: int = 42
