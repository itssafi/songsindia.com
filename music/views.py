import random, string, os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View, RedirectView
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
from .models import Album, Song
from .forms import UserForm, AlbumForm, SongForm, AlbumFormUpdate
from utils.forms.custom_forms import PasswordResetForm, ChangePasswordForm, LoginForm, ChangePasswordFormUnAuth
from utils.send_email import send_email
from utils.send_sms import SendTextMessage


class HomeView(View):
    template_name = 'music/home.html'

    def get(self, request):
        albums = Album.objects.all().order_by('album_title')
        query = request.GET.get('search')
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
        if not request.user.is_authenticated():
            return render(request, self.template_name,
                {'albums': albums, 'is_authenticated': False})
        return render(request, self.template_name,
            {'albums': albums, 'is_authenticated': True})

class IndexView(View):
    template_name = 'music/index.html'

    def get(self, request):
        albums = Album.objects.all().order_by('album_title')
        query = request.GET.get('search')
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
        if not request.user.is_authenticated():
            return render(request, 'music/home.html', {'albums': albums})

        user = get_object_or_404(User, username=request.user)
        song_results = Song.objects.all()
        query = request.GET.get('search')
        if query:
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                request.session['query'] = query
                return render(request, self.template_name,
                              {'song_results': song_results})
        return render(request, self.template_name,
                      {'albums': albums, 'user_name': user.first_name})

    def post(self, request):
        if not request.user.is_authenticated():
            return redirect('music:login')

        query = request.session['query']
        if query:
            song_results = Song.objects.all()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                context = {
                    'song_results': song_results,
                    'audio': str(self.request.POST.get('audio_url')),
                    'song_title': str(self.request.POST.get('song_title')),
                    'artist': str(self.request.POST.get('artist')),
                    'album_title': str(self.request.POST.get('album_title'))
                }
                return render(request, self.template_name, context)


class SongView(View):

    def get(self, request, filter_by):
        if not self.request.user.is_authenticated():
            return redirect('music:login')
        try:
            song_ids = []
            for album in Album.objects.all():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                user_albums = Album.objects.filter(user=request.user)
                users_songs = users_songs.filter(Q(is_favorite=True) & Q(album__in=user_albums))
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'all_songs': users_songs,
            'filter_by': filter_by,
        })

    def post(self, request, filter_by):
        if not self.request.user.is_authenticated():
            return redirect('music:login')

        try:
            song_ids = []
            for album in Album.objects.all():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                user_albums = Album.objects.filter(user=request.user)
                users_songs = users_songs.filter(Q(is_favorite=True) & Q(album__in=user_albums))
        except Album.DoesNotExist:
            users_songs = []

        context = {
            'all_songs': users_songs,
            'filter_by': filter_by,
            'audio': str(self.request.POST.get('audio_url')),
            'song_title': str(self.request.POST.get('song_title')),
            'artist': str(self.request.POST.get('artist')),
            'album_title': str(self.request.POST.get('album_title'))
        }
        context = select_next_pre_song(users_songs, context)
        return render(request, 'music/songs.html', context)


class DetailView(View):
    template_name = 'music/detail.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            album = get_object_or_404(Album, id=album_id)
            return render(request, 'music/detail_visitor.html',
                {'album': album, 'is_authenticated': False})

        album = get_object_or_404(Album, id=album_id)
        return render(request, self.template_name,
            {'album': album, 'is_authenticated': True})

    def post(self, request, album_id):
        context = {
            'audio': str(self.request.POST.get('audio_url')),
            'song_title': str(self.request.POST.get('song_title')),
            'artist': str(self.request.POST.get('artist')),
            'album_title': str(self.request.POST.get('album_title')),
        }
        if not request.user.is_authenticated():
            album = get_object_or_404(Album, id=album_id)
            context['album'] = album
            context['is_authenticated'] = False
            context = select_next_pre_song(album.song_set.all(), context)
            return render(request, 'music/detail_visitor.html', context)

        album = get_object_or_404(Album, id=album_id)
        context['album'] = album
        context['is_authenticated'] = True
        context = select_next_pre_song(album.song_set.all(), context)
        return render(request, self.template_name, context)


class AlbumCreate(View):
    form_class = AlbumForm
    template_name = 'music/album_form.html'

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated():
            return redirect('music:login')
        
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated():
            return redirect('music:login')

        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.save()
            albums = Album.objects.all().order_by('album_title')
            return render(request, 'music/index.html',
                {'albums': albums, 'user_name': album.user.first_name})

        return render(request, self.template_name, {'form': form})


