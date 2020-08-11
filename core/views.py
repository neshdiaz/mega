import datetime
import json
from django.views.decorators.csrf import requires_csrf_token
from django.utils import timezone
from django.db.models import F
from django.db import transaction
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Lista, Jugador, Juego, Cobrador, Clon, User,\
                    JugadorNivel, Nivel, Cuenta, Configuracion, Movimiento

@requires_csrf_token
def index(request):
    return render(request, 'core/index.html')


@login_required
@requires_csrf_token
def mis_referidos(request):

    return render(request, 'core/mis_referidos.html', {
        'base_url': request.build_absolute_uri('/')[:-1].strip("/")})

@login_required
@requires_csrf_token
def mis_clones(request):
    return render(request, 'core/mis_clones.html', {
        'base_url': request.build_absolute_uri('/')[:-1].strip("/")})

@login_required
@requires_csrf_token
def mi_tienda(request):

    return render(request, 'core/mi_tienda.html', {
        'base_url': request.build_absolute_uri('/')[:-1].strip("/")})

@login_required
@requires_csrf_token
def mis_niveles(request):

    jugador = Jugador.objects.get(usuario__username=request.user.username)
    niveles = list(JugadorNivel.objects.filter(jugador=jugador))

    return render(request, 'core/mis_niveles.html',
                  {'niveles_jugador': niveles,
                   'base_url': request.build_absolute_uri('/')[:-1].strip("/")})


@login_required
@requires_csrf_token
def mis_finanzas(request):
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    cuenta_jugador = Cuenta.objects.get(jugador=jugador)

    return render(request, 'core/mis_finanzas.html', {
        'base_url': request.build_absolute_uri('/')[:-1].strip("/"),
        'cuenta': cuenta_jugador
        })

@login_required
@requires_csrf_token
def home(request, id_usuario=None, id_lista=None):
    hora_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    listas_activas = JugadorNivel.objects.filter(jugador__usuario__username=request.user.username, \
                                                       estado='A')
    tiene_niveles_activos = listas_activas.exists()

    jugador = Jugador.objects.get(usuario__username=request.user.username)
    jugador_niveles = JugadorNivel.objects.filter(jugador=jugador)

    tiene_bloqueo_nivel = False
    tiene_bloqueo_clon = False
    for jugador in jugador_niveles:
        if jugador.bloqueo_x_cobros_nivel == True:
            tiene_bloqueo_nivel = True
        if jugador.bloqueo_y_cobros_clon == True:
            tiene_bloqueo_clon = True

    return render(request, 'core/home.html', {
        'hora_local': hora_local,
        'base_url': request.build_absolute_uri('/')[:-1].strip("/"),
        'tiene_niveles_activos': tiene_niveles_activos,
        'tiene_bloqueo_nivel':tiene_bloqueo_nivel,
        'tiene_bloqueo_clon':tiene_bloqueo_clon})

# @receiver(post_save, sender=Jugador)
#def activar_jugador(instance, created, **kwargs):
#    if created:
#        asignar_jugador(instance)

#@receiver(post_save, sender=Cobrador)
#def signal_cobrador(instance, created, **kwargs):
    #if created:
    # jugador_inc_cobros(instance.jugador, instance.nivel)

@transaction.atomic
def asignar_jugador(nuevo_jugador, nivel_lista):
    jugador_nivel = JugadorNivel.objects.get(jugador=nuevo_jugador, \
        nivel=nivel_lista)
    patrocinador = jugador_nivel.patrocinador
    log_registrar('log.txt', ' ')
    log_registrar('log.txt', 'Entra NUEVO JUGADOR: ' + str(nuevo_jugador) +
                  ' Patrocinado por: ' + str(patrocinador))

    # buscar lista y posicion valida del patrocinador
    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    nueva_ubicacion = buscar_ubicacion(patrocinador, nivel_lista)

    nueva_lista = nueva_ubicacion['lista']
    nueva_posicion = nueva_ubicacion['posicion']
    if nueva_ubicacion['posicion'] != -1:

        # Creamos el juego para enlazar la lista con el nuevo jugador
        juego = Juego(lista=nueva_ubicacion['lista'],
                      jugador=nuevo_jugador,
                      posicion=nueva_ubicacion['posicion'])
        juego.save()
        juego.refresh_from_db()


        log_registrar('log.txt', 'Jugador ' + str(nuevo_jugador) +
                      ' agregado a lista ' + str(nueva_ubicacion['lista']) +
                      ' en posicion: ' +
                      str(nueva_ubicacion['posicion']))

        # procesos post asignacion directa
        lista_inc_item(nueva_ubicacion['lista'])

        jugador_inc_referidos(patrocinador, nueva_ubicacion['lista'].nivel)
        jugador_validar_bloqueos(patrocinador, nueva_ubicacion['lista'].nivel)
        jugador_validar_pcs(patrocinador, nueva_ubicacion['lista'].nivel)
        jugador_inc_activos_abuelo(patrocinador, nueva_ubicacion['lista'].nivel)
              
        if nueva_ubicacion['posicion'] != 3:
            jugador_pago(nuevo_jugador, nueva_ubicacion['lista'])
            jugador_que_cobra = Juego.objects.get(lista=nueva_ubicacion['lista'], posicion=0).jugador
            jugador_inc_cobros(jugador_que_cobra, nueva_ubicacion['lista'].nivel)

        lista_nuevo_cobrador(nueva_ubicacion['lista'])

        respuesta = 'Jugador asignado correctamente'
        notificar_asignacion()

        # Creacion de lista nueva
        if nueva_ubicacion['posicion'] == 4:
            lista_nueva(nueva_ubicacion['lista'])
        # bloque de ciclaje de jugadores
        elif nueva_ubicacion['posicion'] == 3:
            # ciclo la lista en la nueva ubicacion
            # empieza el ciclaje
            usuario_que_paga = '(' + str(nuevo_jugador) + '-> '
            # ciclo la lista donde se ubico la posicion libre
            ret_ciclado = lista_ciclar(nueva_ubicacion['lista'])
            
            usuario_que_paga += str(ret_ciclado['jugador_ciclado'])
            ret_id = ret_ciclado['juego'].id
            # guardo en BD
            ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
            ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
            ultimo_ciclaje_juego.save()
            ultimo_ciclaje_juego.refresh_from_db()
            
            # se reparte el pago completo a la cabeza de la lista para ciclar
            jugador_repartir_pago_ciclaje(nuevo_jugador, nueva_ubicacion['lista'], True)
            
            lista_nuevo_cobrador(ret_ciclado['lista'])
            ret_id = ret_ciclado['juego'].id

            # si cae en 3 y despues en posicion diferente de ciclaje
            # guardo y cierro la cadena con )
            if ret_ciclado['posicion'] != 3:
                usuario_que_paga += ')'
                # guardo en BD
                ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                ultimo_ciclaje_juego.save()
                ultimo_ciclaje_juego.refresh_from_db()
                jugador_pago(ret_ciclado['jugador_ciclado'], ret_ciclado['lista'])
                # 
                jugador_que_cobra = Juego.objects.get(lista=ret_ciclado['lista'], posicion=0).jugador
                jugador_inc_cobros(jugador_que_cobra, ret_ciclado['lista'].nivel)

            if ret_ciclado['posicion'] == 4:
                lista_nueva(ret_ciclado['lista'])

            # bloque de multiples asignaciones en posicion de ciclaje
            # 2 o mas ciclajes
            while ret_ciclado['posicion'] == 3:
                # cayendo en posicion de ciclaje
                ret_ciclado = lista_ciclar(ret_ciclado['lista'])
                usuario_que_paga += '-> ' + str(ret_ciclado['jugador_ciclado'])

                lista_nuevo_cobrador(ret_ciclado['lista'])
                ret_id = ret_ciclado['juego'].id

                jugador_repartir_pago_ciclaje(ret_ciclado['jugador_ciclado'], ret_ciclado['lista'], False)

                # guardo en BD
                ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                ultimo_ciclaje_juego.save()
                ultimo_ciclaje_juego.refresh_from_db()

                # si cae en 3 y despues en posicion diferente de ciclaje
                # guardo y cierro la cadena con )
                if ret_ciclado['posicion'] != 3:
                    usuario_que_paga += ')'
                    # guardo en BD
                    ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                    ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                    ultimo_ciclaje_juego.save()
                    ultimo_ciclaje_juego.refresh_from_db()

                    jugador_pago(ret_ciclado['jugador_ciclado'], \
                        ret_ciclado['lista'])
                    jugador_que_cobra = Juego.objects.get(lista=ret_ciclado['lista'], posicion=0).jugador
                    jugador_inc_cobros(jugador_que_cobra, ret_ciclado['lista'].nivel)
                    
                if ret_ciclado['posicion'] == 4:
                    lista_nueva(ret_ciclado['lista'])

                if ret_ciclado['posicion'] == 2:
                    jugador_pago(ret_ciclado['jugador_ciclado'], \
                    ret_ciclado['lista'])
                    jugador_que_cobra = Juego.objects.get(lista=ret_ciclado['lista'], posicion=0).jugador
                    jugador_inc_cobros(jugador_que_cobra, ret_ciclado['lista'].nivel)
    else:
        respuesta = 'No se encontraron posiciones disponibles'
        log_registrar('log.txt', 'No se encontraron posiciones disponibles')
    
    return patrocinador, nueva_lista, nueva_posicion

