from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
import uuid
from PIL import Image


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="External image URL (e.g., Google Drive link)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Get the category image URL - prioritize external URL over local file"""
        if self.image_url:
            return Project.convert_google_drive_url(self.image_url)
        elif self.image:
            return self.image.url
        return None
    
    def __str__(self):
        return self.name


class Project(models.Model):
    DELIVERY_CHOICES = [
        ('download', 'Download Link'),
        ('email', 'Email Delivery'),
        ('physical', 'Physical Delivery'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='projects')
    tags = models.CharField(max_length=500, help_text="Comma-separated tags (e.g., Web, AI, ML)")
    
    # Images and videos
    featured_image = models.ImageField(upload_to='projects/images/', blank=True, null=True)
    featured_image_url = models.URLField(blank=True, null=True, help_text="External image URL (e.g., Google Drive link)")
    demo_video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    
    # Delivery
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='download')
    download_file = models.FileField(upload_to='projects/files/', blank=True, null=True)
    download_url = models.URLField(blank=True, help_text="External download link")
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
        # Resize image if too large
        if self.featured_image:
            img = Image.open(self.featured_image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.featured_image.path)
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug': self.slug})
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def get_featured_image_url(self):
        """Get the featured image URL - prioritize external URL over local file"""
        if self.featured_image_url:
            return self.convert_google_drive_url(self.featured_image_url)
        elif self.featured_image:
            return self.featured_image.url
        return None
    
    @staticmethod
    def convert_google_drive_url(url):
        """Convert Google Drive sharing URL to direct image URL"""
        if 'drive.google.com' in url and '/file/d/' in url:
            try:
                file_id = url.split('/file/d/')[1].split('/')[0]
                # Use Google User Content format which has better CORS support
                return f'https://lh3.googleusercontent.com/d/{file_id}=w800'
            except IndexError:
                return url
        return url
    
    def get_embed_video_url(self):
        """Convert YouTube/Vimeo URL to embeddable format"""
        if not self.demo_video_url:
            return None
        
        url = self.demo_video_url
        
        # Convert YouTube URLs
        if 'youtube.com/watch' in url:
            try:
                video_id = url.split('v=')[1].split('&')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            except IndexError:
                pass
        elif 'youtu.be/' in url:
            try:
                video_id = url.split('youtu.be/')[1].split('?')[0]
                return f'https://www.youtube.com/embed/{video_id}'
            except IndexError:
                pass
        
        # Convert Vimeo URLs
        elif 'vimeo.com/' in url:
            try:
                video_id = url.split('vimeo.com/')[1].split('?')[0]
                return f'https://player.vimeo.com/video/{video_id}'
            except IndexError:
                pass
        
        # If already an embed URL or other format, return as-is
        return url
    
    def __str__(self):
        return self.title


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/gallery/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="External image URL (e.g., Google Drive link)")
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image if too large
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 1200 or img.width > 1200:
                output_size = (1200, 1200)
                img.thumbnail(output_size)
                img.save(self.image.path)
    
    def get_image_url(self):
        """Get the image URL - prioritize external URL over local file"""
        if self.image_url:
            return Project.convert_google_drive_url(self.image_url)
        elif self.image:
            return self.image.url
        return None
    
    def __str__(self):
        return f"{self.project.title} - Image {self.order}"


class Cart(models.Model):
    session_key = models.CharField(max_length=40)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart {self.id} - {self.user or self.session_key}"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'project']
    
    def get_total_price(self):
        return self.project.price * self.quantity
    
    def __str__(self):
        return f"{self.project.title} x {self.quantity}"
