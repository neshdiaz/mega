

function get_lista_canastas(url_request){
    if ($('#lista-canastas').length > 0){
        var templateCanastaActiva = ''
        templateCanastaActiva += '<div class = "canasta-activa">'
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
        templateCanastaInactiva += '<div class="canasta-inactiva">'
        templateCanastaInactiva += '  <a href="'+ url_activar_nivel  +'{{jugador_nivel_id}}">'
        templateCanastaInactiva += '    <div class="container-fluid">'
        templateCanastaInactiva += '      <div class = "row no-gutters">'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"><span class="badge badge-pill badge-primary">{{id}}</span></div>'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right">'
        templateCanastaInactiva += '          <span class="badge badge-pill badge-primary"><i class="fas fa-shopping-basket"></i></span>'
        templateCanastaInactiva += '        </div>'
        templateCanastaInactiva += '      </div>'
        templateCanastaInactiva += '      <div class = "row no-gutters">'
        templateCanastaInactiva += '        <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaInactiva += '        <div class = "col-6 col-xs-6 col-md-6 col-lg-6 cartera-monto text-center">{{monto}} US$</div>'
        templateCanastaInactiva += '        <div class = "col-3 col-xs-3 col-md-3 col-lg-3"></div>'
        templateCanastaInactiva += '      </div>'
        templateCanastaInactiva += '      <div class = "row no-gutters">'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4 referidos"><span><i class="fas fa-people-carry"></i>{{referidos}}</span></div>'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
        templateCanastaInactiva += '        <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right ciclajes"><i class="fas fa-recycle"></i>{{ciclajes}}</div>'
        templateCanastaInactiva += '      </div>'
        templateCanastaInactiva += '    </div>  '
        templateCanastaInactiva += '  </a>'
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