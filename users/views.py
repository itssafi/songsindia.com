import random, string, logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View, RedirectView
# from django.contrib.auth.models import User
from django.conf import settings
from users.models import User
from users.forms import UserForm, UserUpdateForm
from music.utils.messaging import SendEmailMessage, SendTextMessage
from music.utils.forms.custom_forms import PasswordResetForm, ChangePasswordForm, LoginForm, ChangePasswordFormUnAuth
from music.utils.utils import sms_message, register_email_body, forget_pass_email_body, change_pass_email_body

log = logging.getLogger(__name__)


class UserFormView(View):
    form_class = UserForm
    template_name = 'users/registration_form.html'
    email = SendEmailMessage(settings.EMAIL_HOST, settings.EMAIL_PORT,
                             settings.EMAIL_HOST_NAME, settings.EMAIL_HOST_PASSWORD)

    # Display blank form
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('music:index')

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Cleaned normalized data
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password1']
            phone_number = form.cleaned_data['phone_number']
            user.set_password(password)
            user.save()
            log.debug("'{0}' registered successfully.".format(email))

            sms = SendTextMessage(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            sms_code = sms.validate_phone_number(phone_number)

            if sms_code:
                log.info('Phone verification for {0}: {1}'.format(phone_number, sms_code))
                return render(request, self.template_name,
                    {'form': form, 'phone_code': sms_code})
            # Formatting text message data
            message = sms_message.format(
                form.cleaned_data['first_name'], request.get_host())
            # Sending text message to proviede phone number
            sms.send_sms(settings.FROM_SMS_NO, phone_number, message)
            # Formatting email data
            subject = 'Welcome to - SongsIndia.com'
            email_body = register_email_body.format(
                    form.cleaned_data['first_name'], email, password)
            # Sending email to proviede email ID
            self.email.send_email(form.cleaned_data['email'], subject, email_body)
            # Returns User objects if credentials are correct
            user = authenticate(username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('music:index')

        return render(request, self.template_name, {'form': form})


class UserUpdateView(View):
    form_class = UserUpdateForm
    template_name = 'users/update_form.html'
    email = SendEmailMessage(settings.EMAIL_HOST, settings.EMAIL_PORT,
                             settings.EMAIL_HOST_NAME, settings.EMAIL_HOST_PASSWORD)

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        user = User.objects.get(email=request.user)
        form = self.form_class(instance=user)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        form = self.form_class(request.POST or None, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = form.save(commit=False)
            user.set_password(password)
            user.save()
            log.debug("'{0}' updated successfully.".format(email))

            # user = authenticate(username=email, password=password)
            # if user is not None:
            #     if user.is_active:
            #         login(request, user)

            return render(request, self.template_name,
                          {'form': form, 'success_msg': "Your account '{}' is updated successfully.".format(email)})

        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    form_class = LoginForm
    login_template = 'users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('music:index')

        form = self.form_class(None)
        return render(request, self.login_template, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    log.debug("'{0}' logged in successfully.".format(email))
                    return redirect('music:index')
                else:
                    return render(request, self.login_template,
                                  {'form': form,
                                   'error_message': 'Your account has been disabled. ' \
                                   'Please reset the password with the details sent in your ' \
                                   'email associated with the account or click forget password.'})
            else:
                return render(request, self.login_template,
                              {'form': form, 'error_message': 'Login failed... username or password is incorrect.'})

        return render(request, self.login_template, {'form': form})

class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/users/login/'

    def get(self, request, *args, **kwargs):
        log.debug("'{0}' logged out successfully.".format(request.user))
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class ForgetPasswordView(View):
    form_class = PasswordResetForm
    template_name = 'users/forget_password.html'
    email = SendEmailMessage(settings.EMAIL_HOST, settings.EMAIL_PORT,
                             settings.EMAIL_HOST_NAME, settings.EMAIL_HOST_PASSWORD)

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            if not user:
                context = {'form': form,
                           'error_message': 'Username does not exists.'}
                return render(request, self.template_name, context)

            if user.phone_number != phone_number:
                context = {'form': form,
                           'error_message': 'Provided email address does not matching with the phone number.'}
                return render(request, self.template_name, context)

            temp_pass = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
            user.set_password(temp_pass)
            user.is_active = False
            user.save()
            log.debug("'{0}' requsted to reset password.".format(request.user))
            # Formatting email data to Reset password
            subject = 'Reset Password - SongsIndia.com'
            email_body = forget_pass_email_body.format(
                user.first_name, user.email, temp_pass, request.get_host())

            success_message = 'An email has been sent to {0}. Please check its inbox to continue '\
                              'reset your password.'.format(email)
            context = {'form': form,
                       'success_message': success_message
                       }
            self.email.send_email(form.cleaned_data['email'], subject, email_body)
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(View):
    form_class = ChangePasswordForm
    template_name = 'users/change_password.html'
    email = SendEmailMessage(settings.EMAIL_HOST, settings.EMAIL_PORT,
                             settings.EMAIL_HOST_NAME, settings.EMAIL_HOST_PASSWORD)

    def get(self, request):
        if not request.user.is_authenticated:
            self.form_class = ChangePasswordFormUnAuth
            self.template_name = 'users/change_password1.html'
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if not request.user.is_authenticated:
            self.form_class = ChangePasswordFormUnAuth
            self.template_name = 'users/change_password1.html'

        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            current_password = form.cleaned_data['password']
            new_password = form.cleaned_data['password1']
            if not request.user.is_authenticated:
                email = form.cleaned_data['email']
                user = User.objects.get(email=email)
                auth = authenticate(username=email, password=current_password)
            else:
                user = User.objects.get(email=request.user)
                auth = authenticate(username=request.user, password=current_password)
            if not auth:
                context = {'form': form,
                           'error_message': 'Current password is incorrect.'}
                return render(request, self.template_name, context)

            user.set_password(new_password)
            user.is_active = True
            user.save()
            log.debug("'{0}' is changed password successfully.".format(request.user))

            subject = 'Password Changed Successfully - SongsIndia.com'
            email_body = change_pass_email_body.format(user.first_name,
                user.email, new_password, request.get_host())
            self.email.send_email(user.email, subject, email_body)
            return redirect('users:login')
        return render(request, self.template_name, {'form': form})
