function init(){
    compartirReferido();
    get_listas();
    //get_lista_content(url_lista_content);
    //relojInit(relojActual);
    get_lista_clones();
    get_lista_referidos();
    get_lista_inactivos();  
    get_lista_cobrando();   
    get_lista_canastas(url_lista_canastas)
    //consulta_saldos_usuario()
    consulta_movimientos_usuario()
    websocket();
}   


function compartirReferido(){
    btn = document.getElementById("btnWhatsapp");  
    btn = document.getElementById("btnCopiar");  
    txt = document.getElementById("txtEnlaceReferido");
    btn.onclick = function(){
        txt.select()
        document.execCommand("copy");
        redir = "whatsapp://send?text=Haz sido invitado a pasamano.com%20" + txt.value
        window.location.href = redir
        
    }
}

// Ajax para notificaciones
function websocket(){
    var chatSocket = new WebSocket('ws://' + window.location.host +
    '/ws/home/');
    chatSocket.onmessage = function(e) {
      var data = JSON.parse(e.data);
      var message = data['message'];
      if (message == "Nuevo jugador en lista"){
        setTimeout("actualizar_pantalla()", 1000);
      }
      // document.querySelector('#chat-log').innerHTML += (message + '\n');
    }
}

function actualizar_pantalla(){
    get_listas()
    // get_lista_content();
    get_lista_clones();
    get_lista_referidos();
    get_lista_cobrando();
    load_lista_canastas(url_lista_canastas)
    //consulta_saldos_usuario()
    
}

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