from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    
    path('home/', views.home, name='home'),
    path('referidos/', views.mis_referidos, name='mis_referidos'),
    path('clones/', views.mis_clones, name='mis_clones'),
    path('tienda/', views.mi_tienda, name='mi_tienda'),
    path('niveles/', views.mis_niveles, name='mis_niveles'),
    path('finanzas/', views.mis_finanzas, name='mis_finanzas'),

    path('home/activar_clon/<int:clon_id>/', views.activar_clon, name='activar_clon'),
    path('home/activar_clon/', views.activar_clon, name='activar_clon'),
    
    path('ajax/lista_content/', views.lista_content, name='lista_content'),
    path('ajax/lista_content/<int:id_lista>/', views.lista_content,
         name='lista_content'),
    path('ajax/lista_content/<int:id_lista>/<str:n_usuario>/', views.lista_content,
         name='lista_content'),

    path('ajax/listas/', views.listas, name='listas'),
    path('ajax/listas/<str:usr>', views.listas, name='listas'),
    
    path('ajax/clones/', views.clones, name='clones'),
    path('ajax/referidos/<str:n_usuario>/', views.referidos, name='referidos'),
    path('ajax/referidos/', views.referidos, name='referidos'),
    path('ajax/cobrando/', views.cobrando, name='cobrando'),
    path('ajax/consulta_usuario/<str:n_usuario>/', views.consulta_usuario, name='consulta_usuario'),
    path('ajax/consulta_usuario/', views.consulta_usuario, name='consulta_usuario')
]
