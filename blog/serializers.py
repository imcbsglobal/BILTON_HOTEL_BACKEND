from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Blog

User = get_user_model()


class BlogSerializer(serializers.ModelSerializer):
    """Field names are camelCase on purpose — they're written to match
    what the React admin dashboard and public blog pages read directly
    off the post object (post.coverImage, post.categoryLabel, etc.).
    `updated_at` / `created_at` stay snake_case because that's what the
    dashboard table already uses for its date formatting.

    Note: tags / seoKeywords / body arrive as JSON strings when the request
    is multipart/form-data (the frontend JSON.stringify()s them). DRF's
    JSONField parses those strings itself, so no manual decoding is needed
    here. Do NOT json.loads() them in to_internal_value — putting a Python
    list back into the QueryDict gets turned into a single-quoted string,
    which fails with "Value must be valid JSON."."""

    categoryLabel = serializers.CharField(source="category_label", read_only=True)
    categoryLabelOverride = serializers.CharField(
        source="category_label_override", required=False, allow_blank=True
    )
    coverImage = serializers.ImageField(source="cover_image", required=False, allow_null=True)
    coverImageAlt = serializers.CharField(source="cover_image_alt", required=False, allow_blank=True)
    coverImageCaption = serializers.CharField(
        source="cover_image_caption", required=False, allow_blank=True
    )
    socialShareImage = serializers.ImageField(
        source="social_share_image", required=False, allow_null=True
    )
    readTime = serializers.CharField(source="read_time", required=False, allow_blank=True)
    seoTitle = serializers.CharField(source="seo_title", required=False, allow_blank=True)
    metaDescription = serializers.CharField(source="meta_description", required=False, allow_blank=True)
    seoKeywords = serializers.JSONField(source="seo_keywords", required=False)
    allowComments = serializers.BooleanField(source="allow_comments", required=False)
    publishAt = serializers.DateTimeField(source="publish_at", required=False, allow_null=True)
    is_published = serializers.BooleanField(read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "author",
            "category",
            "categoryLabel",
            "categoryLabelOverride",
            "tags",
            "readTime",
            "coverImage",
            "coverImageAlt",
            "coverImageCaption",
            "body",
            "seoTitle",
            "metaDescription",
            "seoKeywords",
            "socialShareImage",
            "status",
            "featured",
            "allowComments",
            "publishAt",
            "is_published",
            "date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_published", "created_at", "updated_at"]

    def get_date(self, obj):
        moment = obj.publish_at or obj.created_at
        return f"{moment.strftime('%b')} {moment.day}, {moment.strftime('%Y')}" if moment else None


class BlogListSerializer(BlogSerializer):
    """Lighter payload for list views — leaves out body/SEO fields that
    only the editor and the single-post page need."""

    class Meta(BlogSerializer.Meta):
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "author",
            "category",
            "categoryLabel",
            "tags",
            "readTime",
            "coverImage",
            "status",
            "featured",
            "is_published",
            "date",
            "updated_at",
        ]


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "is_staff", "is_superuser", "is_active", "date_joined"]