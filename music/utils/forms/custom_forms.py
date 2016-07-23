import re
from django import forms
from django.utils.translation import ugettext_lazy as _


class PasswordResetForm(forms.Form):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=50)))


class ChangePasswordForm(forms.Form):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))
    password = forms.CharField(label=_("Current password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
    password1 = forms.CharField(label=_("New Password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
    password2 = forms.CharField(label=_("New Password confirmation"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
 
    def clean_password2(self):
        pattern = '^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=]).*$'
        if not re.findall(pattern, self.cleaned_data['password1']):
            err_text = """Your password must follow all of these:\n\t
            1. At least 8 characters.\n\t
            2. Uppercase letter.\n\t
            3. Lowercase letter.\n\t
            4. Numeric.\n\t
            5. Any of the special characters: ! @ # $ % ^ * + = """
            raise forms.ValidationError(_(err_text))

        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data['password1']


class LoginForm(forms.Form):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(attrs=dict(required=True, max_length=15)))
    password = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
