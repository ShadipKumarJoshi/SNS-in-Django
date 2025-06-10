from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount, Comment
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from itertools import chain
from django.db.models import Prefetch
import random

# HOME FEED
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount, Comment
from django.db.models import Prefetch
from itertools import chain
import random

@login_required(login_url='signin')
def index(request):
    user_profile = Profile.objects.get(user=request.user) # Ensure profile exists for the current user
    user_following = FollowersCount.objects.filter(follower=request.user).values_list('user', flat=True) # Users the current user is following

    # Posts from followed users and the current user
    posts = Post.objects.filter(user__in=list(user_following) + [request.user]).select_related('user').order_by('-created_at')

    # Prefetch related comments and comment.user in one go
    posts = posts.prefetch_related(
        Prefetch('comment_set', queryset=Comment.objects.select_related('user').order_by('-created_at'))
    )

    # Attach profiles to posts and comments
    for post in posts:
        post.user_profile = Profile.objects.get(user=post.user)

        for comment in post.comment_set.all():
            comment.profile = Profile.objects.get(user=comment.user)

    # Suggest users to follow
    all_users = User.objects.filter(is_superuser=False, is_staff=False).exclude(id=request.user.id)
    following_users = set(user_following)
    suggestions = [user for user in all_users if user.id not in following_users]

    random.shuffle(suggestions)
    suggestions_profiles = [Profile.objects.get(user=user)for user in suggestions[:3]]

    context = {
        'user_profile': user_profile,
        'posts': posts,
        'suggestions_username_profile_list': suggestions_profiles,
    }

    return render(request, 'index.html', context)
def validate_signup_data(username, email, password, password2):
    errors = []

    if not username or not email or not password or not password2:
        errors.append("All fields are required.")

    if len(password) < 6:
        errors.append("Password must be at least 6 characters long.")

    if password != password2:
        errors.append("Passwords do not match!")

    if User.objects.filter(email=email).exists():
        errors.append("Email is already registered!")

    if User.objects.filter(username=username).exists():
        errors.append("Username is already registered!")

    return errors

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
         # ✅ Prepare context for re-rendering the form with input preserved
        context = {
            'username': username,
            'email': email
        }
        
        # Use helper function for error
        errors = validate_signup_data(username, email, password, password2)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'signup.html', context)

        # ✅ NEW: Create and login user, create profile
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)
        auth.login(request, user)
        messages.success(request, 'Your account has been created successfully!')
        return redirect('settings')
    else:
        return render(request, 'signup.html')

def signin(request):
       
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = auth.authenticate(username=username, password=password)
        
        if user:
            auth.login(request, user) # creates a session for the user
            messages.success(request, 'Welcome to your account!')
            return redirect('/')
        else:
            messages.info(request, ' Invalid credentials!')
            # ✅ preserve username in context
            context = {'username': username}
            return render(request, 'signin.html', context)
 
    else:
        return render(request, 'signin.html')
    
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You have successfully logged out!')
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
        bio = request.POST.get('bio', user_profile.bio) # means value = some_dict.get('key', 'default_value')

        location = request.POST.get('location', user_profile.location)

        # Update profile
        user_profile.profileimg = image
        user_profile.coverimg = cover_image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()
        messages.success(request, 'You have successfully updated your profile!')

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})

# PROFILE
@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile= Profile.objects.get(user=user_object)

       # ✅ NEW: filter by User object
    user_posts = Post.objects.filter(user=user_object)
    user_post_length=len(user_posts)
  
    follower = request.user
    user = user_object
    
    # if FollowersCount.objects.filter(follower= follower, user=user).first():
    if FollowersCount.objects.filter(follower=follower, user=user).exists():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'
    user_followers = FollowersCount.objects.filter(user=user).count()
    user_following = FollowersCount.objects.filter(follower=user).count()
   
    
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
        follower = request.user # currently logged-in user
        user = User.objects.get(username=request.POST['user'])  # target user

        if FollowersCount.objects.filter(follower=follower, user=user).exists():
            FollowersCount.objects.get(follower=follower, user=user).delete()
        else:
            FollowersCount.objects.create(follower=follower, user=user)

        return redirect('/profile/' + user.username)
            
    else:
        return redirect('/')

# POSTS

@login_required(login_url='signin')
def upload(request):

    if request.method =='POST':
        user = request.user
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        # new_post.save() # create already saves itself
        messages.success(request, 'Your post is successfully made!')
        
        return redirect('/')
    else:
        return redirect('/')

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Allow only the owner to delete the post
    if post.user == request.user:
        post.delete()
        messages.success(request, 'Your post is successfully deleted!')
        
    return redirect('/') 


# LIKEs

@login_required(login_url='signin')
def like_post(request):
    user = request.user
    post_id = request.POST.get('post_id')
    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post=post, user=user).first()
    if like_filter is None:
        LikePost.objects.create(post=post, user=user)
        post.no_of_likes += 1
        post.save()
    else:
        like_filter.delete()
        post.no_of_likes -= 1
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
    user_profile, _ = Profile.objects.get(user=user_object)  #


    if request.method == 'POST':
        username = request.POST['username']
        username_objects = User.objects.filter(username__icontains=username)
        username_profile_list = [Profile.objects.get(user=user) for user in username_objects]

        return render(request, 'search.html', {
            'user_profile': user_profile,
            'username_profile_list': username_profile_list
        })

    return redirect('/')