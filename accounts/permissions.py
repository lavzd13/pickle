from rest_framework import permissions


class IsOwnerOrSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow owners of a session or superusers to edit/delete it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            # Non-superusers can only read sessions they created
            if not request.user.is_superuser:
                return obj.created_by == request.user
            return True

        # Write permissions only for owner or superuser
        if request.user.is_superuser:
            return True
        
        return obj.created_by == request.user


class CanViewOldSessions(permissions.BasePermission):
    """
    Permission to view sessions older than 60 days (superuser only).
    """
    
    def has_permission(self, request, view):
        # Only superusers can access old sessions endpoint
        return request.user.is_superuser
