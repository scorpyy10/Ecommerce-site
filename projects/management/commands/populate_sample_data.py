from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projects.models import Category, Project
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {'name': 'Science Projects', 'slug': 'science', 'description': 'Science exhibition and fair projects'},
            {'name': 'Engineering Projects', 'slug': 'engineering', 'description': 'Engineering diploma and degree projects'},
            {'name': 'Robotics', 'slug': 'robotics', 'description': 'All kinds of robotics projects'},
            {'name': 'AI & ML', 'slug': 'ai-ml', 'description': 'Artificial Intelligence and Machine Learning projects'},
            {'name': 'Drone Technology', 'slug': 'drone-tech', 'description': 'Drone and UAV projects'},
            {'name': 'IoT Projects', 'slug': 'iot', 'description': 'Internet of Things projects'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        
        # Create sample projects
        projects_data = [
            {
                'title': 'Solar Power Plant Model',
                'slug': 'solar-power-plant-model',
                'description': 'A working model of solar power plant with battery storage and LED indicators. Perfect for science exhibitions and fairs.',
                'price': Decimal('2500.00'),
                'category_slug': 'science',
                'tags': 'solar, renewable energy, exhibition, science fair',
                'delivery_type': 'download',
            },
            {
                'title': 'Line Following Robot',
                'slug': 'line-following-robot',
                'description': 'Arduino-based line following robot with sensors and motors. Complete with source code and assembly instructions.',
                'price': Decimal('3500.00'),
                'category_slug': 'robotics',
                'tags': 'arduino, robot, sensors, automation',
                'delivery_type': 'download',
            },
            {
                'title': 'Smart Home Automation System',
                'slug': 'smart-home-automation',
                'description': 'IoT-based home automation system using ESP32. Control lights, fans, and appliances via mobile app.',
                'price': Decimal('4500.00'),
                'category_slug': 'iot',
                'tags': 'IoT, ESP32, home automation, smart home',
                'delivery_type': 'download',
            },
            {
                'title': 'Machine Learning Stock Predictor',
                'slug': 'ml-stock-predictor',
                'description': 'Python-based machine learning model to predict stock prices using historical data and technical indicators.',
                'price': Decimal('3000.00'),
                'category_slug': 'ai-ml',
                'tags': 'machine learning, python, stock prediction, AI',
                'delivery_type': 'download',
            },
            {
                'title': 'Automatic Plant Watering System',
                'slug': 'automatic-plant-watering',
                'description': 'Sensor-based automatic plant watering system with soil moisture detection and water pump control.',
                'price': Decimal('2000.00'),
                'category_slug': 'engineering',
                'tags': 'automation, sensors, agriculture, electronics',
                'delivery_type': 'download',
            },
            {
                'title': 'Quadcopter Drone Kit',
                'slug': 'quadcopter-drone-kit',
                'description': 'Complete quadcopter drone kit with flight controller, motors, and remote control. Assembly guide included.',
                'price': Decimal('8000.00'),
                'category_slug': 'drone-tech',
                'tags': 'drone, quadcopter, flight controller, UAV',
                'delivery_type': 'physical',
            },
            {
                'title': 'Traffic Light Controller',
                'slug': 'traffic-light-controller',
                'description': 'Microcontroller-based traffic light system with timer control and emergency override features.',
                'price': Decimal('1800.00'),
                'category_slug': 'engineering',
                'tags': 'traffic, microcontroller, automation, electronics',
                'delivery_type': 'download',
            },
            {
                'title': 'Voice Controlled Robot',
                'slug': 'voice-controlled-robot',
                'description': 'Voice recognition robot that responds to spoken commands. Uses speech recognition and Arduino control.',
                'price': Decimal('4200.00'),
                'category_slug': 'robotics',
                'tags': 'voice control, speech recognition, robot, AI',
                'delivery_type': 'download',
            },
        ]
        
        for project_data in projects_data:
            category = Category.objects.get(slug=project_data['category_slug'])
            project, created = Project.objects.get_or_create(
                slug=project_data['slug'],
                defaults={
                    'title': project_data['title'],
                    'description': project_data['description'],
                    'price': project_data['price'],
                    'category': category,
                    'tags': project_data['tags'],
                    'delivery_type': project_data['delivery_type'],
                    'created_by': admin_user,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created project: {project.title}')
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
