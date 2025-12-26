# Design Document: Multi-Tenant Info Spots Platform

## Overview

This document outlines the technical design for a multi-tenant SaaS platform enabling organizations to create QR/NFC-based information points. The system uses Django with HTMX for dynamic interactions and Bootstrap for responsive UI. The architecture supports tenant isolation via shared database with tenant identifiers, subdomain-based routing, and differentiated access control for ticketed venues (anonymous access) versus public spots (authenticated access with optional payment).

**Technology Stack:**
- Backend: Django 5.x with Python 3.11+
- Frontend: HTMX 1.9+, Bootstrap 5.3+
- Database: PostgreSQL 15+ (shared database, shared schema with tenant isolation)
- QR Code Generation: django-qr-code with Segno library
- Payment Processing: Stripe API
- Media Storage: Django storage backend (local/S3-compatible)
- Caching: Redis for session management and content caching

## Architecture

### Multi-Tenancy Strategy

The system implements a **shared database, shared schema** approach with tenant identification through a `tenant_id` foreign key. This strategy balances isolation, scalability, and resource efficiency.

**Rationale:**
- Shared database reduces infrastructure complexity and costs
- Tenant identifier provides logical data isolation
- Easier to maintain and deploy updates across all tenants
- Supports dynamic tenant provisioning without database operations
- Suitable for SaaS with many tenants sharing similar data structures

### Subdomain Routing

Each tenant receives a unique subdomain (e.g., `museum.infospot.com`, `zoo.infospot.com`). A custom Django middleware extracts the subdomain from the request and sets the active tenant context for the request lifecycle.

```
Request Flow:
1. User accesses museum.infospot.com/spot/123
2. TenantMiddleware extracts "museum" subdomain
3. Middleware queries Tenant model to find tenant
4. Sets tenant in thread-local storage for request duration
5. All queries automatically filter by tenant_id
6. Response rendered with tenant-specific branding
```

### Authentication Architecture

The system implements **dual authentication modes**:

1. **Shared End User Authentication**: Global user accounts accessible across all tenant subdomains
   - Single sign-on experience across tenants
   - Centralized user profile management
   - Required for public spot access
   - Optional for ticketed venue access

2. **Tenant Admin Authentication**: Separate admin accounts per tenant
   - Isolated administrative access
   - Tenant-specific permissions
   - Access via tenant subdomain admin interface

**Session Management:**
- Django sessions with Redis backend for cross-subdomain support
- Session cookies set with domain=`.infospot.com` for subdomain sharing
- Separate session keys for end users vs tenant admins

## Components and Interfaces

### Core Models

#### Tenant Model
```python
class Tenant(models.Model):
    """Represents an organization using the platform"""
    subdomain = models.SlugField(unique=True, max_length=63)
    name = models.CharField(max_length=255)
    venue_type = models.CharField(
        max_length=50,
        choices=[
            ('ticketed', 'Ticketed Venue'),
            ('public', 'Public Spots'),
            ('mixed', 'Mixed')
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Branding
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    
    # Metadata
    contact_email = models.EmailField()
    timezone = models.CharField(max_length=50, default='UTC')
```

#### TenantAdmin Model
```python
class TenantAdmin(models.Model):
    """Admin users for specific tenants"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Administrator'),
            ('editor', 'Content Editor')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'tenant')
```

#### InfoSpot Model
```python
class InfoSpot(models.Model):
    """Represents a physical location with QR/NFC code"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location_description = models.CharField(max_length=500, blank=True)
    
    # Access Control
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('free_ticketed', 'Free (Ticketed Venue)'),
            ('free_public', 'Free (Public)'),
            ('paid', 'Paid (Credits Required)')
        ]
    )
    credit_cost = models.IntegerField(
        default=1,
        help_text="Number of credits required to access this spot"
    )
    
    # QR/NFC Identifiers
    qr_code_data = models.CharField(max_length=500, unique=True)
    nfc_tag_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Ordering
    display_order = models.IntegerField(default=0)
```

#### Content Model
```python
class Content(models.Model):
    """Audio and text content for info spots"""
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE, related_name='contents')
    language = models.CharField(max_length=10, default='en')
    
    # Content Types
    title = models.CharField(max_length=255)
    text_content = models.TextField(blank=True)
    audio_file = models.FileField(
        upload_to='audio_content/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['mp3', 'wav', 'aac', 'm4a'])]
    )
    audio_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration in seconds"
    )
    
    # Metadata
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('info_spot', 'language')
```

