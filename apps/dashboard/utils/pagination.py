from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings


def get_paginated_queryset(request, queryset, per_page=None):
    """Get paginated queryset with error handling"""
    if per_page is None:
        per_page = getattr(settings, 'DASHBOARD_ITEMS_PER_PAGE', 25)
    
    # Allow per_page override from request
    try:
        per_page = int(request.GET.get('per_page', per_page))
        # Limit per_page to reasonable values
        per_page = min(max(per_page, 10), 100)
    except (ValueError, TypeError):
        per_page = 25
    
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj, paginator


def get_pagination_context(page_obj, paginator):
    """Get pagination context for templates"""
    context = {
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
        'paginator': paginator,
    }
    
    # Add page range for navigation
    current_page = page_obj.number
    total_pages = paginator.num_pages
    
    # Show 5 pages around current page
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)
    
    # Adjust if we're near the beginning or end
    if current_page <= 3:
        end_page = min(total_pages, 5)
    elif current_page >= total_pages - 2:
        start_page = max(1, total_pages - 4)
    
    context['page_range'] = range(start_page, end_page + 1)
    context['show_first'] = start_page > 1
    context['show_last'] = end_page < total_pages
    
    return context


def build_pagination_url(request, page_number):
    """Build pagination URL preserving current filters"""
    params = request.GET.copy()
    params['page'] = page_number
    return f"?{params.urlencode()}"