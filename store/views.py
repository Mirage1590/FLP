from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile, Shoe,ShoeLike,Cart,Order, OrderItem,Coupon,UserCoupon,ChatRoom,Review
from .forms import ProfileForm,ReviewForm,ShoeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db import IntegrityError
import os
import pandas as pd
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from decimal import Decimal
from django.utils.timezone import now,make_aware
from datetime import datetime
from django.utils import timezone
from django.db.models import Sum,Avg,Q
import stripe


like_data = {}
cart_items = []
stripe.api_key = 'sk_test_51R1lmzGjdx3kU1kq8ZXX2TcEPbenND5NMJmB5mLrOUGD2sjlVmMgqYu8qPDwYp4SqRzCI7SmLnzPWwJdF2JFCnGe00Ji3kdoyn'

def start(request):
    return render(request, 'start.html')

def custom_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # ตรวจสอบว่าผู้ใช้เป็น Superuser หรือไม่
            if user.is_superuser:
                return redirect('admin_dashboard')  # พาไปหน้า Admin Django
            else:
                return redirect('shop')  # พาไปหน้า Home ปกติ

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def custom_register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        if not username or not password or not email or not phone_number:
            messages.error(request, "All fields are required")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered")
        else:
            try:
                # สร้างผู้ใช้ใหม่
                user = User.objects.create_user(username=username, password=password, email=email)
                user.save()

                # เพิ่มข้อมูล Profile
                Profile.objects.create(user=user, phone_number=phone_number)

                messages.success(request, "Registration successful")
                return redirect('custom_login')
            except IntegrityError:
                messages.error(request, "An error occurred during registration")

    return render(request, 'register.html')

def custom_logout(request):
    logout(request)
    return redirect('custom_login')

def shop(request):
    shoes = Shoe.objects.all().order_by('?')[:8]
    room = ChatRoom.objects.filter(users=request.user).first()
    cart_count = 0

    if request.user.is_authenticated:  # ถ้าผู้ใช้ล็อกอินอยู่
        cart_count = Cart.objects.filter(user=request.user).count()

    if not room:
        # หากไม่พบห้องแชท, สร้างห้องแชทใหม่
        room = ChatRoom.objects.create(name=f"Chat with {request.user.username}")
        room.users.add(request.user)  # เพิ่มผู้ใช้ในห้องแชท

    return render(request, "shop.html", {"shoes": shoes, "cart_count": cart_count ,"room": room })

@login_required
def profile(request):
    user = request.user

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None  # กรณีที่ไม่มีโปรไฟล์

    # ดึงข้อมูลจาก Profile
    full_name = f"{user.first_name} {user.last_name}"

    # ดึงคำสั่งซื้อของผู้ใช้ที่ล็อกอิน
    orders = Order.objects.filter(user=request.user).order_by('-created_at')  # เรียงจากใหม่ไปเก่า

    exchange_rate = 30
    for order in orders:
        order.price_thb = round(order.final_price * exchange_rate, 2)

    # ตรวจสอบโปรไฟล์ภาพ
    profile_picture_url = profile.profile_picture.url if profile and profile.profile_picture else 'https://via.placeholder.com/100'

    # ส่งค่าต่างๆ ให้กับ template
    return render(request, 'profile.html', {
        'orders': orders,
        'profile_picture_url': profile_picture_url,
        'user': user,
        'profile': profile,
        'first_name': user.first_name,  # ใช้ first_name จาก User model
        'last_name': user.last_name,    # ใช้ last_name จาก User model
    })

@login_required
def delete_order(request, order_id):
    # ตรวจสอบว่าการร้องขอเป็น POST
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)

        # ลบคำสั่งซื้อ
        order.delete()

        # ส่งผลลัพธ์กลับในรูปแบบ JSON
        return JsonResponse({"success": True, "message": "Order deleted successfully."})

    # ถ้าการร้องขอไม่ใช่ POST ให้ส่งข้อผิดพลาด
    return JsonResponse({"success": False, "error": "Invalid request method."})

@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'edit_profile.html', {'profile': profile})

@login_required
def update_profile(request):
    if request.method == "POST":
        profile, created = Profile.objects.get_or_create(user=request.user)
        # รับข้อมูลจากฟอร์ม
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "profile_picture_url": profile.profile_picture.url if profile.profile_picture else None
            })
        else:
            return JsonResponse({"success": False, "error": "Invalid form data"})

    return JsonResponse({"success": False, "error": "Invalid request method"})

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        logout(request)
        return JsonResponse({"success": True, "message": "Your account has been deleted."})

    return JsonResponse({"success": False, "error": "Invalid request method."})

