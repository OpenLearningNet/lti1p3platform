from django.db import models


class LineItem(models.Model):
    id = models.AutoField(primary_key=True)
    scoreMaximum = models.IntegerField()
    label = models.CharField(max_length=255)
    resourceId = models.CharField(max_length=255)
    tag = models.CharField(max_length=255, null=True)
    resourceLinkId = models.CharField(max_length=255, null=True)
    startDateTime = models.DateTimeField(null=True)
    endDateTime = models.DateTimeField(null=True)
    gradesReleased = models.BooleanField(null=True)


class Score(models.Model):
    scoreGiven = models.IntegerField()
    scoreMaximum = models.IntegerField(null=True)
    comment = models.CharField(max_length=255, null=True)
    activityProgress = models.CharField(max_length=255)
    gradingProgress = models.CharField(max_length=255)
    userId = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    submissionStartedAt = models.DateTimeField(null=True)
    submissionEndedAt = models.DateTimeField(null=True)
    lineItem = models.ForeignKey(LineItem, on_delete=models.CASCADE)
