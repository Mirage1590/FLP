from django.contrib import admin
from .models import Coupon,Order,Shoe, Review

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'expiry_date', 'status')  # เปลี่ยนจาก is_active -> status
    list_filter = ('discount_type', 'status')  # เปลี่ยนจาก is_active -> status
    search_fields = ('code',)
    ordering = ('-expiry_date',)

admin.site.register(Coupon, CouponAdmin)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "status", "created_at")
    search_fields = ("user__username", "status")
    list_filter = ("status", "created_at")


admin.site.register(Shoe)
admin.site.register(Review)