from django import forms
from .models import Profile,Review,Shoe

class ProfileForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Profile
        fields = ['phone_number', 'date_of_birth', 'profile_picture', 'address']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class ShoeForm(forms.ModelForm):
    class Meta:
        model = Shoe
        fields = ['brand', 'model', 'price', 'size', 'shoe_type', 'gender', 'material', 'image']