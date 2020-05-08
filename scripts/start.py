from core.models import *

def run():

    # Creamos la configuracion inicial General
    conf = Configuracion(nombre='General')
    conf.save()

    # Creamos todos los niveles
    nivel = Nivel(monto=5)
    nivel.save()
    nivel = Nivel(monto=10)
    nivel.save()
    nivel = Nivel(monto=20)
    nivel.save()
    nivel = Nivel(monto=50)
    nivel.save()
    nivel = Nivel(monto=100)
    nivel.save()
    nivel = Nivel(monto=200)
    nivel.save()
    nivel = Nivel(monto=500)
    nivel.save()
    nivel = Nivel(monto=1000)   
    nivel.save()
    nivel = Nivel(monto=2000)
    nivel.save()
    nivel = Nivel(monto=5000)
    nivel.save()
    nivel = Nivel(monto=10000)
    nivel.save()
    nivel = Nivel(monto=20000)
    nivel.save()
    nivel = Nivel(monto=50000)
    nivel.save()
    nivel = Nivel(monto=100000)
    nivel.save()
    nivel = Nivel(monto=200000)
    nivel.save()

    # Creamos las listas
    todos_los_niveles = Nivel.objects.all()
    for nivel in todos_los_niveles:
        lista_nueva = Lista(alias='Primera lista', 
                            nivel=nivel,
                            estado='A',
                            items=3)
        lista_nueva.save()

    # Creamos usuarios de primera y segunda linea
    # Nombres personalizados
    jugador1_name = 'Ethan'
    jugador2_name = 'Tadeo'

    sistema = User(username='System')
    sistema.save()
    sistema.refresh_from_db()

    user1 = User(username=jugador1_name)
    user1.save()
    user1.refresh_from_db()

    user2 = User(username=jugador2_name)
    user2.save()
    user2.refresh_from_db()

    # Creamos jugadores
    jugador0 = Jugador(usuario=sistema, estado='A')
    jugador0.save()
    jugador0.refresh_from_db()
    
    jugador1 = Jugador(usuario=user1, promotor=jugador0, estado='A')
    jugador1.save()
    jugador1.refresh_from_db()

    jugador2 = Jugador(usuario=user2, promotor=jugador0, estado='A')
    jugador2.save()
    jugador2.refresh_from_db()

    # Creamos las cuentas de los jugadores
    nueva_cuenta = Cuenta(jugador=jugador0)
    nueva_cuenta.save()
    nueva_cuenta = Cuenta(jugador=jugador1)
    nueva_cuenta.save()
    nueva_cuenta = Cuenta(jugador=jugador2)
    nueva_cuenta.save()

    # Asignamos los jugadores a cada lista y lo activamos en ese nivel
    todas_las_listas = Lista.objects.all()
    for lista in todas_las_listas:
        nuevo_juego = Juego(lista=lista,
                            jugador=jugador0,
                            posicion=0)
        nuevo_juego.save()
        nuevo_juego.refresh_from_db()

        nuevo_jugador_nivel = JugadorNivel(jugador=jugador0, nivel=lista.nivel, estado='A', 
                                           patrocinador=None, color='green', n_referidos=2)
        nuevo_jugador_nivel.save()
        nuevo_jugador_nivel.refresh_from_db()
        
        nuevo_juego = Juego(lista=lista,
                            jugador=jugador1,
                            posicion=1)
        nuevo_juego.save()
        nuevo_juego.refresh_from_db()
        nuevo_jugador_nivel = JugadorNivel(jugador=jugador1, nivel=lista.nivel, estado='A',
                                           patrocinador=jugador0)
        nuevo_jugador_nivel.save()
        nuevo_jugador_nivel.refresh_from_db()

        nuevo_juego = Juego(lista=lista,
                            jugador=jugador2,
                            posicion=2)
        nuevo_juego.save()
        nuevo_juego.refresh_from_db()

        nuevo_jugador_nivel = JugadorNivel(jugador=jugador2, nivel=lista.nivel, estado='A',
                                           patrocinador=jugador0)
        nuevo_jugador_nivel.save()
        nuevo_jugador_nivel.refresh_from_db()
