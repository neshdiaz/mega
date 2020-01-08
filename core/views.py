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
from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Lista, Jugador, Juego, Clon

def index(request):
    return render(request, 'core/index.html')


@login_required
@requires_csrf_token
def home(request, id_usuario=None, id_lista=None):
    hora_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render(request, 'core/home.html', {
        'hora_local': hora_local,
        'base_url': request.build_absolute_uri('/')[:-1].strip("/")})


@receiver(post_save, sender=Jugador)
def activar_jugador(instance, created, **kwargs):
    if created:
        asignar_jugador(instance)


@transaction.atomic
def asignar_jugador(nuevo_jugador):
    log_registrar('log.txt', 'NUEVO JUGADOR Patrocinador ' +
                  str(nuevo_jugador.patrocinador) + ' Jugador: ' +
                  str(nuevo_jugador))

    # buscar lista y posición valida del patrocinador
    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    nueva_ubicacion = buscar_ubicacion(nuevo_jugador.patrocinador)

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

        jugador_inc_referidos(nuevo_jugador.patrocinador)
        jugador_validar_bloqueos(nuevo_jugador.patrocinador)
        jugador_validar_pcs(nuevo_jugador.patrocinador)
        jugador_inc_activos_abuelo(nuevo_jugador.patrocinador, nueva_ubicacion['lista'].nivel)
 
        respuesta = 'Jugador asignado correctamente'
        notificar_asignacion()

        # Creacion de lista nueva
        if nueva_ubicacion['posicion'] == 4:
            lista_nueva(nueva_ubicacion['lista'])

        # bloque de ciclaje de jugadores
        elif nueva_ubicacion['posicion'] == 3:
            #ciclo la lista en la nueva ubicacion
            usuario_que_paga = str(nuevo_jugador)
            # ciclo la lista donde se ubicó la posicion libre
            ret_ciclado = lista_ciclar(nueva_ubicacion['lista'])
            if ret_ciclado['posicion'] == 4:
                lista_nueva(ret_ciclado['lista'])
            #bloque de multiples asignaciones en posición de ciclaje
            while ret_ciclado['posicion'] == 3:
                ret_ciclado = lista_ciclar(ret_ciclado['lista'])
                usuario_que_paga += ret_ciclado['jugador_ciclado']
                if ret_ciclado['posicion'] == 4:
                    lista_nueva(ret_ciclado['lista'])
    else:
        respuesta = 'No se encontraron posiciones disponibles'
        log_registrar('log.txt', 'No se encontraron posiciones disponibles')
        # Encolar al jugador...
    return respuesta


@transaction.atomic
def asignar_clon(clon):
    log_registrar('log.txt', 'asgnando clon de ' + str(clon.jugador))
    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    nueva_ubicacion = lista_buscar_mas_antigua()

    if nueva_ubicacion['posicion'] != -1:
        # Creamos el juego para enlazar la lista con el nuevo jugador
        juego = Juego(lista=nueva_ubicacion['lista'],
                      jugador=clon,
                      posicion=nueva_ubicacion['posicion'])
        juego.save()
        juego.refresh_from_db()
        log_registrar('log.txt', 'Jugador ' + str(clon) +
                      ' agregado a lista ' + str(nueva_ubicacion['lista']) +
                      ' en posicion: ' +
                      str(nueva_ubicacion['posicion']))

        # procesos post asignacion directa
        lista_inc_item(nueva_ubicacion['lista'])

        respuesta = 'Jugador asignado correctamente'
        notificar_asignacion()

        # Creacion de lista nueva
        if nueva_ubicacion['posicion'] == 4:
            lista_nueva(nueva_ubicacion['lista'])

        # bloque de ciclaje de jugadores
        elif nueva_ubicacion['posicion'] == 3:
            #ciclo la lista en la nueva ubicacion
            usuario_que_paga = str(clon)
            ret_ciclado = lista_ciclar(nueva_ubicacion['lista'])
            if ret_ciclado['posicion'] == 3:
                lista_nueva(ret_ciclado['lista'])
            #bloque de multiples asignaciones en posición de ciclaje
            while ret_ciclado['posicion'] == 3:
                ret_ciclado = lista_ciclar(ret_ciclado['lista'])
                usuario_que_paga += ret_ciclado['jugador_ciclado']
                if ret_ciclado['posicion'] == 4:
                    lista_nueva(ret_ciclado['lista'])
    else:
        pass
    return HttpResponse(reverse('core:home'))

def buscar_ubicacion(patrocinador):
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}

    # if patrocinador is not None:
    ubicacion = lista_buscar_padre(patrocinador)

    if ubicacion['posicion'] != -1:
        return ubicacion
    else:
        ubicacion = lista_buscar_descendencia(patrocinador)
        if ubicacion['posicion'] != -1:
            return ubicacion
        else:
            ubicacion = lista_buscar_mas_antigua()
            if ubicacion['posicion'] != -1:
                return ubicacion
            else:
                log_registrar('log.txt', 'no hay listas disponibles')
                return ubicacion

  
        




