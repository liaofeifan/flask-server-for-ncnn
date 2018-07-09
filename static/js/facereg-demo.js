/*
Copyright 2015-2016 Carnegie Mellon University

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
function btnStartOnclick(){
    var name = $("#addPersonTxt").val();
    if(document.getElementById("addPersonTxt").value=='')
    { alert("Please input your name!"); return; }

    console.log("in btnStartOnclick");
    sendMessage("ADDPERSON_REQ", name);
}


function btnDeleteOnclick(){
    var name = $("#addPersonTxt").val();
    if(document.getElementById("addPersonTxt").value=='')
    { alert("Please input your name!"); return; }

    console.log("in btnDeleteOnclick");
    sendMessage("DELPERSON_REQ", name);
}
function btnRefreshOnclick(){
    console.log("in btnRefreshOnclick");
    sendMessage("GETNAMES_REQ", name);
}

function redrawPeople(peopleNames) {
   document.getElementById("identity").value=peopleNames;
}

function sendMessage(type, msg) {
    var msg = {
               'type': type,
               'data' : msg };
    socket.emit('request', msg);
}

function createSocket(wesocket_url) {
    socket = io.connect(wesocket_url);

    sendMessage("GETNAMES_REQ", name);
    socket.on('response',function(data){
        if (data.code == '200'){
            redrawPeople(data.msg);
        }
        else{
            alert('ERROR:' + data.msg);
        }
    });

}
var left,right,center;
function createSocket2(address) {
    var numConnect = 0;
    console.log("createSocket");
    socket = new WebSocket(address);
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {
        console.log("On open");
        socket.send(JSON.stringify({'type': 'CONNECT_REQ'}));
        $("#trainingStatus").html("Recognizing.");
    }
    socket.onmessage = function(e) {
        console.log(e);
        j = JSON.parse(e.data)
        if (j.type == "CONNECT_RESP") {
            if (numConnect >= 10) {
                sendMessage("LOADNAME_REQ", "");
            } else {
                numConnect ++;
                socket.send(JSON.stringify({'type': 'CONNECT_REQ'}));
            }
        } else if (j.type == "INITCAMERA") {
                initCamera();
                createCacheConvas();
                processFrameLoop();
        } else if (j.type == "INITVIDEO") {
                initVideo();
        } else if (j.type == "LOADNAME_RESP") {
        } else if (j.type == "RECGFRAME_RESP") {
            recgRet = j['msg'];
        } else if (j.type == "TRAINSTART_RESP") {
            $("#trainingStatus").html("Recoding.");
            showProcessBars();
            left = right = center = 0;
        } else if (j.type == "TRAINFINISH_RESP") {
            hideProcessImg();
            $("#trainingStatus").html("Recognizing.");
        } else if (j.type == "ERROR_MSG") {
            alert(j['msg']);
        } else if (j.type == "TRAINPROCESS") {
            setProcessBards(j['msg']['Left'], j['msg']['Right'], j['msg']['Center'])
            if (j['msg']['Left'] >= 15 && j['msg']['Right'] >= 15 &&  j['msg']['Center'] >= 15) {
                hideProcessBars();
                showProcessImg();
                $("#trainingStatus").html("Training.");
                sendMessage("RECODFINISH_REQ", "");
            }

        } else {
            console.log("Unrecognized message type: " + j.type);
        }
    }
    socket.onerror = function(e) {
        console.log("Error creating WebSocket connection to " + address);
        console.log(e);
    }
    socket.onclose = function(e) {
        if (e.target == socket) {
            $("#trainingStatus").html("Disconnected.");
        }
    }
}

