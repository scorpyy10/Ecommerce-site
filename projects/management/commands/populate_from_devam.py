from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import json
from pathlib import Path
from projects.models import Project, Category, ProjectImage
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate projects with data from scraped Devam Project images'

    def handle(self, *args, **kwargs):
        json_file_path = Path('devam_scraped_data.json')

        if not json_file_path.exists():
            self.stdout.write(self.style.ERROR('JSON file not found. Make sure devam_scraped_data.json is in the project root.'))
            return

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Get or create a superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # Define project templates based on scraped images
        project_templates = [
            {
                'title': 'Modern Web Development Portfolio',
                'description': 'A comprehensive web development portfolio showcasing modern design principles and responsive layouts. Perfect for showcasing your development skills.',
                'category': 'Web Development',
                'tags': 'HTML, CSS, JavaScript, Portfolio, Responsive',
                'price': Decimal('49.99'),
                'image_keywords': ['project', 'banner', 'feature']
            },
            {
                'title': 'Professional Team Management System',
                'description': 'Complete team management dashboard with user authentication, role management, and project tracking capabilities.',
                'category': 'Software Development',
                'tags': 'Django, Python, Management, Dashboard, Admin',
                'price': Decimal('89.99'),
                'image_keywords': ['team', 'counter', 'service']
            },
            {
                'title': 'FAQ and Support System',
                'description': 'Interactive FAQ system with search functionality, categorization, and admin panel for content management.',
                'category': 'Web Development',
                'tags': 'FAQ, Support, Search, Admin, Django',
                'price': Decimal('34.99'),
                'image_keywords': ['faq', 'message', 'mail']
            },
            {
                'title': 'Blog and Content Management Platform',
                'description': 'Full-featured blogging platform with rich text editor, image uploads, comments, and SEO optimization.',
                'category': 'Content Management',
                'tags': 'Blog, CMS, Content, SEO, Publishing',
                'price': Decimal('79.99'),
                'image_keywords': ['blog', 'testimonial', 'quote']
            },
            {
                'title': 'Corporate Business Website Template',
                'description': 'Professional business website template with service pages, team showcase, and contact forms.',
                'category': 'Web Design',
                'tags': 'Business, Corporate, Template, Professional',
                'price': Decimal('59.99'),
                'image_keywords': ['banner', 'feature', 'service', 'footer']
            }
        ]

        # Create categories
        for template in project_templates:
            category, created = Category.objects.get_or_create(
                name=template['category'],
                defaults={'description': f'Projects related to {template["category"]}'}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Filter useful images (exclude logos and generic icons)
        useful_images = []
        for img in data['images']:
            alt_text = img['alt'].lower()
            # Skip logos and generic icons
            if not any(skip in alt_text for skip in ['logo', 'icon', 'shape', 'globe']):
                useful_images.append(img)

        self.stdout.write(f'Found {len(useful_images)} useful images out of {len(data["images"])} total images')

        # Create projects
        created_projects = 0
        for template in project_templates:
            # Find matching images for this project
            matching_images = []
            for img in useful_images:
                alt_text = img['alt'].lower()
                if any(keyword in alt_text for keyword in template['image_keywords']):
                    matching_images.append(img)

            if not matching_images:
                # If no specific matches, use some general project images
                matching_images = [img for img in useful_images if 'project' in img['alt'].lower()][:2]

            # Create the project
            category = Category.objects.get(name=template['category'])
            project = Project.objects.create(
                title=template['title'],
                description=template['description'],
                price=template['price'],
                category=category,
                tags=template['tags'],
                delivery_type='download',
                is_active=True,
                created_by=admin_user,
                meta_description=template['description'][:150]
            )

            # Add featured image URL to demo_video_url field for display
            if matching_images:
                featured_img = matching_images[0]
                project.demo_video_url = featured_img['url']  # Store image URL here for display
                # Add image URLs to the description for reference
                project.description += f"\n\nFeatured Images:\n"
                for img in matching_images[:3]:
                    project.description += f"- {img['alt']}: {img['url']}\n"
                project.save()

            created_projects += 1
            self.stdout.write(f'Created project: {project.title} with {len(matching_images)} images')

        # Add some additional projects with remaining images
        remaining_images = [img for img in useful_images if img['alt'] not in ['project-img', 'team-img', 'blog-img']]
        if remaining_images:
            additional_templates = [
                {
                    'title': 'IT Consulting Services Platform',
                    'description': 'Professional consulting platform with service listings, testimonials, and client management.',
                    'category': 'Business Solutions',
                    'tags': 'Consulting, Services, Business, Client Management',
                    'price': Decimal('99.99')
                },
                {
                    'title': 'Modern Dashboard Template',
                    'description': 'Clean and modern dashboard template with charts, widgets, and responsive design.',
                    'category': 'Web Design',
                    'tags': 'Dashboard, Admin, Template, Charts, Widgets',
                    'price': Decimal('44.99')
                }
            ]

            for template in additional_templates:
                category, created = Category.objects.get_or_create(
                    name=template['category'],
                    defaults={'description': f'Projects related to {template["category"]}'}
                )

                project = Project.objects.create(
                    title=template['title'],
                    description=template['description'],
                    price=template['price'],
                    category=category,
                    tags=template['tags'],
                    delivery_type='download',
                    is_active=True,
                    created_by=admin_user,
                    meta_description=template['description'][:150]
                )

                # Add random images to the description
                if remaining_images:
                    random_images = random.sample(remaining_images, min(2, len(remaining_images)))
                    project.description += f"\n\nFeatured Images:\n"
                    for img in random_images:
                        project.description += f"- {img['alt']}: {img['url']}\n"
                        if not project.demo_video_url:  # Use first image as demo URL
                            project.demo_video_url = img['url']
                    project.save()

                created_projects += 1
                self.stdout.write(f'Created additional project: {project.title}')

        # Summary
        total_projects = Project.objects.count()
        total_images = ProjectImage.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated database!\n'
                f'Created {created_projects} new projects\n'
                f'Total projects in database: {total_projects}\n'
                f'Total project images: {total_images}\n'
                f'Source: {data["source_url"]}\n'
                f'Scraped on: {data["scraped_at"]}'
            )
        )
