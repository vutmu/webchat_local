$('#xoxo').on('click', ()=>{
    $.get('/games', {subfunction: 'get_token'}, function (response) {
        response=jQuery.parseJSON(response)
        console.log(response)
//        var XHR = ("onload" in new XMLHttpRequest()) ? XMLHttpRequest : XDomainRequest;
//        var xhr = new XHR();
//        xhr.open('GET', 'https://wasmoh-xoxo.herokuapp.com/', true);
//        xhr.onload = function() {
//        alert( this.responseText );
//        }
//        xhr.onerror = function() {
//        alert( 'Ошибка ' + this.status );
//        }
//        xhr.send();
        let ref='http://localhost:8080/?token='+response.token
//        let ref='https://wasmoh-xoxo.herokuapp.com/?token='+response.token
        window.open(ref, "_self")

    })
})