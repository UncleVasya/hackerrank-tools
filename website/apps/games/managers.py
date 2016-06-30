from django.db import models
from django.db.models import Count


class FullMatchManager(models.Manager):
    def get_queryset(self):
        queryset = super(FullMatchManager, self).get_queryset()

        queryset = queryset.annotate(
            bots_num=Count('bots')
        ).filter(bots_num=2)

        return queryset
