from django.contrib import admin
from .models import Profile, Post, LikePost, FollowersCount, Comment


# 🔁 Original Code:
# admin.site.register(Profile)
# admin.site.register(Post)
# admin.site.register(LikePost)
# admin.site.register(FollowersCount)
# admin.site.register(Comment)

# ✅ Enhanced Admin Configuration

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')  # Shows in admin list
    # Searchable by username/location
    search_fields = ('user__username', 'location')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Visible columns in list view
    list_display = ('user', 'created_at', 'no_of_likes')
    # Makes caption and username searchable
    search_fields = ('user__username', 'caption')
    list_filter = ('created_at',)  # Adds filter by date
    readonly_fields = ('id', 'created_at')  # Make UUID and timestamp readonly


@admin.register(LikePost)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ('post', 'user')
    search_fields = ('post__id', 'user__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')  # Show useful fields
    search_fields = ('user__username', 'post__id',
                     'comment_text')  # Add useful search
    list_filter = ('created_at',)


@admin.register(FollowersCount)
class FollowersCountAdmin(admin.ModelAdmin):
    list_display = ('follower', 'user')  # Shows follower and followee
    # Search by usernames
    search_fields = ('follower__username', 'user__username')
