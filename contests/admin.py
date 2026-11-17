from django.contrib import admin

from .models import Award, Contest, Entry, ThemeSong


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(ThemeSong)
class ThemeSongAdmin(admin.ModelAdmin):
    list_display = ["title", "artist", "start_date", "end_date"]


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 0


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["date", "note"]
    inlines = [EntryInline]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ["word", "speaker", "award", "contest"]
    list_filter = ["award"]
    search_fields = ["word", "speaker", "description"]
