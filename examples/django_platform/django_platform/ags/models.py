# pylint: disable=too-many-instance-attributes
from django.db import models


class LineItem(models.Model):
    id = models.AutoField(primary_key=True)
    score_maximum = models.IntegerField()
    label = models.CharField(max_length=255)
    resource_id = models.CharField(max_length=255)
    tag = models.CharField(max_length=255, null=True)
    resource_link_id = models.CharField(max_length=255, null=True)
    start_date_time = models.DateTimeField(null=True)
    end_date_time = models.DateTimeField(null=True)
    grades_released = models.BooleanField(null=True)


class Score(models.Model):
    score_given = models.IntegerField()
    score_maximum = models.IntegerField(null=True)
    comment = models.CharField(max_length=255, null=True)
    activity_progress = models.CharField(max_length=255)
    grading_progress = models.CharField(max_length=255)
    userId = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    submission_started_at = models.DateTimeField(null=True)
    submission_ended_at = models.DateTimeField(null=True)
    lineItem = models.ForeignKey(LineItem, on_delete=models.CASCADE)
