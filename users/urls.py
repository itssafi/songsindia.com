from django.conf.urls import url
from users import views

app_name = 'users'

urlpatterns = [
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    url(r'^update/$', views.UserUpdateView.as_view(), name='update'),
    url(r'^login/$', views.UserLoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^forget-password/$', views.ForgetPasswordView.as_view(), name='forget-password'),
    url(r'^change-password/$', views.ChangePasswordView.as_view(), name='change-password'),
]
