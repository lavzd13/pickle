from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import web_views
from .views import AccountDetailViewSet, PaymentViewSet, PlaySessionViewSet, PlatformViewSet, NetworkViewSet, ProxyVpnViewSet, WalletProviderViewSet

router = DefaultRouter()
router.register(r'accounts', AccountDetailViewSet, basename='account')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'sessions', PlaySessionViewSet, basename='session')
router.register(r'platforms', PlatformViewSet, basename='platform')
router.register(r'networks', NetworkViewSet, basename='network')
router.register(r'proxy-vpns', ProxyVpnViewSet, basename='proxy-vpn')
router.register(r'wallet-providers', WalletProviderViewSet, basename='wallet-provider')

urlpatterns = [
    path('', include(router.urls)),
    path('random-accounts/', web_views.get_random_accounts, name='get_random_accounts'),
]
