from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Apartment, Room, Booking


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['name', 'price', 'address', 'desc', 'image', 'lat', 'lng']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'lat': forms.NumberInput(attrs={'class': 'form-control'}),
            'lng': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['apartment', 'room_name', 'max_people', 'is_available', 'note']
        widgets = {
            'apartment': forms.Select(attrs={'class': 'form-control'}),
            'room_name': forms.TextInput(attrs={'class': 'form-control'}),
            'max_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomerBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'customer_name', 'phone', 'email', 'check_in', 'check_out', 'guests', 'note']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập họ và tên'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09xxxxxxxx'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@gmail.com'}),
            'check_in': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Yêu cầu thêm nếu có'}),
        }

    def __init__(self, *args, apartment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if apartment is not None:
            self.fields['room'].queryset = apartment.rooms.filter(is_available=True)
        self.fields['room'].empty_label = 'Chọn phòng còn trống'

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        guests = cleaned_data.get('guests')
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out and check_in >= check_out:
            self.add_error('check_out', 'Ngày trả phòng phải sau ngày nhận phòng.')

        if room and guests and guests > room.max_people:
            self.add_error('guests', f'Phòng này chỉ tối đa {room.max_people} người.')

        if room and not room.is_available:
            self.add_error('room', 'Phòng này hiện không còn trống.')

        return cleaned_data


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['apartment', 'room', 'customer_name', 'phone', 'email', 'check_in', 'check_out', 'guests', 'status', 'note']
        widgets = {
            'apartment': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'check_in': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        apartment = cleaned_data.get('apartment')
        room = cleaned_data.get('room')
        guests = cleaned_data.get('guests')
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if room and apartment and room.apartment_id != apartment.id:
            self.add_error('room', 'Phòng phải thuộc đúng căn hộ đã chọn.')

        if room and guests and guests > room.max_people:
            self.add_error('guests', f'Phòng này chỉ tối đa {room.max_people} người.')

        if check_in and check_out and check_in >= check_out:
            self.add_error('check_out', 'Ngày trả phòng phải sau ngày nhận phòng.')

        return cleaned_data


class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
