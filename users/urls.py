from django.urls import path
from users import views

urlpatterns = [
    path('register/', views.register_view, name='auth_register'),
    path('login/', views.login_view, name='auth_login'),
    path('profile/', views.profile_view, name='auth_profile'),
]
