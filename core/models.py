from django.db import models
from django.contrib.auth.models import User


class Lista(models.Model):
    ESTADO_CHOICES = (
        ('A', 'ABIERTA'),
        ('C', 'CERRADA'),
        ('B', 'BLOQUEADA')
    )
    alias = models.CharField(default='', max_length=20, blank=True, null=True)
    nivel = models.ForeignKey('Nivel', blank=True, null=True,
                              on_delete=models.CASCADE)
    max_items = models.SmallIntegerField(default=5)
    items = models.SmallIntegerField(default=0)
    cycle_position = models.SmallIntegerField(default=4)
    ciclo = models.BigIntegerField(default=0)
    jugador = models.ManyToManyField('Jugador', default='', blank=True,
                                     through='Juego',
                                     through_fields=('lista', 'jugador'))
    lista_padre = models.ForeignKey('self', on_delete=models.CASCADE,
                                    null=True,
                                    blank=True)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES,
                              default='A')
    nivel = models.ForeignKey('Nivel', on_delete=models.CASCADE, default=1)
    pc = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = 'Listas'
        ordering = ['created']


class Juego(models.Model):
    lista = models.ForeignKey(Lista, on_delete=models.CASCADE)
    jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE)

    posicion = models.SmallIntegerField(default=-1)
    posicion_cerrado = models.SmallIntegerField(default=-1)
    color_cerrado = models.CharField(max_length=10, default='red')
    cadena_ciclaje = models.TextField(default='')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.jugador) + ' jugando en lista ' + str(self.lista)

    class Meta:
        verbose_name_plural = 'Juegos'
        ordering = ['created']


class Jugador(models.Model):
    nuevo = models.BooleanField(default=True)
    usuario = models.OneToOneField(User,
                                   on_delete=models.CASCADE)
    n_referidos = models.SmallIntegerField(default=0)
    n_referidos_activados = models.SmallIntegerField(default=0)
    color = models.CharField(max_length=10, default='red')
    ciclo = models.BigIntegerField(default=0)
    patrocinador = models.ForeignKey('self', blank=True, null=True,
                                     on_delete=models.CASCADE)
    whatsapp = models.CharField(max_length=10, blank=True, null=True)
    celular = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return str(self.usuario)

    class Meta:
        verbose_name_plural = 'Jugadores'


class Nivel(models.Model):
    indice = models.SmallIntegerField(default=1, unique=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=50000)

    def __str__(self):
        return "Nivel " + str(self.monto)

    class Meta:
        verbose_name_plural = 'Niveles'


class Clon(models.Model):
    ESTADO_CHOICES = (
        ('P', 'PENDIENTE ACTIVAR'),
        ('A', 'ACTIVO'),
    )
    jugador = models.ForeignKey('jugador', blank=True, null=True,
                                on_delete=models.CASCADE)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES,
                              default='P')
    nivel = models.ForeignKey('Nivel', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return 'clon de ' + str(self.jugador)

    class Meta:
        verbose_name_plural = 'Clones'
