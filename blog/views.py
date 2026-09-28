from django.contrib.auth import authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Blog, BlogContentUpload, BlogStatus
from .serializers import BlogListSerializer, BlogSerializer


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response({"detail": "Invalid email or password."}, status=400)

        if not user.is_superuser:
            return Response({"detail": "You are not authorized to access the admin panel."}, status=403)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "is_superuser": user.is_superuser,
            },
        })


class BlogListCreateView(APIView):
    """
    GET  /api/blog/posts/   -> public visitors see published posts only
                                (plus scheduled posts whose time has already
                                passed, as a safety net ahead of the next
                                scheduler tick); authenticated admins see
                                everything (so the dashboard's tabs work).
    POST /api/blog/posts/   -> create a post (admin only).
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        qs = Blog.objects.all()
        if not (request.user and request.user.is_authenticated):
            qs = qs.filter(
                Q(status=BlogStatus.PUBLISHED)
                | Q(status=BlogStatus.SCHEDULED, publish_at__lte=timezone.now())
            )
        serializer = BlogListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = BlogSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            print(serializer.errors)  # prints to your runserver terminal
        serializer.is_valid(raise_exception=True)
        author = request.data.get("author") or request.user.email
        serializer.save(created_by=request.user, author=author)
        return Response(serializer.data, status=201)


class BlogDetailView(APIView):
    """
    GET    /api/blog/posts/<slug>/
    PUT    /api/blog/posts/<slug>/  (admin only)
    DELETE /api/blog/posts/<slug>/  (admin only)
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, slug):
        return get_object_or_404(Blog, slug=slug)

    def get(self, request, slug):
        blog = self.get_object(slug)
        is_admin = bool(request.user and request.user.is_authenticated)
        is_due_scheduled = (
            blog.status == BlogStatus.SCHEDULED
            and blog.publish_at
            and blog.publish_at <= timezone.now()
        )
        if blog.status != BlogStatus.PUBLISHED and not is_due_scheduled and not is_admin:
            return Response({"detail": "Not found."}, status=404)
        return Response(BlogSerializer(blog, context={"request": request}).data)

    def put(self, request, slug):
        blog = self.get_object(slug)
        serializer = BlogSerializer(blog, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug):
        blog = self.get_object(slug)
        blog.delete()
        return Response(status=204)


class BlogTogglePublishView(APIView):
    """POST /api/blog/posts/<slug>/toggle-publish/
    Flips between draft and published — used by the status pill in the
    dashboard table."""

    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        blog = get_object_or_404(Blog, slug=slug)
        blog.status = BlogStatus.DRAFT if blog.status == BlogStatus.PUBLISHED else BlogStatus.PUBLISHED
        blog.save()
        return Response(BlogSerializer(blog, context={"request": request}).data)


class BlogContentUploadView(APIView):
    """POST /api/blog/upload/
    Used by the content-block editor to upload an image/video for a single
    block, independent of saving the whole post. Returns {url, type}."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file provided."}, status=400)

        upload = BlogContentUpload.objects.create(
            file=file_obj,
            uploaded_by=request.user if request.user.is_authenticated else None,
        )
        url = request.build_absolute_uri(upload.file.url)
        content_type = getattr(file_obj, "content_type", "") or ""
        file_type = "video" if content_type.startswith("video") else "image"
        return Response({"url": url, "type": file_type}, status=201)