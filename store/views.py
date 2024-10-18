from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import Profile, Shoe
from django.shortcuts import render

def start(request):
    return render(request, 'start.html')

def custom_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('shop')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def custom_register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        email = request.POST['email']
        phone_number = request.POST['phone_number']

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken")
        else:
            # สร้างผู้ใช้ใหม่
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()

            # เพิ่มข้อมูล Profile
            profile = Profile(user=user, phone_number=phone_number)
            profile.save()

            messages.success(request, "Registration successful")
            return redirect('custom_login')

    return render(request, 'register.html')

def custom_logout(request):
    logout(request)
    return redirect('custom_login')

def shop(request):
    return render(request, 'shop.html')

def profile(request):
    return render(request, 'profile.html')

def edit_profile(request):
    user = request.user

    # ตรวจสอบว่าผู้ใช้มี Profile หรือไม่ ถ้าไม่มีก็สร้างขึ้นมา
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.username = request.POST['username']
        user.email = request.POST['email']

        password = request.POST['password']
        if password:
            user.set_password(password)

        # อัปเดตข้อมูลใน Profile
        profile = user.profile
        profile.phone_number = request.POST['phone_number']
        profile.date_of_birth = request.POST['date_of_birth']

        user.save()
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('edit_profile')

    return render(request, 'edit_profile.html', {'user': request.user, 'profile': request.user.profile})

def shoe_list(request):
        # ดึงค่าจาก GET Request (query parameters) ที่ใช้สำหรับกรองข้อมูล
        brand = request.GET.get('brand')
        shoe_type = request.GET.get('shoe_type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        # ดึงข้อมูลทั้งหมดก่อน จากนั้นกรองตามเงื่อนไข
        shoes = Shoe.objects.all()

        # กรองตามแบรนด์
        if brand:
            shoes = shoes.filter(brand=brand)

        # กรองตามประเภท
        if shoe_type:
            shoes = shoes.filter(shoe_type=shoe_type)

        # กรองตามช่วงราคา
        if min_price:
            shoes = shoes.filter(price__gte=min_price)
        if max_price:
            shoes = shoes.filter(price__lte=max_price)

        # ส่งข้อมูลไปยัง template
        return render(request, 'shoe_list.html', {'shoes': shoes})

def shoe_all(request):
    shoes = Shoe.objects.all()  # ดึงข้อมูลรองเท้าทั้งหมดจากฐานข้อมูล
    return render(request, 'shoe_all.html', {'shoes': shoes})
