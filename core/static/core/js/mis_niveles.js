var templateCanasta = ''

templateCanasta +='  <div class="col-4">'
templateCanasta +='    <div class = "container-fluid {{estado}}">'
templateCanasta +='      <div class="container-fluid">'
templateCanasta +='        <div class = "row">'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4"><span class="badge badge-pill badge-primary">{{id}}</span></div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right"><span class="badge badge-pill badge-primary"><i class="fas fa-shopping-cart"></i></span></div>'
templateCanasta +='        </div>'
templateCanasta +='      </div>  '

templateCanasta +='      <div class="container-fluid">'
templateCanasta +='        <div class = "row">'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4 cartera-monto text-center">{{monto}} US$</div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
templateCanasta +='        </div>'
templateCanasta +='      </div>  '
templateCanasta +='      '
templateCanasta +='      <div class="container-fluid">'
templateCanasta +='        <div class = "row">'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4 referidos"><i class="fas fa-people-carry"></i>10</div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4"></div>'
templateCanasta +='          <div class = "col-4 col-xs-4 col-md-4 col-lg-4 text-right ciclajes"><i class="fas fa-recycle"></i>12</div>'
templateCanasta +='        </div>'
templateCanasta +='      </div>'
templateCanasta +='    </div>'
templateCanasta +='  </div>'
//crear plantilla completa de los 15 niveles y renderear 
var dato = { 
    estado:"canasta-activa",
    id: "1",
    monto:"5"
} 

function get_lista_canastas(url_request){
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
            //document.getElementById('lista-canastas').appendChild (Mustache.render(templateCanasta, dato))


    
        }

        
    });
}   