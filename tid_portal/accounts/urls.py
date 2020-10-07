from django.contrib.auth import views
from django.urls import path
from .views import change_password


urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('password_change/', change_password, name='password_change'),
]

