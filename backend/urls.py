from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.welcome,name='welcome'),
    path('home/', views.home, name='home'),
    path('results/', views.results,name='results'),
    path('about/', views.about,name='about'),
    path('contact/', views.contact,name='contact'),
    path('signin/', views.signin,name='signin'),
    path('signup/', views.signup,name='signup'),
    path('h_contact/', views.h_contact,name='h_contact'),
    path('h_about/', views.h_about,name='h_about'),
    path('tnc/', views.tnc,name='tnc'),
    path('pr/', views.pr,name='pr'),
    path('logout/',views.logout_view,name='logout')
]