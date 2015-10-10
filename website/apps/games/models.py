from django.db import models
from jsonfield import JSONField


class Game(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)
    difficulty = models.CharField(max_length=200, null=True)
    # bots = models.PositiveIntegerField()
    hk_id = models.PositiveIntegerField(unique=True)  # game id on hackerrank.com
    hk_json = JSONField()  # original json data received from hackerrank API

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % self.name

# "id" : 27,
# "slug" : "hex",
# "name" : "Hex",
# "preview" : "hex game",
#
# "kind" : "game",
# "category" : "ai",
# "player_count" : 2,
#
# "deleted" : false,
# "active" : true,
#
# "difficulty" : 0.5434782608695652,
# "difficulty_name" : "Difficult"
#
# "total_count" : 287,
# "solved_count" : 105,