@transaction.atomic
def asignar_clon(clon, nivel_lista):
    log_registrar('log.txt', 'asignando clon de ' + str(clon.jugador))
    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    nueva_ubicacion = lista_buscar_mas_antigua(nivel_lista)


    if nueva_ubicacion['posicion'] != -1:
        # Creamos el juego para enlazar la lista con el nuevo jugador
        juego = Juego(lista=nueva_ubicacion['lista'],
                      jugador=clon.jugador,
                      posicion=nueva_ubicacion['posicion'])
        juego.save()
        juego.refresh_from_db()

        
        log_registrar('log.txt', 'Clon ' + str(clon.jugador) +
                      ' agregado a lista ' + str(nueva_ubicacion['lista']) +
                      ' en posicion: ' +
                      str(nueva_ubicacion['posicion']))

        # procesos post asignacion directa
        lista_inc_item(nueva_ubicacion['lista'])

        lista_nuevo_cobrador(nueva_ubicacion['lista'])

        respuesta = 'Clon asignado correctamente'
        notificar_asignacion()

        # Creacion de lista nueva
        if nueva_ubicacion['posicion'] == 4:
            lista_nueva(nueva_ubicacion['lista'])   
        # bloque de ciclaje de jugadores
        elif nueva_ubicacion['posicion'] == 3:
            # ciclo la lista en la nueva ubicacion
            # empieza el ciclaje
            usuario_que_paga = '(' + str(clon.jugador) + '-> '
            # ciclo la lista donde se ubico la posicion libre
            ret_ciclado = lista_ciclar(nueva_ubicacion['lista'])
            usuario_que_paga += str(ret_ciclado['jugador_ciclado'])
            ret_id = ret_ciclado['juego'].id
            # guardo en BD
            ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
            ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
            ultimo_ciclaje_juego.save()
            ultimo_ciclaje_juego.refresh_from_db()


            lista_nuevo_cobrador(ret_ciclado['lista'])
            ret_id = ret_ciclado['juego'].id

            # si cae en 3 y despues en posicion diferente de ciclaje
            # guardo y cierro la cadena con )
            if ret_ciclado['posicion'] != 3:
                usuario_que_paga += ')'
                # guardo en BD
                ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                ultimo_ciclaje_juego.save()
                ultimo_ciclaje_juego.refresh_from_db()

            if ret_ciclado['posicion'] == 4:
                lista_nueva(ret_ciclado['lista'])

            # bloque de multiples asignaciones en posicion de ciclaje
            # 2 o mas ciclajes
            while ret_ciclado['posicion'] == 3:
                ret_ciclado = lista_ciclar(ret_ciclado['lista'])
                usuario_que_paga += '-> ' + str(ret_ciclado['jugador_ciclado'])
                lista_nuevo_cobrador(ret_ciclado['lista'])
                ret_id = ret_ciclado['juego'].id

                # guardo en BD
                ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                ultimo_ciclaje_juego.save()
                ultimo_ciclaje_juego.refresh_from_db()

                # si cae en 3 y despues en posicion diferente de ciclaje
                # guardo y cierro la cadena con )            
                if ret_ciclado['posicion'] != 3:
                    usuario_que_paga += ')'
                    # guardo en BD
                    ultimo_ciclaje_juego = Juego.objects.get(pk=ret_id)
                    ultimo_ciclaje_juego.cadena_ciclaje = str(usuario_que_paga)
                    ultimo_ciclaje_juego.save()
                    ultimo_ciclaje_juego.refresh_from_db()
                    # movimiento entrada salida por pago completo por ciclaje
                    jugador_repartir_pago(ret_ciclado['jugador_ciclado'], ret_ciclado['lista'].nivel, True)
                    

                if ret_ciclado['posicion'] == 4:
                    lista_nueva(ret_ciclado['lista'])
    else:
        respuesta = 'No se encontraron posiciones disponibles'
        log_registrar('log.txt', 'No se encontraron posiciones disponibles')

    return HttpResponse(reverse('core:mis_clones'))


@transaction.atomic
def jugador_repartir_pago_ciclaje(jugador_origen, lista, primer_ciclaje):
    jugador_destino = Jugador.objects.get(juego__lista=lista.id, juego__posicion=0)
        
    cuenta_jugador_origen = Cuenta.objects.get(jugador=jugador_origen)
    cuenta_jugador_destino = Cuenta.objects.get(jugador=jugador_destino)

    if primer_ciclaje:
        nuevo_movimiento_destino = Movimiento(cuenta=cuenta_jugador_destino,
                                        billetera='D',
                                        tipo='E',
                                        concepto='CI',
                                        descripcion='Saldo a favor en ciclaje de usuario ' + str(cuenta_jugador_origen.jugador) + ' en nivel ' + str(lista.nivel.id) + ' lista ' + str(lista.id),
                                        valor=(lista.nivel.monto * 50) / 100,
                                        )
        nuevo_movimiento_destino.save()

        nuevo_movimiento_destino = Movimiento(cuenta=cuenta_jugador_destino,
                                        billetera='D',
                                        tipo='S',
                                        concepto='CI',
                                        descripcion='Reintegro a favor en ciclaje a usuario ' + str(cuenta_jugador_destino.jugador) + ' en nivel ' + str(lista.nivel.id) + ' lista ' + str(lista.id),
                                        valor=(lista.nivel.monto * 50) / 100,
                                        )
        nuevo_movimiento_destino.save()


    else:
        nuevo_movimiento_origen = Movimiento(cuenta=cuenta_jugador_origen,
                                            billetera='D',
                                            tipo='S',
                                            concepto='CI',
                                            descripcion='Reintegro en ciclaje a usuario ' + str(cuenta_jugador_destino.jugador) + ' en nivel ' + str(lista.nivel.id) + ' lista ' + str(lista.id),
                                            valor=(lista.nivel.monto * 50) / 100,
                                        )

        nuevo_movimiento_destino = Movimiento(cuenta=cuenta_jugador_destino,
                                            billetera='D',
                                            tipo='E',
                                            concepto='CI',
                                            descripcion='Saldo a favor en ciclaje de usuario ' + str(cuenta_jugador_origen.jugador) + ' en nivel ' + str(lista.nivel.id) + ' lista ' + str(lista.id),
                                            valor=(lista.nivel.monto * 50) / 100,
                                        )                                    
        nuevo_movimiento_origen.save()
        nuevo_movimiento_destino.save()



@transaction.atomic
def jugador_pago(jugador, lista):
    # se consulta los datos de division de pagos en la bd
    conf = Configuracion.objects.get(pk=1)
    monto = lista.nivel.monto
    cuenta_jugador = Cuenta.objects.get(jugador=jugador)

    # Estableciendo porcentajes para cada jugador
    porcent_posicion_cobro = (monto * conf.porcent_posicion_cobro)/100

    # Estableciendo jugadores para comision
    jugador_posicion_cobro = Juego.objects.get(lista=lista, posicion=0).jugador

    # Actualizamos cuentas y movimientos de cada jugador
   

    # Movimientos de entrada de el cobrador de la lista
    cuenta_posicion_cobro = Cuenta.objects.get(jugador=jugador_posicion_cobro)
    cuenta_posicion_cobro.saldo_disponible = F('saldo_disponible') + porcent_posicion_cobro

    cuenta_posicion_cobro.saldo_total = F('saldo_total') + porcent_posicion_cobro
    cuenta_posicion_cobro.beneficios_totales = F('beneficios_totales') + porcent_posicion_cobro
    cuenta_posicion_cobro.save()
    cuenta_posicion_cobro.refresh_from_db()
    
    movimiento_posicion_cobro = Movimiento(cuenta=cuenta_posicion_cobro,
                                           billetera='D',
                                           tipo='E',
                                           concepto='PN',
                                           descripcion='Pago de jugador ' + str(jugador) + ' en nivel ' + str(lista.nivel.id) + ' lista ' + str(lista.id),
                                           valor=porcent_posicion_cobro)
    movimiento_posicion_cobro.save()


