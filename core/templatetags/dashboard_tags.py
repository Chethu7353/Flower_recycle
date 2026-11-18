from django import template
from django.db.models import Sum

from core.models import Collection, CollectionRecord, CustomUser, FlowerSubmission, Temple

register = template.Library()


@register.simple_tag
def admin_dashboard_totals():
    total_collections = CollectionRecord.objects.count() or Collection.objects.count()
    total_collected_weight = (
        CollectionRecord.objects.aggregate(total=Sum("collected_weight"))["total"]
        or Collection.objects.aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    return {
        "temples": Temple.objects.count(),
        "temple_owners": CustomUser.objects.filter(role=CustomUser.Role.TEMPLE_OWNER).count(),
        "collectors": CustomUser.objects.filter(role=CustomUser.Role.COLLECTOR).count(),
        "submissions": FlowerSubmission.objects.count(),
        "collections": total_collections,
        "flower_waste": total_collected_weight,
    }
