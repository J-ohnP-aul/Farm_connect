from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Profile', {'fields': ('name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'role', 'password1', 'password2'),
        }),
    )
    list_display = ('phone_number', 'name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('phone_number', 'name')
    ordering = ('-created_at',)
