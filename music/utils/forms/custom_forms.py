import re
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class PasswordResetForm(forms.Form):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=50)))


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
 
    def clean_password2(self):
        if self.cleaned_data.has_key('password1'):
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))


class ChangePasswordFormUnAuth(ChangePasswordForm):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))

    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            raise forms.ValidationError(_("The username don't exist. Please retry with correct one."))
        return self.cleaned_data['username']


class LoginForm(forms.Form):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True,
                                max_length=15, placeholder='Enter username')))
    password = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                    max_length=30, render_value=False,
                                    placeholder='Enter password')))