@transaction.atomic
def jugador_repartir_pago_comisiones(jugador, nivel_a_activar):
    # se consulta los datos de division de pagos en la bd
    conf = Configuracion.objects.get(pk=1)
    monto = nivel_a_activar.nivel.monto
    cuenta_jugador = Cuenta.objects.get(jugador=jugador)

    # Estableciendo porcentajes para cada jugador
    porcent_plataforma = (monto * conf.porcent_plataforma)/100
    porcent_patrocinador_directo = (monto * conf.porcent_patrocinador_directo)/100
    porcent_segunda_generacion = (monto * conf.porcent_segunda_generacion)/100
    porcent_tercera_generacion = (monto * conf.porcent_tercera_generacion)/100
    

    # Estableciendo jugadores para comision

    jugador_plataforma = Jugador.objects.get(usuario__username='System')
    jugador_patrocinador = jugador.promotor
    if jugador_patrocinador is None:
        jugador_patrocinador = Jugador.objects.get(usuario__username='System')

    jugador_nivel_patrocinador = JugadorNivel.objects.get(jugador=jugador_patrocinador,\
        nivel=nivel_a_activar.nivel)
    jugador_segunda_generacion = jugador_nivel_patrocinador.patrocinador
    if jugador_segunda_generacion is None:
        jugador_segunda_generacion = Jugador.objects.get(usuario__username='System')

    jugador_nivel_patrocinador_3 = JugadorNivel.objects.get(jugador=jugador_segunda_generacion,\
        nivel=nivel_a_activar.nivel)
    jugador_tercera_generacion = jugador_nivel_patrocinador_3.patrocinador
    if jugador_tercera_generacion is None:
        jugador_tercera_generacion = Jugador.objects.get(usuario__username='System')
    
    
    # Actualizamos cuentas y movimientos de cada jugador
    # cuenta_plataforma arranca con todos los niveles activos no se valida autoactivacion
    cuenta_plataforma = Cuenta.objects.get(jugador=jugador_plataforma)
    
    cuenta_plataforma.saldo_activacion = F('saldo_activacion') + porcent_plataforma
    
    cuenta_plataforma.saldo_total = F('saldo_total') + porcent_plataforma
    
    cuenta_plataforma.beneficios_totales = F('beneficios_totales') + porcent_plataforma
    
    cuenta_plataforma.save()
    cuenta_plataforma.refresh_from_db()

    movimiento_plataforma_e = Movimiento(cuenta=cuenta_plataforma,
                                        billetera="A",
                                        tipo='E',
                                        concepto='CP',
                                        descripcion='Comisión a plataforma de usuario ' + \
                                            str(jugador) + ' en nivel ' + str(nivel_a_activar.nivel.id),
                                        valor=porcent_plataforma)
    movimiento_plataforma_e.save()

    # cuenta_patrocinador_directo
    cuenta_patrocinador_directo = Cuenta.objects.get(jugador=jugador_patrocinador)
    cuenta_patrocinador_directo.saldo_activacion = F('saldo_activacion') + porcent_patrocinador_directo
    
        
    cuenta_patrocinador_directo.saldo_total = F('saldo_total') + porcent_patrocinador_directo
    cuenta_patrocinador_directo.beneficios_totales = F('beneficios_totales') + porcent_patrocinador_directo
    cuenta_patrocinador_directo.save()
    cuenta_patrocinador_directo.refresh_from_db()
    # Validamos si tiene saldo de comisiones suficiente para activar niveles pendientes

    movimiento_patrocinador_directo = Movimiento(cuenta=cuenta_patrocinador_directo,
                                                 billetera='A',
                                                 tipo='E',  
                                                 concepto='C1',
                                                 descripcion='Comisión por patrocinador directo de \
                                                     jugador ' + str(jugador)  + ' en nivel ' + str(nivel_a_activar.nivel.id),
                                                 valor=porcent_patrocinador_directo)
    movimiento_patrocinador_directo.save()
    jugador_validar_auto_nivel_up(jugador_patrocinador, nivel_a_activar.nivel)

    cuenta_segunda_generacion = Cuenta.objects.get(jugador=jugador_segunda_generacion)
    cuenta_segunda_generacion.saldo_activacion = F('saldo_activacion') + porcent_segunda_generacion
    
    cuenta_segunda_generacion.saldo_total = F('saldo_total') + porcent_segunda_generacion
    cuenta_segunda_generacion.beneficios_totales = F('beneficios_totales') + porcent_segunda_generacion
    cuenta_segunda_generacion.save()
    cuenta_segunda_generacion.refresh_from_db()
    # Validamos si tiene saldo de comisiones suficiente para activar niveles pendientes

    movimiento_segunda_generacion = Movimiento(cuenta=cuenta_segunda_generacion,
                                               billetera='A',
                                               tipo='E',
                                               concepto='C2',
                                               descripcion='Comisión por segunda generacion de\
                                                     jugador ' + str(jugador) + ' en nivel ' + str(nivel_a_activar.nivel.id),
                                               valor=porcent_segunda_generacion)
    movimiento_segunda_generacion.save()
    jugador_validar_auto_nivel_up(jugador_segunda_generacion, nivel_a_activar.nivel)

    cuenta_tercera_generacion = Cuenta.objects.get(jugador=jugador_tercera_generacion)
    cuenta_tercera_generacion.saldo_activacion = F('saldo_activacion') + porcent_tercera_generacion
    
    cuenta_tercera_generacion.saldo_total = F('saldo_total') + porcent_tercera_generacion
    cuenta_tercera_generacion.beneficios_totales = F('beneficios_totales') + porcent_tercera_generacion
    cuenta_tercera_generacion.save()
    cuenta_tercera_generacion.refresh_from_db()
    # Validamos si tiene saldo de comisiones suficiente para activar niveles pendientes

    movimiento_tercera_generacion = Movimiento(cuenta=cuenta_tercera_generacion,
                                               billetera='A',
                                               tipo='E',
                                               concepto='C3',
                                               descripcion='Comisión por tercera generación de jugador ' + str(jugador) + ' en nivel ' + str(nivel_a_activar.nivel.id),
                                               valor=porcent_tercera_generacion)
    movimiento_tercera_generacion.save()
    jugador_validar_auto_nivel_up(jugador_tercera_generacion, nivel_a_activar.nivel)

@transaction.atomic
def jugador_validar_auto_nivel_up(jugador, nivel_lista):
    cuenta_jugador = Cuenta.objects.get(jugador=jugador)
    niveles_creados = Nivel.objects.all()
    niveles_jugador = JugadorNivel.objects.filter(jugador=jugador)
    for nivel_jugador in niveles_jugador:
        if cuenta_jugador.saldo_activacion > nivel_jugador.nivel.monto and \
            nivel_jugador.estado == 'P':
            nivel_jugador.estado = 'A'
            nivel_jugador.save()
            nivel_jugador.refresh_from_db()

            jugador.estado = 'A'
            jugador.save()
            jugador.refresh_from_db()

            # Descontar de la cuenta y registrar el movimiento auto
            cuenta_jugador.saldo_activacion = F('saldo_activacion') - nivel_jugador.nivel.monto
            cuenta_jugador.saldo_total = F('saldo_total') - nivel_jugador.nivel.monto
            cuenta_jugador.save()
            cuenta_jugador.refresh_from_db()

            desc_movimiento = 'Pago activación automática nivel  ' + str(nivel_jugador.nivel.id)
            nuevo_movimiento = Movimiento(cuenta=cuenta_jugador,
                                        billetera='A',
                                        tipo='S',
                                        concepto='PA',
                                        descripcion=desc_movimiento,
                                        valor=nivel_jugador.nivel.monto)
            nuevo_movimiento.save()
            nuevo_movimiento.refresh_from_db()

            asignar_jugador(jugador, nivel_jugador.nivel.id)
            
            # Reparto las comisiones de cada generación
            jugador_repartir_pago_comisiones(jugador, nivel_jugador)
            
            nivel_anterior_id = nivel_jugador.nivel.id - 1
            if nivel_anterior_id > 0:
                nivel_anterior = Nivel.objects.get(pk=nivel_anterior_id)
                nivel_anterior_jugador = JugadorNivel(jugador=jugador,
                                                      nivel=nivel_anterior)
                if nivel_anterior_jugador.bloqueo_x_cobros_nivel == True:
                    nivel_anterior_jugador.bloqueo_x_cobros_nivel = False
                    nivel_anterior_jugador.color = 'green'


