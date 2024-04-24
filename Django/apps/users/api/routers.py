from rest_framework.routers import DefaultRouter

from apps.users.api.viewsets.user_viewset import UserModelViewset

router = DefaultRouter()
router.trailing_slash = r"/?"

router.register(r'user', UserModelViewset, basename='user-viewset')

urlpatterns = router.urls