#### EndUser Model
```python
class EndUser(models.Model):
    """Global end user accounts (extends Django User)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_language = models.CharField(max_length=10, default='en')
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### SpotAccess Model
```python
class SpotAccess(models.Model):
    """Tracks user access to info spots"""
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Null for anonymous ticketed venue access"
    )
    
    # Access Details
    accessed_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Content Consumption
    content_language = models.CharField(max_length=10)
    audio_played = models.BooleanField(default=False)
    audio_play_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Seconds of audio played"
    )
    text_viewed = models.BooleanField(default=False)
```

#### UserCredit Model
```python
class UserCredit(models.Model):
    """Tracks user credit balance"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credits')
    balance = models.IntegerField(default=0, help_text="Number of credits available")
    total_purchased = models.IntegerField(default=0, help_text="Total credits ever purchased")
    total_spent = models.IntegerField(default=0, help_text="Total credits ever spent")
    updated_at = models.DateTimeField(auto_now=True)
```

#### CreditPurchase Model
```python
class CreditPurchase(models.Model):
    """Tracks credit purchase transactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Purchase Details
    credits_purchased = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    price_per_credit = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Details
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('succeeded', 'Succeeded'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded')
        ]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class CreditTransaction Model
```python
class CreditTransaction(models.Model):
    """Tracks individual credit spending on spots"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info_spot = models.ForeignKey(InfoSpot, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Transaction Details
    credits_spent = models.IntegerField()
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('spot_access', 'Spot Access'),
            ('refund', 'Refund')
        ],
        default='spot_access'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
```

### Middleware Components

#### TenantMiddleware
```python
class TenantMiddleware:
    """
    Extracts tenant from subdomain and sets active tenant context.
    Handles both tenant admin and end user requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract subdomain from request.get_host()
        host = request.get_host().split(':')[0]
        subdomain = self.extract_subdomain(host)
        
        if subdomain and subdomain != 'www':
            try:
                tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                request.tenant = tenant
                # Set thread-local for query filtering
                set_current_tenant(tenant)
            except Tenant.DoesNotExist:
                return HttpResponseNotFound("Tenant not found")
        else:
            request.tenant = None
        
        response = self.get_response(request)
        clear_current_tenant()
        return response
```

#### TenantQuerySetMixin
```python
class TenantQuerySetMixin:
    """
    Automatically filters querysets by current tenant.
    Applied to all tenant-scoped models.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            return qs.filter(tenant=tenant)
        return qs
```

### View Layer Architecture

#### Base Views

**TenantAdminView**: Base class for all tenant admin views
- Requires authentication and tenant admin permission
- Automatically filters data by tenant
- Provides tenant context to templates

**EndUserView**: Base class for end user views
- Optional authentication (required for public spots)
- Provides user context and access history
- Handles language preference

**HTMXMixin**: Mixin for HTMX-enabled views
- Detects HTMX requests via `HX-Request` header
- Returns partial templates for HTMX requests
- Returns full templates for regular requests

#### Key View Patterns

**Info Spot Access View**:
```python
class InfoSpotAccessView(View):
    """
    Handles QR/NFC code scans and content display.
    Implements access control logic based on spot type.
    """
    
    def get(self, request, spot_uuid):
        spot = get_object_or_404(InfoSpot, uuid=spot_uuid, is_active=True)
        
        # Access control logic
        if spot.access_type == 'free_ticketed':
            # Allow anonymous access
            return self.render_content(request, spot)
        
        elif spot.access_type == 'free_public':
            # Require authentication
            if not request.user.is_authenticated:
                return redirect('login', next=request.path)
            return self.render_content(request, spot)
        
        elif spot.access_type == 'paid':
            # Require authentication and sufficient credits
            if not request.user.is_authenticated:
                return redirect('login', next=request.path)
            
            # Check if user has already accessed this spot
            if self.has_accessed(request.user, spot):
                return self.render_content(request, spot)
            
            # Check if user has sufficient credits
            user_credits = request.user.credits.balance
            if user_credits >= spot.credit_cost:
                return self.render_credit_prompt(request, spot)
            else:
                return self.render_insufficient_credits(request, spot)
```

### HTMX Integration Patterns

**Partial Template Structure**:
```
templates/
├── base.html                    # Full page layout
├── info_spots/
│   ├── spot_detail.html        # Full page template
│   ├── _spot_content.html      # Partial: content section
│   ├── _audio_player.html      # Partial: audio controls
│   └── _payment_form.html      # Partial: payment UI
```

**HTMX Attributes Usage**:
- `hx-get`: Load content dynamically (e.g., language switching)
- `hx-post`: Submit forms without page reload (e.g., payment)
- `hx-target`: Specify which element to update
- `hx-swap`: Control how content is swapped (innerHTML, outerHTML, etc.)
- `hx-trigger`: Define trigger events (click, change, load)
- `hx-indicator`: Show loading states during requests

