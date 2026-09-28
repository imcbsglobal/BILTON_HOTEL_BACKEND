from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminLoginView,
    BlogContentUploadView,
    BlogDetailView,
    BlogListCreateView,
    BlogTogglePublishView,
)

urlpatterns = [
    path("admin-login/", AdminLoginView.as_view(), name="admin-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    path("posts/", BlogListCreateView.as_view(), name="blog-list-create"),
    path("posts/<slug:slug>/", BlogDetailView.as_view(), name="blog-detail"),
    path("posts/<slug:slug>/toggle-publish/", BlogTogglePublishView.as_view(), name="blog-toggle-publish"),

    path("upload/", BlogContentUploadView.as_view(), name="blog-content-upload"),
]