def shoe_all(request):
    # โหลดข้อมูลจากไฟล์ Excel
    file_path = os.path.join(settings.MEDIA_ROOT, 'Shoe_prices0.xlsx')

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        return render(request, "shoe_all.html", {"error": "Shoe data file not found."})

    # เปลี่ยนชื่อคอลัมน์ให้เป็นรูปแบบที่ใช้ในโค้ด
    df.rename(columns={"Price (USD)": "Price_USD", "Image_URL": "Image"}, inplace=True)
    df["Price_USD"] = df["Price_USD"].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df["Price_USD"] = pd.to_numeric(df["Price_USD"], errors="coerce")
    df["Price_USD"] = df["Price_USD"].fillna(0)
    # กำหนดตัวเลือกฟิลเตอร์
    categories = sorted(df["Type"].dropna().unique())
    brands = sorted(df["Brand"].dropna().unique())

    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)

    selected_categories = request.GET.getlist("category")
    selected_brands = request.GET.getlist("brand")
    if selected_categories:
        df = df[df["Type"].isin(selected_categories)]
    if selected_brands:
        df = df[df["Brand"].isin(selected_brands)]

    # จัดเรียงไซส์จากน้อยไปมาก
    sizes = sorted(
        df["Size"].dropna().unique(),
        key=lambda x: float(str(x).replace("US ", "")) if "US" in str(x) else float(x)
    )

    # กำหนดสีหลัก ๆ เพื่อให้ตัวเลือกสีไม่มากเกินไป
    main_colors = ["Black", "White", "Red", "Blue", "Green", "Yellow", "Beige", "Brown", "Purple", "Pink", "Orange",
                   "Grey", "Gold", "Silver"]
    df["Main_Color"] = df["Color"].dropna().apply(
        lambda x: next((color for color in main_colors if color in str(x)), "Other"))
    colors = sorted(df["Main_Color"].unique())

    # กำหนดช่วงราคาที่ใช้เป็นตัวเลือกใน Filter
    price_ranges = ["Under $50", "$50 - $100", "$100 - $200", "Over $200"]

    # รับค่าจาก Filter ที่ผู้ใช้เลือก
    selected_categories = request.GET.getlist("category")
    selected_brands = request.GET.getlist("brand")
    selected_sizes = request.GET.getlist("size")
    selected_colors = request.GET.getlist("color")
    selected_price_range = request.GET.getlist("price_range")

    # กรองข้อมูลตามค่าที่เลือก
    if selected_categories:
        df = df[df["Type"].isin(selected_categories)]
    if selected_brands:
        df = df[df["Brand"].isin(selected_brands)]
    if selected_sizes:
        df = df[df["Size"].astype(str).isin(selected_sizes)]
    if selected_colors:
        df = df[df["Main_Color"].isin(selected_colors)]

    # กรองตามช่วงราคา
    if selected_price_range:
        price_conditions = []
        for price_range in selected_price_range:
            if price_range == "Under $50":
                price_conditions.append(df["Price_USD"] <= 50)
            elif price_range == "$50 - $100":
                price_conditions.append(df["Price_USD"].between(50, 100))
            elif price_range == "$100 - $200":
                price_conditions.append(df["Price_USD"].between(100, 200))
            elif price_range == "Over $200":
                price_conditions.append(df["Price_USD"] >= 200)

        if price_conditions:
            df = df[pd.concat(price_conditions, axis=1).any(axis=1)]

    # แปลง DataFrame เป็น dictionary เพื่อใช้ใน template
    shoes = df.to_dict(orient="records")

    return render(request, "shoe_all.html", {
        "shoes": shoes,
        "categories": categories,
        "brands": brands,
        "sizes": sizes,
        "colors": colors,
        "price_ranges": price_ranges,
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
        "selected_sizes": selected_sizes,
        "selected_colors": selected_colors,
        "selected_price_range": selected_price_range,
    })

def shoe_detail(request, shoe_id):
    shoe = get_object_or_404(Shoe, id=shoe_id)
    reviews = Review.objects.filter(product=shoe).order_by('-created_at')
    # สร้างสินค้าที่เกี่ยวข้อง (ตัวอย่าง: เอาสินค้ารุ่นเดียวกัน แต่คนละสี)
    related_shoes = Shoe.objects.filter(brand=shoe.brand).exclude(id=shoe.id)[:5]
    is_liked = ShoeLike.objects.filter(user=request.user, shoe=shoe).exists()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__payment_status="paid",
        shoe=shoe
    ).exists()

    print("🧪 Current user:", request.user.username)
    print("🧪 Checking purchase for shoe:", shoe.model)
    print("✅ has_purchased:", has_purchased)

    if request.method == "POST" and has_purchased:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = shoe  # เชื่อมโยงกับสินค้านี้
            review.user = request.user  # เชื่อมโยงกับผู้ใช้ที่รีวิว
            review.save()  # บันทึกรีวิว
            return redirect('shoe_detail', shoe_id=shoe.id)  # รีเฟรชหน้าเพื่อแสดงรีวิวใหม่
    else:
        form = ReviewForm()

    return render(request, 'shoe_detail.html', {
        'shoe': shoe,
        'related_shoes': related_shoes,
        'is_liked': is_liked,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'form': form,
        "has_purchased": has_purchased,
    })

