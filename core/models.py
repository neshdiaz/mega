from django.db import models
from django.contrib.auth.models import User

class Configuracion(models.Model):
    nombre = models.CharField(default='', max_length=20)
    lista_max_items = models.SmallIntegerField(default=5)
    lista_cycle_position = models.SmallIntegerField(default=4)
    porcent_plataforma = models.SmallIntegerField(default=20)
    porcent_patrocinador_directo = models.SmallIntegerField(default=20)
    porcent_segunda_generacion = models.SmallIntegerField(default=3)
    porcent_tercera_generacion = models.SmallIntegerField(default=7)
    porcent_posicion_cobro = models.SmallIntegerField(default=50)
    monto_minimo_retiro = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    comision_retiro = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    tope_cobros_nivel = models.SmallIntegerField(default=6)
    tope_cobros_clon = models.SmallIntegerField(default=10)

    def __str__(self):
        return "Configuracion" + str(self.nombre)

    class Meta:
        verbose_name_plural = 'Configuraciones'

class Cuenta(models.Model):
    jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE)
    saldo_activacion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_disponible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    beneficios_totales = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Cuenta " + str(self.id) + " " + str(self.jugador)

    class Meta:
        verbose_name_plural = 'Cuentas'
        ordering = ['created']

class Movimiento(models.Model):
    TIPO_CHOICES = (
        ('A', 'ABONO'),
        ('P', 'PAGO'),
        ('R', 'RETIRO')
    )
    cuenta = models.ForeignKey('Cuenta', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES,
                            default='A')
    descripcion = models.CharField(default='', max_length=100, blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = 'Movimientos'
        ordering = ['created']

class Lista(models.Model):
    ESTADO_CHOICES = (
        ('A', 'ABIERTA'),
        ('C', 'CERRADA'),
        ('B', 'BLOQUEADA')
    )
    alias = models.CharField(default='', max_length=20, blank=True, null=True)
    nivel = models.ForeignKey('Nivel', blank=True, null=True,
                              on_delete=models.CASCADE)

    items = models.SmallIntegerField(default=0)
    jugador = models.ManyToManyField('Jugador', default='', blank=True,
                                     through='Juego',
                                     through_fields=('lista', 'jugador'))
    lista_padre = models.ForeignKey('self', on_delete=models.CASCADE,
                                    null=True,
                                    blank=True)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES,
                              default='A')
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
    cadena_ciclaje = models.TextField(default='', blank=True, null=True)

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
    promotor = models.ForeignKey('Jugador', blank=True, null=True,
                                 on_delete=models.CASCADE, related_name='jugador_promotor')
    nivel = models.ManyToManyField('Nivel', default='', blank=True,
                                   through='JugadorNivel',
                                   through_fields=('jugador', 'nivel'))
    whatsapp = models.CharField(max_length=10, blank=True, null=True)
    celular = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return str(self.usuario)

    class Meta:
        verbose_name_plural = 'Jugadores'


class Nivel(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return "Nivel " + str(self.id)

    class Meta:
        verbose_name_plural = 'Niveles'


class JugadorNivel(models.Model):
    ESTADO_CHOICES = (
        ('P', 'PENDIENTE DE ACTIVAR'),
        ('A', 'ACTIVO'),
        ('B', 'BLOQUEADO'),
    )

    jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE)
    nivel = models.ForeignKey('Nivel', on_delete=models.CASCADE)
    patrocinador = models.ForeignKey('Jugador', blank=True, null=True,
                                     on_delete=models.CASCADE, related_name='patrocinador')
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES,
                              default='P')
    
    n_referidos = models.SmallIntegerField(default=0)
    n_referidos_activados = models.SmallIntegerField(default=0)
    color = models.CharField(max_length=10, default='red')
    ciclo = models.BigIntegerField(default=0)
    cobros = models.BigIntegerField(default=0)
    bloqueo_x_cobros_nivel = models.BooleanField(default=False)
    bloqueo_y_cobros_clon = models.BooleanField(default=False)
    
    def __str__(self):
        return "Jugador " + str(self.jugador) + " " + str(self.nivel)

    class Meta:
        verbose_name_plural = 'Jugador Niveles'       

class Clon(models.Model):
    ESTADO_CHOICES = (
        ('P', 'PENDIENTE ACTIVAR'),
        ('A', 'ACTIVO'),
    )
    TIPO_CHOICES = (
        ('R', 'POR REFERIDOS'),
        ('C', 'POR CICLOS'),
    )
    jugador = models.ForeignKey('jugador', blank=True, null=True,
                                on_delete=models.CASCADE)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES,
                              default='P')
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES,
                            default='R')
    nivel = models.ForeignKey('Nivel', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return 'clon de ' + str(self.jugador)

    class Meta:
        verbose_name_plural = 'Clones'

class Cobrador(models.Model):
    jugador = models.ForeignKey('jugador', blank=True, null=True,
                                on_delete=models.CASCADE)
    nivel = models.ForeignKey('Nivel', on_delete=models.CASCADE, default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.jugador)

    class Meta:
        verbose_name_plural = 'Cobradores'
        ordering = ['-created']