class AlbumUpdateView(View):
    template_name = 'music/album_update_form.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id)
        form = AlbumFormUpdate(instance=album)
        return render(request, self.template_name, {'form': form})

    def post(self, request, album_id):
        album = get_object_or_404(Album, id=album_id, user=request.user)
        existing_logo = album.album_logo.url
        form = AlbumFormUpdate(request.POST or None, request.FILES or None, instance=album)
        if form.is_valid():
            form.save(commit=False)
            if request.FILES:
                os.system('rm -rf .%s' % existing_logo)
            album.save()
            albums = Album.objects.all().order_by('album_title')
            return render(request, 'music/index.html',
                {'albums': albums, 'user_name': album.user.first_name})

        return render(request, self.template_name, {'form': form})


class AlbumDelete(View):

    def post(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id, user=request.user)
        for song in album.song_set.all():
            os.system('rm -rf .%s' % song.audio_file.url)

        os.system('rm -rf .%s' % album.album_logo.url)
        album.delete()
        albums = Album.objects.all().order_by('album_title')
        return render(request, 'music/index.html',
            {'albums': albums, 'user_name': album.user.first_name})


class SongCreate(View):
    form_class = SongForm
    template_name = 'music/song_form.html'

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated():
            return redirect('music:login')

        form = self.form_class
        form.base_fields['album'].queryset = Album.objects.filter(user=request.user)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated():
            return redirect('music:login')
        
        form = SongForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album_id = int(request.POST.get('album'))
            album = get_object_or_404(Album, id=album_id)
            albums_songs = album.song_set.all()
            for song in albums_songs:
                if song.song_title == form.cleaned_data.get("song_title"):
                    context = {
                        'album': album,
                        'form': form,
                        'error_message': 'You already added that song',
                    }
                    return render(request, self.template_name, context)
            song = form.save(commit=False)
            song.album = album
            song.save()
            context = {
                'album': album,
                'is_authenticated': True
            }
            return render(request, 'music/detail.html', context)
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


class SongDelete(View):

    def post(self, request, album_id, song_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id)
        song = get_object_or_404(Song, id=song_id)
        os.system('rm -rf .%s' % song.audio_file.url)
        song.delete()
        return render(request, 'music/detail.html',
            {'album': album, 'is_authenticated': True})


class SongFavoriteView(View):

    def post(self, request, filter_by):
        if not request.user.is_authenticated():
            return redirect('music:login')
        song_ids = []
        albums = Album.objects.all()
        song_id = request.POST.get('song_id')
        template = request.POST.get('template')
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        songs = Song.objects.filter(pk__in=song_ids)
        song = get_object_or_404(Song, pk=song_id)
        try:
            if song.is_favorite:
                song.is_favorite = False
            else:
                song.is_favorite = True
            song.save()
        except (KeyError, Song.DoesNotExist):
            if template == 'songs':
                return render(request, 'music/songs.html',
                              {'all_songs': songs,
                               'filter_by': filter_by,
                               'error_message': 'Song does not exists'})
            else:
                return render(request, 'music/detail.html',
                              {'albums': albums,
                               'filter_by': filter_by,
                               'is_authenticated': True,
                               'error_message': 'Song does not exists'})
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        if template == 'songs':
            if filter_by == 'all':
                songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            else:
                user_albums = Album.objects.filter(user=request.user)
                songs = Song.objects.filter(Q(pk__in=song_ids) & Q(album__in=user_albums) & Q(is_favorite=True))
            return render(request, 'music/songs.html',
                          {'all_songs': songs,
                           'filter_by': filter_by})
        else:
            album = get_object_or_404(Album, pk=song.album_id)
            return render(request, 'music/detail.html',
                          {'album': album, 'filter_by': filter_by,
                           'is_authenticated': True})


class AlbumFavoriteView(View):

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        albums = Album.objects.all().order_by('album_title')
        album = get_object_or_404(Album, pk=album_id)
        try:
            if album.is_favorite:
                album.is_favorite = False
            else:
                album.is_favorite = True
            album.save()
        except (KeyError, Album.DoesNotExist):
            context = {
                'albums': albums,
                'user_name': album.user.first_name,
                'error_message': 'Album does not exists.',
            }
            return render(request, 'music/index.html', context)
        else:
            return render(request, 'music/index.html',
                {'albums': albums, 'user_name': album.user.first_name})