def load_more_shoes(request):
    page = int(request.GET.get("page", 1))
    category = request.GET.get("category", None)
    file_path = os.path.join(settings.MEDIA_ROOT, 'Shoe_prices0.xlsx')

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        return JsonResponse({"shoes": []})

    df.rename(columns={"Price (USD)": "price", "Image_URL": "image_url", "Brand": "brand", "Model": "model"}, inplace=True)
    df["id"] = range(1, len(df) + 1)

    if category:
        df = df[df["Type"] == category]

    shoes_list = df.to_dict(orient="records")
    paginator = Paginator(shoes_list, 5)
    shoes = paginator.get_page(page)

    return JsonResponse({"shoes": list(shoes)})

@login_required
def like_shoe(request, shoe_id):
    shoe = get_object_or_404(Shoe, id=shoe_id)
    user = request.user

    liked = ShoeLike.objects.filter(user=user, shoe=shoe).exists()

    if liked:
        # ถ้าเคยกดถูกใจ → ยกเลิกถูกใจ (Unlike)
        ShoeLike.objects.filter(user=user, shoe=shoe).delete()
        shoe.likes -= 1
        liked = False
    else:
        # ถ้ายังไม่เคยกด → กดถูกใจ (Like)
        ShoeLike.objects.create(user=user, shoe=shoe)
        shoe.likes += 1
        liked = True

    shoe.save()
    return JsonResponse({"likes": shoe.likes, "liked": liked})

def add_to_cart(request, shoe_id):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

        shoe = get_object_or_404(Shoe, id=shoe_id)
        user = request.user

        # ตรวจสอบว่าสินค้าอยู่ในตะกร้าแล้วหรือไม่
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            shoe=shoe,
            defaults={'price': shoe.price, 'image': shoe.image}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return JsonResponse({"status": "success", "cart_count": Cart.objects.filter(user=user).count()})

    except Exception as e:
        print(f"Error in add_to_cart: {e}")  # Debug error
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt  # ปิด CSRF ชั่วคราวเพื่อทดสอบ (หลังจากใช้งานได้แล้ว ควรใช้ CSRF Token)
@require_POST
def update_cart(request, cart_id):
    try:
        print(f"📌 Received request for cart_id {cart_id}")

        if not request.body:
            print("❌ No data received in request body")
            return JsonResponse({"status": "error", "message": "No data received"}, status=400)

        data = json.loads(request.body)
        print(f"✅ Received data: {data}")

        change = int(data.get("quantity", 0))
        print(f"🔄 Quantity change: {change}")

        # ใช้ Cart แทน CartItem
        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        print(f"🛒 Found cart: {cart}")

        cart.quantity = max(1, cart.quantity + change)
        cart.save()

        new_total_price = cart.quantity * cart.shoe.price  # ตรวจสอบว่า Cart มี shoe.price
        cart_total = sum(item.quantity * item.shoe.price for item in Cart.objects.filter(user=request.user))

        print(f"✅ Updated quantity: {cart.quantity}, Total price: {new_total_price}")

        return JsonResponse({
            "status": "success",
            "new_quantity": cart.quantity,
            "new_total_price": float(new_total_price),  # ไม่แปลง currency ที่นี่
            "cart_total": float(cart_total)
        })

    except Exception as e:
        print("❌ Error:", str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def cart_view(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    total_price = sum(item.total_price() for item in cart_items)
    user_coupons = UserCoupon.objects.filter(user=request.user, used=False).select_related('coupon')  # ดึงคูปองที่ยังใช้งานได้
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price, 'coupons': user_coupons,})

def remove_from_cart(request, shoe_id):
    if request.method == "POST":
        try:
            cart_item = get_object_or_404(Cart, shoe_id=shoe_id, user=request.user)
            cart_item.delete()
            return JsonResponse({"status": "success", "message": "Item removed from cart"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"})

def clear_cart(request):
    Cart.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'success'})

