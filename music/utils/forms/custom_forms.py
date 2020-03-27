from django import forms
from django.utils.translation import ugettext_lazy as _
from users.models import User


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=50)))
    phone_number = forms.CharField(label=_("Phone number"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))


class ChangePasswordForm(forms.Form):
    password = forms.CharField(label=_("Current password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
    pattern = r'^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=]).*$'
    err_text = """Your password must have all of these:\n\t
            1. At least 8 characters.\n\t
            2. Uppercase letter.\n\t
            3. Lowercase letter.\n\t
            4. Numeric.\n\t
            5. Any of the special characters: ! @ # $ % ^ * + = """
    password1 = forms.RegexField(label=_("New Password"), regex=pattern,
                                 error_messages={'invalid': _(err_text)},
                                 widget=forms.PasswordInput(attrs=dict(required=True,
                                                                       max_length=30,
                                                                       render_value=False)))
    password2 = forms.CharField(label=_("New Password Confirmation"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))

    def clean_password1(self):
        if self.cleaned_data.get('password1'):
            if self.cleaned_data.get('password') == self.cleaned_data.get('password1'):
                raise forms.ValidationError(_("The new password can't be same with the current password."))

    def clean_password2(self):
        if self.cleaned_data.get('password1'):
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The new password and confirm new password didn't match."))


class ChangePasswordFormUnAuth(ChangePasswordForm):
    email = forms.EmailField(label=_("Email ID"),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=15)))

    def clean_email(self):
        try:
            User.objects.get(email__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            raise forms.ValidationError(_("The email id don't exist. Please retry with correct one."))
        return self.cleaned_data['email']


class LoginForm(forms.Form):
    email = forms.CharField(label=_("Email"),
                               widget=forms.TextInput(attrs=dict(required=True,
                                max_length=15, placeholder='Enter email id')))
    password = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                    max_length=30, render_value=False,
                                    placeholder='Enter password')))
