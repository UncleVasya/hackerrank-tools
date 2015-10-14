from django.db import models


class Game(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)
    difficulty = models.CharField(max_length=200, null=True)
    slug = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % self.name


class Player(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=200, null=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % self.name


class Bot(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    score = models.FloatField()
    language = models.CharField(max_length=200)
    submitted_at = models.CharField(max_length=200)