def cart_count_view(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
    return JsonResponse({"cart_count": cart_count})

@login_required
def create_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            user = request.user
            shipping_address = data.get("shipping_address", "")
            payment_method = data.get("payment_method", "")
            coupon_code = data.get("coupon_code", None)
            final_price = Decimal(data.get("final_price", "0"))

            cart_items = Cart.objects.filter(user=user)
            if not cart_items:
                return JsonResponse({"success": False, "error": "Cart is empty."}, status=400)

            total_price = sum(Decimal(item.total_price()) for item in cart_items)
            discount = total_price - final_price

            # ✅ ดึง Coupon instance จาก database แทนการใช้ string
            coupon_instance = None
            if coupon_code:
                try:
                    coupon_instance = Coupon.objects.get(code=coupon_code)
                except Coupon.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Invalid coupon."}, status=400)

            order = Order.objects.create(
                user=user,
                total_price=total_price,
                discount=discount,
                final_price=final_price,
                shipping_address=shipping_address,
                payment_method=payment_method,
                coupon=coupon_instance  # ✅ ใช้ Coupon Object แทน string
            )

            for item in cart_items:
                order.items.create(
                    product_name=item.shoe.model,
                    quantity=item.quantity,
                    price=item.shoe.price,
                    image=item.shoe.image if isinstance(item.shoe.image, str) else item.shoe.image.url
                )

            cart_items.delete()
            return JsonResponse({"success": True, "order_id": order.id, "final_price": str(final_price)})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Server Error: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)

@login_required
def order_history(request):
    exchange_rate = 30  # USD → THB

    orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")

    for order in orders:
        order.price_thb = round(order.final_price * exchange_rate, 2)
        for item in order.items.all():
            item.price_thb = round(item.price * exchange_rate, 2)  # ✅ ต้องตั้งค่า price_thb สำหรับแต่ละ item

    return render(request, "order_history.html", {"orders": orders})


def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)  # ดึงรายการสินค้าในคำสั่งซื้อ

    exchange_rate = 30
    total_price_thb = order.total_price * exchange_rate

    # สร้าง context ให้ส่งไปยัง template
    context = {
        'order': order,
        'order_items': order_items,  # ส่งรายการสินค้า
        'total_price_thb': total_price_thb
    }
    return render(request, 'order_detail.html', context)

@login_required
def checkout(request):
    if request.method == "POST":
        data = json.loads(request.body)
        shipping_address = data.get("shipping_address")
        payment_method = data.get("payment_method")

        order = Order.objects.filter(user=request.user, status="pending").order_by('-created_at').first()
        if not order:
            return JsonResponse({"error": "No pending order found. Please create an order first."}, status=400)

        order.shipping_address = shipping_address
        order.payment_method = payment_method
        order.save()

        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request."}, status=400)

