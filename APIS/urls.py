# urls.py (inside your Django app)

from django.urls import path
from . import views
urlpatterns = [
    path("", views.index, name="index"),  
    path("login/", views.LoginView.as_view(), name="login"),  
    path("check_phone/", views.check_phone.as_view(), name="signin"),  
    path('set_upi/', views.set_upi.as_view(), name='set_upi'),
    path('change-upi/', views.ChangeUpiPin.as_view(), name='change_upi'),
    path('transfer_money/',views.TransferMoney.as_view(),name='transfer_money'),
    path('receive_page/',views.Receiver.as_view(),name='receive_page'),
    path('enter_pin/',views.VerifyPin.as_view(),name='enter_pin'),
    path('success/',views.success,name='success'),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
    path('balance/',views.balance_enquary.as_view(),name='balance'),
    path('upi-scan/', views.Scan_Pay.as_view(), name="upi-scan"),
    path('test-db/', views.test_db),
    path('load-data/', views.load_data),
    path('recharge/', views.MobileRecharge.as_view(), name='mobile_recharge'),
    path('electricity/', views.ElectricityBill.as_view(), name='electricity_bill'),
    path('bus-booking/', views.BusBooking.as_view(), name='bus_booking'),
    path('utility/', views.UtilityBill.as_view(), name='utility_bill'),
]
