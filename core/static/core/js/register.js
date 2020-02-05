$( "#id_username" ).focusout(function buscar_username(){
    if ($( "#id_username" ).val() != null){
        consulta_username(url_consulta_usuario , $('#id_username').val())
    }
});   

// Tokens de seguridad para ajax
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ajax para consulta de usuario
function consulta_username(url, username){
    var csrftoken = getCookie('csrftoken');
    $.ajax({
        url: url + username + "/",
        method: "post",
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
        success: function(respuesta){
            json = JSON.parse(respuesta);
            if (json=='True'){
                $('#mensajes').html("<div class='alert alert-danger'>" + username + " YA EXISTE en el sistema, intenta con uno diferente.</div>");
                
            }
            else{
                $('#mensajes').html("<div></div>");
            }
        }        
    });
}