def buscar_ubicacion(patrocinador, nivel_lista):
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}

    # if patrocinador is not None:
    log_registrar('log.txt', 'BUSCANDO EN LISTAS DEL PATROCINADOR ')
    ubicacion = lista_buscar_padre(patrocinador, nivel_lista)
    if ubicacion['posicion'] == -1:
        log_registrar('log.txt', 'No hay posiciones libres en las listas del patrocinador ' +
                      str(patrocinador))
        log_registrar('log.txt', 'BUSCANDO EN  LISTAS DE LA DESCENDENCIA')
        ubicacion = lista_buscar_descendencia(patrocinador, nivel_lista)
        if ubicacion['posicion'] == -1:
            log_registrar('log.txt', 'No hay posiciones libres en las listas de la descendencia ')
            log_registrar('log.txt', 'BUSCANDO EN LISTA MAS ANTIGUA')
            ubicacion = lista_buscar_mas_antigua(nivel_lista)
    return ubicacion






# Busquedas de posicion sobre las listas
def lista_buscar_padre(patrocinador, nivel_lista):
    log_registrar('log.txt', 'Buscando en las listas del patrocinador ' + str(patrocinador))
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}
    if patrocinador is not None:
        listas_padre_a = Lista.objects\
                              .filter(juego__jugador=patrocinador)\
                              .filter(estado='A', nivel=nivel_lista)\
                              .order_by('created')
        # listas_padre_a = 
        if listas_padre_a.exists():
            for lista in listas_padre_a:
                log_registrar('log.txt', 'Buscando en la lista: ' + str(lista))
                posicion = posicion_nuevo_jugador(patrocinador, lista)
                if posicion != -1:
                    ubicacion['lista'] = lista
                    ubicacion['posicion'] = posicion
                    ubicacion['patrocinador'] = patrocinador
                    log_registrar('log.txt', 'Posicion ' + str(posicion) +
                                  ' libre: en lista ' + str(lista))
                    break
                else:
                    log_registrar('log.txt', 'Sin posicion libre...')
    return ubicacion


def lista_nuevo_cobrador(lista):
    cobrador = Jugador.objects.get(juego__lista=lista, juego__posicion=0)
    nuevo_cobrador = Cobrador(jugador=cobrador, nivel=lista.nivel)
    nuevo_cobrador.save()


def lista_buscar_descendencia(patrocinador, nivel_lista):
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}

    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    if patrocinador is not None:
        log_registrar('log.txt', 'Buscando en descendencia de : ' + str(patrocinador))
        jugador_nivel_patrocinador = JugadorNivel.objects.get(jugador=patrocinador, nivel=nivel_lista)
        
        
        
        if jugador_nivel_patrocinador.patrocinador is not None:

            abuelo = jugador_nivel_patrocinador.jugador
            jugador_nivel_abuelo = JugadorNivel.objects.get(jugador=abuelo, nivel=nivel_lista)
            while abuelo is not None and nueva_ubicacion['posicion'] == -1:
                log_registrar('log.txt', 'Buscando en listas del descendiente : ' + str(abuelo))
                nueva_ubicacion = lista_buscar_padre(abuelo, nivel_lista)
                if nueva_ubicacion['posicion'] != -1:
                    ubicacion['posicion'] = nueva_ubicacion['posicion']
                    ubicacion['lista'] = nueva_ubicacion['lista']
                    ubicacion['patrocinador'] = nueva_ubicacion[
                        'patrocinador']
                    log_registrar('log.txt', 'Posicion ' + str(nueva_ubicacion['posicion'])+
                                  ' libre: en lista ' + str(nueva_ubicacion['lista']))
                else:
                    if jugador_nivel_abuelo.patrocinador is not None:
                        jugador_nivel_abuelo = JugadorNivel.objects.get(jugador=abuelo,
                                                                        nivel=nivel_lista)
                        patrocinador_abuelo = jugador_nivel_abuelo.patrocinador
                        if patrocinador_abuelo is not None:
                            abuelo = Jugador.objects.get(pk=patrocinador_abuelo.id)
                        else:
                            abuelo = None
    return ubicacion


def lista_buscar_mas_antigua(nivel_lista):
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}
    listas_abiertas = Lista.objects.filter(estado='A', nivel=nivel_lista)\
                                   .order_by('created')                                     
    for lista in listas_abiertas:
        log_registrar('log.txt', 'Buscando en lista ' + str(lista))
        # si la lista no tienen items es porque empezamos el juego
        if lista.items == 0:
            ubicacion['lista'] = lista
            ubicacion['posicion'] = 0
            ubicacion['patrocinador'] = None
            break
        else:
            patrocinador = Jugador.objects.filter(juego__lista=lista,
                                                  juego__posicion=0)
            nueva_posicion = posicion_nuevo_jugador(patrocinador[0], lista)
            ubicacion['lista'] = lista
            ubicacion['posicion'] = nueva_posicion

            if nueva_posicion != -1:
                log_registrar('log.txt', 'Posicion ' + str(nueva_posicion)+
                              ' libre: en lista ' + str(lista))
                break
    return ubicacion


def posicion_nuevo_jugador(padre, lista_validacion):
    if padre is not None:
        jugador_padre = padre
        posicion = -1
        casillas = [
            "vacia",
            "vacia",
            "vacia",
            "vacia",
            "vacia",
        ]
        juego_padre = Juego.objects.filter(jugador=jugador_padre). \
            filter(lista=lista_validacion)
        posicion_padre = juego_padre[0].posicion
        # obtengo todos los jugadores de la lista del padre
        juego_jugador = Juego.objects.filter(lista=lista_validacion)
        # lleno las casillas en las posiciones de los jugadores activos
        for juego in juego_jugador:
            casillas[juego.posicion] = "llena"
        cont = 0
        for casilla in casillas:
            if casilla == "vacia":
                posicion = cont
                break
            else:
                cont += 1
    else:
        posicion = -1

    return posicion


# ciclaje de las listas

def lista_ciclar(lista):
    ciclado = {'lista': None, 'posicion': -1, 'jugador_ciclado': None}

    # jugador cabeza de lista que se va a ciclar
    jugador0 = Jugador.objects.get(juego__lista=lista.id, juego__posicion=0)
    jugador_nivel0 = JugadorNivel.objects.get(jugador=jugador0, nivel=lista.nivel)
    log_registrar('log.txt', 'CICLANDO A: ' + str(jugador0) + ' EN LISTA: ' + str(lista))

    patrocinador = JugadorNivel.objects.get(jugador=jugador0, nivel=lista.nivel).patrocinador
    
    
    if patrocinador is None:
        abuelo = None
    else:
        abuelo = patrocinador

    log_registrar('log.txt', 'Buscando ubicacion en posicion del abuelo: ' + str(abuelo))

    nueva_ubicacion = buscar_ubicacion(abuelo, lista.nivel)
    if nueva_ubicacion['posicion'] == -1:
        log_registrar('log.txt', 'no existen posiciones para ciclar')
    else:
        nuevo_juego = Juego(lista=nueva_ubicacion['lista'],
                            jugador=jugador0,
                            posicion=nueva_ubicacion['posicion'])

        nuevo_juego.save()
        nuevo_juego.refresh_from_db()

        

 

        notificar_asignacion()
        log_registrar('log.txt', 'Jugador ' + str(jugador0) +
                      ' ciclado y agregado a lista ' + str(nueva_ubicacion['lista']) +
                      ' en la posicion: ' + str(nueva_ubicacion['posicion']))

        lista_inc_item(nueva_ubicacion['lista'])
        jugador_inc_ciclo(jugador_nivel0)
        jugador_inc_listas_cerradas(jugador0, lista.nivel)

        ciclado['lista'] = nueva_ubicacion['lista']
        ciclado['posicion'] = nueva_ubicacion['posicion']
        ciclado['jugador_ciclado'] = jugador0
        ciclado['juego'] = nuevo_juego

    return ciclado