**Example HTMX Template**:
```html
<!-- Language switcher -->
<select hx-get="{% url 'spot_content' spot.uuid %}" 
        hx-target="#content-area"
        hx-swap="innerHTML"
        hx-indicator="#loading"
        name="language">
    <option value="en">English</option>
    <option value="es">Español</option>
</select>

<!-- Content area -->
<div id="content-area">
    {% include 'info_spots/_spot_content.html' %}
</div>

<!-- Loading indicator -->
<div id="loading" class="htmx-indicator">
    <div class="spinner-border" role="status"></div>
</div>
```

### QR Code Generation

**QR Code Data Format**:
```
https://{tenant_subdomain}.infospot.com/spot/{spot_uuid}
```

**Generation Process**:
1. When InfoSpot is created, generate unique UUID
2. Construct QR code URL with tenant subdomain and UUID
3. Use django-qr-code to generate QR image
4. Store QR data string in `qr_code_data` field
5. Provide download endpoint for tenant admins

**Implementation**:
```python
from qr_code.qrcode.utils import QRCodeOptions
from django_qr_code.qrcode.maker import make_qr_code_image

def generate_qr_code(info_spot):
    """Generate QR code for info spot"""
    url = f"https://{info_spot.tenant.subdomain}.infospot.com/spot/{info_spot.uuid}"
    info_spot.qr_code_data = url
    info_spot.save()
    
    # Generate QR code image
    options = QRCodeOptions(size='L', border=4, error_correction='M')
    qr_image = make_qr_code_image(url, qr_code_options=options)
    return qr_image
```

### Payment Integration

**Stripe Integration Flow for Credit Purchase**:
1. User clicks "Buy Credits" button
2. HTMX loads credit purchase form with package options (e.g., 10 credits for $5, 20 credits for $9, 50 credits for $20)
3. User selects package and enters payment details
4. Frontend creates Stripe PaymentIntent via AJAX
5. Backend validates and processes payment
6. On success, add credits to user's balance
7. Record purchase in CreditPurchase model
8. Redirect to success page showing new balance

**Credit Spending Flow**:
1. User scans paid spot QR code
2. System checks if user has already accessed this spot (no double-charging)
3. If not accessed, check credit balance
4. If sufficient credits, show "Unlock with X credits" button
5. User confirms, system deducts credits atomically
6. Record transaction in CreditTransaction model
7. Grant access and display content

**Credit Purchase View**:
```python
class PurchaseCreditsView(LoginRequiredMixin, View):
    """Handles credit package purchase"""
    
    CREDIT_PACKAGES = [
        {'credits': 10, 'price': 5.00, 'price_per_credit': 0.50},
        {'credits': 20, 'price': 9.00, 'price_per_credit': 0.45},
        {'credits': 50, 'price': 20.00, 'price_per_credit': 0.40},
    ]
    
    def post(self, request):
        package_id = request.POST.get('package_id')
        package = self.CREDIT_PACKAGES[int(package_id)]
        
        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(package['price'] * 100),  # Convert to cents
            currency='usd',
            metadata={
                'user_id': request.user.id,
                'credits': package['credits'],
                'type': 'credit_purchase'
            }
        )
        
        # Create CreditPurchase record
        purchase = CreditPurchase.objects.create(
            user=request.user,
            credits_purchased=package['credits'],
            amount=package['price'],
            price_per_credit=package['price_per_credit'],
            stripe_payment_intent_id=intent.id,
            status='pending'
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'purchase_id': purchase.id
        })

class SpendCreditsView(LoginRequiredMixin, View):
    """Handles spending credits to access paid spots"""
    
    def post(self, request, spot_uuid):
        spot = get_object_or_404(InfoSpot, uuid=spot_uuid, access_type='paid')
        
        # Check if already accessed
        if CreditTransaction.objects.filter(
            user=request.user,
            info_spot=spot,
            transaction_type='spot_access'
        ).exists():
            return JsonResponse({'error': 'Already accessed'}, status=400)
        
        # Atomic credit deduction
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
            'redirect_url': reverse('spot_content', args=[spot.uuid])
        })
```

## Data Models

### Entity Relationship Diagram

