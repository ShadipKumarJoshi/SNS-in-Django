from django.db import models
from django.contrib.auth import get_user_model
import uuid 
from datetime import datetime
 
User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)  # Ensures one profile per user
    bio = models.TextField(blank=True, null=True)  # Allows empty and null values
    coverimg = models.ImageField(upload_to='cover_images', default='cover-picture.jpg')
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Better relational integrity
    image = models.ImageField(upload_to='post_images')
    caption = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically sets timestamp
    no_of_likes = models.PositiveIntegerField(default=0)  # Prevents negative likes
    
    def __str__(self):
        return f"{self.user.username}'s Post"

class LikePost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)  # Links like to a real Post object
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links like to a real User object

        # A user can only like the same post once.
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['post', 'user'], name='unique_like')
    ]
    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} on {self.post.id}'

    class Meta:
        verbose_name_plural = "Comments"  # Improves admin display

class FollowersCount(models.Model):
   # follower: the person who follows.// user: the person being followed. // related_name helps with reverse lookups. Example:
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)  # Link to User following others
    user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)      # Link to User being followed

    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['follower', 'user'], name='unique_follow')
    ]
    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"

    