from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from .models import Coupon, UserCoupon

def assign_coupon_to_user(user, coupon_code):
    """
    แจกคูปองให้ผู้ใช้
    """
    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        if coupon.is_valid():
            UserCoupon.objects.create(user=user, coupon=coupon)
            return {"success": True, "message": f"Coupon {coupon_code} assigned to {user.username}."}
        return {"success": False, "message": "Coupon is expired or inactive."}
    except ObjectDoesNotExist:
        return {"success": False, "message": "Invalid coupon code."}

def apply_coupon(user, coupon_code):
    """
    ใช้คูปองตอน Checkout
    """
    try:
        user_coupon = UserCoupon.objects.get(user=user, coupon__code=coupon_code, is_used=False, coupon__is_active=True)
        if user_coupon.coupon.is_valid():
            user_coupon.is_used = True
            user_coupon.used_at = now()
            user_coupon.save()
            return {"success": True, "message": f"Coupon {coupon_code} applied successfully!", "discount": user_coupon.coupon.discount_value}
        return {"success": False, "message": "Coupon is expired or already used."}
    except ObjectDoesNotExist:
        return {"success": False, "message": "Invalid or unavailable coupon."}