def lista_nueva(lista):
    # Lista nueva PAR
    log_registrar('log.txt', 'LISTA NUEVA PAR')
    nueva_lista_par = Lista(items=2,
                            lista_padre=lista,
                            estado='B',
                            nivel=lista.nivel)
    nueva_lista_par.save()
    nueva_lista_par.refresh_from_db()
    # Traer las dos primeras posiciones
    jugador0 = Jugador.objects.filter(juego__lista=lista,
                                      juego__posicion=1)
    jugador1 = Jugador.objects.filter(juego__lista=lista,
                                      juego__posicion=3)

    nuevo_juego0 = Juego(lista=nueva_lista_par,
                         jugador=jugador0[0],
                         posicion=0)
    nuevo_juego1 = Juego(lista=nueva_lista_par,
                         jugador=jugador1[0],
                         posicion=1)

    nuevo_juego0.save()
    nuevo_juego0.refresh_from_db()
    nuevo_juego1.save()
    nuevo_juego1.refresh_from_db()

    log_registrar('log.txt', 'Jugador ' + str(jugador0[0]) +
                  ' agregado a lista ' + str(nueva_lista_par) + ' en posicion: 0')
    log_registrar('log.txt', 'Jugador ' + str(jugador1[0]) +
                  ' agregado a lista ' + str(nueva_lista_par) + ' en posicion: 1')
    lista_inc_ciclo(nueva_lista_par)
    lista_validar_bloqueo(nueva_lista_par)
    lista_validar_pc(nueva_lista_par)

    # Lista nueva IMPAR

    log_registrar('log.txt', 'LISTA NUEVA IMPAR')
    nueva_lista_impar = Lista(items=2,
                              lista_padre=lista,
                              estado='B',
                              nivel=lista.nivel)
    nueva_lista_impar.save()
    nueva_lista_impar.refresh_from_db()
    # Traer las dos primeras posiciones
    jugador0 = Jugador.objects.filter(juego__lista=lista,
                                      juego__posicion=2)
    jugador1 = Jugador.objects.filter(juego__lista=lista,
                                      juego__posicion=4)

    nuevo_juego0 = Juego(lista=nueva_lista_impar,
                         jugador=jugador0[0],
                         posicion=0)
    nuevo_juego1 = Juego(lista=nueva_lista_impar,
                         jugador=jugador1[0],
                         posicion=1)

    nuevo_juego0.save()
    nuevo_juego0.refresh_from_db()
    nuevo_juego1.save()
    nuevo_juego1.refresh_from_db()

    log_registrar('log.txt', 'Jugador ' + str(jugador0[0]) +
                  ' agregado a lista ' + str(nueva_lista_impar) + ' en posicion: 0' + 'Jugador ' + str(jugador1[0]) +
                  ' agregado a lista ' + str(nueva_lista_impar) + ' en posicion: 1')
    lista_inc_ciclo(nueva_lista_impar)
    lista_validar_bloqueo(nueva_lista_impar)
    lista_validar_pc(nueva_lista_impar)

def lista_llena(lista):
    resultado = False
    ele = Lista.objects.filter(items__gte=5, pk=lista.id)
    if ele:
        resultado = True
    return resultado


def lista_inc_item(lista):
    lista.items = F('items') + 1
    lista.save()
    lista.refresh_from_db()
    if lista.items >= 5:
        lista.estado = 'C'
        lista.save()
        lista.refresh_from_db()
        lista_guardar_cierre(lista)
        

def lista_guardar_cierre(lista):
    juegos_lista = Juego.objects.select_related('jugador').filter(lista=lista)
    for juego in juegos_lista:
        jugador_nivel = JugadorNivel.objects.get(jugador=juego.jugador, nivel=lista.nivel)
        juego.posicion_cerrado = juego.posicion
        juego.color_cerrado = jugador_nivel.color
        juego.save()
        juego.refresh_from_db()


def lista_inc_ciclo(lista):
    lista.ciclo = F('ciclo') + 1
    lista.save()
    lista.refresh_from_db()



def jugador_inc_listas_cerradas(jugador, nivel):
    jugador_nivel=JugadorNivel.objects.get(jugador=jugador, nivel=nivel)
    patrocinador = jugador_nivel.patrocinador
    if jugador_nivel.ciclo == 0:
        patrocinador.n_listas_cerradas = F('n_listas_cerradas') + 1
        patrocinador.save() 
    
    jugador_nivel.n_listas_cerradas = F('n_listas_cerradas') + 1
    jugador_nivel.save()

def jugador_inc_referidos(patrocinador, nivel_lista):
    jugador_nivel = JugadorNivel.objects.get(jugador=patrocinador, nivel=nivel_lista)
    if jugador_nivel is not None:
        jugador_nivel.n_referidos = F('n_referidos') + 1
        jugador_nivel.save()
        jugador_nivel.refresh_from_db()
        if jugador_nivel.n_referidos == 0:
            jugador_nivel.color = 'red'
        elif jugador_nivel.n_referidos == 1:
            jugador_nivel.color = '#d6d007'
        elif jugador_nivel.n_referidos >= 2:
            jugador_nivel.color = 'green'
        jugador_nivel.save()
        jugador_nivel.refresh_from_db()


def jugador_inc_activos_abuelo(patrocinador, nivel_lista):
    jugador_nivel_patrocinador = JugadorNivel.objects.get(jugador=patrocinador, nivel=nivel_lista)
    abuelo = jugador_nivel_patrocinador.patrocinador
    if abuelo  is not None:
        jugador_nivel_abuelo = JugadorNivel.objects.get(jugador=abuelo, nivel=nivel_lista)
        
        if jugador_nivel_patrocinador.n_referidos == 2:
            jugador_nivel_abuelo.n_referidos_activados = F('n_referidos_activados') + 1
            jugador_nivel_abuelo.save()
            jugador_nivel_abuelo.refresh_from_db()
            if jugador_nivel_abuelo.n_referidos_activados % 2 == 0 and \
                jugador_nivel_abuelo.n_referidos_activados != 0:
                nuevo_clon = Clon(jugador=abuelo,
                                estado='P',
                                nivel=nivel_lista)  
                nuevo_clon.save()
                nuevo_clon.refresh_from_db()


@transaction.atomic
def jugador_inc_cobros(jugador, nivel_lista):
    tope_cobros_nivel = Configuracion.objects.get(pk=1).tope_cobros_nivel
    tope_cobros_clon = Configuracion.objects.get(pk=1).tope_cobros_clon

    jugador_nivel = JugadorNivel.objects.get(jugador=jugador, nivel=nivel_lista)
    jugador_nivel.cobros = F('cobros') + 1
    jugador_nivel.save()
    jugador_nivel.refresh_from_db()


    if not niveles_full(jugador):
        if jugador_nivel.cobros == tope_cobros_nivel:
            jugador_nivel.bloqueo_x_cobros_nivel = True
            jugador_nivel.color = 'orange'
            jugador_nivel.save()
            jugador_nivel.refresh_from_db()

    if jugador_nivel.cobros == tope_cobros_clon:
        if not jugador.usuario.is_staff:
            jugador_nivel.bloqueo_y_cobros_clon = True
            jugador_nivel.color = 'blue'
            jugador_nivel.save()
            jugador_nivel.refresh_from_db() 
        # Generamos el nuevo clon especial
        nuevo_clon_especial = Clon(jugador=jugador, estado='P', tipo='C', nivel=nivel_lista)
        nuevo_clon_especial.save()


def jugador_inc_ciclo(jugador_nivel):
    jugador_nivel.ciclo = F('ciclo') + 1
    jugador_nivel.save()
    jugador_nivel.refresh_from_db()
    

def jugador_inc_cierre_lista(jugador):
    jugador.cierre_lista = F('cierre_lista') + 1
    jugador.save()
    jugador.refresh_from_db()


@transaction.atomic
def niveles_full(jugador):
    niveles_jugador = JugadorNivel.objects.filter(jugador=jugador)
    n_full = True
    for nivel_jugador in niveles_jugador:
        if nivel_jugador.estado == 'P':
            n_full = False
    return n_full

# Inicio del bloque de funciones validaciones pc y bloqueo

def lista_desbloquear(lista):
    if lista_llena(lista):
        lista.estado = 'C'
    else:
        lista.estado = 'A'
    lista.save()
    lista.refresh_from_db()


# Validamos la lista para desbloquearla
def lista_validar_bloqueo(lista):
    juegos = Juego.objects.select_related('lista', 'jugador')\
                          .filter(lista=lista)
    
    juego0 = Juego.objects.get(lista=lista, posicion=0)
    juego1 = Juego.objects.get(lista=lista, posicion=1)
    
    jugador_nivel_0 = JugadorNivel.objects.get(jugador=juego0.jugador, nivel=lista.nivel)
    jugador_nivel_1 = JugadorNivel.objects.get(jugador=juego1.jugador, nivel=lista.nivel)

    color0 = jugador_nivel_0.color
    color1 = jugador_nivel_1.color
    
    if color0 != 'blue' and color0 != 'orange': #Si no tiene bloqueo por cobros
        if color0 == 'green' or\
            color1 == 'green':
            lista_desbloquear(lista)

