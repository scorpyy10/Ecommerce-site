from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        ('phone', 'is_verified'),
        ('address', 'city', 'state'),
        ('country', 'postal_code'),
        'bio',
        'date_of_birth',
        'profile_image',
        ('email_notifications', 'sms_notifications', 'marketing_emails'),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone', 'get_is_verified')
    list_filter = BaseUserAdmin.list_filter + ('profile__is_verified',)
    
    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') else ''
    get_phone.short_description = 'Phone'
    
    def get_is_verified(self, obj):
        return obj.profile.is_verified if hasattr(obj, 'profile') else False
    get_is_verified.short_description = 'Verified'
    get_is_verified.boolean = True


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'country', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'country', 'created_at', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Profile Information', {
            'fields': ('bio', 'date_of_birth', 'profile_image')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'marketing_emails')
        }),
        ('Account Status', {
            'fields': ('is_verified', 'verification_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
