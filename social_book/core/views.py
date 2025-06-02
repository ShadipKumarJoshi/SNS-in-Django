from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount, Comment
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from itertools import chain
import random

# Create your views here.
@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    
    user_following_list =[]
    feed = []
    
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    for users in user_following:
        user_following_list.append(users.user)
    
    # Fetch posts of followed users    
    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)
    
    # Add the logged-in user's own posts
    my_posts = Post.objects.filter(user=request.user.username)
    feed.append(my_posts)
    
    # Merge all post querysets into a single list    
    feed_list = list(chain(*feed))
    
    # Enrich posts with profile and comments
    for post in feed_list:
        post.user_profile = Profile.objects.get(user__username=post.user)
    
        post.comments = Comment.objects.filter(post=post).order_by('-created_at')

        # Attach commenter profile to each comment
        for comment in post.comments:
            comment.profile = Profile.objects.get(user=comment.user)
        
    # user suggestion starts
    all_users = User.objects.all()
    user_following_all = []
    
    for user in user_following:
        user_list =User.objects.get(username =user.user)
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)
    
    username_profile = []
    username_profile_list =[]
    
    for users in final_suggestions_list:
        username_profile.append(users.id)
        
    for ids in username_profile:
        profile_lists =Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)
    suggestions_username_profile_list =list(chain(*username_profile_list))
    
    
    # posts = Post.objects.all()
    return render(request, 'index.html', {'user_profile': user_profile, 'posts' : feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list[:3]})

def signup(request):
    if request.method == "POST":
        username = request.POST['username'] 
        email = request.POST['email'] 
        password = request.POST['password'] 
        password2 = request.POST['password2']  
        
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email is already registered!')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username is already registered!')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                
                #Log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                
                
                #create a Profile page for new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user= user_model.id)
                new_profile.save()
                return redirect('settings')
        else:  
            messages.info(request, 'Passwords donnot match!')
            return redirect('signup')
    else:
        return render(request, 'signup.html')

def signin(request):
       
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, ' Invalid credentials!')
            return redirect('signin')
            
    
    else:
        return render(request, 'signin.html')
    
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)  # Profile has a OneToOne relationship with User

    if request.method == 'POST':
        # Get uploaded files or fallback to current ones
        image = request.FILES.get('image')
        cover_image = request.FILES.get('coverimg')

        if image is None:
            image = user_profile.profileimg

        if cover_image is None:
            cover_image = user_profile.coverimg

        # Get text fields
        bio = request.POST.get('bio', user_profile.bio)
        location = request.POST.get('location', user_profile.location)

        # Update profile
        user_profile.profileimg = image
        user_profile.coverimg = cover_image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})

# PROFILE
@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length=len(user_posts)
    
    follower = request.user.username
    user =pk 
    
    if FollowersCount.objects.filter(follower= follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'
        
    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))
        
    
    context= {
        'user_object' : user_object,
        'user_profile' : user_profile,
        'user_posts' : user_posts,
        'user_post_length' : user_post_length,
        'button_text' : button_text,
        'user_followers' : user_followers,
        'user_following' : user_following,

    }
    return render(request, 'profile.html', context)

# FOLLOW
@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']
        
        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower =  FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower=FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
            
    else:
        return redirect('/')

# POSTS

@login_required(login_url='signin')
def upload(request):

    if request.method =='POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        
        return redirect('/')
    else:
        return redirect('/')
    return HttpResponse('<h1> UPload View </h1>')

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Allow only the owner to delete the post
    if post.user == request.user:
        post.delete()
        
    return redirect('/') 


# LIKEs

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')
    
    post = Post.objects.get(id=post_id)
    
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    
    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes+1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes-1
        post.save()
        return redirect('/')
        
# COMMENTS
@login_required(login_url='signin')
def add_comment(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        comment_text = request.POST.get('comment_text')
        user = request.user

        post = Post.objects.get(id=post_id)

        new_comment = Comment.objects.create(post=post, user=user, comment_text=comment_text)
        new_comment.save()

        return redirect('/')
    else:
        return redirect('/')
    
@login_required(login_url='signin')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user == request.user:
        comment.delete()
    return redirect('/')

@login_required(login_url='signin')
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:
        return redirect('/')

    if request.method == 'POST':
        new_text = request.POST.get('comment_text')
        comment.comment_text = new_text
        comment.save()
    return redirect('/')


       
# SEARCH
@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})