@login_required
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.price * item.quantity for item in cart_items)
    total_item = sum(item.quantity for item in cart_items)

    user_coupons = UserCoupon.objects.filter(user=request.user, saved=True, coupon__status='active')
    coupons = [user_coupon.coupon for user_coupon in user_coupons if user_coupon.coupon.expiry_date >= timezone.now() and user_coupon.coupon.status != 'used']
    final_price = total_price

    if request.method == "POST":
        shipping_address = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        coupon_code = request.POST.get('coupon_code')

        coupon = Coupon.objects.filter(code=coupon_code, status='active', expiry_date__gte=timezone.now()).first()
        discount = 0
        if coupon:
            user_coupon = UserCoupon.objects.filter(user=request.user, coupon=coupon).first()
            if user_coupon and user_coupon.coupon.status == 'used':
                return JsonResponse({"success": False, "error": "Coupon has already been used"})

            if coupon.discount_type == 'percentage':
                discount = (total_price * coupon.discount_value) / 100
            elif coupon.discount_type == 'fixed':
                discount = coupon.discount_value

            if not user_coupon:
                user_coupon = UserCoupon.objects.create(user=request.user, coupon=coupon, saved=False)

            user_coupon.coupon.status = 'used'
            user_coupon.coupon.save()
            user_coupon.saved = False
            user_coupon.save()

        final_price = total_price - discount if total_price > discount else 0

        # Set payment status to 'pending' for Cash on Delivery (COD)
        payment_status = 'pending'
        if payment_method == 'cod':
            payment_status = 'pending'  # Status should be 'pending' for COD

        # Create the order with payment_status as 'pending'
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            shipping_address=shipping_address,
            payment_method=payment_method,
            discount=discount,
            final_price=final_price,
            coupon=coupon,
            payment_status=payment_status  # Set to 'pending' for COD
        )

        # Create order items for the COD order
        if payment_method == 'cod':
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,  # Link the order with the OrderItem
                    shoe=cart_item.shoe,
                    product_name=cart_item.shoe.model,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    image=cart_item.image
                )

            # After the order is created, delete the items from the cart
            cart_items.delete()

            # Redirect to order confirmation page after successful order creation
            return redirect('order_confirmation', order_id=order.id)

        # Create a Stripe checkout session for other payment methods like 'prompt_pay'
        if payment_method == 'prompt_pay':
            session = stripe.checkout.Session.create(
                payment_method_types=['promptpay'],
                line_items=[{
                    'price_data': {
                        'currency': 'thb',
                        'product_data': {'name': 'Order Payment'},
                        'unit_amount': int(final_price * 3000),  # Convert to cents (i.e., Thai baht)
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/order_confirmation/{order.id}/'),  # Redirect to order confirmation page with order_id
                cancel_url=request.build_absolute_uri(f'/checkout/'),
                client_reference_id=order.id  # Store the order id in the session
            )

            order.stripe_checkout_session_id = session.id
            order.save()

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    shoe=cart_item.shoe,
                    product_name=cart_item.shoe.model,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    image=cart_item.image
                )

            cart_items.delete()

            return redirect(session.url, code=303)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_item': total_item,
        'final_price': final_price,
        'coupons': coupons,
    }
    return render(request, 'checkout.html', context)

def order_confirmation(request, order_id):
    # ดึงคำสั่งซื้อที่เกี่ยวข้อง
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    exchange_rate = 30
    total_price_thb = order.total_price * exchange_rate

    # ปรับสถานะการชำระเงิน
    if order.payment_status == "pending":
        if order.payment_method == "cod":
            # หากเป็น COD ให้สถานะการชำระเงินเป็น "pending"
            order.payment_status = "pending"
        elif order.payment_method == "prompt_pay":
            # หากเป็น Prompt Pay ให้สถานะการชำระเงินเป็น "paid"
            order.payment_status = "paid"

        order.payment_date = timezone.now()  # ตั้งเวลาการชำระเงินเป็นเวลาปัจจุบัน
        order.save()

    context = {
        'order': order,
        'order_items': order_items,
        'total_price_thb': total_price_thb,
    }

    return render(request, 'order_confirmation.html', context)

def process_checkout(request):
    if request.method == "POST":
        shipping_address = request.POST.get("shipping_address")
        payment_method = request.POST.get("payment_method")
        coupon_code = request.POST.get("coupon_code")

        total_price = sum(item.product.price * item.quantity for item in request.user.cart.items.all())

        if coupon_code and coupon_code != "none":
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                total_price -= coupon.discount
                if total_price < 0:
                    total_price = 0
            except Coupon.DoesNotExist:
                pass

        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            payment_method=payment_method,
            total_price=total_price
        )

        return redirect("success_page")

    return redirect("checkout_view")

@login_required
def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")
        total_price = Decimal(request.POST.get("total_price", "0.00"))

        discount = Decimal("0.00")
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            discount = coupon.discount_value
        except Coupon.DoesNotExist:
            pass

        final_price = max(total_price - discount, Decimal("0.00"))
        return JsonResponse({"final_price": f"${final_price:.2f}"})
    return JsonResponse({"error": "Invalid request"}, status=400)


def available_coupons_view(request):
    # ดึงคูปองทั้งหมดที่ยังไม่ถูกบันทึก
    available_coupons = Coupon.objects.filter(status='active', expiry_date__gte=now())
    saved_coupon_ids = UserCoupon.objects.filter(user=request.user, saved=True).values_list('coupon__id', flat=True)

    for coupon in available_coupons:
        coupon.update_status()

    context = {
        'available_coupons': available_coupons,
        'saved_coupon_ids': saved_coupon_ids,  # คูปองที่ผู้ใช้บันทึกแล้ว
    }
    return render(request, 'available_coupons.html', context)


def save_coupon(request, coupon_id):
    if request.method == "POST":
        coupon = Coupon.objects.get(id=coupon_id)

        # ตรวจสอบว่า UserCoupon ของคูปองนี้ถูกบันทึกไปแล้วหรือไม่
        if UserCoupon.objects.filter(user=request.user, coupon=coupon).exists():
            # ถ้าผู้ใช้ได้บันทึกคูปองนี้ไปแล้ว
            return JsonResponse({"success": False, "error": "บันทึกไปแล้ว"})

        # ตรวจสอบว่าคูปองนั้นยังไม่ได้ใช้
        if coupon.status == 'active':
            # บันทึกคูปอง
            user_coupon = UserCoupon.objects.create(user=request.user, coupon=coupon, saved=True)

            # เปลี่ยนสถานะคูปองให้เป็น 'saved' ในหน้า Available Coupons
            coupon.status = 'saved'
            coupon.save()

            return JsonResponse({'success': True, 'coupon': coupon.to_dict()})  # ส่งข้อมูลคูปองที่ถูกบันทึก

    return JsonResponse({'success': False, 'error': 'Invalid coupon.'})

