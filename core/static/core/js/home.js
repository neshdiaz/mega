relojActual = Date.now();
lista_desplegada = 1;
primera_carga = false;
url_listas = "";
url_lista_content = "";
mis_listas = [];

$(document).ready(function(){
  $('[data-toggle="tooltip"]').tooltip();
});

function init(){
    compartirReferido(); 
    get_listas(url_listas);
    //get_lista_content(url_lista_content);
    relojInit(relojActual);
    get_lista_clones(url_clones);
    get_lista_referidos(url_referidos);   
    get_lista_cobrando(url_lista_cobrando);   
    websocket();
}

function compartirReferido(){
    btn = document.getElementById("btnWhatsapp");  
    btn = document.getElementById("btnCopiar");  
    txt = document.getElementById("txtEnlaceReferido");
    btn.onclick = function(){
        txt.select()
        document.execCommand("copy");
    }
    btnWhatsapp.onclick = function(){
        redir = "whatsapp://send?text=Haz sido invitado a pasamano.com%20" + txt.value
        window.location.href = redir
    }
}

function relojInit(HoraActual){
    relojActual = new Date(HoraActual);
    setTimeout("relojRefresh()",1000);
}

function relojRefresh(){
    horas = "";
    minutos = "";
    segundos = "";
    relojActual.setSeconds(relojActual.getSeconds()+1)
    hor = relojActual.getHours();
    min = relojActual.getMinutes();
    seg = relojActual.getSeconds();
    if (hor < 10){
        horas = "0"+hor;
    } else{
        horas ="" + hor
    }

    if (min < 10){
        minutos = "0"+min;
    } else{
        minutos ="" + min
    }
    
    if (seg < 10){
        segundos = "0"+seg;
    } else{
        segundos ="" + seg
    }
    
    //document.getElementById("reloj").innerHTML="<b> "+horas+":"+minutos+":"+segundos+"</b>";
    setTimeout("relojRefresh()",1000);
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
    get_listas(url_listas)
    get_lista_content(url_lista_content, lista_desplegada);
    get_lista_clones(url_clones);
    get_lista_referidos(url_referidos);
    get_lista_cobrando(url_lista_cobrando);
    
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

// ajax para cargar las listas del usuario
function get_listas(url_listas, id, usuario){
    ur = url_listas;
    if (id !=undefined){
        ur += "/" + id;
    }
    if (usuario != undefined){
        ur += "/" + usuario;
    }
    var csrftoken = getCookie('csrftoken');
    $.ajax({
        url: ur,
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
            listas_json = JSON.parse(respuesta);
            //actualizar el contenido del div        
            displayListas(listas_json);
        }        
    });
}

function displayListas(listas_json){
    if($("#listasContainer").length > 0){
        ContenedorListas = document.getElementById("listasContainer");
        htmlListas = "";
        htmlListas += "<div class ='btn-group role='group'>";
        htmlListas += "  <div class = 'btn-group-vertical'>";
        listas_json.forEach(function(item, index){
            url = url_lista_content;
            htmlListas += "    <button class='btn btn-primary' onclick=get_lista_content('" + url + "'," + item.id + ",'"+ item.usuario +"');>" + "Lista " + item.id + " " + item.estado + "</button>";
        })
        htmlListas += "</div></div>";
        ContenedorListas.innerHTML = htmlListas;
    }
}

// ajax para cargar los datos de la lista
function get_lista_content(url_lista_content, id, usr){
    console.log(usr);
    ur = url_lista_content + id + "/"+ usr + "/";
    $.ajax({
        url: ur,
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
            lista_json = JSON.parse(respuesta);
            lista_desplegada = id;
            // actualizar el contenido del div
            displayListaContent(lista_json);
        }        
    });
}