# Busquedas de posición sobre las listas
def lista_buscar_padre(patrocinador):
    log_registrar('log.txt', 'Busqueda por padre')
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}
    if patrocinador is not None:
        listas_padre_a = Lista.objects\
                              .filter(juego__jugador_id=patrocinador.id)\
                              .filter(estado='A')\
                              .order_by('created')
        if listas_padre_a.exists():
            for lista in listas_padre_a:
                posicion = posicion_nuevo_jugador(patrocinador, lista)
                if posicion != -1:
                    ubicacion['lista'] = lista
                    ubicacion['posicion'] = posicion
                    ubicacion['patrocinador'] = patrocinador
                    break
    return ubicacion


def lista_buscar_descendencia(patrocinador):
    log_registrar('log.txt', 'Busqueda por descendencia')
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}

    nueva_ubicacion = {'lista': None,
                       'posicion': -1,
                       'patrocinador': None}

    if patrocinador is not None:
        patrocinador = Jugador.objects.get(pk=patrocinador.id)
        if patrocinador.patrocinador is not None:
            abuelo = Jugador.objects.get(pk=patrocinador.patrocinador.id)
            while abuelo is not None and nueva_ubicacion['posicion'] == -1:
                nueva_ubicacion = lista_buscar_padre(abuelo)
                if nueva_ubicacion['posicion'] != -1:
                    ubicacion['posicion'] = nueva_ubicacion['posicion']
                    ubicacion['lista'] = nueva_ubicacion['lista']
                    ubicacion['patrocinador'] = nueva_ubicacion[
                        'patrocinador']
                else:
                    if abuelo.patrocinador is not None:
                        patrocinador_abuelo = abuelo.patrocinador
                        abuelo = Jugador.objects.get(pk=patrocinador_abuelo.id)
                    else:
                        abuelo = None
    return ubicacion


def lista_buscar_mas_antigua():
    log_registrar('log.txt', 'Busqueda lista más antigua')
    ubicacion = {'lista': None,
                 'posicion': -1,
                 'patrocinador': None}
    listas_abiertas = Lista.objects.filter(estado='A')\
                                   .order_by('created')
    for lista in listas_abiertas:
        # si la lista no tienen items es porque empezamos el juego
        if lista.items == 0:
            ubicacion['lista'] = lista
            ubicacion['posicion'] = 0
            ubicacion['patrocinador'] = None
            return ubicacion
        else:
            ubicacion['lista'] = lista
            ubicacion['posicion'] = 0
            ubicacion['patrocinador'] = None
            patrocinador = Jugador.objects.filter(juego__lista=lista,
                                                  juego__posicion=0)
            patrocinador = patrocinador[0]
            nueva_posicion = posicion_nuevo_jugador(patrocinador, lista)
            if nueva_posicion != -1:
                ubicacion['lista'] = lista
                ubicacion['posicion'] = nueva_posicion
                ubicacion['patrocinador'] = None
    return ubicacion



def posicion_nuevo_jugador(padre, lista_validacion):
    log_registrar('log.txt', 'Buscando posicion para el nuevo jugador')
    if padre is not None:
        jugador_padre = padre
        log_registrar('log.txt', 'Validando usuario padre: ' +
                      str(jugador_padre))
        log_registrar('log.txt', 'Validando lista: ' + str(lista_validacion))

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

    if posicion == -1:
        log_registrar('log.txt', 'No se encontró una posicion disponible en la\
                      lista ' + str(lista_validacion))
    else:
        log_registrar('log.txt', 'Se ubicó la posicion ' + str(posicion) +
                      ' libre en la lista ' + str(lista_validacion))
    return posicion


# ciclaje de las listas

