
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
            return response
        }        
    });
}

function listBox(url, params, objetoRender){
    // Template mustage
    var templateListboxButton = '<button type="button" class="btn btn-secondary">Lista <span class = "{{id}}"> <i class="{{iconEstado}}"></button>'
    
    var templateListbox = ''
        templateListbox += '<div class="btn-group-vertical">'
        templateListbox += templateListboxButton
        templateListbox += '<button type="button" class="btn btn-secondary">2</button>'
        
        templateListbox += '</div>' 
    

    // Solicitar datos con get_data y mostrarlo en objetoRender
    data = getData(url, params)
    
    // Render data con plantilla sobre mustage con jquery
    
}

function listContentBox(url, params, objetoRender){
    //template mustage

    // Solicitar datos con get_data y mostrarlo en objetoRender
    data = getData(url, params)
}

listBox()