```mermaid
erDiagram
    Tenant ||--o{ InfoSpot : "has many"
    Tenant ||--o{ TenantAdmin : "has many"
    Tenant ||--o{ CreditTransaction : "receives revenue from"
    
    InfoSpot ||--o{ Content : "has many"
    InfoSpot ||--o{ SpotAccess : "tracks"
    InfoSpot ||--o{ CreditTransaction : "requires credits"
    
    User ||--o| EndUser : "extends"
    User ||--o| UserCredit : "has"
    User ||--o{ TenantAdmin : "can be"
    User ||--o{ SpotAccess : "creates"
    User ||--o{ CreditPurchase : "makes"
    User ||--o{ CreditTransaction : "spends"
    
    Tenant {
        string subdomain PK
        string name
        string venue_type
        boolean is_active
        string logo
        string primary_color
        string secondary_color
    }
    
    InfoSpot {
        uuid uuid PK
        fk tenant_id
        string name
        string access_type
        int credit_cost
        string qr_code_data
        string nfc_tag_id
        boolean is_active
    }
    
    Content {
        int id PK
        fk info_spot_id
        string language
        string title
        text text_content
        file audio_file
        int version
    }
    
    SpotAccess {
        int id PK
        fk info_spot_id
        fk user_id
        datetime accessed_at
        string content_language
        boolean audio_played
        int audio_play_duration
    }
    
    Payment {
        int id PK
        fk user_id
        fk info_spot_id
        fk tenant_id
        decimal amount
        string stripe_payment_intent_id
        string status
    }
    
    UserCredit {
        int id PK
        fk user_id
        int balance
        int total_purchased
        int total_spent
    }
    
    CreditPurchase {
        int id PK
        fk user_id
        int credits_purchased
        decimal amount
        string stripe_payment_intent_id
        string status
    }
    
    CreditTransaction {
        int id PK
        fk user_id
        fk info_spot_id
        fk tenant_id
        int credits_spent
        string transaction_type
    }
```

### Database Indexes

