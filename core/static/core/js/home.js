relojActual = Date.now();
lista_desplegada = 1;
primera_carga = false;
url_listas = "";
url_lista_content = "";
mis_listas = [];
var referido_activo = "";
var Filtro_estado = "Todos"
var Filtro_nivel = "Todos"


var Filtro_estado_ref = "Todos"
var Filtro_nivel_ref = "Todos"

$(document).ready(function(){
    Filtro_estado = "Todos"
    Filtro_nivel = "Todos"
    Filtro_estado_ref = "Todos"
    Filtro_nivel_ref = "Todos"
});

function init(){
    compartirReferido(); 
    get_listas();
    //get_lista_content(url_lista_content);
    relojInit(relojActual);
    get_lista_clones(url_clones);
    get_lista_referidos();  
    get_lista_cobrando(url_lista_cobrando);   
    websocket();
}

function borrar_filtros(){
    $("#inlineFormCustomSelect").val('Todos');
    $("#inlineFormCustomSelect2").val('Todos');
    Filtro_estado = "Todos"
    Filtro_nivel = "Todos"
    get_listas();
}

function borrar_filtros_ref(){
    $("#inlineFormCustomSelectRef").val('Todos');
    $("#inlineFormCustomSelect2Ref").val('Todos');
    Filtro_estado_ref = "Todos"
    Filtro_nivel_ref = "Todos"
    get_lista_referidos();
}

function cambiarEstado(){
   Filtro_estado = $("#inlineFormCustomSelect").val();
   get_listas(); 
}
function cambiarNivel(){
    Filtro_nivel = $("#inlineFormCustomSelect2").val();
    get_listas();
}

function cambiarEstadoRef(){
    Filtro_estado_ref = $("#inlineFormCustomSelectRef").val();
    get_lista_referidos(referido_activo); 
    //$('#listasReferidoContainer').html("");
    $('#encabezado_lista').html("");
}

