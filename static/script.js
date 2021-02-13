




function generate(n){
    for (var i=1; i <= n; i++){
        var s = "file" + i;
        var e = document.querySelector("input[name='" + s + "']");
        var l = document.querySelector("label[for='" + s + "']");
    
        e.style.visibility = "hidden";
        e.name = "generated" + i;
        l.textContent = "spreadsheet" + ((n == 1)? '' : i) + ".csv";
    }
    return false;
}



function spinner(){
    var word = "Working";
    var n = word.length;
    var e = document.getElementById("spinner");
    var end = e.innerHTML.substring(n);

    if (end == ""){end = ".";}
    else if (end == "."){end = "..";}
    else if (end == ".."){end = "...";}
    else end = "";
     e.innerHTML = word + end;
}

function show_spinner(){
    var e = document.querySelector("input[id='file']");
    if (e == null){
        //document.querySelector("input[id='file1']").disabled = true;
        //document.querySelector("input[id='file2']").disabled = true;
    } else {e.disabled = true;}

    document.querySelector("button[type='button']").disabled = true;
    
    document.getElementById("spinner").style.visibility = "visible";
    window.setInterval(spinner, 500);
    //document.querySelector("input[type='submit']").disabled = true;
}

let path = window.location.pathname.split('/').pop();
if (path == "merge" | path == "detect") {
    window.onload = function() {
        if (document.querySelector("input[type='submit']") != null){
        document.querySelector("input[type='submit']").onclick = show_spinner;}
    }
}