**Critical Indexes for Performance**:
```python
class InfoSpot(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['uuid']),
            models.Index(fields=['qr_code_data']),
            models.Index(fields=['nfc_tag_id']),
        ]

class SpotAccess(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['info_spot', 'accessed_at']),
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['session_id']),
        ]

class Payment(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]

class CreditPurchase(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', 'created_at']),
        ]

class CreditTransaction(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['info_spot', 'user']),  # Check if already accessed
        ]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Tenant Subdomain Uniqueness
*For any* two tenants in the system, their subdomains must be unique and no two tenants can share the same subdomain identifier.
**Validates: Requirements 1.1**

### Property 2: Tenant Data Isolation
*For any* query executed within a tenant context, the results must only include data belonging to that tenant and must not include data from any other tenant.
**Validates: Requirements 1.2, 1.3**

### Property 3: Tenant Deletion Cascade
*For any* tenant that is deleted, all data associated with that tenant (info spots, content, payments) must be removed, while data belonging to other tenants must remain unchanged.
**Validates: Requirements 1.5**

### Property 4: Global User Authentication
*For any* end user account created in the system, that account must be accessible and usable for authentication across all tenant subdomains without requiring separate registration.
**Validates: Requirements 2.1, 2.3**

### Property 5: User Profile Global Consistency
*For any* end user profile update, the changes must be immediately visible across all tenant subdomains where that user accesses the system.
**Validates: Requirements 2.4, 2.5**

### Property 6: Ticketed Venue Anonymous Access
*For any* info spot belonging to a ticketed venue, anonymous (unauthenticated) users must be able to access the content without login or payment requirements.
**Validates: Requirements 5.1, 5.2, 5.3, 8.1**

### Property 7: Public Spot Authentication Requirement
*For any* info spot marked as public (free or paid), unauthenticated access attempts must be rejected and redirected to login.
**Validates: Requirements 2.2, 6.2, 8.2**

### Property 8: Credit-Based Access Gating
*For any* authenticated user accessing a paid spot without prior access and with insufficient credits, the system must prompt for credit purchase and block content access until sufficient credits are available.
**Validates: Requirements 6.4, 8.3**

### Property 9: Credit Spending Unlocks Content
*For any* paid spot, when a user with sufficient credits spends the required credits, they must immediately gain access to that spot's content and the credits must be deducted from their balance.
**Validates: Requirements 6.5, 9.2**

### Property 10: Tenant Admin Data Association
*For any* info spot created by a tenant admin, that spot must be associated exclusively with the admin's tenant and must not be visible or accessible to other tenants.
**Validates: Requirements 3.2, 3.4**

### Property 11: QR Code Uniqueness and Round-Trip
*For any* info spot, the generated QR code must be unique across all spots, and scanning the QR code must resolve to the exact same info spot and tenant that generated it.
**Validates: Requirements 4.1, 4.3, 4.4**

### Property 12: NFC Tag Uniqueness and Resolution
*For any* info spot with an NFC tag, the tag identifier must be unique across all spots, and tapping the tag must resolve to the correct info spot and tenant.
**Validates: Requirements 4.2, 4.5**

### Property 13: Audio Format Validation
*For any* audio file upload, the system must accept files in MP3, WAV, or AAC formats and reject files in other formats.
**Validates: Requirements 7.1**

### Property 14: Multiple Content Per Spot
*For any* info spot, tenant admins must be able to associate multiple content items (different languages, audio and text combinations) with that single spot.
**Validates: Requirements 7.3**

### Property 15: Content Update Immediacy
*For any* content update made by a tenant admin, end users accessing that info spot must immediately see the updated content without caching delays.
**Validates: Requirements 7.4**

### Property 16: File Size Validation
*For any* content file upload, the system must enforce maximum file size limits and reject uploads that exceed the defined threshold.
**Validates: Requirements 7.5**

### Property 17: Access History Tracking
*For any* authenticated user accessing public spots, those access events must be recorded in their history and be retrievable later.
**Validates: Requirements 8.6**

### Property 18: Credit Purchase and Transaction Records
*For any* completed credit purchase or credit spending transaction, the system must create and persist records accessible to both the end user and the tenant admin (for credit spending).
**Validates: Requirements 9.4, 9.5**

### Property 18a: Credit Balance Accuracy
*For any* user, their credit balance must equal total purchased credits minus total spent credits at all times.
**Validates: Requirements 9.2**

### Property 18b: No Double Charging
*For any* paid spot, a user must only be charged credits once for accessing that spot, and subsequent accesses must not deduct additional credits.
**Validates: Requirements 6.5**

### Property 19: Revenue Calculation Accuracy
*For any* tenant, the total revenue displayed in the dashboard must equal the sum of all credit spending transactions (credits spent × tenant's credit value) for that tenant's paid spots.
**Validates: Requirements 10.1**

### Property 20: Transaction Report Completeness
*For any* credit spending transaction, the transaction report must include all required fields: date, credits spent, user information, and spot information.
**Validates: Requirements 10.2**

### Property 21: Date Range Filtering
*For any* date range filter applied to transaction reports, only credit transactions with timestamps within that range must be included in the results.
**Validates: Requirements 10.3**

### Property 22: Analytics Access Recording
*For any* info spot access, the system must record an analytics event with timestamp, and for ticketed venues the event must not include user identification, while for public spots it must include user identification.
**Validates: Requirements 14.1, 14.2, 14.3, 5.4, 6.6**

### Property 23: Access Count Accuracy
*For any* info spot, the access count displayed in analytics must equal the number of recorded access events for that spot.
**Validates: Requirements 14.4**

### Property 24: Popularity Ranking
*For any* set of info spots within a tenant, when ranked by popularity, spots with higher access counts must appear before spots with lower access counts.
**Validates: Requirements 14.6**

### Property 25: Average Consumption Time Calculation
*For any* info spot with recorded consumption times, the average consumption time displayed must equal the arithmetic mean of all recorded consumption durations.
**Validates: Requirements 14.7**

### Property 26: Multi-Language Content Support
*For any* info spot, tenant admins must be able to create multiple content versions in different languages, with each language version being unique per spot.
**Validates: Requirements 15.1, 15.2**

### Property 27: Language Preference Matching
*For any* end user with a preferred language accessing an info spot, if content exists in that language, the system must display that language version; otherwise, it must fall back to the default language.
**Validates: Requirements 15.3, 15.4**

### Property 28: Language Switching
*For any* info spot with multiple language versions, end users must be able to manually switch between available languages and see the corresponding content update.
**Validates: Requirements 15.5**

### Property 29: Content Versioning
*For any* content update, the version number must increment, enabling offline cache invalidation and synchronization.
**Validates: Requirements 16.2, 16.5**

### Property 30: Rate Limiting Enforcement
*For any* user or IP address making requests, when the request rate exceeds the defined threshold, subsequent requests must be rejected with rate limit errors.
**Validates: Requirements 17.4**

### Property 31: Data Deletion with Analytics Preservation
*For any* end user requesting data deletion, their personal information must be removed from the system while anonymized analytics data must be preserved.
**Validates: Requirements 17.5**

### Property 32: Tenant Branding Application
*For any* tenant with configured branding (logo and colors), those branding elements must be applied to all pages within that tenant's subdomain.
**Validates: Requirements 18.1, 18.2, 18.3, 18.5**

## Error Handling

### Error Categories

**1. Tenant Resolution Errors**
- Invalid subdomain: Return 404 with "Tenant not found" message
- Inactive tenant: Return 403 with "Tenant is not active" message
- Missing tenant context: Redirect to main platform landing page

**2. Authentication Errors**
- Unauthenticated access to public spot: Redirect to login with `next` parameter
- Invalid credentials: Return 401 with error message
- Session expired: Redirect to login with session timeout message
- Cross-tenant admin access: Return 403 with "Access denied" message

**3. Authorization Errors**
- Tenant admin accessing another tenant's data: Return 403 with "Access denied"
- Non-admin user accessing admin endpoints: Return 403 with "Admin access required"
- Insufficient credits for paid spot: Display credit purchase prompt, not error
- Already accessed spot: Allow access without additional charge

**4. Payment and Credit Errors**
- Payment processing failure: Display user-friendly error with retry option
- Invalid payment amount: Return 400 with validation error
- Duplicate payment attempt: Return 409 with "Payment already processed"
- Insufficient credits: Display credit balance and purchase options
- Invalid credit package: Return 400 with "Invalid package selection"
- Concurrent credit spending: Use database locks to prevent race conditions
- Stripe API errors: Log detailed error, show generic message to user

**5. Content Errors**
- Invalid file format: Return 400 with "Unsupported file format" and list of accepted formats
- File size exceeded: Return 413 with "File too large" and maximum size
- Missing required content: Return 400 with specific field errors
- Content not found: Return 404 with "Content not available"

**6. QR/NFC Errors**
- Invalid QR code format: Return 400 with "Invalid QR code"
- QR code for inactive spot: Return 410 with "This info spot is no longer available"
- NFC tag not found: Return 404 with "NFC tag not recognized"

**7. Data Validation Errors**
- Duplicate subdomain: Return 400 with "Subdomain already exists"
- Invalid subdomain format: Return 400 with format requirements
- Missing required fields: Return 400 with list of missing fields
- Invalid data types: Return 400 with type mismatch details

### Error Response Format

**API Errors (JSON)**:
```json
{
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "You don't have enough credits to access this spot.",
    "details": {
      "balance": 5,
      "required": 10,
      "spot_name": "Ancient Artifact Display"
    },
    "timestamp": "2024-12-26T10:30:00Z"
  }
}
```

**Web Errors (HTML)**:
- Use Bootstrap alert components for inline errors
- Dedicated error pages for 404, 403, 500
- HTMX error handling with `hx-error` events
- Toast notifications for non-blocking errors

### Error Logging

**Log Levels**:
- ERROR: Credit purchase failures, authentication failures, data integrity issues, concurrent credit spending conflicts
- WARNING: Rate limit hits, invalid file uploads, missing content, insufficient credits
- INFO: Successful operations, user actions, tenant provisioning, credit purchases, credit spending
- DEBUG: Query details, middleware operations, cache operations

**Log Context**:
- Tenant ID and subdomain
- User ID (if authenticated)
- Request ID for tracing
- IP address and user agent
- Timestamp and duration

## Testing Strategy

### Dual Testing Approach

The system will employ both **unit testing** and **property-based testing** to ensure comprehensive coverage and correctness.

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Test specific user flows (registration, login, spot access, credit purchase, credit spending)
- Test edge cases (empty content, invalid formats, boundary values, zero credits, negative credits)
- Test error conditions (payment failures, invalid auth, missing data, insufficient credits, concurrent spending)
- Test integration between components (middleware, views, models, atomic transactions)

**Property-Based Tests**: Verify universal properties across all inputs
- Test correctness properties defined in this document
- Generate random valid inputs to test properties hold universally
- Minimum 100 iterations per property test
- Each property test references its design document property

### Property-Based Testing Framework

**Library**: Hypothesis for Python
- Integrates with pytest
- Provides strategies for generating test data
- Supports stateful testing for complex workflows
- Allows custom strategies for domain models

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(
    tenant=st.builds(TenantFactory),
    spot=st.builds(InfoSpotFactory)
)
def test_property_2_tenant_data_isolation(tenant, spot):
    """
    Feature: multi-tenant-info-spots, Property 2: Tenant Data Isolation
    For any query executed within a tenant context, the results must only 
    include data belonging to that tenant.
    """
    # Test implementation
    pass
```