def lista_ciclar(lista):
    log_registrar('log.txt', 'CICLAJE')
    ciclado = {'lista': None, 'posicion': -1, 'jugador_ciclado': None}

    # jugador cabeza de lista que se va a ciclar
    jugador0 = Jugador.objects.get(juego__lista=lista.id, juego__posicion=0)
    log_registrar('log.txt', 'Jugador a ciclar ' + str(jugador0))
    if jugador0.patrocinador is None:
        abuelo = None
    else:
        abuelo = jugador0.patrocinador
    log_registrar('log.txt', ' id patrocinador del patrocinador ' +
                  str(abuelo))
    nueva_ubicacion = buscar_ubicacion(abuelo)
    if nueva_ubicacion['posicion'] == -1:
        log_registrar('log.txt', 'no existen posiciones para ciclar')
    else:
        nuevo_juego = Juego(lista=nueva_ubicacion['lista'],
                            jugador=jugador0,
                            posicion=nueva_ubicacion['posicion'])

        nuevo_juego.save()
        nuevo_juego.refresh_from_db()
        notificar_asignacion()
        log_registrar('log.txt', 'Jugador ciclado ' + str(jugador0) +
                      ' agregado a lista ' + str(nueva_ubicacion['lista']) +
                      ' en posicion: ' + str(nueva_ubicacion['posicion']))

        lista_inc_item(nueva_ubicacion['lista'])
        jugador_inc_ciclo(jugador0)
        ciclado['lista'] = nueva_ubicacion['lista']
        ciclado['posicion'] = nueva_ubicacion['posicion']
        ciclado['jugador_ciclado'] = jugador0
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
                  ' agregado a lista ' + str(nueva_lista_impar) + ' en posicion: 0')
    log_registrar('log.txt', 'Jugador ' + str(jugador1[0]) +
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
    if lista.items >= lista.max_items:
        lista.estado = 'C'
        lista.save()
        lista.refresh_from_db()
        lista_guardar_cierre(lista)

def lista_guardar_cierre(lista):
    juegos_lista = Juego.objects.select_related('jugador').filter(lista=lista)
    for juego in juegos_lista:
        juego.posicion_cerrado = juego.posicion
        juego.color_cerrado = juego.jugador.color
        juego.save()
        juego.refresh_from_db()


def lista_inc_ciclo(lista):
    lista.ciclo = F('ciclo') + 1
    lista.save()
    lista.refresh_from_db()


def jugador_inc_referidos(patrocinador):
    if patrocinador is not None:
        patrocinador.n_referidos = F('n_referidos') + 1
        patrocinador.save()
        patrocinador.refresh_from_db()
        if patrocinador.n_referidos == 0:
            patrocinador.color = 'red'
        elif patrocinador.n_referidos == 1:
            patrocinador.color = '#d6d007'
        elif patrocinador.n_referidos >= 2:
            patrocinador.color = 'green'
        patrocinador.save()
        patrocinador.refresh_from_db()


def jugador_inc_activos_abuelo(patrocinador, nivel_lista):
    try:
        abuelo = patrocinador.patrocinador
        if patrocinador.n_referidos == 2:
            abuelo.n_referidos_activados = F('n_referidos_activados') + 1
            abuelo.save()
            abuelo.refresh_from_db()
            if abuelo.n_referidos_activados % 2 == 0 and \
                abuelo.n_referidos_activados != 0:
                nuevo_clon = Clon(jugador=abuelo,
                                  estado='P',
                                  nivel=nivel_lista)
                nuevo_clon.save()
                nuevo_clon.refresh_from_db()
    except AttributeError:
        print('Sin patrocinador, Posible creacion de usuario System')

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
    if juegos[0].jugador.color == 'green' or\
        juegos[1].jugador.color == 'green':
        lista_desbloquear(lista)


# Validamos todas las listas del patrocinador bloqueadas para activarlas
def jugador_validar_bloqueos(patrocinador):
    if patrocinador is not None:
        listas_patrocinador = Lista.objects \
                                   .filter(jugador=patrocinador)\
                                   .filter(estado='B')\
                                   .exclude(estado='C')

        for lista in listas_patrocinador:
            juegos = Juego.objects.select_related('jugador', 'lista') \
                                  .filter(lista=lista)
            if juegos[0].jugador.color == 'green' or \
                    juegos[1].jugador.color == 'green':
                lista_desbloquear(lista)


# Buscamos todas las listas del patrocinador para generar el premio castigo
def jugador_validar_pcs(patrocinador):
    if patrocinador is not None:
        listas_patrocinador = Lista.objects \
                                   .filter(jugador=patrocinador)\
                                   .exclude(estado='C')\
                                   .filter(pc=False)

        for lista in listas_patrocinador:
            juegos = Juego.objects.select_related('jugador', 'lista')\
                                  .filter(lista=lista)
            # validamos si hay 2 o más jugadores en el juego
            # de lo contrario estaríamos arrancando el juego
            if juegos.count() >= 2 and juegos[0].jugador.color != 'green':
                # recorremos la lista para buscar algun verde que suba de posicion
                # en caso de que la cabeza no este en verde
                if juegos[1].jugador.color == 'green':
                    obj_asc = Juego.objects.get(pk=juegos[1].id)
                    obj_desc = Juego.objects.get(pk=juegos[0].id)
                    obj_asc.posicion = 0
                    obj_asc.save()
                    obj_asc.refresh_from_db()
                    obj_desc.posicion = 1
                    obj_desc.save()
                    obj_desc.refresh_from_db()
                    lista.pc = True
                    lista.save()
                    lista.refresh_from_db()
                    log_registrar('log.txt', 'jugador ' +
                                  str(juegos[1].jugador.usuario) +
                                  ' en posicion 2 se activa en verde ')

#  Validamos lista para generar el premio castigo
def lista_validar_pc(lista):

    juegos = Juego.objects.select_related('lista', 'jugador')\
                          .filter(lista=lista)\
                          .exclude(lista__estado='C')\
                          .filter(lista__pc=False)

    if juegos.count() >= 2 and juegos[0].jugador.color != 'green':
        # recorremos la lista para buscar algun verde que suba de posicion
        # en caso de que la cabeza no este en verde
        if juegos[1].jugador.color == 'green':
            obj_asc = Juego.objects.get(pk=juegos[1].id)
            obj_desc = Juego.objects.get(pk=juegos[0].id)

            obj_asc.posicion = 0
            obj_asc.save()
            obj_asc.refresh_from_db()
            obj_desc.posicion = 1
            obj_desc.save()
            obj_desc.refresh_from_db()

            lista.pc = True
            lista.save()
            lista.refresh_from_db()
            log_registrar('log.txt', 'Premio castigo en lista ' +
                          str(lista))


# Fin del bloque de funciones validaciones pc y bloqueo

def jugador_inc_ciclo(jugador):
    jugador.ciclo = F('ciclo') + 1
    jugador.save()
    jugador.refresh_from_db()


def jugador_inc_cierre_lista(jugador):
    jugador.cierre_lista = F('cierre_lista') + 1
    jugador.save()
    jugador.refresh_from_db()


def log_registrar(nombre_archivo, texto):
    archivo = open(str(nombre_archivo), "a")
    archivo.write(str(timezone.now()) + ' ' + texto + '\n')
    archivo.close()


def notificar_asignacion():
    layer = get_channel_layer()
    async_to_sync(layer.group_send)('handler_notifications', {
        'type': 'notification.message',
        'message': 'Nuevo jugador en lista'
    })



# Funciones de visualización para ajax
# A partir de aquí se definen las funciones que llamará ajax para
# actualizar la página


@requires_csrf_token
def lista_content(request, id_lista=None):

    dict_list = [{'user': '', 'color': 'white'},
                 {'user': '', 'color': 'white'},
                 {'user': '', 'color': 'white'},
                 {'user': '', 'color': 'white'},
                 {'user': '', 'color': 'white'},
                 {'lista_id': '', 'estado': '', 'nivel': ''}]

    juegos_en_lista = Juego.objects.select_related('jugador', 'lista')\
                                   .filter(lista=id_lista)

    mi_lista = Lista.objects \
        .select_related('nivel').get(pk=id_lista)
    estado_lista = mi_lista.get_estado_display()
    nivel = mi_lista.nivel.monto


# Validamos si el usuario pertenece a la lista que esta solicitando
# solo en este caso se devuelve el contenido de la lista

    validado = False
    if request.user.is_staff:
        validado = True

    for juego in juegos_en_lista:
        if request.user.username == juego.jugador.usuario.username:
            validado = True
    # conformamos un dicionario con los datos de la lista
    if validado:
        if estado_lista == 'CERRADA':
            for juego in juegos_en_lista:
                dict_list[juego.posicion_cerrado]['user'] = \
                    juego.jugador.usuario.username
                dict_list[juego.posicion_cerrado]['color'] = \
                    juego.color_cerrado
        else:
            for juego in juegos_en_lista:
                dict_list[juego.posicion]['user'] = \
                    juego.jugador.usuario.username
                dict_list[juego.posicion]['color'] = \
                    juego.jugador.color

        # posicion 5 para el encabezado de la lista
        dict_list[5]['lista_id'] = mi_lista.id
        dict_list[5]['estado'] = estado_lista
        dict_list[5]['nivel'] = str(nivel)
    json_response = json.dumps(dict_list)
    return HttpResponse(json_response)


@requires_csrf_token
def listas(request):
    if request.user.is_staff:
        lista_listas = Lista.objects.all().distinct()
        lst_listas = []
        for lista in lista_listas:
            ele = {"id": lista.id}
            lst_listas.append(ele)

    else:
        lista_listas = Lista.objects\
            .filter(jugador__usuario__username=request.user.username)\
            .distinct()
        lst_listas = []
        for lista in lista_listas:
            ele = {"id": lista.id, "nivel": str(lista.nivel)}
            lst_listas.append(ele)

    json_response = json.dumps(lst_listas)
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
               "nivel": str(clon.nivel),
               }

        lst_clones.append(ele)

    json_response = json.dumps(lst_clones)
    return HttpResponse(json_response)


@requires_csrf_token
def activar_clon(request, clon_id=None):
    if clon_id is not None:
        clon = Clon.objects.get(pk=clon_id)
        if clon.estado == 'P':
            clon.estado = 'A'
            clon.save()
            clon.refresh_from_db()
            asignar_clon(clon)
    return redirect(reverse('core:home'))
