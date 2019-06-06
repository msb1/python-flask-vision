var csocket;
var vsocket;


$(document).ready(function () {
    bsCustomFileInput.init();
});


$(document).ready(function () {
    $('a.dropdown-item.detect').on('click', function(){
        console.log("dropdown active detect mod...");
        $('a.dropdown-item.detect').removeClass('active');
        $(this).addClass('active');
    });
});


$(document).ready(function () {
    $('a.dropdown-item.source').on('click', function(){
        console.log("dropdown active source mod...");
        $('a.dropdown-item.source').removeClass('active');
        $(this).addClass('active');
    });
});

$(document).ready(function () {
    $('a.dropdown-item.classify').on('click', function(){
        console.log("dropdown active classify mod...");
        $('a.dropdown-item.classify').removeClass('active');
        $(this).addClass('active');
    });
});

$(document).ready(function () {
    $('a.dropdown-item.track').on('click', function(){
        console.log("dropdown active track mod...");
        $('a.dropdown-item.track').removeClass('active');
        $(this).addClass('active');
    });
});


$(document).ready(function(){
    
    csocket = io.connect('http://' + document.domain + ':' + location.port + '/comm');
    
    csocket.on('message', function(msg) {

        if(msg.type === 'videoInfo') {
            console.log('videoInfo: ' + msg);
            document.getElementById('fps').value = msg.fps;
            document.getElementById('delay').value = msg.delay;
            document.getElementById('fwidth').value = msg.fwidth;
            document.getElementById('fheight').value = msg.fheight;
            document.getElementById('fnumber').value = msg.fnumber;
            document.getElementById('fplay').value = msg.fplay;
        }
        else if(msg.type === 'status') {
            console.log('status: ' + msg);
            document.getElementById('messageBox').value = msg.status;
        }
        else {
            console.log(msg);
        }

    });

});


$(document).ready(function(){

    vsocket = io.connect('http://' + document.domain + ':' + location.port + '/video');
    
    vsocket.on('frame', function(img) {
        console.log(String(img.percentComplete) + '  ' + String(img.frameCtr));
        document.getElementById('cvision').src = img.image;
        var bar = document.getElementById('progress-bar');
        bar.style.setProperty('width', String(img.percentComplete) + '%');
        bar.setAttribute('aria-valuenow', String(img.percentComplete));
        bar.innerText = 'frame: ' + String(img.frameCtr);
    });

});

function play() {
    var obj = JSON.stringify({msgType : 'playerControl', selected : 'play'});
	csocket.emit('message', obj);
}

function stop() {
	var obj = JSON.stringify({msgType : 'playerControl', selected : 'stop'});
	csocket.emit('message', obj);
}

function pause() {
	var obj = JSON.stringify({msgType : 'playerControl', selected : 'pause'});
	csocket.emit('message', obj);
}

function fast() {
	var obj = JSON.stringify({msgType : 'playerControl', selected : 'fast'});
	csocket.emit('message', obj);
}

function slow() {
	var obj = JSON.stringify({msgType : 'playerControl', selected : 'slow'});
	csocket.emit('message', obj);
}

// var filename = /([^\\]+)$/.exec(fullPath)[1];

function saveFile() {
    var inFullFilePath = document.getElementById('inFile').value;
    var inFile = inFullFilePath.replace(/^.*[\\\/]/, '');
    var outFile = document.getElementById('outFile').value;
    var fpath = document.getElementById('fpath').value;
    var obj = JSON.stringify({msgType : 'ioFile', input : inFile, output: outFile, filePath: fpath});
	csocket.emit('message', obj);
}

function playVideoFile() {
    var fpath = document.getElementById('sourceInput').value;
    var obj = JSON.stringify({msgType : 'source', 'player' : 'vidfile', 'fpath': fpath});
	csocket.emit('message', obj);
}

function playYouTube() {
    var url = document.getElementById('sourceInput').value;
    var obj = JSON.stringify({msgType : 'source', 'player' : 'youtube', 'url': url});
	csocket.emit('message', obj);
}

function playWebCam() {
    var obj = JSON.stringify({msgType : 'source', 'player' : 'webcam', 'number': 0});
	csocket.emit('message', obj);
}

function detector(method) {
    console.log("detector method: " + method);
    var obj = JSON.stringify({msgType : 'detector', 'type' : method});
	csocket.emit('message', obj);
}

function tracker(method) {
    console.log("tracker method: " + method);
    var obj = JSON.stringify({msgType : 'tracker', 'type' : method});
	csocket.emit('message', obj);
}

function selectTrack() {
    console.log("select track box with mouse: ");
    var obj = JSON.stringify({msgType : 'selectTrack'});
	csocket.emit('message', obj);
}