function displayListaContent(lista_json){
    if($("#lista_content").length > 0){
        texto_usuario = lista_json[0].user + ' ' +  lista_json[0].cadena_ciclaje
        pat = lista_json[0].patrocinador;
        $("#j0").text(texto_usuario); 
        $("#j0").html('<div>'+ texto_usuario +'</div>');
        $("#j0").css({"color": lista_json[0].color});
        
        texto_usuario = lista_json[1].user + ' ' +  lista_json[1].cadena_ciclaje
        pat = lista_json[1].patrocinador;
        $("#j1").text(texto_usuario); 
        $("#j1").html('<div>'+ texto_usuario +'</div>');
        $("#j1").css({"color": lista_json[1].color}); 
        
        texto_usuario = lista_json[2].user + ' ' +  lista_json[2].cadena_ciclaje
        pat = lista_json[2].patrocinador;
        $("#j2").text(texto_usuario); 
        $("#j2").html('<div>'+ texto_usuario +'</div>');
        $("#j2").css({"color": lista_json[2].color}); 
        
        texto_usuario = lista_json[3].user + ' ' +  lista_json[3].cadena_ciclaje
        pat = lista_json[3].patrocinador;
        $("#j3").text(texto_usuario); 
        $("#j3").html('<div>'+ texto_usuario +'</div>');
        $("#j3").css({"color": lista_json[3].color}); 

        texto_usuario = lista_json[4].user + ' ' +  lista_json[4].cadena_ciclaje
        pat = lista_json[4].patrocinador;
        $("#j4").text(texto_usuario);
        $("#j4").html('<div data-toggle="tooltip" title="Patrocinador: '+ pat +'">'+ texto_usuario +'</div>');
        $("#j4").css({"color": lista_json[4].color});
        
        $("#encabezado_lista").html('<i class="fas fa-people-carry"></i>');
        enc = '    Lista ' + lista_json[5].lista_id + ' ' + lista_json[5].estado //+ ' ' + lista_json[5].nivel
        $("#encabezado_lista").text(enc);
    }
    
}

function get_lista_clones(url_lista_clones){
    $.ajax({
        url: url_lista_clones,
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
            lista_json = JSON.parse(respuesta);
            // actualizar el contenido del div
            displayListaClones(lista_json);
        }        
    });
}

function displayListaClones(clones_json){
    if($("#clonesContainer").length > 0){
        ContenedorClones = document.getElementById("clonesContainer");
        htmlClones = "";
        htmlClones += "<div class ='btn-group role='group'>";
        htmlClones += "<div class = 'btn-group-vertical'>";
        clones_json.forEach(function(item, index){
            url = url_clones;
            htmlClones += "    <a href = " + url_activar_clon + item.id +">" + "Clon " + item.estado + " " + item.nivel + " </a>" ;
        })
        htmlClones += "</div></div>";
        ContenedorClones.innerHTML = htmlClones
    }
}

function get_lista_referidos(url_lista_referidos){
    $.ajax({
        url: url_lista_referidos,
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
            lista_json = JSON.parse(respuesta);
            // actualizar el contenido del div
            displayListaReferidos(lista_json);
        }        
    });
}

function displayListaReferidos(referidos_json){
    if($("#referidosContainer").length > 0 ){
        ul = $("<ul>");
        boton=$("<button>");
        referidos_json.forEach(function(item, index){
            boton.preventDefault;
            htmlBoton =  "<button class='btn btn-primary' onclick=get_listas('" + url_listas + item.usuario + "');>" + item.usuario + "</button>";
            boton.append(htmlBoton);
            $("#referidosContainer").append(boton);
        })

    }
}

function get_lista_cobrando(url_lista_cobrando){
    $.ajax({
        url: url_lista_cobrando,
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
            lista_json = JSON.parse(respuesta);
            // actualizar el contenido del div
            displayListaCobrando(lista_json);
        }        
    });
}

function displayListaCobrando(cobrando_json){
    if($("#cobrando_container").length > 0){
        ContenedorCobrando = document.getElementById("cobrando_container");
        htmlCobrando = "";
        htmlCobrando = "<ul>";
        cobrando_json.forEach(function(item, index){
            url = url_lista_cobrando;
            htmlCobrando += "    <li>" + item.usuario + "</li>" ;
        })
        htmlCobrando += "</ul>";
        ContenedorCobrando.innerHTML = htmlCobrando
    }
}