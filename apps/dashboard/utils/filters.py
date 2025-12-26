from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone


def apply_search_filter(queryset, search_query, search_fields):
    """Apply search filter to queryset"""
    if not search_query or not search_fields:
        return queryset
    
    search_filter = Q()
    for field in search_fields:
        # Handle related field searches
        if '__' in field:
            search_filter |= Q(**{f"{field}__icontains": search_query})
        else:
            search_filter |= Q(**{f"{field}__icontains": search_query})
    
    return queryset.filter(search_filter)


def apply_date_filter(queryset, date_field, date_from=None, date_to=None):
    """Apply date range filter to queryset"""
    if date_from:
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        queryset = queryset.filter(**{f"{date_field}__gte": date_from})
    
    if date_to:
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        # Include the entire day
        date_to = timezone.make_aware(
            datetime.combine(date_to, datetime.max.time())
        )
        queryset = queryset.filter(**{f"{date_field}__lte": date_to})
    
    return queryset


def apply_status_filter(queryset, status_field, status_value):
    """Apply status filter to queryset"""
    if status_value:
        if status_value.lower() == 'active':
            return queryset.filter(**{status_field: True})
        elif status_value.lower() == 'inactive':
            return queryset.filter(**{status_field: False})
    return queryset


def apply_choice_filter(queryset, field_name, choice_value):
    """Apply choice field filter to queryset"""
    if choice_value:
        return queryset.filter(**{field_name: choice_value})
    return queryset


def get_date_range_options():
    """Get predefined date range options"""
    now = timezone.now()
    return {
        'today': (now.date(), now.date()),
        'yesterday': (now.date() - timedelta(days=1), now.date() - timedelta(days=1)),
        'last_7_days': (now.date() - timedelta(days=7), now.date()),
        'last_30_days': (now.date() - timedelta(days=30), now.date()),
        'this_month': (now.replace(day=1).date(), now.date()),
        'last_month': (
            (now.replace(day=1) - timedelta(days=1)).replace(day=1).date(),
            (now.replace(day=1) - timedelta(days=1)).date()
        ),
    }


def build_filter_context(request, filter_fields):
    """Build filter context for templates"""
    filters = {}
    for field in filter_fields:
        value = request.GET.get(field)
        if value:
            filters[field] = value
    
    return {
        'current_filters': filters,
        'has_filters': bool(filters),
        'filter_count': len(filters)
    }