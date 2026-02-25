from django.urls import path
from django.contrib.auth import views as auth_views
from . import web_views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboard
    path('', web_views.dashboard, name='dashboard'),
    
    # Sessions
    path('sessions/', web_views.session_list, name='session_list'),
    path('sessions/create/', web_views.session_create, name='session_create'),
    path('sessions/<int:pk>/edit/', web_views.session_edit, name='session_edit'),
    path('sessions/<int:pk>/delete/', web_views.session_delete, name='session_delete'),
    path('sessions/manage/<int:account_id>/<str:date>/', web_views.manage_day_sessions, name='manage_day_sessions'),
    
    # Gaming Accounts (superuser only)
    path('accounts/', web_views.account_list, name='account_list'),
    path('accounts/create/', web_views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', web_views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', web_views.account_delete, name='account_delete'),
    path('accounts/<int:pk>/sessions/', web_views.account_sessions, name='account_sessions'),
    
    # System Users (superuser only)
    path('users/', web_views.user_list, name='user_list'),
    path('users/create/', web_views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', web_views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', web_views.user_delete, name='user_delete'),

	# Play
	path('play/', web_views.play, name='play'),
    path('play/eligible-account/', web_views.eligible_account, name='eligible_account'),
    path('play/start-session/', web_views.start_session_play, name='start_session_play'),
    path('play/finish-session/', web_views.finish_session_play, name='finish_session_play'),
    path('play/active-sessions/', web_views.active_sessions, name='active_sessions'),
    path('play/pause-session/', web_views.pause_session_play, name='pause_session_play'),
    path('play/resume-session/', web_views.resume_session_play, name='resume_session_play'),
    path('play/stop-session/', web_views.stop_session, name='stop_session'),
    path('play/cancel-pending/', web_views.cancel_pending_session, name='cancel_pending_session'),
    path('play/dismiss-session/', web_views.dismiss_session, name='dismiss_session'),

    # Deposit/Withdrawals
    path('deposit-withdrawal/', web_views.deposit_withdrawal, name='deposit_withdrawal'),
    path('deposit/create/', web_views.deposit_create, name='deposit_create'),
    path('withdrawal/create/', web_views.withdrawal_create, name='withdrawal_create'),
    path('deposit-order/create/', web_views.deposit_order_create, name='deposit_order_create'),
    path('withdrawal-order/create/', web_views.withdrawal_order_create, name='withdrawal_order_create'),
    path('dw-entry/update/', web_views.dw_entry_update, name='dw_entry_update'),
    path('dw-entry/delete/', web_views.dw_entry_delete, name='dw_entry_delete'),
    path('deposit-withdrawal/new/deposit/', web_views.deposit_new_page, name='deposit_new_page'),
    path('deposit-withdrawal/new/withdrawal/', web_views.withdrawal_new_page, name='withdrawal_new_page'),
    path('deposit-withdrawal/order/deposit/<int:account_id>/', web_views.deposit_order_new_page, name='deposit_order_new_page'),
    path('deposit-withdrawal/order/withdrawal/<int:account_id>/', web_views.withdrawal_order_new_page, name='withdrawal_order_new_page'),
    path('deposit-withdrawal/entry/<str:entry_type>/<int:pk>/', web_views.dw_entry_page, name='dw_entry_page'),
    path('deposit-withdrawal/reports/', web_views.deposit_withdrawal_reports, name='deposit_withdrawal_reports'),
    path('deposit-withdrawal/history/', web_views.deposit_withdrawal_history, name='deposit_withdrawal_history'),
    path('account-search/', web_views.account_search, name='account_search'),

    # Service Worker (must be at root for full scope)
    path('sw.js', web_views.service_worker_js, name='service_worker_js'),
]
