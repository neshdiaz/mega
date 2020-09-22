
/**************************    FUNCIONES GLOBALES  ***************************/

function getData(urlRequest, params){
    //Enviar solicitud ajax y recibir datos con ajax
    $.ajax({
        url: urlRequest,
        method: "post",
        data: params,
        beforeSend: function (xhr, settings) {
            var csrftoken = getCookie('csrftoken');
            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },   
        success: function(response){
            alert(response)
            return response
        }        
    });
}

/**************************    FUNCIONES COMPONENTES  ************************/

function listBox(url, params, target){
    //variables
    var templateListboxButton = '<button type="button" class="btn btn-secondary">Lista <span class = "{{id}}"> <i class="{{iconEstado}}"></button>'
    
    var templateListbox = ''
        templateListbox += '<div class="btn-group-vertical">'
        templateListbox += templateListboxButton
        templateListbox += '<button type="button" class="btn btn-secondary">2</button>'
        
        templateListbox += '</div>'
    
    //metodos...
    data = getData(url, params)
    alert("datos" + data)
    render(data);
    
    // Render data con plantilla sobre mustage con jquery
    // meter aqui la plantilla mustage y rellenar con data
    // incrustar logica

    function render(data){
        htmlTempl = '<h1> Datos obtenidos y mostrados por el componente </h1>'
        data.forEach(function(item, index){
            htmlTempl += "<h2>" + item.estado + "</h2>"
        })

        // Volcado de datos en el contenedor
        objTarget = $("#" + target)
        $(htmlTempl).appendTo(objTarget)
    }
}   

function listContentBox(url, params, target){
    //template mustage

    // Solicitar datos con get_data y mostrarlo en objetoRender
    data = getData(url, params)
}

