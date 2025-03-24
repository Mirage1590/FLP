from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """ ให้ Social Login เชื่อมบัญชีที่มี Email เดียวกันแทนที่จะสร้างใหม่ """
        if sociallogin.is_existing:
            return  # ถ้าบัญชี Social Login มีอยู่แล้วให้ผ่านไปเลย

        email = sociallogin.user.email
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)  # เชื่อมบัญชี Social กับ User ที่มีอยู่
            except User.DoesNotExist:
                pass  # ถ้าไม่มีบัญชีให้สมัครใหม่ได้ปกติ
