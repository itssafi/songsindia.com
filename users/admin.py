"""Integrate with admin module."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from users.models import User
from music.models import Album, Song
from users.forms import UserForm


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    """Define admin model for custom User model with no email field."""
    # form = UserForm
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


admin.site.register(Album)
admin.site.register(Song)

if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, EmailUserAdmin)


def __email_unicode__(self):
    return self.email
