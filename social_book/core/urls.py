from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    
    # user accounts 
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('logout', views.logout, name='logout'),
    path('settings', views.settings, name='settings'),
    
    #profile
    path('profile/<str:pk>', views.profile, name='profile'),
    
    #follow
    path('follow', views.follow, name='follow'),
    
    #search
    path('search', views.search, name='search'),
        
    #posts
    path('upload', views.upload, name='upload'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete-post'),
    
    #like-post
    path('like-post', views.like_post, name='like-post'),
    
    # Comments
    path('add-comment', views.add_comment, name='add-comment'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete-comment'),
    path('edit-comment/<int:comment_id>/', views.edit_comment, name='edit-comment'),


]