var track = document.getElementById('track');
var playButton = document.getElementById('playButton');
var muteButton = document.getElementById('muteButton');

var fullDuration = document.getElementById('fullDuration');
var currentTime = document.getElementById('currentTime');

var minutes = pad(parseInt(track.duration/60));
var seconds = pad(parseInt(track.duration%60));

var barSize = 640;
var bar = document.getElementById('defaultBar');
var progressBar = document.getElementById('progressBar');

fullDuration.innerHTML = minutes + ':' + seconds;

playButton.addEventListener('click', playOrPause, false);
muteButton.addEventListener('click', muteOrSpeaker, false);
bar.addEventListener('click', clickedBar, false);

function playOrPause() {
    if(!track.paused && !track.ended){
        track.pause();
        playButton.style.backgroundImage = 'url(../../play.png)';
        window.clearInterval(updateTime);
    }
    else {
        track.play();
        playButton.style.backgroundImage = 'url(../../pause.png)';
        updateTime = setInterval(update, 500);
    }
}

function muteOrSpeaker() {
    if(track.muted == true){
        track.muted = false;
        muteButton.style.backgroundImage = 'url(../../speaker.png)';
    }
    else {
        track.muted = true;
        muteButton.style.backgroundImage = 'url(../../mute.png)';
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
        playButton.style.backgroundImage = 'url(../../play.png)';
        progressBar.style.width = '0px';
        window.clearInterval(updateTime);
    }
}

function clickedBar(e) {
    if(!track.ended){
        var mouseX = e.pageX - bar.offsetLeft;
        track.currentTime = mouseX*track.duration/barSize;
        progressBar.style.width = mouseX + 'px'
    }
}

function pad(d) {
    return (d < 10) ? '0' + d.toString() : d.toString();
}

function playMusic(audioUrl) {
    return audioUrl
}
