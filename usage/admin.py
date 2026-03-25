from django.contrib import admin
from .models import AppCategory, AppUsage, WeeklyUsageGoal, DailyUsageSummary, DailyAppUsageTop

admin.site.register(AppCategory)
admin.site.register(AppUsage)
admin.site.register(WeeklyUsageGoal)
admin.site.register(DailyUsageSummary)
admin.site.register(DailyAppUsageTop)