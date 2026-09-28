from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class UserManager(BaseUserManager):
    """Custom manager where email is the unique identifier instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model that logs in with email instead of username."""

    username = None
    email = models.EmailField(unique=True)

    groups = models.ManyToManyField(Group, related_name="blog_user_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="blog_user_permissions_set", blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class BlogCategory(models.TextChoices):
    """Edit these to change the categories shown in the admin dashboard
    and the public blog filter tabs. The `value` is what's stored/sent
    over the API; the label is what's displayed."""

    NEWS = "news", "Hotel News"
    EVENTS = "events", "Events"
    DINING = "dining", "Dining"
    OFFERS = "offers", "Offers"
    TRAVEL = "travel", "Travel Tips"


class BlogStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


def blog_cover_upload_to(instance, filename):
    return f"blog/covers/{filename}"


def blog_social_upload_to(instance, filename):
    return f"blog/social/{filename}"


class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    # Free-text byline shown publicly (e.g. "Front Office Team") — separate
    # from `created_by`, which tracks which admin user actually made the post.
    author = models.CharField(max_length=150, blank=True)

    category = models.CharField(max_length=20, choices=BlogCategory.choices, default=BlogCategory.NEWS)
    category_label_override = models.CharField(max_length=100, blank=True)

    tags = models.JSONField(default=list, blank=True)
    read_time = models.CharField(max_length=50, blank=True)

    cover_image = models.ImageField(upload_to=blog_cover_upload_to, blank=True, null=True)
    cover_image_alt = models.CharField(max_length=255, blank=True)
    cover_image_caption = models.CharField(max_length=255, blank=True)

    # The block-based body: a JSON list of
    # {id, type, text/image/video/items/label/url, ...}
    body = models.JSONField(default=list, blank=True)

    seo_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    seo_keywords = models.JSONField(default=list, blank=True)
    social_share_image = models.ImageField(upload_to=blog_social_upload_to, blank=True, null=True)

    status = models.CharField(max_length=20, choices=BlogStatus.choices, default=BlogStatus.DRAFT)
    featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    publish_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blogs",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        """Kept for backward compatibility with anything still reading the
        old boolean flag."""
        return self.status == BlogStatus.PUBLISHED

    @property
    def category_label(self):
        return self.category_label_override or self.get_category_display()

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:240] or "post"
            slug = base
            i = 1
            while Blog.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug

        # Publishing without an explicit schedule stamps "now".
        if self.status == BlogStatus.PUBLISHED and not self.publish_at:
            self.publish_at = timezone.now()

        super().save(*args, **kwargs)


def content_upload_to(instance, filename):
    return f"blog/content/{filename}"


class BlogContentUpload(models.Model):
    """Files uploaded from inside the block editor (an image or video
    dropped into a heading/paragraph/image/video block) — not tied to a
    specific Blog row, since the post may not be saved yet."""

    file = models.FileField(upload_to=content_upload_to)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name