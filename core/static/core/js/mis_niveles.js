

function get_lista_canastas(url_request){
    if ($('#lista-canastas').length > 0){
        var templateCanastaActiva = ''
        templateCanastaActiva += '<button class = "canasta-activa">'
        templateCanastaActiva += '  <div class="container-fluid">'
        templateCanastaActiva += '    <div class = "row no-gutters">'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"><span class="badge badge-pill badge-primary">{{id}}</span></div>'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaActiva += '    </div>'
        templateCanastaActiva += '    <div class = "row no-gutters">'
        templateCanastaActiva += '        <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaActiva += '        <div class = "col-6 col-xs-6 col-md-6 col-lg-6 cartera-monto text-center">{{monto}} US$</div>'
        templateCanastaActiva += '        <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaActiva += '    </div>'
        templateCanastaActiva += '    <div class = "row no-gutters">'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4 referidos"><i class="fas fa-people-carry"></i>{{referidos}}</div>'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaActiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right ciclajes"><i class="fas fa-recycle"></i>{{ciclajes}}</div>'
        templateCanastaActiva += '    </div>'
        templateCanastaActiva += '  </div>'
        templateCanastaActiva += '</div>'

        var templateCanastaInactiva = ''
        templateCanastaInactiva += '<button class="canasta-inactiva btn btn-primary" data-toggle="modal" data-target="#exampleModal" data-nivel-a-activar="{{jugador_nivel_id}}" data-nivel="{{id}}" >'
        templateCanastaInactiva += '  <div class="container-fluid">'
        templateCanastaInactiva += '    <div class = "row no-gutters">'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4"><span class="badge badge-pill badge-primary">{{id}}</span></div>'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right">'
        templateCanastaInactiva += '        <span class="badge badge-pill badge-primary"><i class="fas fa-shopping-basket"></i></span>'
        templateCanastaInactiva += '      </div>'
        templateCanastaInactiva += '    </div>'
        templateCanastaInactiva += '    <div class = "row no-gutters">'
        templateCanastaInactiva += '      <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaInactiva += '      <div class = "col-6 col-xs-6 col-md-6 col-lg-6 cartera-monto text-center">{{monto}} US$</div>'
        templateCanastaInactiva += '      <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaInactiva += '    </div>'
        templateCanastaInactiva += '    <div class = "row no-gutters">'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4 referidos"><span><i class="fas fa-people-carry"></i>{{referidos}}</span></div>'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaInactiva += '      <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right ciclajes"><i class="fas fa-recycle"></i>{{ciclajes}}</div>'
        templateCanastaInactiva += '    </div>'
        templateCanastaInactiva += '  </div>  '
        templateCanastaInactiva += '</div>'
        
        $.ajax({
            url: url_request,
            method: "post",
            beforeSend: function (xhr, settings){
                var csrftoken = getCookie('csrftoken');
                function csrfSafeMethod(method) {
                    // these HTTP methods do not require CSRF protection
                    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
                }
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },   
            success: function(resp){
                json = JSON.parse(resp);
                htmlTemp = ''
                for (nivel in json){
                    if (json[nivel].estado == "ACTIVO"){
                        htmlTemp += Mustache.render(templateCanastaActiva, json[nivel])
                    }
                    else{
                        htmlTemp += Mustache.render(templateCanastaInactiva, json[nivel])
                    }
                }
                document.getElementById('lista-canastas').innerHTML = htmlTemp
            }
        });
    }    
} 

// Funcion para variar el contenido del cuadro de dialogo de confirmación para activar nivel

$('#exampleModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    var nivel_a_activar = button.data('nivel-a-activar') // Extract info from data-* attributes
    var nivel = button.data('nivel') // Extract info from data-* attributes

    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    var modal = $(this)
    modal.find('.modal-title').text('Esta seguro que quiere activar el nivel ' + nivel)
    modal.find('.modal-body input').val(nivel)
    modal.find('.modal-footer .confirm-link').attr('href', url_activar_nivel  + nivel_a_activar)
  })