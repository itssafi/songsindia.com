import random, string, os
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.utils.http import is_safe_url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View, FormView, RedirectView
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Album, Song
from .forms import UserForm, AlbumForm, SongForm
from utils.forms.custom_forms import PasswordResetForm, ChangePasswordForm, LoginForm


class IndexView(View):
    template_name = 'music/index.html'

    def get(self, request):
        if not request.user.is_authenticated():
            return render(request, 'music/home.html')

        albums = Album.objects.filter(user=request.user)
        song_results = Song.objects.all()
        query = request.GET.get('search')
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                request.session['query'] = query
                return render(request, self.template_name,
                              {'song_results': song_results})
        return render(request, self.template_name, {'albums': albums})

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
            for album in Album.objects.filter(user=self.request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
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
            for album in Album.objects.filter(user=self.request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
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
        return render(request, 'music/songs.html', context)


class DetailView(View):
    template_name = 'music/detail.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id, user=request.user)
        return render(request, self.template_name, {'album': album})

    def post(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id, user=request.user)
        context = {
            'album': album,
            'audio': str(self.request.POST.get('audio_url')),
            'song_title': str(self.request.POST.get('song_title')),
            'artist': str(self.request.POST.get('artist')),
            'album_title': str(self.request.POST.get('album_title'))
        }
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
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in settings.IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, self.template_name, context)
            album.save()
            albums = Album.objects.filter(user=request.user).order_by('album_title')
            return render(request, 'music/index.html', {'albums': albums})

        return render(request, self.template_name, {'form': form})


class AlbumUpdateView(View):
    template_name = 'music/album_update_form.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, id=album_id)
        form = AlbumForm(instance=album)
        return render(request, self.template_name, {'form': form})

    def post(self, request, album_id):
        album = get_object_or_404(Album, id=album_id, user=request.user)
        existing_logo = album.album_logo.url
        form = AlbumForm(request.POST or None, request.FILES or None, instance=album)
        if form.is_valid():
            form.save(commit=False)
            if request.FILES:
                os.system('rm -rf .%s' % existing_logo)
                file_type = album.album_logo.url.split('.')[-1]
                file_type = file_type.lower()
                if file_type not in settings.IMAGE_FILE_TYPES:
                    context = {
                        'album': album,
                        'form': form,
                        'error_message': 'Image file must be PNG, JPG, or JPEG',
                    }
                    return render(request, self.template_name, context)
            album.save()
            albums = Album.objects.filter(user=request.user)
            return render(request, 'music/index.html', {'albums': albums})

        return render(request, self.template_name, {'form': form})


class AlbumDelete(View):

    def post(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = Album.objects.get(id=album_id)
        for song in album.song_set.all():
            os.system('rm -rf .%s' % song.audio_file.url)

        os.system('rm -rf .%s' % album.album_logo.url)
        album.delete()
        albums = Album.objects.filter(user=request.user).order_by('album_title')
        return render(request, 'music/index.html', {'albums': albums})


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
            song.audio_file = request.FILES['audio_file']
            file_type = song.audio_file.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in settings.AUDIO_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Audio file must be WAV, MP3, MP4 or OGG',
                }
                return render(request, self.template_name, context)
            song.save()
            return render(request, 'music/detail.html', {'album': album})
        context = {
            'form': form
        }
        return render(request, 'music/song_form.html', context)


class SongDelete(View):

    def post(self, request, album_id, song_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        album = get_object_or_404(Album, pk=album_id)
        song = Song.objects.get(pk=song_id)
        os.system('rm -rf .%s' % song.audio_file.url)
        song.delete()
        return render(request, 'music/detail.html', {'album': album})


class SongFavoriteView(View):

    def post(self, request, filter_by):
        if not request.user.is_authenticated():
            return redirect('music:login')
        song_ids = []
        albums = Album.objects.filter(user=self.request.user)
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
                return render(request, 'music/index.html',
                              {'albums': albums,
                               'filter_by': filter_by,
                               'error_message': 'Song does not exists'})
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        if template == 'songs':
            if filter_by == 'all':
                songs = Song.objects.filter(pk__in=song_ids)
            else:
                songs = Song.objects.filter(Q(pk__in=song_ids) & Q(is_favorite=True))
            return render(request, 'music/songs.html',
                          {'all_songs': songs,
                           'filter_by': filter_by})
        else:
            album = get_object_or_404(Album, pk=song.album_id)
            return render(request, 'music/detail.html',
                          {'album': album, 'filter_by': filter_by})


class AlbumFavoriteView(View):

    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return redirect('music:login')

        albums = Album.objects.filter(user=request.user)
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
                'error_message': 'Album does not exists.',
            }
            return render(request, 'music/index.html', context)
        else:
            return render(request, 'music/index.html', {'albums': albums})


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
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            # Returns User objects if credentials are correct
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # send_mail('Welcome to SongsIndia.com', 'Mail body', settings.EMAIL_HOST_NAME,
                    #           [form.email], fail_silently=True)
                    return redirect('music:index')
        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    form_class = LoginForm
    login_template = 'music/login.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.login_template, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    albums = Album.objects.filter(user=request.user)
                    return render(request, 'music/index.html',
                                  {'form': form, 'albums': albums})
                else:
                    return render(request, self.login_template,
                                  {'form': form, 'error_message': 'Your account has been disabled'})
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
        auth_logout(request)
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
            email = form.cleaned_data['email_address']
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

            # if not user.is_active:
            #     context = {'form': form,
            #                'error_message': 'Your account has been disabled'}
            #     return render(request, self.template_name, context)

            temp_pass = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
            user.set_password(temp_pass)
            user.is_active = False

            email_body = """Hello {0},\n\nYour Songs India credentials:\n\n\t
            Username: {1}\n\tTemporary Password: {2}\n\n
            Please <a href="{3}/music/change-password/">click here</a>
            to reset your password\n\n\n\nRegards,\nSongsIndia Team""".format(
                user.first_name, user.username, temp_pass, self.request.get_host())

            # email_body = """<p>Hello {0}, <br/><br/>Your Songs India credentials:<br/><br/>
            # Username: {1}<br/>Temporary Password: {2}<br/><br/>
            # Please <a href="{3}/music/change-password/">click here</a>
            # to reset your password<br/><br/><br/><br/>Regards,<br/>SongsIndia Team</p>""".format(
            #     user.first_name, user.username, temp_pass, self.request.get_host())
            
            subject = 'Reset Password - SongsIndia.com'
            # send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL,
            #           [email], fail_silently=False)
            success_message = 'An email has been sent to {0}. Please check its inbox to continue '\
                              'reset your password({1}).'.format(email, temp_pass)
            context = {'form': form,
                       'success_message': email_body
                       }
            user.save()
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(View):
    form_class = ChangePasswordForm
    template_name = 'music/change_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            username = form.cleaned_data['username']
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            if not User.objects.filter(username=username):
                context = {'form': form,
                           'error_message': 'Username does not exists.'}
                return render(request, self.template_name, context)
            user = authenticate(username=username, password=current_password)
            if not user:
                context = {'form': form,
                           'error_message': 'Current password is incorrect.'}
                return render(request, self.template_name, context)

            if new_password != confirm_password:
                context = {'form': form,
                           'error_message': 'Password mis-match.'}
                return render(request, self.template_name, context)
            user.set_password(new_password)
            user.is_active = True
            context = {'success_message':
                       'Password has been changed successfully. Please login with the changed password.'}
            user.save()
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})


class LoginView(FormView):
     """
     Provides the ability to login as a user with a username and password
     """
     template_name = 'music/login.html'
     success_url = '/music/'
     form_class = AuthenticationForm
     redirect_field_name = REDIRECT_FIELD_NAME

     @method_decorator(sensitive_post_parameters('password'))
     @method_decorator(csrf_protect)
     @method_decorator(never_cache)
     def dispatch(self, request, *args, **kwargs):
         # Sets a test cookie to make sure the user has cookies enabled
         request.session.set_test_cookie()

         return super(LoginView, self).dispatch(request, *args, **kwargs)

     def form_valid(self, form):
         auth_login(self.request, form.get_user())

         # If the test cookie worked, go ahead and
         # delete it since its no longer needed
         if self.request.session.test_cookie_worked():
             self.request.session.delete_test_cookie()

         return super(LoginView, self).form_valid(form)

     def get_success_url(self):
         redirect_to = self.request.POST.get(self.redirect_field_name)
         if not is_safe_url(url=redirect_to, host=self.request.get_host()):
             redirect_to = self.success_url
         return redirect_to