# Validamos todas las listas del patrocinador bloqueadas para activarlas
def jugador_validar_bloqueos(patrocinador, nivel_lista):
    if patrocinador is not None:
        listas_patrocinador = Lista.objects \
                                   .filter(jugador=patrocinador)\
                                   .filter(estado='B', nivel=nivel_lista)\
                                   .exclude(estado='C')

        for lista in listas_patrocinador:
            juegos = Juego.objects.select_related('jugador', 'lista') \
                                  .filter(lista=lista)
            jugador_nivel_0 = JugadorNivel.objects.get(jugador=juegos[0].jugador, nivel=lista.nivel)
            jugador_nivel_1 = JugadorNivel.objects.get(jugador=juegos[1].jugador, nivel=lista.nivel)

            if jugador_nivel_0.color != 'blue' and jugador_nivel_0.color != 'orange': #Si no tiene bloqueo por cobros
                if jugador_nivel_0.color == 'green' or \
                    jugador_nivel_1.color == 'green':
                    lista_desbloquear(lista)


# Buscamos todas las listas del patrocinador para generar el premio castigo
def jugador_validar_pcs(patrocinador, nivel_lista):
    if patrocinador is not None:
        listas_patrocinador = Lista.objects \
                                   .filter(jugador=patrocinador)\
                                   .exclude(estado='C')\
                                   .filter(pc=False, nivel=nivel_lista)

        for lista in listas_patrocinador:
            
            juegos = Juego.objects.select_related('jugador', 'lista')\
                                  .filter(lista=lista)
            
            # filtramos los juegos de la lista posiciones 0 y 1
            juego_posicion_0 = juegos.filter(posicion=0)
            juego_posicion_1 = juegos.filter(posicion=1)
            
            # Traigo los datos de jugadorNivel para verificar el color
            jugador_nivel_0 = JugadorNivel.objects.get(jugador=juego_posicion_0[0].jugador, nivel=lista.nivel)
            jugador_nivel_1 = JugadorNivel.objects.get(jugador=juego_posicion_1[0].jugador, nivel=lista.nivel)
            
            # traigo los objetos que se van a modificar
            objPosicion0 = Juego.objects.get(pk=juego_posicion_0[0].id)
            objPosicion1 = Juego.objects.get(pk=juego_posicion_1[0].id)

            if jugador_nivel_0.color == 'red' or jugador_nivel_0.color == '#d6d007':
                # recorremos la lista para buscar algun verde que suba de posicion
                # en caso de que la cabeza no este en verde
                if jugador_nivel_1.color == 'green':
                    objPosicion1.posicion = 0
                    objPosicion1.save()
                    objPosicion1.refresh_from_db()

                    objPosicion0.posicion = 1
                    objPosicion0.save()
                    objPosicion0.refresh_from_db()

                    lista.pc = True
                    lista.save()
                    lista.refresh_from_db()
                    log_registrar('log.txt', 'jugador ' +
                                    str(objPosicion1.jugador.usuario) +
                                    ' en posicion 2 se activa en verde ')

#  Validamos lista para generar el premio castigo
def lista_validar_pc(lista):
    
    #juegos de la lista (jugador-lista)
    juegos = Juego.objects.filter(lista=lista)\
                          .exclude(lista__estado='C')\
                          .filter(lista__pc=False)
                          
    if juegos.exists():
        # Posiciones 0 y 1
        juego_0 = juegos.filter(posicion=0)
        juego_1 = juegos.filter(posicion=1)

        jugador_nivel_0 = JugadorNivel.objects.get(jugador=juego_0[0].jugador,
                                                   nivel=lista.nivel)
        jugador_nivel_1 = JugadorNivel.objects.get(jugador=juego_1[0].jugador,
                                                   nivel=lista.nivel)
        
        posicion0 = juego_0[0]
        posicion1 = juego_1[0]

        if jugador_nivel_0.color == 'red' or jugador_nivel_0.color == '#d6d007':
            # recorremos la lista para buscar algun verde que suba de posicion
            # en caso de que la cabeza no este en verde
            if jugador_nivel_1.color == 'green':
                posicion1.posicion = 0
                posicion1.save()
                posicion1.refresh_from_db()

                posicion0.posicion = 1
                posicion0.save()
                posicion0.refresh_from_db()

                lista.pc = True
                lista.save()
                lista.refresh_from_db()
                log_registrar('log.txt', 'Premio castigo en lista ' +
                            str(lista))
            


# Fin del bloque de funciones validaciones pc y bloqueo

def log_registrar(nombre_archivo, texto):
    archivo = open(str(nombre_archivo), "a")
    archivo.write('' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+ ' ' + texto + '\n')
    archivo.close()

def notificar_asignacion():
    layer = get_channel_layer()
    async_to_sync(layer.group_send)('handler_notifications', {
        'type': 'notification.message',
        'message': 'Nuevo jugador en lista'
    })



# Funciones de visualizacion para ajax
# A partir de aquí se definen las funciones que llamará ajax para
# actualizar la página

@requires_csrf_token
def consulta_usuario(request, n_usuario=None):
    nombre_usuario = User.objects.filter(username=n_usuario)
    if nombre_usuario.exists():
        resp = "True"
    else:
        resp = "False"
    json_response = json.dumps(resp)
    return HttpResponse(json_response)

@requires_csrf_token
def consulta_saldos_usuario(request):
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    cuenta = Cuenta.objects.get(jugador=jugador)
    saldos = {'saldo_activacion': str(cuenta.saldo_activacion),
              'saldo_disponible': str(cuenta.saldo_disponible),
              'saldo_total': str(cuenta.saldo_total),
    }
    json_response = json.dumps(saldos)
    return HttpResponse(json_response)


@login_required
@requires_csrf_token
def lista_content(request, id_lista=None, n_usuario=None):

    dict_list = [{'user': '', 'color': 'white', 'cadena_ciclaje':'', 'patrocinador':'',
                  'n_referidos':'', 'n_referidos_activados':''},
                 {'user': '', 'color': 'white', 'cadena_ciclaje':'', 'patrocinador':'',
                  'n_referidos':'', 'n_referidos_activados':''},
                 {'user': '', 'color': 'white', 'cadena_ciclaje':'', 'patrocinador':'',
                  'n_referidos':'', 'n_referidos_activados':''},
                 {'user': '', 'color': 'white', 'cadena_ciclaje':'', 'patrocinador':'',
                  'n_referidos':'', 'n_referidos_activados':''},
                 {'user': '', 'color': 'white', 'cadena_ciclaje':'', 'patrocinador':'',
                  'n_referidos':'', 'n_referidos_activados':''},
                 {'lista_id': '', 'estado': '', 'nivel': ''}]

    juegos_en_lista = Juego.objects.select_related('jugador', 'lista')\
                                   .filter(lista=id_lista)

    mi_lista = Lista.objects \
        .select_related('nivel').get(pk=id_lista)
    estado_lista = mi_lista.get_estado_display()
    nivel = mi_lista.nivel.id


