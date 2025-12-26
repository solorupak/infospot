from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import InfoSpot, Content, CreditTransaction, UserCredit
from .utils import generate_qr_code_image, is_tenant_admin


class TenantRequiredMixin:
    """Mixin to ensure tenant context is available"""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            return redirect('tenant_not_found')
        return super().dispatch(request, *args, **kwargs)


class TenantAdminRequiredMixin(TenantRequiredMixin):
    """Mixin to ensure user is a tenant admin"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not is_tenant_admin(request.user, request.tenant):
            return redirect('access_denied')
        
        return super().dispatch(request, *args, **kwargs)


class InfoSpotAccessView(TenantRequiredMixin, View):
    """
    Handles QR/NFC code scans and content display.
    Implements access control logic based on spot type.
    """
    
    def get(self, request, spot_uuid):
        spot = get_object_or_404(InfoSpot, uuid=spot_uuid, is_active=True, tenant=request.tenant)
        
        # Access control logic
        if spot.access_type == 'free_ticketed':
            # Allow anonymous access
            return self.render_content(request, spot)
        
        elif spot.access_type == 'free_public':
            # Require authentication
            if not request.user.is_authenticated:
                return redirect('account_login', next=request.path)
            return self.render_content(request, spot)
        
        elif spot.access_type == 'paid':
            # Require authentication and sufficient credits
            if not request.user.is_authenticated:
                return redirect('account_login', next=request.path)
            
            # Check if user has already accessed this spot
            if self.has_accessed(request.user, spot):
                return self.render_content(request, spot)
            
            # Check if user has sufficient credits
            user_credits = getattr(request.user, 'credits', None)
            if user_credits and user_credits.balance >= spot.credit_cost:
                return self.render_credit_prompt(request, spot)
            else:
                return self.render_insufficient_credits(request, spot)
    
    def has_accessed(self, user, spot):
        """Check if user has already accessed this paid spot"""
        return CreditTransaction.objects.filter(
            user=user,
            info_spot=spot,
            transaction_type='spot_access'
        ).exists()
    
    def render_content(self, request, spot):
        """Render the content for the spot"""
        # Get user's preferred language or default to 'en'
        preferred_language = 'en'
        if request.user.is_authenticated and hasattr(request.user, 'enduser'):
            preferred_language = request.user.enduser.preferred_language
        
        # Get content in preferred language or fallback to default
        content = spot.contents.filter(language=preferred_language).first()
        if not content:
            content = spot.contents.first()
        
        context = {
            'spot': spot,
            'content': content,
            'available_languages': spot.contents.values_list('language', flat=True).distinct(),
        }
        
        # Record access
        self.record_access(request, spot, content.language if content else 'en')
        
        return render(request, 'tenants/spot_detail.html', context)
    
    def render_credit_prompt(self, request, spot):
        """Render credit spending prompt"""
        context = {
            'spot': spot,
            'user_credits': request.user.credits.balance,
            'required_credits': spot.credit_cost,
        }
        return render(request, 'tenants/credit_prompt.html', context)
    
    def render_insufficient_credits(self, request, spot):
        """Render insufficient credits page"""
        context = {
            'spot': spot,
            'user_credits': request.user.credits.balance,
            'required_credits': spot.credit_cost,
        }
        return render(request, 'tenants/insufficient_credits.html', context)
    
    def record_access(self, request, spot, language):
        """Record spot access for analytics"""
        from .models import SpotAccess
        
        SpotAccess.objects.create(
            info_spot=spot,
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            content_language=language,
        )
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SpendCreditsView(LoginRequiredMixin, TenantRequiredMixin, View):
    """Handles spending credits to access paid spots"""
    
    def post(self, request, spot_uuid):
        spot = get_object_or_404(InfoSpot, uuid=spot_uuid, access_type='paid', tenant=request.tenant)
        
        # Check if already accessed
        if CreditTransaction.objects.filter(
            user=request.user,
            info_spot=spot,
            transaction_type='spot_access'
        ).exists():
            return JsonResponse({'error': 'Already accessed'}, status=400)
        
        # Atomic credit deduction
        try:
            with transaction.atomic():
                user_credits = UserCredit.objects.select_for_update().get(user=request.user)
                
                if user_credits.balance < spot.credit_cost:
                    return JsonResponse({
                        'error': 'Insufficient credits',
                        'balance': user_credits.balance,
                        'required': spot.credit_cost
                    }, status=402)
                
                # Deduct credits
                user_credits.balance -= spot.credit_cost
                user_credits.total_spent += spot.credit_cost
                user_credits.save()
                
                # Record transaction
                CreditTransaction.objects.create(
                    user=request.user,
                    info_spot=spot,
                    tenant=spot.tenant,
                    credits_spent=spot.credit_cost
                )
            
            return JsonResponse({
                'success': True,
                'new_balance': user_credits.balance,
                'redirect_url': f'/spot/{spot.uuid}/'
            })
            
        except UserCredit.DoesNotExist:
            return JsonResponse({'error': 'User credit account not found'}, status=400)


class QRCodeDownloadView(TenantAdminRequiredMixin, View):
    """Download QR code image for info spot"""
    
    def get(self, request, spot_uuid):
        spot = get_object_or_404(InfoSpot, uuid=spot_uuid, tenant=request.tenant)
        
        # Generate QR code image
        qr_image = generate_qr_code_image(spot)
        
        # Return as image response
        response = HttpResponse(content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{spot.name}_qr_code.png"'
        qr_image.save(response, 'PNG')
        return response


class TenantNotFoundView(TemplateView):
    """View for when tenant is not found"""
    template_name = 'tenants/tenant_not_found.html'


class AccessDeniedView(TemplateView):
    """View for access denied"""
    template_name = 'tenants/access_denied.html'