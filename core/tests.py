from django.test import TestCase
from core.models import  *
from core.views import *

class wordcycle_test(TestCase):
    def setup(self):
        conf = Configuracion(nombre='General')
        conf.save()


    def test_repartir_pago(jugador_patrocinador, lista):
        # se consulta los datos de division de pagos en la bd
        conf = Configuracion.objects.get(pk=1)
        cnf_porcent_plataforma = conf.porcent_plataforma
        cnf_porcent_patrocinador_directo = conf.porcent_patrocinador_directo
        cnf_porcent_segunda_generacion = conf.porcent_segunda_generacion
        cnf_porcent_tercera_generacion = conf.porcent_tercera_generacion
        cnf_porcent_posicion_cobro = conf.porcent_posicion_cobro

        monto = lista.nivel.monto
        print(conf.porcent_plataforma)