### Test Organization

```
tests/
├── unit/
│   ├── test_models.py              # Model validation, relationships
│   ├── test_views.py               # View logic, permissions
│   ├── test_middleware.py          # Tenant resolution, session handling
│   ├── test_qr_generation.py      # QR code creation
│   ├── test_credits.py             # Credit purchase and spending
│   └── test_atomic_transactions.py # Concurrent credit spending
├── property/
│   ├── test_tenant_isolation.py    # Properties 1-3
│   ├── test_authentication.py      # Properties 4-7
│   ├── test_access_control.py      # Properties 8-9
│   ├── test_credits.py             # Properties 18, 18a, 18b
│   ├── test_content_management.py  # Properties 10-16
│   ├── test_analytics.py           # Properties 22-25
│   └── test_multi_language.py      # Properties 26-28
├── integration/
│   ├── test_spot_access_flow.py    # End-to-end spot access
│   ├── test_credit_flow.py         # End-to-end credit purchase and spending
│   └── test_admin_workflow.py      # Admin CRUD operations
└── fixtures/
    ├── factories.py                # Factory Boy factories
    └── sample_data.py              # Sample content files
```

### Test Data Generation

**Factory Boy for Models**:
```python
import factory
from factory.django import DjangoModelFactory

class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant
    
    subdomain = factory.Sequence(lambda n: f'tenant{n}')
    name = factory.Faker('company')
    venue_type = factory.Iterator(['ticketed', 'public', 'mixed'])
    contact_email = factory.Faker('email')

class InfoSpotFactory(DjangoModelFactory):
    class Meta:
        model = InfoSpot
    
    tenant = factory.SubFactory(TenantFactory)
    name = factory.Faker('sentence', nb_words=4)
    access_type = factory.Iterator(['free_ticketed', 'free_public', 'paid'])
    credit_cost = factory.LazyAttribute(
        lambda o: random.randint(1, 10) if o.access_type == 'paid' else 0
    )

class UserCreditFactory(DjangoModelFactory):
    class Meta:
        model = UserCredit
    
    user = factory.SubFactory(UserFactory)
    balance = factory.Faker('random_int', min=0, max=100)
    total_purchased = factory.LazyAttribute(lambda o: o.balance)
    total_spent = 0
```

