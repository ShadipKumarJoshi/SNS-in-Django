from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount, Comment
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from itertools import chain
import random

# HOME FEED
# Create your views here.
@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    # user_profile = Profile.objects.get(user=user_object)
    user_profile, _ = Profile.objects.get_or_create(user=user_object)  # ✅ creates profile if needed

    
    # Get usernames the user follows
    user_following_list =[]
    feed = []
    
    # ❌ OLD: used username string comparison
    # user_following = FollowersCount.objects.filter(follower=request.user.username)
    # ✅ NEW: use ForeignKey comparison
    user_following = FollowersCount.objects.filter(follower=request.user)

    for users in user_following:
        user_following_list.append(users.user)
    
    # Fetch posts of followed users    
    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)
    
    # Add the logged-in user's own posts
    # ❌ OLD: used username string for filtering posts
    # my_posts = Post.objects.filter(user=request.user.username)
    # ✅ NEW: filter with ForeignKey `User` object
    my_posts = Post.objects.filter(user=request.user)
    feed.append(my_posts)
    
    # Merge all post querysets into a single list    
    feed_list = list(chain(*feed))
    
    # Enrich posts with profile and comments
    for post in feed_list:
        # ❌ OLD: was getting Profile with user__username, now unnecessary
        # post.user_profile = Profile.objects.get(user__username=post.user)
        # ✅ NEW: simpler lookup with ForeignKey directly
        # post.user_profile = Profile.objects.get(user=post.user)
        post.user_profile, _ = Profile.objects.get_or_create(user=post.user)  # ✅ creates profile if missing

        
        post.comments = Comment.objects.filter(post=post).order_by('-created_at')

        # Attach commenter profile to each comment
        for comment in post.comments:
            # comment.profile = Profile.objects.get(user=comment.user)
            comment.profile, _ = Profile.objects.get_or_create(user=comment.user)

        
    # user suggestion starts
    # all_users = User.objects.all()    #showing admin after code enhance
    all_users = User.objects.filter(is_superuser=False, is_staff=False)

    user_following_all = []
    
    for user in user_following:
        # user_list =User.objects.get(username =user.user)
        user_list = user.user
        user_following_all.append(user_list)
    
    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    # current_user = User.objects.filter(username=request.user.username)
    # final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    final_suggestions_list = [x for x in new_suggestions_list if x != request.user]
    random.shuffle(final_suggestions_list)
    
    # ❌ OLD: used id_user, which no longer exists
    # username_profile = []
    # username_profile_list =[]
    
    # for users in final_suggestions_list:
    #     username_profile.append(users.id)
        
    # for ids in username_profile:
    #     profile_lists =Profile.objects.filter(id_user=ids)
    #     username_profile_list.append(profile_lists)
        
    # suggestions_username_profile_list =list(chain(*username_profile_list))
    
     # ✅ NEW: directly use ForeignKey `user` to fetch Profile
    suggestions_username_profile_list = [
        # Profile.objects.get(user=user) for user in final_suggestions_list
        Profile.objects.get_or_create(user=user)[0] for user in final_suggestions_list
    ]
    
    # posts = Post.objects.all()
    return render(request, 'index.html', {'user_profile': user_profile, 'posts' : feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list[:3]})

def signup(request):
    if request.method == "POST":
        # ❌ OLD: No check for empty or invalid inputs
        # username = request.POST['username'] 
        # email = request.POST['email'] 
        # password = request.POST['password'] 
        # password2 = request.POST['password2'] 
         
        # ✅ NEW: Handles missing fields and trims whitespace
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
         # ✅ Prepare context for re-rendering the form with input preserved
        context = {
            'username': username,
            'email': email
        }
        
         # ✅ NEW: Check for empty fields
        if not username or not email or not password or not password2:
            messages.error(request, 'All fields are required.')
            return render(request, 'signup.html', context)

        # ✅ NEW: Enforce password strength
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'signup.html', context)
        
        # ❌ OLD: Only compared passwords without any other validation
        # if password == password2:
        #     if User.objects.filter(email=email).exists():
        #         messages.info(request, 'Email is already registered!')
        #         return redirect('signup')
        #     elif User.objects.filter(username=username).exists():
        #         messages.info(request, 'Username is already registered!')
        #         return redirect('signup')
        #     else:
        #         user = User.objects.create_user(username=username, email=email, password=password)
        #         user.save()
                
        #         #Log user in and redirect to settings page
        #         user_login = auth.authenticate(username=username, password=password)
        #         auth.login(request, user_login)
                
                
        #         #create a Profile page for new user
        #         user_model = User.objects.get(username=username)
        #         # new_profile = Profile.objects.create(user=user_model, id_user= user_model.id)
        #         new_profile = Profile.objects.create(user=user_model)  # id_user no longer exists
        #         new_profile.save()
        #         return redirect('settings')
        # else:  
        #     messages.info(request, 'Passwords donnot match!')
        #     return redirect('signup')
        
         # ✅ NEW: Validate password match
        if password != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'signup.html', context)

        # ✅ NEW: Check for existing email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered!')
            return render(request, 'signup.html', context)

        # ✅ NEW: Check for existing username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already registered!')
            return render(request, 'signup.html', context)

        # ✅ NEW: Create and login user, create profile
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        auth.login(request, user)
        Profile.objects.get_or_create(user=user)
        messages.success(request, 'Your account has been created successfully!')
        return redirect('settings')
    else:
        return render(request, 'signup.html')