def your_coupons_view(request):
    user_coupons = UserCoupon.objects.filter(user=request.user, saved=True).select_related('coupon')

    for uc in user_coupons:
        uc.coupon.update_status()  # 🔁 เช็คและอัปเดตสถานะให้แต่ละคูปอง

    context = {
        'user_coupons': user_coupons
    }
    return render(request, 'your_coupons.html', context)

@login_required
def save_coupon_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        coupon_id = data.get("coupon_id")

        try:
            coupon = Coupon.objects.get(id=coupon_id)

            # Ensure the coupon is not already marked as used
            if coupon.status != 'used':
                # Only save if the coupon is active and not used yet
                UserCoupon.objects.get_or_create(user=request.user, coupon=coupon, saved=True)  # ป้องกันซ้ำซ้อน
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Coupon already used."})

        except Coupon.DoesNotExist:
            return JsonResponse({"success": False, "error": "Coupon not found."})

    return JsonResponse({"success": False, "error": "Invalid request."})


@login_required
def save_coupon(request, coupon_id):
    # Get the coupon from the database
    coupon = Coupon.objects.get(id=coupon_id)

    if coupon.status == "active":  # Only save if coupon is active
        # Check if the user has already saved this coupon
        user_coupon = UserCoupon.objects.filter(user=request.user, coupon=coupon, saved=True).first()

        if user_coupon:
            # If the user already saved this coupon, no need to save again
            return JsonResponse({"success": False, "error": "Coupon already saved."})

        else:
            # If it's a new coupon, associate the coupon with the user and mark as saved
            UserCoupon.objects.create(user=request.user, coupon=coupon, saved=True)

        return JsonResponse({
            'success': True,
            'coupon': {
                'code': coupon.code,
                'discount_value': coupon.discount_value,
                'discount_type': coupon.discount_type,
                'expiry_date': coupon.expiry_date,
                'status': coupon.status  # Send updated status
            }
        })

    return JsonResponse({'success': False})

def admin_required(user):
    return user.is_superuser

def admin_orders_view(request):
    if not request.user.is_superuser:
        return redirect("shop")  # ✅ ป้องกัน User ปกติจากการเข้าถึง

    orders = Order.objects.all().order_by('-created_at')

    # กรองคำสั่งซื้อที่ต้องการ
    if 'search' in request.GET:
        order_id = request.GET.get('order_id', None)
        customer_name = request.GET.get('customer_name', None)
        payment_status = request.GET.get('payment_status', None)

        if order_id:
            orders = orders.filter(id__icontains=order_id)
        if customer_name:
            orders = orders.filter(user__username__icontains=customer_name)
        if payment_status:
            orders = orders.filter(payment_status=payment_status)

    return render(request, "admin_orders.html", {"orders": orders})

def admin_coupons_view(request):
    if request.method == "POST":
        coupon_id = request.POST.get("coupon_id")
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.mark_as_used()
            return redirect('coupon_management')
        except Coupon.DoesNotExist:
            return HttpResponse("Coupon not found")

    # ✅ ตรวจสอบสถานะทุกคูปองก่อนแสดงผล
    coupons = Coupon.objects.all()
    for coupon in coupons:
        coupon.update_status()

    return render(request, 'admin_coupons.html', {'coupons': coupons})


def add_coupon(request):
    if request.method == "POST":
        code = request.POST['code']
        discount_value = request.POST['discount_value']
        discount_type = request.POST['discount_type']
        expiry_date = request.POST['expiry_date']  # รับค่าเวลาจากฟอร์ม

        print(f"Expiry Date Received: {expiry_date}")  # เพิ่มเพื่อแสดงค่าที่รับมาจากฟอร์ม

        # แปลงเวลาที่ผู้ใช้กรอกเป็น datetime object
        try:
            # เช็คว่าค่าที่รับมาจากฟอร์มเป็น datetime แบบไหน
            if "T" in expiry_date:
                # If the date includes a 'T' like '2025-03-12T05:00'
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M")
            else:
                # If it's in the format '2025-03-12 05:00'
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M")

            # ใช้ timezone.make_aware เพื่อแปลงเวลาเป็น timezone-aware datetime
            expiry_date = timezone.make_aware(expiry_date)

        except ValueError:
            return JsonResponse({'error': 'Invalid expiry date format'})

        # ถ้าคูปองหมดอายุแล้ว ให้ตั้งสถานะคูปองเป็น "expired"
        if expiry_date < timezone.now():
            status = 'expired'
        else:
            status = 'active'

        # สร้างคูปองใหม่
        coupon = Coupon.objects.create(
            code=code,
            discount_value=discount_value,
            discount_type=discount_type,
            expiry_date=expiry_date,
            status=status  # ใช้สถานะที่กำหนด
        )

        return redirect('admin_coupons')  # เปลี่ยนเส้นทางไปหน้าจัดการคูปอง

    return render(request, 'add_coupon.html')

