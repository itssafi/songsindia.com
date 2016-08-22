
var AlbumsListPage = {
	init: function() {
		this.$container = $('.albums-container');
		this.render();
		this.bindEvents();
	},

	render: function() {

	},

	bindEvents: function() {
		$('.btn-favorite', this.$container).on('click', function(e) {
			e.preventDefault();

			var self = $(this);
			var url = $(this).attr('href');
			$.getJSON(url, function(result) {
				if (result.success) {
					$('.glyphicon-star', self).toggleClass('active');
				}
			});

			return false;
		});
	}
};

var SongsListPage = {
	init: function() {
		this.$container = $('.songs-container');
		this.render();
		this.bindEvents();
	},

	render: function() {

	},

	bindEvents: function() {
		$('.btn-favorite', this.$container).on('click', function(e) {
			e.preventDefault();

			var self = $(this);
			var url = $(this).attr('href');
			$.getJSON(url, function(result) {
				if (result.success) {
					$('.glyphicon-star', self).toggleClass('active');
				}
			});

			return false;
		});
	}
};

// $(document).ready(function() {
// 	AlbumsListPage.init();
// 	SongsListPage.init();
// });

function IsEmpty(){
    username = document.getElementById("id_username").value
	password = document.getElementById("id_password").value
    if(username.length == 0 && password.length == 0){
        document.getElementById("errorMsgUname").innerHTML = "Username is required";
        document.getElementById("errorMsgPwd").innerHTML = "Password is required";
        document.getElementById("id_username").focus()
        return false
    }
    if(username.length == 0 && password.length != 0){
        document.getElementById("errorMsgPwd").innerHTML = "";
        document.getElementById("errorMsgUname").innerHTML = "Username is required";
        document.getElementById("id_username").focus()
        return false
    }
    if(username.length != 0 && password.length == 0){
        document.getElementById("errorMsgUname").innerHTML = "";
        document.getElementById("errorMsgPwd").innerHTML = "Password is required";
        document.getElementById("id_password").focus()
        return false
    }
    else{
        document.getElementById("errorMsgUname").innerHTML = "";
        document.getElementById("errorMsgPwd").innerHTML = "";
        return true
    }
}