class UserFormView(View):
    form_class = UserForm
    template_name = 'music/registration_form.html'

    # Display blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Cleaned normalized data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            # Returns User objects if credentials are correct
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    subject = 'Welcome to - SongsIndia.com'
                    email_body = """Hello {0},<br><br>Thank you for register with our 
                    online music application.<br><br>Your login credentials:<br>
                    Username: {1}<br>Password: {2}<br><br>If you like this web site please
                    share it with you friends.<br><br><br>Thank you,<br>Songs India Team<br>""".format(
                        form.cleaned_data['first_name'], username, password)
                    send_email(settings.DEFAULT_FROM_EMAIL, settings.EMAIL_HOST_PASSWORD,
                        form.cleaned_data['email'], subject, email_body)
                    return redirect('music:index')
        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    form_class = LoginForm
    login_template = 'music/login.html'

    def get(self, request):
        if request.user.is_authenticated():
            albums = Album.objects.filter(user=request.user).order_by('album_title')
            user = get_object_or_404(User, username=request.user)
            return render(request, 'music/index.html',
                          {'albums': albums, 'user_name': user.first_name})
        form = self.form_class(None)
        return render(request, self.login_template, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            # sms = SendTextMessage(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            # res = sms.validate_phone_number(phone_number)
            # sms.send_sms(settings.FROM_SMS_NO, phone_number,
            #     'Hi {0}, Login successful.'.format(user.first_name))
            if user is not None:
                if user.is_active:
                    login(request, user)
                    albums = Album.objects.all().order_by('album_title')
                    return render(request, 'music/index.html',
                                  {'form': form, 'albums': albums, 'user_name': user.first_name})
                else:
                    return render(request, self.login_template,
                                  {'form': form,
                                   'error_message': 'Your account has been disabled. '\
                                   'Please reset the password with the details sent in your '\
                                   'email associated with the account or click forget password.'})
            else:
                return render(request, self.login_template,
                              {'form': form, 'error_message': 'Login failed... username or password is incorrect.'})

        return render(request, self.login_template, {'form': form})

class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/music/login/'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class ForgetPasswordView(View):
    form_class = PasswordResetForm
    template_name = 'music/forget_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            if not User.objects.filter(username=username):
                context = {'form': form,
                           'error_message': 'Username does not exists.'}
                return render(request, self.template_name, context)
            
            try:
                user = User.objects.get(Q(username=username) & Q(email=email))
            except User.DoesNotExist:
                context = {'form': form,
                           'error_message': 'Provided email address does not matching with the username.'}
                return render(request, self.template_name, context)

            temp_pass = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
            user.set_password(temp_pass)
            user.is_active = False
            user.save()
            subject = 'Reset Password - SongsIndia.com'
            email_body = """Hello {0},<br><br>Your Songs India credentials:<br><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Username: {1}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Temporary Password: {2}<br><br>
            Please <a href="{3}/music/change-password/">click here</a>
            to reset your password.<br><br><br>Thank you,<br>Songs India Team""".format(
                user.first_name, user.username, temp_pass, request.get_host())

            success_message = 'An email has been sent to {0}. Please check its inbox to continue '\
                              'reset your password.'.format(email)
            context = {'form': form,
                       'success_message': success_message
                       }
            send_email(settings.DEFAULT_FROM_EMAIL, settings.EMAIL_HOST_PASSWORD,
                form.cleaned_data['email'], subject, email_body)
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(View):
    form_class = ChangePasswordForm
    template_name = 'music/change_password.html'

    def get(self, request):
        if not request.user.is_authenticated():
            self.form_class = ChangePasswordFormUnAuth
            self.template_name = 'music/change_password1.html'
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if not request.user.is_authenticated():
            self.form_class = ChangePasswordFormUnAuth
            self.template_name = 'music/change_password1.html'

        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            current_password = form.cleaned_data['password']
            new_password = form.cleaned_data['password1']
            if not request.user.is_authenticated():
                username = form.cleaned_data['username']
                user = User.objects.get(username=username)
                auth = authenticate(username=username, password=current_password)
            else:
                user = User.objects.get(username=request.user)
                auth = authenticate(username=request.user, password=current_password)
            if not auth:
                context = {'form': form,
                           'error_message': 'Current password is incorrect.'}
                return render(request, self.template_name, context)
            if current_password == new_password:
                context = {'form': form,
                           'error_message': 'Current pasword and new password is same.'}
                return render(request, self.template_name, context)

            user.set_password(new_password)
            user.is_active = True
            user.save()

            subject = 'Password Changed Successfully - SongsIndia.com'
            email_body = """Hello {0},<br><br>Your password has been changed successfully.
            Your new Songs India credentials:<br><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Username: {1}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;New Password: {2}<br><br>
            Please <a href="{3}/music/login/">click here</a> 
            to login your account.<br><br><br>
            Thank You,<br>Songs India Team""".format(user.first_name,
                user.username, new_password, request.get_host())
            send_email(settings.DEFAULT_FROM_EMAIL, settings.EMAIL_HOST_PASSWORD,
                user.email, subject, email_body)
            context = {'form': LoginForm(None),
                       'success_message': 'Password has been changed successfully.'\
                       ' Please login with the changed password.'}
            return redirect('music:login')
        return render(request, self.template_name, {'form': form})


def select_next_pre_song(songs, context):
    pre_song, next_song, is_found = None, None, False
    for index, song in enumerate(songs):
        if is_found:
            context['next_song'] = song
            break
        elif song.song_title == context['song_title']:
            is_found = True
            context['previous_song'] = pre_song
            if songs.count() == index + 1:
                context['next_song'] = next_song
                break
        else:
            pre_song = song

    return context