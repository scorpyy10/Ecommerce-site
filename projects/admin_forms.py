from django import forms
from django.forms import inlineformset_factory
from .models import Project, Category, ProjectImage


class ProjectBaseForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'price', 'category', 'tags',
            'featured_image', 'featured_image_url', 'demo_video_url',
            'delivery_type', 'download_file', 'download_url',
            'is_active', 'meta_description'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Enter project title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Detailed description of the project...',
                'rows': 8
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Web, AI, ML, Python (comma-separated)'
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'accept': 'image/*'
            }),
            'featured_image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'https://drive.google.com/file/d/...'
            }),
            'demo_video_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'delivery_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
            }),
            'download_file': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200'
            }),
            'download_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'https://drive.google.com/file/d/...'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'SEO meta description (max 160 characters)',
                'maxlength': '160'
            }),
        }
        
        labels = {
            'title': 'Project Title *',
            'description': 'Description *',
            'price': 'Price (₹) *',
            'category': 'Category *',
            'tags': 'Tags',
            'featured_image': 'Featured Image (Upload)',
            'featured_image_url': 'Featured Image URL (External)',
            'demo_video_url': 'Demo Video URL',
            'delivery_type': 'Delivery Type *',
            'download_file': 'Download File (Upload)',
            'download_url': 'Download URL (External)',
            'is_active': 'Active',
            'meta_description': 'SEO Meta Description'
        }
        
        help_texts = {
            'tags': 'Comma-separated tags for better searchability',
            'featured_image_url': 'External image URL (e.g., Google Drive share link)',
            'demo_video_url': 'YouTube or Vimeo URL for project demo',
            'download_file': 'Upload file directly to server',
            'download_url': 'External download link (e.g., Google Drive)',
            'meta_description': 'Brief description for search engines (max 160 characters)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom styling for checkbox
        self.fields['is_active'].widget.attrs.update({
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
        })
        
        # Make certain fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['price'].required = True
        self.fields['category'].required = True
        self.fields['delivery_type'].required = True
        
        # Make tags optional
        self.fields['tags'].required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Clean and validate tags
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if len(tag_list) > 10:
                raise forms.ValidationError('Maximum 10 tags allowed.')
            return ', '.join(tag_list)
        return tags

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        download_file = cleaned_data.get('download_file')
        download_url = cleaned_data.get('download_url')
        
        # Validate delivery options
        if delivery_type in ['download', 'email']:
            if not download_file and not download_url:
                raise forms.ValidationError(
                    'Either upload a download file or provide a download URL for digital delivery.'
                )
        
        # Validate image options
        featured_image = cleaned_data.get('featured_image')
        featured_image_url = cleaned_data.get('featured_image_url')
        
        if not featured_image and not featured_image_url:
            raise forms.ValidationError(
                'Please provide either an uploaded image or an external image URL.'
            )
        
        return cleaned_data


class ProjectCreateForm(ProjectBaseForm):
    pass


class ProjectUpdateForm(ProjectBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For updates, we can be more lenient with image requirements
        pass


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'image_url']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Enter category name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Category description...',
                'rows': 4
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'accept': 'image/*'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'https://drive.google.com/file/d/...'
            })
        }
        
        labels = {
            'name': 'Category Name *',
            'description': 'Description',
            'image': 'Category Image (Upload)',
            'image_url': 'Category Image URL (External)'
        }
        
        help_texts = {
            'image': 'Upload an image directly to the server',
            'image_url': 'External image URL (e.g., Google Drive share link)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        
        # Check for duplicate names (excluding current instance for updates)
        queryset = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('A category with this name already exists.')
        
        return name


class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = ProjectImage
        fields = ['image', 'image_url', 'alt_text', 'order']
        
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'accept': 'image/*'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Alt text for accessibility'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200',
                'min': '0'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        alt_text = cleaned_data.get('alt_text')
        
        # Only validate if at least one field has data (not an empty form)
        if image or image_url or alt_text:
            if not image and not image_url:
                raise forms.ValidationError('Please provide either an uploaded image or an image URL.')
        
        return cleaned_data


# Formset for managing multiple project images
ProjectImageFormSet = inlineformset_factory(
    Project,
    ProjectImage,
    form=ProjectImageForm,
    extra=3,
    can_delete=True,
    max_num=10,
    validate_min=False,
    min_num=0
)
