from django.contrib.postgres.fields import JSONField
from django.db import models
from solo.models import SingletonModel


class Game(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)
    difficulty = models.FloatField(null=True)
    difficulty_text = models.CharField(max_length=200, null=True)
    slug = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % self.name


class Player(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=200, null=True)
    avatar = models.URLField()

    class Meta:
        ordering = ['pk']

    def __unicode__(self):
        return u'%s' % self.name


class Bot(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    rank = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=15, decimal_places=12)
    language = models.CharField(max_length=200)

    class Meta:
        ordering = ['rank']

    def __unicode__(self):
        return u'%s (%s)' % (self.player, self.game)


class Match(models.Model):
    game = models.ForeignKey(Game)
    bots = models.ManyToManyField(Bot, through='Opponent')
    result = models.PositiveIntegerField()
    message = models.TextField()
    date = models.DateTimeField()
    replay = JSONField(null=True)
    hk_id = models.PositiveIntegerField(unique=True)  # id on hackerrank.com

    class Meta:
        ordering = ['-date']

    def get_bots(self):
        return self.bots.order_by('opponent__position')


class Opponent(models.Model):
    match = models.ForeignKey(Match)
    bot = models.ForeignKey(Bot)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']


class ParsingInfo(SingletonModel):
    oldest_parsed_match = models.PositiveIntegerField(null=True, blank=True)
    newest_parsed_match = models.PositiveIntegerField(null=True, blank=True)
