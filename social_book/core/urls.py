from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    
    # user accounts 
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),
    path('settings', views.settings, name='settings'),
    
    #posts
    path('upload', views.upload, name='upload'),
    
    #like-post
    path('like-post', views.like_post, name='like-post'),
    
]