from django.contrib import admin

from .models import ProductRequest


@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "request_author",
        "short_description",
        "final_code",
    )
    list_filter = ("created_at",)
    search_fields = ("description", "user__username", "final__recommended_code")
    ordering = ("-created_at", "-id")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "final")

    @admin.display(description="Пользователь")
    def request_author(self, obj):
        return obj.user.get_username() if obj.user_id else "Гость / без аккаунта"

    @admin.display(description="Что искали")
    def short_description(self, obj):
        text = " ".join((obj.description or "").split())
        return (text[:97] + "…" if len(text) > 100 else text) or "Без описания"

    @admin.display(description="Итоговый код")
    def final_code(self, obj):
        result = getattr(obj, "final", None)
        return result.recommended_code if result else "—"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False