**Hypothesis Strategies**:
```python
import hypothesis.strategies as st
from hypothesis.extra.django import from_model

# Strategy for generating valid tenants
tenants = from_model(
    Tenant,
    subdomain=st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd')),
        min_size=3,
        max_size=20
    )
)

# Strategy for generating valid info spots
info_spots = from_model(
    InfoSpot,
    tenant=tenants,
    access_type=st.sampled_from(['free_ticketed', 'free_public', 'paid'])
)
```

### Integration Testing

**HTMX Testing**:
- Use Django test client with custom headers (`HX-Request: true`)
- Verify partial templates are returned for HTMX requests
- Test `hx-target` and `hx-swap` behavior
- Verify HTMX response headers (`HX-Trigger`, `HX-Redirect`)

**Payment Testing**:
- Use Stripe test mode with test card numbers
- Mock Stripe API for unit tests
- Use Stripe test webhooks for integration tests
- Test credit purchase success, failure, and refund scenarios
- Test concurrent credit spending with database locks
- Test credit balance accuracy after multiple transactions

**Multi-Tenant Testing**:
- Use Django test client with custom `HTTP_HOST` header
- Create multiple tenants in test database
- Verify tenant isolation in all operations
- Test cross-subdomain session sharing

### Performance Testing

**Load Testing Targets**:
- Info spot page load: < 2 seconds (p95)
- Audio streaming start: < 1 second (p95)
- QR code generation: < 500ms
- Credit purchase processing: < 3 seconds (p95)
- Credit spending (atomic transaction): < 200ms (p95)
- Analytics query: < 1 second for 10k records

**Tools**:
- Locust for load testing
- Django Debug Toolbar for query analysis
- django-silk for profiling
- PostgreSQL EXPLAIN ANALYZE for query optimization

### Continuous Integration

**CI Pipeline**:
1. Lint (flake8, black, isort)
2. Type checking (mypy)
3. Unit tests (pytest)
4. Property-based tests (pytest with Hypothesis)
5. Integration tests (pytest with Django test database)
6. Coverage report (minimum 80% coverage)
7. Security scan (bandit, safety)

**Test Execution**:
```bash
# Run all tests
pytest

# Run only property tests
pytest tests/property/

# Run with coverage
pytest --cov=infospot --cov-report=html

# Run specific property test
pytest tests/property/test_tenant_isolation.py::test_property_2_tenant_data_isolation
```

## Implementation Notes

### Django Settings Structure

**Multi-Tenant Configuration**:
```python
# settings/base.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'infospot.middleware.TenantMiddleware',  # Custom tenant middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Session configuration for cross-subdomain support
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_DOMAIN = '.infospot.com'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = True  # Production only

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Audio file settings
AUDIO_MAX_FILE_SIZE = 52428800  # 50MB
AUDIO_ALLOWED_FORMATS = ['mp3', 'wav', 'aac', 'm4a']
```

### URL Configuration