# Validamos si el usuario pertenece a la lista que esta solicitando
# solo en este caso se devuelve el contenido de la lista

    validado = False
    if request.user.is_staff:
        # conformamos un dicionario con los datos de la lista

        if estado_lista == 'CERRADA':
            for juego in juegos_en_lista:
                dict_list[juego.posicion_cerrado]['user'] = \
                    juego.jugador.usuario.username
                dict_list[juego.posicion_cerrado]['color'] = \
                    juego.color_cerrado
                dict_list[juego.posicion]['cadena_ciclaje'] = \
                    juego.cadena_ciclaje

                jugador_nivel = JugadorNivel(jugador=juego.jugador, nivel=mi_lista.nivel)
                if jugador_nivel.patrocinador is not None:
                    dict_list[juego.posicion]['patrocinador'] = \
                        jugador_nivel.patrocinador.usuario.username
        # Lista abierta
        else:
            for juego in juegos_en_lista:
                jugador_nivel = JugadorNivel.objects.get(jugador=juego.jugador, nivel=mi_lista.nivel)
                dict_list[juego.posicion]['user'] = \
                    juego.jugador.usuario.username
                dict_list[juego.posicion]['color'] = \
                    jugador_nivel.color
                dict_list[juego.posicion]['cadena_ciclaje'] = \
                    juego.cadena_ciclaje
                if jugador_nivel.patrocinador is not None:
                    dict_list[juego.posicion]['patrocinador'] = \
                        jugador_nivel.patrocinador.usuario.username 


        # posicion 5 para el encabezado de la lista
        dict_list[5]['lista_id'] = mi_lista.id
        dict_list[5]['estado'] = estado_lista
        dict_list[5]['nivel'] = str(nivel)

    else:
        if n_usuario == request.user.username:
            lst = Lista.objects.get(pk=id_lista)
            
            # patrocinador logueado
            pat = JugadorNivel.objects.get(jugador__usuario__username=request.user.username, nivel=lst.nivel).jugador
            # si el usuario logeado esta en la lista solicitada validamos
            lst_id = lst.id
            if Lista.objects.filter(jugador=pat, pk=lst_id).exists():
                validado = True
        else:
            # solicita datos de un referido del usuario logueado
            lst = Lista.objects.get(pk=id_lista)
            jug = Jugador.objects.get(usuario__username=n_usuario)
            niv = lst.nivel
            jugador_nivel = JugadorNivel.objects.get(jugador=jug, nivel=niv)
            pat = jugador_nivel.patrocinador
            if pat.usuario.username == request.user.username:
                validado = True
      
        # conformamos un dicionario con los datos de la lista
        if validado:
            if estado_lista == 'CERRADA':
                for juego in juegos_en_lista:
                    jugador_nivel = JugadorNivel.objects.get(jugador=juego.jugador, nivel=mi_lista.nivel)
                    dict_list[juego.posicion_cerrado]['user'] = \
                        juego.jugador.usuario.username
                    dict_list[juego.posicion_cerrado]['color'] = \
                        juego.color_cerrado
                    dict_list[juego.posicion]['cadena_ciclaje'] = \
                        juego.cadena_ciclaje
                    if jugador_nivel.patrocinador is not None:
                        dict_list[juego.posicion]['patrocinador'] = \
                        jugador_nivel.patrocinador.usuario.username
            else:
                for juego in juegos_en_lista:
                    jugador_nivel = JugadorNivel.objects.get(jugador=juego.jugador, nivel=mi_lista.nivel)
                    dict_list[juego.posicion]['user'] = \
                    juego.jugador.usuario.username
                    dict_list[juego.posicion]['color'] = \
                    jugador_nivel.color
                    dict_list[juego.posicion]['cadena_ciclaje'] = \
                    juego.cadena_ciclaje
                    if jugador_nivel.patrocinador is not None:
                        dict_list[juego.posicion]['patrocinador'] = \
                            jugador_nivel.patrocinador.usuario.username


        # posicion 5 para el encabezado de la lista
        dict_list[5]['lista_id'] = mi_lista.id
        dict_list[5]['estado'] = estado_lista
        dict_list[5]['nivel'] = str(nivel)

    json_response = json.dumps(dict_list)
    return HttpResponse(json_response)


@requires_csrf_token
def listas(request, usr=None):
    filtro_estado = request.POST.get('estado')
    filtro_nivel = request.POST.get('nivel')
    nivel_referido = request.POST.get('nivel_referido')


    if usr is None:
        usuario = User.objects.get(username=request.user.username)
    else:
        usuario = User.objects.get(username=usr)
        nivel_ref = Nivel.objects.get(pk=nivel_referido)

    if usuario.is_staff:
        lista_listas = Lista.objects.all()\
            .order_by('nivel', 'id')\
            .distinct()
                    
        # aplicamos los filtros
        if filtro_estado != 'Todos':
            lista_listas = lista_listas.filter(estado=filtro_estado)
        
        if filtro_nivel != 'Todos':
            lista_listas = lista_listas.filter(nivel=int(filtro_nivel))
        
        
        lst_listas = []
        for lista in lista_listas:
            ele = {"id": lista.id, "nivel": str(lista.nivel), "nivel_id": str(lista.nivel.id), "estado":str(lista.get_estado_display()), "usuario":str(usuario.username)}
            lst_listas.append(ele)

    else:
        lista_listas = Lista.objects\
            .filter(jugador__usuario__username=usuario.username)\
            .order_by('nivel', 'id')\
            .distinct()
                    
        # aplicamos los filtros
        if filtro_estado != 'Todos':
            lista_listas = lista_listas.filter(estado=filtro_estado)
        
        if filtro_nivel != 'Todos':
            print(filtro_nivel)
            lista_listas = lista_listas.filter(nivel=int(filtro_nivel)) 
        
        
        lst_listas = []
        for lista in lista_listas:
            ele = {"id": lista.id, "nivel": str(lista.nivel), "nivel_id": str(lista.nivel.id), "estado":str(lista.get_estado_display()), "usuario":str(usuario.username)}
            lst_listas.append(ele)

    json_response = json.dumps(lst_listas)
    return HttpResponse(json_response)

@requires_csrf_token
def listasReferido(request):
    filtro_estado = request.POST.get('estado')
    filtro_nivel = request.POST.get('nivel')
    usr = request.POST.get('referido')
    usuario = User.objects.get(username=usr)

    if usuario.is_staff:
        lista_listas = Lista.objects.all()\
        .order_by('nivel', 'id')\
        .distinct()
        lst_listas = []
        
        # aplicamos los filtros
        if filtro_estado != 'Todos':
            lista_listas = lista_listas.filter(estado=filtro_estado)
        
        if filtro_nivel != 'Todos':
            lista_listas = lista_listas.filter(nivel=filtro_nivel)

        
        lst_listas = []
        for lista in lista_listas:
            ele = {
                "id": lista.id,
                "nivel": str(lista.nivel), 
                "nivel_id":lista.nivel.id, 
                "estado":str(lista.get_estado_display()), 
                "usuario":str(usuario.username)
            }
            lst_listas.append(ele)
    else:
        lista_listas = Lista.objects\
            .filter(jugador__usuario__username=usuario.username)\
            .order_by('nivel', 'id')\
            .distinct()
                    
        # aplicamos los filtros
        if filtro_estado != 'Todos':
            lista_listas = lista_listas.filter(estado=filtro_estado)

        if filtro_nivel != 'Todos':
            lista_listas = lista_listas.filter(nivel=filtro_nivel)
        
        lst_listas = []
        for lista in lista_listas:
            ele = {"id": lista.id, "nivel": str(lista.nivel), "nivel_id":lista.nivel.id, "estado":str(lista.get_estado_display()), "usuario":str(usuario.username)}
            lst_listas.append(ele)

    json_response = json.dumps(lst_listas)
    return HttpResponse(json_response)

@requires_csrf_token
def listaReferidos(request, n_usuario=None):
    filtro_nivel = request.POST.get('nivel')
    filtro_estado = request.POST.get('estado')
    usr = None
    if n_usuario is None:
        usr = User.objects.get(username=request.user.username)
    else:
        usr = User.objects.get(username=n_usuario)

    
    lista_referidos = JugadorNivel.objects.filter(patrocinador__usuario__username=usr.username)\
                                    .filter(estado='A')
                                    
    if filtro_nivel != 'Todos':
        lista_referidos = lista_referidos.filter(nivel=int(filtro_nivel))

    if filtro_estado != 'Todos':
        lista_referidos = lista_referidos.filter(estado=filtro_estado)
    
    lista_referidos = lista_referidos.order_by('jugador__usuario__username', 'nivel').distinct()



    lst_referidos = []
    for referido in lista_referidos:

        ele = {"id": referido.id,
                "nivel": str(referido.nivel),
                "estado":str(referido.get_estado_display()),
                "usuario":str(referido.jugador.usuario.username),
                "color":str(referido.color),
                "n_referidos":str(referido.n_referidos),
                "n_referidos_activados":str(referido.n_referidos_activados)
                }

        lst_referidos.append(ele)

    response = json.dumps(lst_referidos)
    
    return JsonResponse(response, safe=False)


@requires_csrf_token
def listaNiveles(request):
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    niveles_jugador = JugadorNivel.objects.filter(jugador=jugador)
    json_response = json.dumps(niveles_jugador)

    return HttpResponse(json_response)    


@requires_csrf_token
def cobrando(request):
    lista_cobrando = Cobrador.objects.all()[:10]
    lst_cobrando = []
    for cobrador in lista_cobrando:
        ele = {"usuario": cobrador.jugador.usuario.username,
               "nivel": cobrador.nivel.id}
        lst_cobrando.append(ele)

    json_response = json.dumps(lst_cobrando)
    return HttpResponse(json_response)


@requires_csrf_token
def referidos_inactivos(request):
    patrocinador = Jugador.objects.get(usuario__username=request.user.username)
    lista_referidos_p = Jugador.objects.filter(promotor=patrocinador,
                                               estado='R')
    lst_referidos_p = []
    for referido_p in lista_referidos_p:
        ele = {"usuario": referido_p.usuario.username}
        lst_referidos_p.append(ele)

    json_response = json.dumps(lst_referidos_p)
    return HttpResponse(json_response)

@requires_csrf_token
def clones(request):
    lista_clones = Clon.objects.filter(
        jugador__usuario__username=request.user.username)
    lst_clones = []
    for clon in lista_clones:
        ele = {"id": clon.id,
               "jugador": str(clon.jugador),
               "estado": clon.get_estado_display(),
               "tipo": clon.get_tipo_display(),
               "nivel": str(clon.nivel),
               }

        lst_clones.append(ele)

    json_response = json.dumps(lst_clones)
    return HttpResponse(json_response)