def edit_coupon(request, coupon_id):

    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == "POST":
        coupon.code = request.POST["code"]
        coupon.discount_type = request.POST["discount_type"]
        coupon.discount_value = request.POST["discount_value"]

        # ✅ แปลง expiry_date เป็น timezone-aware datetime
        expiry_date_str = request.POST["expiry_date"]
        expiry_date_naive = datetime.strptime(expiry_date_str, "%Y-%m-%dT%H:%M")
        coupon.expiry_date = make_aware(expiry_date_naive)

        # ✅ ตรวจสอบสถานะว่าหมดอายุหรือยัง
        coupon.status = "active" if coupon.expiry_date > now() else "expired"

        coupon.save()
        return redirect("admin_coupons")

    return render(request, "edit_coupon.html", {"coupon": coupon})

def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    return redirect("admin_coupons")

@login_required
@user_passes_test(admin_required)
def admin_dashboard_view(request):
    # คำนวณจำนวนคำสั่งซื้อทั้งหมด
    total_orders = Order.objects.count()

    # คำนวณรายได้ทั้งหมดจากคำสั่งซื้อ
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0

    # คำนวณจำนวนคูปองที่ยังใช้งานอยู่
    active_coupons = Coupon.objects.filter(status='active').count()

    # คำนวณจำนวนผู้ใช้ทั้งหมด
    total_users = User.objects.count()

    total_shoes = Shoe.objects.count()

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'active_coupons': active_coupons,
        'total_users': total_users,
        'total_shoes': total_shoes,
    }

    return render(request, 'admin_dashboard.html', context)


# จัดการผู้ใช้
@login_required
@user_passes_test(admin_required)
def manage_users_view(request):
    users = User.objects.all()
    return render(request, 'manage_users.html', {'users': users})

# ฟังก์ชันเพิ่มผู้ใช้
@login_required
@user_passes_test(admin_required)
def create_user_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        return redirect('manage_users')
    return render(request, 'create_user.html')

# ฟังก์ชันแก้ไขผู้ใช้
@login_required
@user_passes_test(admin_required)
def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.username = request.POST['username']
        user.email = request.POST['email']
        user.set_password(request.POST['password'])
        user.save()
        return redirect('manage_users')
    return render(request, 'edit_user.html', {'user': user})

# ลบผู้ใช้
@login_required
@user_passes_test(admin_required)
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot delete admin users.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('manage_users')

@login_required
@user_passes_test(admin_required)
def assign_role_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role = request.POST['role']  # รับค่าบทบาทจากฟอร์ม (เช่น Admin, User)
        if role == 'admin':
            user.is_staff = True
        else:
            user.is_staff = False
        user.save()
        return redirect('manage_users')
    return render(request, 'assign_role.html', {'user': user})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'status': 'failed', 'error': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'status': 'failed', 'error': str(e)}, status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['client_reference_id']

        order = Order.objects.get(id=order_id)
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.save()

    return JsonResponse({'status': 'success'})

@login_required
def change_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        return redirect('admin_orders')
    return render(request, 'change_order_status.html', {'order': order})

def manage_payments(request):
    # ดึงข้อมูลทั้งหมดของการชำระเงิน
    payments = Order.objects.all().order_by('-created_at')

    # สรุปยอดวันนี้
    today = timezone.now().date()
    total_revenue_today = Order.objects.filter(created_at__date=today).aggregate(Sum('final_price'))['final_price__sum'] or 0

    # สรุปยอดเดือนที่ผ่านมา
    last_month = today.replace(day=1) - timezone.timedelta(days=1)
    total_revenue_last_month = Order.objects.filter(created_at__month=last_month.month).aggregate(Sum('final_price'))['final_price__sum'] or 0

    # การกรองข้อมูลตามช่วงเวลา
    filter_from = request.GET.get('from', '')
    filter_to = request.GET.get('to', '')
    if filter_from and filter_to:
        payments = payments.filter(created_at__range=[filter_from, filter_to])

    # คำนวณยอดรวมของการชำระเงินทั้งหมด
    total_revenue = Order.objects.aggregate(Sum('final_price'))['final_price__sum'] or 0

    context = {
        'payments': payments,
        'total_revenue_today': total_revenue_today,
        'total_revenue_last_month': total_revenue_last_month,
        'total_revenue': total_revenue,
    }
    return render(request, 'manage_payments.html', context)