**Multi-Tenant URL Routing**:
```python
# urls.py
urlpatterns = [
    # Admin interface (tenant-specific)
    path('admin/', include('infospot.admin_urls')),
    
    # End user interface
    path('', include('infospot.public_urls')),
    
    # API endpoints
    path('api/', include('infospot.api_urls')),
    
    # Authentication
    path('accounts/', include('allauth.urls')),
]
```

### Caching Strategy

**Cache Layers**:
1. **Template Fragment Caching**: Cache rendered content partials
2. **View Caching**: Cache entire views for anonymous users
3. **Query Caching**: Cache expensive analytics queries
4. **Media Caching**: CDN for audio files and images

**Cache Keys**:
```python
# Tenant-specific cache keys
cache_key = f"tenant:{tenant.id}:spot:{spot.uuid}:content:{language}"

# Invalidation on update
def invalidate_spot_cache(spot):
    cache_keys = [
        f"tenant:{spot.tenant.id}:spot:{spot.uuid}:*"
    ]
    cache.delete_many(cache_keys)
```

### Security Considerations

**CSRF Protection**:
- CSRF tokens required for all POST requests
- HTMX automatically includes CSRF token in headers
- Exempt webhook endpoints with proper signature verification

**Rate Limiting**:
```python
# Using django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
def payment_view(request):
    pass

@ratelimit(key='user', rate='100/h', method='GET')
def spot_access_view(request):
    pass
```

**Content Security Policy**:
```python
# CSP headers for XSS protection
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", 'unpkg.com')  # HTMX CDN
CSP_STYLE_SRC = ("'self'", 'cdn.jsdelivr.net')  # Bootstrap CDN
CSP_IMG_SRC = ("'self'", 'data:', 'blob:')
CSP_MEDIA_SRC = ("'self'",)
```

### Deployment Considerations

**Infrastructure**:
- Application: Django on Gunicorn/uWSGI
- Web Server: Nginx for static files and reverse proxy
- Database: PostgreSQL with connection pooling
- Cache: Redis for sessions and caching
- Storage: S3-compatible for media files
- CDN: CloudFront/CloudFlare for static and media

**Environment Variables**:
```bash
# Django
DJANGO_SECRET_KEY=<secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.infospot.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Stripe
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Storage
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=infospot-media
AWS_S3_REGION_NAME=us-east-1
```

**Scaling Strategy**:
- Horizontal scaling: Multiple application servers behind load balancer
- Database: Read replicas for analytics queries
- Cache: Redis cluster for high availability
- Media: CDN with edge caching
- Background tasks: Celery for async processing (analytics, reports)

### Future Mobile App Considerations

**API Design**:
- RESTful API with Django REST Framework
- JWT authentication for mobile apps
- Versioned endpoints (`/api/v1/`)
- Pagination for list endpoints
- Filtering and search capabilities

**Offline Support**:
- Content download endpoint with authentication
- Sync endpoint for incremental updates
- Version tracking for cache invalidation
- Conflict resolution for offline changes

**Data Sync**:
```python
# Sync endpoint response
{
  "spots": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Exhibit A",
      "version": 5,
      "last_modified": "2024-12-26T10:00:00Z",
      "content": {
        "en": {
          "version": 3,
          "audio_url": "https://cdn.infospot.com/audio/...",
          "text": "Description..."
        }
      }
    }
  ],
  "sync_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "has_more": false
}
```

## Conclusion

This design provides a comprehensive architecture for a multi-tenant QR/NFC-based information platform using Django, HTMX, and Bootstrap. The shared database approach with tenant isolation balances scalability and simplicity, while the dual authentication model (optional for ticketed venues, required for public spots) provides flexibility for different use cases.

**Credit-Based Monetization**: The system implements a user-friendly credit-based payment model where users purchase credit packages upfront and spend credits to access paid spots. This eliminates the friction of per-transaction payments and provides better UX. Key features include:
- Bulk credit purchase with volume discounts
- Atomic credit spending with database locks to prevent race conditions
- No double-charging (users only pay once per spot)
- Credit balance tracking and transaction history
- Tenant revenue analytics based on credit spending

Key architectural decisions:
- Shared database with tenant_id for logical isolation
- Subdomain-based tenant routing via middleware
- Credit-based payment system for better UX
- HTMX for dynamic interactions without JavaScript complexity
- Bootstrap for responsive mobile-first UI
- Property-based testing for correctness verification
- Stripe for secure payment processing
- Atomic transactions for credit spending to prevent concurrency issues
- Future-ready API design for mobile app integration

The design addresses all 18 requirements with 34 testable correctness properties (including credit-specific properties), comprehensive error handling, and a robust testing strategy combining unit tests and property-based tests.
