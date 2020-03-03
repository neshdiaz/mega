from django.contrib import admin
from .models import Lista, Jugador, Juego, Nivel, Clon, Cobrador, JugadorNivel, \
    Cuenta, Movimiento, Configuracion

admin.site.register(Lista)
admin.site.register(Jugador)
admin.site.register(Juego)
admin.site.register(Nivel)
admin.site.register(Clon)
admin.site.register(Cobrador)
admin.site.register(JugadorNivel)
admin.site.register(Cuenta)
admin.site.register(Movimiento)
admin.site.register(Configuracion)
