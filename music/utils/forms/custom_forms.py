from django import forms


class PasswordResetForm(forms.Form):
    username = forms.CharField(max_length=15)
    email_address = forms.EmailField()


class ChangePasswordForm(forms.Form):
    username = forms.CharField(max_length=15)
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
