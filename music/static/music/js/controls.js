var track = document.getElementById('track');
var playButton = document.getElementById('playButton');
var muteButton = document.getElementById('muteButton');
var vPlus = document.getElementById('volumePlus');
var vMinus = document.getElementById('volumeMinus');
var backwardButton = document.getElementById('backwardButton');
var forwardButton = document.getElementById('forwardButton');

var fullDuration = document.getElementById('fullDuration');
var currentTime = document.getElementById('currentTime');

var barSize = 640;
var bar = document.getElementById('defaultBar');
var progressBar = document.getElementById('progressBar');

playButton.addEventListener('click', playOrPause, false);
muteButton.addEventListener('click', muteOrSpeaker, false);
bar.addEventListener('click', clickedBar, false);
vPlus.addEventListener('click', volumePlus, false);
vMinus.addEventListener('click', volumeMinus, false);
backwardButton.addEventListener('click', previousSong, false);
forwardButton.addEventListener('click', nextSong, false);

track.addEventListener('loadeddata', function(){
    fullDuration.innerHTML = pad(parseInt(track.duration/60)) + ':' + pad(parseInt(track.duration%60));
});

function playOrPause() {
    if(!track.paused && !track.ended){
        track.pause();
        playButton.style.backgroundImage = 'url(/static/play.png)';
        window.clearInterval(updateTime);
    }
    else {
        track.play();
        track.volume = 0.7;
        playButton.style.backgroundImage = 'url(/static/pause.png)';
        updateTime = setInterval(update, 500);
    }
}

function muteOrSpeaker() {
    if(track.muted == true){
        track.muted = false;
        muteButton.style.backgroundImage = 'url(/static/speaker.png)';
    }
    else {
        track.muted = true;
        muteButton.style.backgroundImage = 'url(/static/mute.png)';
    }
}

function update() {
    if(!track.ended){
        var playedMinutes = pad(parseInt(track.currentTime/60));
        var playedSeconds = pad(parseInt(track.currentTime%60));
        currentTime.innerHTML = playedMinutes + ':' + playedSeconds;
        var size = parseInt(track.currentTime*barSize/track.duration);
        progressBar.style.width = size + 'px';
    }
    else {
        currentTime.innerHTML = "00:00";
        playButton.style.backgroundImage = 'url(/static/play.png)';
        progressBar.style.width = '0px';
        window.clearInterval(updateTime);
    }
}

function clickedBar(e) {
    if(!track.ended){
        var mouseX = e.pageX - bar.offsetLeft;
        track.currentTime = mouseX*track.duration/barSize;
        progressBar.style.width = mouseX + 'px';
    }
}

function pad(d) {
    return (d < 10) ? '0' + d.toString() : d.toString();
}

function volumePlus() {
    if(track.muted == true) {
        track.muted = false;
        muteButton.style.backgroundImage = 'url(/static/speaker.png)';
        console.log("DEBUG: Audio volume: " + track.volume);
    }
    else if(track.muted == false && track.volume < 1.0) {
        track.volume += 0.1;
        console.log("DEBUG: Audio volume: " + track.volume);
    }
    else {
        track.volume += 0.1;
        console.log("DEBUG: Audio volume: " + track.volume);
    }
}

function volumeMinus() {
    if(track.muted == false && track.volume > 0.1) {
        track.volume -= 0.1;
    }
    else if(track.muted == false && track.volume < 0.1) {
        track.volume = 0.0;
        track.muted = true;
        muteButton.style.backgroundImage = 'url(/static/mute.png)';
    }
    else {
        track.volume -= 0.1;
    }
}

function postForm(params) {
    var form = document.getElementById("form");
    for (var key in params) {
        if (params.hasOwnProperty(key)) {
            var hiddenField = document.getElementById(key);
            console.log(key + ':' + params[key]);
            hiddenField.value = params[key];
        }
    }
    form.submit();
}

function previousSong() {
    var audio_url = document.getElementById("previous_song_url").value;
    var title = document.getElementById("previous_song_title").value;
    var artist = document.getElementById("previous_song_artist").value;
    var album_title = document.getElementById("previous_album_title").value;

    postForm({"audio_url": audio_url, "song_title": title, "artist": artist, "album_title": album_title});
    window.onload = function() {
        playOrPause();
    }
}

function nextSong() {
    var audio_url = document.getElementById("next_song_url").value;
    var title = document.getElementById("next_song_title").value;
    var artist = document.getElementById("next_song_artist").value;
    var album_title = document.getElementById("next_album_title").value;

    postForm({"audio_url": audio_url, "song_title": title, "artist": artist, "album_title": album_title});
    window.onload = function() {
        playOrPause();
    }
}
