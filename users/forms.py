from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _
from users.models import User


class UserForm(UserCreationForm):
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True,
                                max_length=50,  placeholder='Enter your Email ID')))
    first_name = forms.CharField(label=_('First name'),
                                 widget=forms.TextInput(attrs=dict(required=True,
                                    max_length=30, placeholder='First name')))
    last_name = forms.CharField(label=_('Last name'),
                                widget=forms.TextInput(attrs=dict(required=True,
                                    max_length=30, placeholder='Last name')))
    pattern = r'^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=]).*$'
    err_text = """Your password must have all of these:\n\t
            1. At least 8 characters.\n\t
            2. Uppercase letter.\n\t
            3. Lowercase letter.\n\t
            4. Numeric.\n\t
            5. Any of the special characters: ! @ # $ % ^ * + = """
    phone_number = forms.RegexField(label=_("Phone number"),
                                    regex=r'^([+][0-9]{1,3})([0-9]{10,11})$',
                                    widget=forms.TextInput(attrs=dict(required=True,
                                        max_length=15, placeholder='+910123456789')),
                                    error_messages={'invalid': _(
                                        "Phone number must be entered with country code. Up to 15 digits allowed.")})
    password1 = forms.RegexField(label=_("Password"), regex=pattern,
                                 error_messages={'invalid': _(err_text)},
                                 widget=forms.PasswordInput(attrs=dict(required=True,
                                                                       max_length=30,
                                                                       render_value=False,
                                                                        placeholder='Password')))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False,
                                                                       placeholder='Password Confirmation')))

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password1']

    def clean_password2(self):
        if self.cleaned_data.get('password1'):
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
            return self.cleaned_data['password1']

    def clean_email(self):
        try:
            User.objects.get(email__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email'].lower()
        raise forms.ValidationError(_("The email address already used. Please try another one."))

    def clean_phone_number(self):
        try:
            User.objects.get(phone_number__iexact=self.cleaned_data['phone_number'])
        except User.DoesNotExist:
            return self.cleaned_data['phone_number']
        raise forms.ValidationError(_("The phone number already used. Please try another one."))

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserUpdateForm(UserForm):

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields.pop('password2')
        self.fields['email'].widget.attrs['readonly'] = True
        password = forms.CharField(label=_("Password"),
                                    widget=forms.PasswordInput(attrs=dict(required=True,
                                                                          max_length=30, render_value=False,
                                                                          placeholder='Enter password')))
        self.fields['password1'] = password

    def clean_email(self):
        return self.cleaned_data.get('email')

    def clean_phone_number(self):
        try:
            user = User.objects.get(email=self.cleaned_data.get('email'))
        except User.DoesNotExist:
            raise forms.ValidationError(_("The user doesn't exists."))

        if user.phone_number != self.cleaned_data.get('phone_number'):
            try:
                User.objects.get(email__iexact=self.cleaned_data['phone_number'])
            except User.DoesNotExist:
                return self.cleaned_data['phone_number'].lower()
            raise forms.ValidationError(_("The phone number already used. Please try another one."))
        return self.cleaned_data['phone_number']

    def clean_password1(self):
        if not authenticate(username=self.cleaned_data.get('email'), password=self.cleaned_data.get('password1')):
            raise forms.ValidationError(_("The provided password didn't match. Please try with correct one."))

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        password = self.cleaned_data["password1"]
        user.set_password(password)
        if commit:
            user.save()
        return user