@requires_csrf_token
def activar_clon(request, clon_id=None, nivel_lista=None):
    if clon_id is not None:
        clon = Clon.objects.get(pk=clon_id)
        if clon.estado == 'P':
            clon.estado = 'A'
            clon.save()
            clon.refresh_from_db()
            asignar_clon(clon, clon.nivel)
            if clon.tipo == 'C':
                jugador_nivel = JugadorNivel.objects.get(jugador=clon.jugador, nivel=nivel_lista)
                if jugador_nivel.color == 'blue' and bloqueo_y_cobros_clon == True:
                    jugador_nivel.color = 'green'
                    jugador_nivel.bloqueo_y_cobros_clon = False
                    jugador_nivel.save()

    return redirect(reverse('core:mis_clones'))

@transaction.atomic
@requires_csrf_token
def activar_nivel(request, jugador_nivel_id):
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    cuenta = Cuenta.objects.get(jugador=jugador)
    niveles = ""
    
    nivel_a_activar = JugadorNivel.objects.get(pk=jugador_nivel_id)
    if nivel_a_activar.estado == 'P':
        # si el saldo de activacion me alcanza o si sumando el saldo disponible me alcanza
        if cuenta.saldo_activacion >= nivel_a_activar.nivel.monto or cuenta.saldo_activacion\
            + cuenta.saldo_disponible >= nivel_a_activar.nivel.monto:

            nivel_a_activar.estado = 'A'
            nivel_a_activar.save()
            nivel_a_activar.refresh_from_db()

            jugador.estado = 'A'
            jugador.save()
            jugador.refresh_from_db()
            
            # genero descuentos temporal en la cuenta
            if cuenta.saldo_activacion > nivel_a_activar.nivel.monto:
                cuenta.saldo_disponible = F('saldo_disponible') - nivel_a_activar.nivel.monto
                cuenta.saldo_total = F('saldo_total') - nivel_a_activar.nivel.monto
                cuenta.save()
                
                desc_movimiento = 'Pago activacion nivel ' + str(nivel_a_activar.nivel.id)
                nuevo_movimiento = Movimiento(cuenta=cuenta,
                                            billetera='D',
                                            tipo='S',
                                            concepto='PN', 
                                            descripcion=desc_movimiento,
                                            valor=nivel_a_activar.nivel.monto)
                nuevo_movimiento.save()
                
            # si no me alcanza el saldo de activacion pero tengo saldo disponible para debitar
            elif cuenta.saldo_activacion < nivel_a_activar.nivel.monto and \
                    nivel_a_activar.nivel.monto <= (cuenta.saldo_activacion + cuenta.saldo_disponible):
                restante = nivel_a_activar.nivel.monto - cuenta.saldo_activacion
                descuento_activacion = cuenta.saldo_activacion
                descuento_disponible = restante
                cuenta.saldo_activacion = 0
                cuenta.saldo_disponible = F('saldo_disponible') - restante
                cuenta.saldo_total = F('saldo_total') - nivel_a_activar.nivel.monto
                cuenta.save()
                
                if descuento_activacion > 0:
                    desc_movimiento = 'Descuento saldo activacion para activar nivel ' + str(nivel_a_activar.nivel.id)
                    nuevo_movimiento = Movimiento(cuenta=cuenta,
                                                billetera='A',
                                                tipo='S',
                                                concepto='PN',  
                                                descripcion=desc_movimiento,
                                                valor=descuento_activacion)
                    nuevo_movimiento.save()
                    nuevo_movimiento.refresh_from_db()

                
                desc_movimiento = 'Descuento saldo disponible para activar nivel ' + str(nivel_a_activar.nivel.id)
                nuevo_movimiento = Movimiento(cuenta=cuenta,
                                                billetera='D',
                                                tipo='S',
                                                concepto='PN',  
                                                descripcion=desc_movimiento,
                                                valor=descuento_disponible)
                nuevo_movimiento.save()
                nuevo_movimiento.refresh_from_db()
            
            # Reparto las comisiones de cada generación
            jugador_repartir_pago_comisiones(jugador, nivel_a_activar)

            # Desbloqueo jugador si activa el siguiente nivel
            if nivel_a_activar.nivel.id > 1:
                nivel_id_anterior = nivel_a_activar.nivel.id-1
                nivel_anterior = Nivel.objects.get(pk=nivel_id_anterior)
                jugador_nivel_anterior = JugadorNivel.objects.get(jugador=jugador, nivel=nivel_anterior)
                if jugador_nivel_anterior.bloqueo_x_cobros_nivel == True and jugador_nivel_anterior.color == 'orange':
                    jugador_nivel_anterior.bloqueo_x_cobros_nivel = False
                    jugador_nivel_anterior.color = 'green'
                    jugador_nivel_anterior.save()
            patrocinador, lista, posicion = asignar_jugador(jugador, nivel_a_activar.nivel.id)
            respuesta = 'Nivel ' + str(nivel_a_activar.nivel.id) + ' activado correctamente, estás en la lista ' + str(lista) + ' y posición ' + str(posicion + 1)
        else:
            respuesta = 'No tienes saldo suficiente para activar el nivel ' + str(nivel_a_activar.nivel.id)
    
    niveles = list(JugadorNivel.objects.filter(jugador=jugador))
    return render(request, 'core/mis_niveles.html', {
                           'niveles_jugador': niveles,
                           'respuesta':respuesta,
                           'base_url': request.build_absolute_uri('/')[:-1].strip("/")})


@requires_csrf_token
def cargar_saldo(request, monto):
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    cuenta = Cuenta.objects.get(jugador=jugador)
    nuevo_movimiento = Movimiento(cuenta=cuenta,
                                  billetera='D',
                                  tipo='E',
                                  concepto='CS',
                                  descripcion='Carga de saldo desde billetera Criptomoneda',
                                  valor=monto)
    nuevo_movimiento.save()
    cuenta.saldo_disponible = F('saldo_disponible') + monto
    cuenta.saldo_total = F('saldo_total') + monto
    cuenta.save()
    return redirect(reverse('core:mis_finanzas'))

@requires_csrf_token
def jugador_ver_movimientos(request):
    filtro_billetera = request.POST.get('billetera')
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    cuenta = Cuenta.objects.get(jugador=jugador)
    
    if filtro_billetera != 'T':
        movimientos = Movimiento.objects.filter(cuenta=cuenta, billetera=filtro_billetera)
    else:
        movimientos = Movimiento.objects.filter(cuenta=cuenta)

    lst_movimientos = []
    for movimiento in movimientos:
        ele = {"codigo":str(movimiento.id),
               "fecha": str(movimiento.created.strftime("%Y-%m-%d")),
               "tipo": movimiento.get_tipo_display(), 
               "billetera": movimiento.get_billetera_display(),
               "concepto": movimiento.get_concepto_display(),
               "descripcion": movimiento.descripcion,
               "valor": str(movimiento.valor),  
               }

        lst_movimientos.append(ele)

    json_response = json.dumps(lst_movimientos)
    return HttpResponse(json_response)

@requires_csrf_token
def lista_canastas(request):    
    jugador = Jugador.objects.get(usuario__username=request.user.username)
    jugador_niveles =JugadorNivel.objects.filter(jugador=jugador)
    
    lst_jugador_niveles = []
    for jugador_nivel in jugador_niveles:
        m = str('{:.0f}'.format(jugador_nivel.nivel.monto))
        ele = {"id": str(jugador_nivel.nivel.id),
               "jugador_nivel_id": str(jugador_nivel.id),
               "estado": jugador_nivel.get_estado_display(),
               "monto": m,
               "ciclajes": str(jugador_nivel.n_listas_cerradas),
               "referidos": str(jugador_nivel.n_referidos),
               }

        lst_jugador_niveles.append(ele)

    json_response = json.dumps(lst_jugador_niveles)
    return HttpResponse(json_response)

# Peticiones tipo WebService

@requires_csrf_token
def ws_list_box(request):
    usuario = User.objects.get(username=request.user.username)
        
    lista_listas = Lista.objects\
        .filter(jugador__usuario__username=usuario.username)\
        .order_by('nivel', 'id')\
        .distinct()
   
    lst_listas = []
    for lista in lista_listas:
        ele = {"id": lista.id, 
                "nivel": str(lista.nivel), 
                "nivel_id": str(lista.nivel.id), 
                "estado":str(lista.get_estado_display()), 
                "usuario":str(usuario.username)}
        lst_listas.append(ele)

    json_response = json.dumps(lst_listas)
    return HttpResponse(json_response)
