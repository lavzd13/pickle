from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import AccountDetail, Payment, PlaySession


class PlaySessionModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass123')
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass123')
        
        # Create test account
        self.account = AccountDetail.objects.create(
            user=self.user1,
            nick='TestNick',
            country='Austria',
            email='test@example.com',
            phone='123456789'
        )
    
    def test_session_creation(self):
        """Test creating a play session"""
        session = PlaySession.objects.create(
            account=self.account,
            session_date=timezone.now().date(),
            is_active=True,
            created_by=self.user1
        )
        self.assertEqual(session.account, self.account)
        self.assertTrue(session.is_active)
    
    def test_60_day_retention(self):
        """Test that sessions older than 60 days are filtered"""
        # Create a session from 70 days ago
        old_date = timezone.now() - timedelta(days=70)
        old_session = PlaySession.objects.create(
            account=self.account,
            session_date=old_date.date(),
            is_active=True,
            created_by=self.user1
        )
        
        # Create a recent session
        recent_session = PlaySession.objects.create(
            account=self.account,
            session_date=timezone.now().date(),
            is_active=True,
            created_by=self.user1
        )
        
        # Default queryset should only return recent sessions
        visible_sessions = PlaySession.objects.all()
        self.assertEqual(visible_sessions.count(), 1)
        self.assertEqual(visible_sessions.first(), recent_session)
        
        # all_including_old should return all sessions
        all_sessions = PlaySession.objects.all_including_old()
        self.assertEqual(all_sessions.count(), 2)
    
    def test_is_editable_by(self):
        """Test session editability"""
        session = PlaySession.objects.create(
            account=self.account,
            session_date=timezone.now().date(),
            is_active=True,
            created_by=self.user1
        )
        
        # Creator can edit
        self.assertTrue(session.is_editable_by(self.user1))
        
        # Other user cannot edit
        self.assertFalse(session.is_editable_by(self.user2))
        
        # Superuser can edit
        self.assertTrue(session.is_editable_by(self.superuser))
