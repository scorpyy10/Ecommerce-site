from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from .models import UserProfile
from .forms import ProfileForm, CustomUserCreationForm, CustomAuthenticationForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Welcome! Your account has been created successfully!')
        return response


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().first_name or form.get_user().username}!')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if created:
            print(f"Created new profile for user: {self.request.user.username}")
        
        context['profile'] = profile
        context['orders'] = self.request.user.orders.all()[:5] if hasattr(self.request.user, 'orders') else []
        
        # Add cart count for the template
        from projects.models import Cart
        cart = Cart.objects.filter(user=self.request.user).first()
        context['cart_count'] = cart.items.count() if cart else 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle profile updates from the profile page"""
        try:
            # Update user fields
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
            
        except Exception as e:
            print(f"Profile update error: {str(e)}")
            messages.error(request, 'There was an error updating your profile. Please try again.')
            return redirect('profile')


class EditProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/edit_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if created:
            print(f"Created new profile for user: {self.request.user.username}")
            
        context['form'] = ProfileForm(instance=profile)
        return context
    
    def post(self, request, *args, **kwargs):
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if created:
            print(f"Created new profile for user: {request.user.username}")
            
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        
        return self.render_to_response({'form': form})


@login_required
def custom_logout_view(request):
    """Custom logout view for debugging logout issues"""
    try:
        # Clear any payment-related session data
        session_keys_to_clear = ['address_data', 'last_order_id', 'payment_data']
        for key in session_keys_to_clear:
            if key in request.session:
                del request.session[key]
        
        # Force session save before logout
        request.session.save()
        
        # Store username for goodbye message
        username = request.user.username
        
        # Logout the user
        logout(request)
        
        # Add success message
        messages.success(request, f'Goodbye {username}! You have been successfully logged out.')
        
        # Redirect to home page
        return redirect('home')
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        messages.error(request, 'There was an issue logging you out. Please try again.')
        return redirect('home')
