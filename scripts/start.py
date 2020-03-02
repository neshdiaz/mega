from core.models import Configuracion

def run():
    conf = Configuracion(nombre='General')
    conf.save()
