# accounts/admin.py
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # 에러를 유발하던 provider, provider_uid 필드 삭제
    list_display = ("id", "username", "email")
    search_fields = ("username", "email")