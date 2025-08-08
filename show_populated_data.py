#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devam_marketplace.settings')
django.setup()

from projects.models import Project, Category

def show_populated_data():
    print("=" * 80)
    print("POPULATED DATA FROM DEVAMPROJECT.COM")
    print("=" * 80)
    
    # Show categories
    categories = Category.objects.all()
    print(f"\n📁 CATEGORIES ({categories.count()}):")
    print("-" * 40)
    for category in categories:
        project_count = category.projects.count()
        print(f"• {category.name} ({project_count} projects)")
        if category.description:
            print(f"  Description: {category.description}")
        print()
    
    # Show projects
    projects = Project.objects.all().order_by('category__name', 'title')
    print(f"\n🚀 PROJECTS ({projects.count()}):")
    print("-" * 40)
    
    for project in projects:
        print(f"\n📦 {project.title}")
        print(f"   Category: {project.category.name}")
        print(f"   Price: ${project.price}")
        print(f"   Tags: {project.tags}")
        print(f"   Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        if project.demo_video_url:
            print(f"   Featured Image: {project.demo_video_url}")
        
        # Show description (truncated)
        desc_lines = project.description.split('\n')
        main_desc = desc_lines[0]
        if len(main_desc) > 100:
            main_desc = main_desc[:100] + "..."
        print(f"   Description: {main_desc}")
        
        # Show image URLs if they exist in description
        if "Featured Images:" in project.description:
            image_section = project.description.split("Featured Images:")[1].strip()
            image_lines = [line.strip() for line in image_section.split('\n') if line.strip().startswith('-')]
            if image_lines:
                print(f"   Images ({len(image_lines)}):")
                for img_line in image_lines[:3]:  # Show first 3
                    if ':' in img_line:
                        alt_text = img_line.split(':')[0].replace('-', '').strip()
                        url = ':'.join(img_line.split(':')[1:]).strip()
                        print(f"     • {alt_text}: {url}")
                if len(image_lines) > 3:
                    print(f"     ... and {len(image_lines) - 3} more images")
        
        print(f"   URL: http://127.0.0.1:8000{project.get_absolute_url()}")
        print()
    
    print("=" * 80)
    print("🎉 Data successfully populated from devamproject.com!")
    print("🌐 View your marketplace at: http://127.0.0.1:8000/")
    print("🔧 Admin panel at: http://127.0.0.1:8000/admin/ (admin/admin123)")
    print("=" * 80)

if __name__ == "__main__":
    show_populated_data()