def signin(request):
       
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'Welcome to your account!')
            return redirect('/')
        else:
            messages.info(request, ' Invalid credentials!')
            # return redirect('signin')
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
    # ❌ Old (crashes if profile not found)
    # user_profile = Profile.objects.get(user=user_object)
    user_profile, _ = Profile.objects.get_or_create(user=user_object)



    # ✅ New (creates a profile automatically if it doesn't exist)
    user_profile, _ = Profile.objects.get_or_create(user=user_object)  # ✅ FIXED: prevent DoesNotExist crash

    # ❌ OLD: filtered user_posts by string username
    # user_posts = Post.objects.filter(user=pk)

    # ✅ NEW: filter by User object
    user_posts = Post.objects.filter(user=user_object)
    user_post_length=len(user_posts)
    
    # follower = request.user.username
    # user =pk 
    follower = request.user
    user = user_object
    
    # if FollowersCount.objects.filter(follower= follower, user=user).first():
    if FollowersCount.objects.filter(follower=follower, user=user).exists():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'
        
    # user_followers = len(FollowersCount.objects.filter(user=pk))
    # user_following = len(FollowersCount.objects.filter(follower=pk))
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
        # ❌ OLD: used usernames in FollowersCount
        # follower = request.POST['follower']
        # user = request.POST['user']
        
        # if FollowersCount.objects.filter(follower=follower, user=user).first():
        #     delete_follower =  FollowersCount.objects.get(follower=follower, user=user)
        #     delete_follower.delete()
        #     return redirect('/profile/'+user)
        # else:
        #     new_follower=FollowersCount.objects.create(follower=follower, user=user)
        #     new_follower.save()
        #     return redirect('/profile/'+user)
         # ✅ NEW: use User objects directly
        follower = request.user
        user = User.objects.get(username=request.POST['user'])

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
        # ❌ OLD: Post.user was a string field
        # user = request.user.username

        # ✅ NEW: Post.user is a ForeignKey to User
        user = request.user
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        
        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        messages.success(request, 'Your post is successfully made!')
        
        return redirect('/')
    else:
        return redirect('/')
    # return HttpResponse('<h1> UPload View </h1>')

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
 # ❌ OLD: LikePost used string username & post_id
    # username = request.user.username
    # post_id = request.GET.get('post_id')
    # like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    # ✅ NEW: LikePost uses ForeignKey for both post and user
    user = request.user
    post_id = request.GET.get('post_id')
    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post=post, user=user).first()

    # if like_filter == None:
    #     new_like = LikePost.objects.create(post_id=post_id, username=username)
    #     new_like.save()
    #     post.no_of_likes = post.no_of_likes+1
    #     post.save()
    #     return redirect('/')
    # else:
    #     like_filter.delete()
    #     post.no_of_likes = post.no_of_likes-1
    #     post.save()
    #     return redirect('/')
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
    # user_profile = Profile.objects.get(user=user_object)
    user_profile, _ = Profile.objects.get_or_create(user=user_object)  # ✅ creates profile if needed


    if request.method == 'POST':
        username = request.POST['username']
        username_objects = User.objects.filter(username__icontains=username)

        # ❌ OLD: filtered Profile using id_user
        # username_profile = []
        # username_profile_list = []
        # for users in username_objects:
        #     username_profile.append(users.id)
        # for ids in username_profile:
        #     profile_lists = Profile.objects.filter(id_user=ids)
        #     username_profile_list.append(profile_lists)
        # username_profile_list = list(chain(*username_profile_list))

        # ✅ NEW: get Profile directly using ForeignKey
        username_profile_list = [Profile.objects.get(user=user) for user in username_objects]

        return render(request, 'search.html', {
            'user_profile': user_profile,
            'username_profile_list': username_profile_list
        })

    return redirect('/')