function cambiarNivelRef(){
    Filtro_nivel_ref = $("#inlineFormCustomSelect2Ref").val();
    get_lista_referidos(referido_activo);
    //$('#listasReferidoContainer').html("");
    $('#encabezado_lista').html("");


        
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
    //setTimeout("relojRefresh()",1000);
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
    get_lista_content();
    get_lista_clones();
    get_lista_referidos();
    get_lista_cobrando();
    get_lista_niveles();
    
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
function get_listas(){
    if($("#listasContainer").length > 0){
        var csrftoken = getCookie('csrftoken');
        $.ajax({
            url: url_listas,
            method: "post",
            data:{
                nivel: Filtro_nivel,
                estado: Filtro_estado
            },
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
}

function displayListas(listas_json){
    if($("#listasContainer").length > 0){
        accordion = $('#listasContainer')
        headx = "";
        collapsex = "";
        item_anterior="";
        item_nuevo = "";
        repetido = false;
        collapsex_content = "";
        $(accordion).html("");
        temp = "";
        url = url_lista_content;
        
        listas_json.forEach(function(item, index){
            item_anterior = item.nivel;
            if (item_nuevo != item_anterior || inicial){
                inicial = false;
                headx = "<div id='head" + item.nivel_id + "'>";
                headx += "<button  class='btn btn-warning' data-toggle='collapse' data-target='#";
                headx += "content_" + item.nivel_id + "' aria-expanded='false' aria-controls='content_" + item.nivel_id +"'>> ";
                headx += item.nivel + "</div>";
                // agrego la cabecera
                $(headx).appendTo(accordion);
                collapsex_content = "<div id = 'content_"+ item.nivel_id +"' class='collapse hide' aria-labeldby='head" + item.nivel_id +"'data-parent='#listasContainer'></div>"
                // agrego el div para los botones de niveles
                $(collapsex_content).appendTo(accordion);
                item_nuevo = item.nivel
            }           
        })     
        
        // Agregamos lo botones a las casillas de niveles correspondientes
        listas_json.forEach(function(item, index){
            boton = "<button class='btn btn-secondary ml-4' onclick=get_lista_content('" + url + "',";
            boton += item.id + ",'"+ item.usuario +"');>>> Lista " + item.id;
            boton += " " + item.estado  +  "</button>"
            contentId = "content_" + item.nivel_id.toString();
            $(boton).appendTo('#' + contentId)
        })
    }
}

// ajax para cargar las listas del referido
function get_listas_referido(usr, nivel){
    referido_activo = usr
    if($("#referidosContainer").length > 0){
        ur = url_listas_referido;

        var csrftoken = getCookie('csrftoken');
        $.ajax({
            url: ur,
            method: "post",
            data:{
                nivel: Filtro_nivel_ref,
                estado: Filtro_estado_ref,
                referido: usr,
                nivel_referido:nivel,
            },
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
                accordion = displayListasReferido(listas_json);
            }        
        });
    }
    return accordion;    
}

function displayListasReferido(listas_json){
    usuario = listas_json[0].usuario.toString();
    accordion_id = "#content_"+ usuario; 
    accordion = $(accordion_id);
    headx = "";
    collapsex = "";
    item_anterior="";
    item_nuevo = "";
    repetido = false;
    collapsex_content = "";
    $(accordion).html("");
    temp = "";
    url = url_lista_content;
    //listas_json.forEach(function(item, index)
    for(item of listas_json){
        item_anterior = item.nivel;
        if (item_nuevo != item_anterior || inicial){
            inicial = false;
            headx = "<div id='head_" + usuario +"_nivel_"+ item.nivel_id + "'>";
            headx += "<button  class='btn btn-warning' data-toggle='collapse' data-target='#";
            headx += "content_" + usuario + "_nivel_" + item.nivel_id + "' aria-expanded='true' aria-controls='content_" + usuario + "_nivel_ " + item.nivel_id +"'>>> ";
            headx += item.nivel + "</div>";
            // agrego la cabecera
            $(headx).appendTo(accordion);
            collapsex_content_lista = "<div id = 'content_" + usuario + "_nivel_" + item.nivel_id +"' class='collapse hide' aria-labeldby='head_"
            collapsex_content_lista += usuario + "_nivel_" + item.nivel_id +"'data-parent='#content_"+ usuario +"'></div>"
            // agrego el div para los botones de niveles
            $(collapsex_content_lista).appendTo(accordion);
            item_nuevo = item.nivel
        }           
    }     
    
    // Agregamos lo botones a las casillas de niveles correspondientes
    //listas_json.forEach(function(item, index){
    for(item_lista of listas_json){
        boton = "<button class='btn btn-secondary ml-4' onclick=get_lista_content('" + url + "',";
        boton += item_lista.id + ",'"+ item_lista.usuario +"');>>>> Lista " + item_lista.id;
        boton += " " + item_lista.estado  +  "</button>";
        contentId = "#content_" + usuario + "_nivel_" + item_lista.nivel_id.toString();
        $(boton).appendTo(contentId);
    }
}

// ajax para cargar los datos de la lista
function get_lista_content(url_lista_content, id, usr){ 
    if($("#lista_content").length > 0){
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
        enc = '    Nivel: ' + lista_json[5].nivel + ' Lista: ' + lista_json[5].lista_id + ' ' + lista_json[5].estado
        $("#encabezado_lista").text(enc);
    }
    
}

function get_lista_clones(url_lista_clones){
    if($("#clonesContainer").length > 0){
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
}

function displayListaClones(clones_json){
    if($("#clonesContainer").length > 0){
        contenedorClones = $('#clonesContainer');
        table="";
        thead = "";
        tbody = "";
        td = "";
        tr = "";
        
        $("#clonesContainer").html("");
        if (clones_json.length == 0){
            $("<p>No tienes clones disponibles ... </p>").appendTo(contenedorClones)
        }        
        
        table = $("<table class='table'></table>");
        thead += "<thead>";
        thead += "<tr>";
        thead += "<th scope='col'>Nivel</th>";
        thead += "<th scope='col'>Estado</th>";
        thead += "<th scope='col'>Tipo</th>";
        thead += "<th scope='col'>Activar</th>";
        thead += "</tr>";
        thead += "</thead>";
        // Asigno cabecera a tabla
        $(thead).appendTo(table);
        
        tbody = $("<tbody></tbody>")

        
        clones_json.forEach(function(item, index){
            tr = $("<tr></tr>");
            td = "<td>" + item.nivel +"</td>";
            td += "<td>" + item.estado +"</td>";
            td += "<td>" + item.tipo +"</td>";
            if (item.estado == 'ACTIVO'){
                td += "<td> Activar Clon </td>";
            } else{
                td += "<td> <a href = " + url_activar_clon + item.id +">" + "Activar Clon " +" </a></td>";
            }
            $(td).appendTo(tr);
            $(tr).appendTo(tbody);
        })
        $(tbody).appendTo(table);
        $(table).appendTo(clonesContainer);
    }
}

function get_lista_referidos(){
    if($("#referidosContainer").length > 0 ){
        $.ajax({
            url: url_lista_referidos,
            method: "post",
            data:{
                nivel: Filtro_nivel_ref,
                estado: Filtro_estado_ref
            },
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
}

function displayListaReferidos(referidos_json){
    if($("#referidosContainer").length > 0){
        accordion = $('#referidosContainer')
        headx = "";
        collapsex = "";
        item_anterior="";
        item_nuevo = "";
        collapsex_content = "";
        $(accordion).html("");
                
        referidos_json.forEach(function(item, index){
            item_anterior = item.usuario;
            if (item_nuevo != item_anterior ){
                headx = "<div id='head_" + item.usuario + "'>";
                headx += "<button onclick=get_listas_referido('"+ item.usuario +"');  class='btn btn-warning' data-toggle='collapse' data-target='#";
                headx += "content_" + item.usuario + "' aria-expanded='false' aria-controls='content_" + item.usuario +"'>> ";
                headx += item.usuario + "</div>";
                // agrego la cabecera
                $(headx).appendTo(accordion);
                collapsex_content = "<div id = 'content_"+ item.usuario +"' class='collapse hide ml-4' aria-labeldby='head_" + item.usuario
                collapsex_content += "'data-parent='#referidosContainer'></div>"
                // agrego el div para los botones de niveles
                $(collapsex_content).appendTo(accordion);
                item_nuevo = item.usuario
            }           
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
        //htmlCobrando = "<ol>";
        htmlCobrando = "<div class='container-fluid p-0 m-0'>";
        cobrando_json.forEach(function(item, index){
            htmlCobrando += "<div class='row'>";
            url = url_lista_cobrando;
            //htmlCobrando += "    <li style='list-style:none; margin:0'> <i class='fas fa-hand-holding-usd'></i>" + item.usuario +" " + "<i class='fas fa-sort-amount-up'></i>"+ item.nivel + " " + "</li>" ;
            htmlCobrando += "<div class='col-1'>";
            htmlCobrando += "     <i class='fas fa-hand-holding-usd'></i>" ;
            htmlCobrando +="</div>";
            
            htmlCobrando += "<div class='col-6'>";
            htmlCobrando += item.usuario + " ";
            htmlCobrando +="</div>";
            
            htmlCobrando += "<div class='col-1'>";
            htmlCobrando += "<i class='fas fa-sort-amount-up'></i>";
            htmlCobrando +="</div>";
            
            
            htmlCobrando += "<div class='col-1'>";
            htmlCobrando += item.nivel;
            htmlCobrando += "</div>";

            
            htmlCobrando += "</div>";



        })
        //htmlCobrando += "</ol>";
        htmlCobrando += "</div>";   
        ContenedorCobrando.innerHTML = htmlCobrando
    }
}

function boton_cargar_saldo(){
    monto_carga = $("#monto").val()
    $("#boton_carga_saldo").onclick( window.location.href = url_base + url_cargar_saldo + monto_carga)
}
