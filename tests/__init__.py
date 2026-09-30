"""Suíte de testes do HQ Tools (roda fora do Krita).

O Qt falso é instalado aqui, antes de qualquer import do ``hq_tools``, para a
suíte dar o mesmo resultado na máquina do autor e no CI. Sem isso, o
``compat`` pegava o PyQt de verdade quando ele estava instalado (o cache de
miniaturas "passava" por acaso) e quebrava com ``ImportError`` quando não
estava.
"""

from tests.qt_falso import instalar

instalar()
