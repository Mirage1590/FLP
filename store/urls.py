from django.urls import path ,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.start, name='item_list'),
    path('login/', views.custom_login, name='custom_login'),
    path('register/', views.custom_register, name='custom_register'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('shop/', views.shop, name='shop'),
    path('profile/', views.profile, name='profile'),
    path("update-profile/", views.update_profile, name="update_profile"),
    path('profile_edit/', views.edit_profile_view, name='edit_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('shoes_list/', views.shoe_list, name='shoe_list'),
    path('shoes_all/', views.shoe_all, name='shoe_all'),
    path('shoe/<int:shoe_id>/', views.shoe_detail, name='shoe_detail'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('accounts/', include('allauth.urls')),
    path('accounts/',include('django.contrib.auth.urls')),
    path('load_more_shoes/', views.load_more_shoes, name='load_more_shoes'),
    path("like/<int:shoe_id>/", views.like_shoe, name="like_shoe"),
    path("add_to_cart/<int:shoe_id>/", views.add_to_cart, name="add_to_cart"),
    path('cart/', views.cart_view, name='cart'),
    path("cart/add/<int:shoe_id>/", views.add_to_cart, name="add_to_cart"),
    path('cart/update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path("cart/remove/<int:shoe_id>/", views.remove_from_cart, name="remove_from_cart"),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path("cart/count/", views.cart_count_view, name="cart_count"),
    path("create-order/", views.create_order, name="create_order"),
    path("orders/", views.order_history, name="order_history"),
    path('order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('save-coupon/<int:coupon_id>/', views.save_coupon, name='save_coupon'),
    path('coupons/', views.your_coupons_view, name='your_coupon'),
    path('available_coupons/', views.available_coupons_view, name='available_coupons'),
    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path("admin_orders/", views.admin_orders_view, name="admin_orders"),
    path('change_order_status/<int:order_id>/', views.change_order_status, name='change_order_status'),
    path("admin_payments/", views.manage_payments, name="manage_payments"),
    path('payment_detail/<int:payment_id>/', views.payment_detail ,name='payment_detail'),
    path("admin_coupons/", views.admin_coupons_view, name="admin_coupons"),
    path("admin_coupons_add/", views.add_coupon, name="add_coupon"),
    path("admin_coupons_edit/<int:coupon_id>/", views.edit_coupon, name="edit_coupon"),
    path("admin_coupons_delete/<int:coupon_id>/", views.delete_coupon, name="delete_coupon"),
    path('admin_users/', views.manage_users_view, name='manage_users'),  # แสดงรายการผู้ใช้
    path('admin_users_create/', views.create_user_view, name='create_user'),  # เพิ่มผู้ใช้ใหม่
    path('admin_users_edit/<int:user_id>/', views.edit_user_view, name='edit_user'),  # แก้ไขข้อมูลผู้ใช้
    path('admin_users_delete/<int:user_id>/', views.delete_user_view, name='delete_user'),  # ลบผู้ใช้
    path('admin_users_assign-role/<int:user_id>/', views.assign_role_view, name='assign_role'),  # ตั้งบทบาทผู้ใช้
    path('stripe-webhook/', views.stripe_webhook, name='stripe-webhook'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path("chat/<str:chat_box_name>/", views.chat_box, name="chat"),
    path('search_shoes/', views.search_shoes, name='search_shoes'),

    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name='password_reset.html'),name='reset_password'),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),name='password_reset_confirm'),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)