def payment_detail(request, payment_id):
    order = get_object_or_404(Order, id=payment_id)
    context = {
        'order': order
    }
    return render(request, 'payment_detail.html', context)

def shoe_list(request):
    shoes = Shoe.objects.all()
    query = request.GET.get('q')
    brand_filter = request.GET.get('brand')
    type_filter = request.GET.get('shoe_type')

    if query:
        shoes = shoes.filter(model__icontains=query)

    if brand_filter and brand_filter != 'all':
        shoes = shoes.filter(brand=brand_filter)

    if type_filter and type_filter != 'all':
        shoes = shoes.filter(type=type_filter)

    brands = Shoe.objects.values_list('brand', flat=True).distinct()
    types = Shoe.objects.values_list('shoe_type', flat=True).distinct()
    return render(request, 'admin_shoe_list.html', {
        'shoes': shoes,
        'brands': brands,
        'types': types,
        'selected_brand': brand_filter,
        'selected_type': type_filter,
        'search_query': query,
    })

def add_shoe(request):
    form = ShoeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('shoe_list')
    return render(request, 'admin_shoe_form.html', {'form': form})

def edit_shoe(request, shoe_id):
    shoe = Shoe.objects.get(id=shoe_id)
    form = ShoeForm(request.POST or None, request.FILES or None, instance=shoe)
    if form.is_valid():
        form.save()
        return redirect('shoe_list')
    return render(request, 'admin_shoe_form.html', {'form': form})

def delete_shoe(request, shoe_id):
    shoe = Shoe.objects.get(id=shoe_id)
    shoe.delete()
    return redirect('shoe_list')

@login_required
def chat_box(request, chat_box_name):
    return render(request, "chat_room.html", {"chat_box_name": chat_box_name})

def select_chat_view(request):
    # แยก admin ออก
    admin_user = User.objects.filter(is_superuser=True).first()
    # ผู้ใช้ทั่วไป (ไม่รวมตัวเองและไม่รวม superuser)
    users = User.objects.exclude(id__isnull=True).exclude(id=request.user.id).filter(is_superuser=False)

    return render(request, 'select_chat.html', {
        'admin_user': admin_user,
        'users': users
    })

@login_required
def chat_with_user_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('select_chat')

    user_ids = sorted([request.user.id, target_user.id])
    chat_box_name = f"Chat_{user_ids[0]}_{user_ids[1]}"

    room = ChatRoom.objects.filter(name=chat_box_name).first()

    if not room:
        room = ChatRoom.objects.create(name=chat_box_name)
        room.users.add(request.user)
        room.users.add(target_user)

    return redirect('chat', chat_box_name=room.name)

@user_passes_test(lambda u: u.is_superuser)
def select_chat_admin(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'select_chat_admin.html', {'users': users})

@login_required
def chat_with_admin_view(request):
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        return HttpResponse("Admin not found")

    # ห้องแยกตาม user
    chat_box_name = f"chat_with_admin_{request.user.id}"

    # หา หรือ สร้างห้องใหม่
    room, created = ChatRoom.objects.get_or_create(name=chat_box_name)

    # เพิ่มสมาชิกในห้อง (admin กับ user นี้)
    if created or not room.users.filter(id=request.user.id).exists():
        room.users.add(request.user)
    if not room.users.filter(id=admin_user.id).exists():
        room.users.add(admin_user)

    return redirect('chat', chat_box_name=room.name)

def search_shoes(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        shoes = Shoe.objects.filter(
            Q(model__icontains=query) |
            Q(brand__icontains=query) |
            Q(shoe_type__icontains=query)
        )
        for shoe in shoes:
            results.append({
                'id': shoe.id,
                'model': shoe.model,
                'price': shoe.price,
                'image': shoe.image
            })

    return JsonResponse({'results': results})

def convert_currency(request):
    currency = request.GET.get("currency", "USD")
    exchange_rate = 30  # สมมุติอัตรา USD → THB
    shoes = Shoe.objects.all()

    data = []
    for shoe in shoes:
        price = float(shoe.price)
        converted_price = round(price * exchange_rate, 2) if currency == "THB" else price
        data.append({
            "id": shoe.id,
            "model": shoe.model,
            "price": converted_price,
            "currency": currency,
        })

    return JsonResponse({"shoes": data})