from . import tab_cargar
from . import tab_definir
from . import tab_crosstabs
from . import tab_analisis
from . import tab_distribuciones
from . import tab_poisson
from . import tab_multinomial
from . import tab_iteracion
from . import tab_transiente
from . import tab_simulacion


def registrar_pestanas(app):
    tab_cargar.build(app)
    tab_definir.build(app)
    tab_crosstabs.build(app)
    tab_analisis.build(app)
    tab_distribuciones.build(app)
    tab_poisson.build(app)
    tab_multinomial.build(app)
    tab_iteracion.build(app)
    tab_transiente.build(app)
    tab_simulacion.build(app)
