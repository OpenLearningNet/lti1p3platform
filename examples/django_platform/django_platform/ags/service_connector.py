import typing as t

from dateutil import parser
from django.urls import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from lti1p3platform.service_connector import AssignmentsGradesService, TPage
from lti1p3platform.lineitem import TLineItem
from lti1p3platform.score import TScore, UpdateScoreStatus
from lti1p3platform.exceptions import LineItemNotFoundException, LtiServiceException

from .models import LineItem, Score
from ..helpers import get_url


class AGS(AssignmentsGradesService):
    def lineitem_serializer(self, lineitem: LineItem) -> TLineItem:
        return {
            "id": get_url(reverse("ags-lineitem", args=[lineitem.id])),
            "label": lineitem.label,
            "resourceId": lineitem.resourceId,
            "tag": lineitem.tag,
            "resourceLinkId": lineitem.resourceLinkId,
            "scoreMaximum": lineitem.scoreMaximum,
            "startDateTime": lineitem.startDateTime,
            "endDateTime": lineitem.endDateTime,
        }

    def find_lineitems(
        self,
        page: int = 1,
        limit: int = 10,
        line_item_id: t.Optional[str] = None,
        resource_link_id: t.Optional[str] = None,
        resource_id: t.Optional[str] = None,
        tag: t.Optional[str] = None,
    ) -> TPage:
        line_items = LineItem.objects
        if line_item_id:
            line_items = line_items.filter(id=line_item_id)

        if resource_link_id:
            line_items = line_items.filter(resourceLinkId=resource_link_id)

        if resource_id:
            line_items = line_items.filter(resourceId=resource_id)

        if tag:
            line_items = line_items.filter(tag=tag)

        line_items = line_items.all()
        paginator = Paginator(line_items, limit)
        page = paginator.get_page(page)

        results = []
        for line_item in page:
            results.append(self.lineitem_serializer(line_item))

        return {
            "content": results,
            "next": page.has_next(),
        }

    def find_lineitem_by_id(self, line_item_id: str) -> LineItem:
        lineitem = LineItem.objects.get(id=line_item_id)

        if lineitem is None:
            raise LineItemNotFoundException

        return lineitem

    def find_lineitem(self, line_item_id: str) -> TLineItem:
        lineitem = self.find_lineitem_by_id(line_item_id)

        return self.lineitem_serializer(lineitem)

    def create_lineitem(
        self,
        startDateTime: t.Optional[str] = None,
        endDateTime: t.Optional[str] = None,
        scoreMaximum: t.Optional[float] = None,
        label: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        resourceLinkId: t.Optional[str] = None,
        resourceId: t.Optional[str] = None,
    ) -> TLineItem:
        line_item = LineItem(
            startDateTime=startDateTime,
            endDateTime=endDateTime,
            scoreMaximum=scoreMaximum,
            label=label,
            tag=tag,
            resourceLinkId=resourceLinkId,
            resourceId=resourceId,
        )
        line_item.save()
        return self.lineitem_serializer(line_item)

    def update_lineitem(
        self,
        lineItemId: str,
        startDateTime: t.Optional[str] = None,
        endDateTime: t.Optional[str] = None,
        scoreMaximum: t.Optional[float] = None,
        label: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        resourceLinkId: t.Optional[str] = None,
        resourceId: t.Optional[str] = None,
    ) -> TLineItem:
        line_item = self.find_lineitem_by_id(lineItemId)

        if startDateTime:
            line_item.startDateTime = parser.parse(startDateTime)
        if endDateTime:
            line_item.endDateTime = parser.parse(endDateTime)
        if scoreMaximum:
            line_item.scoreMaximum = scoreMaximum
        if label:
            line_item.label = label
        if tag:
            line_item.tag = tag
        if resourceLinkId:
            line_item.resourceLinkId = resourceLinkId
        if resourceId:
            line_item.resourceId = resourceId
        line_item.save()

        return self.lineitem_serializer(line_item)

    def delete_lineitem(
        self,
        line_item_id: str,
    ):
        line_item = self.find_lineitem_by_id(line_item_id)
        line_item.delete()

    def update_score(self, line_item_id: str, score: TScore) -> UpdateScoreStatus:
        line_item = self.find_lineitem_by_id(line_item_id)
        try:
            target_score = Score.objects.get(lineItem=line_item, userId=score["userId"])
        except ObjectDoesNotExist:
            target_score = None

        is_new = False
        if target_score is None:
            target_score = Score(lineItem=line_item, userId=score["userId"])
            is_new = True

        if "timestamp" in score:
            timestamp = parser.parse(score["timestamp"])
            if target_score.timestamp and timestamp < target_score.timestamp:
                return UpdateScoreStatus.OLD_TIMESTAMP

            target_score.timestamp = timestamp

        if "scoreGiven" in score:
            target_score.scoreGiven = score["scoreGiven"]

        if "scoreMaximum" in score:
            target_score.scoreMaximum = score["scoreMaximum"]

        if "comment" in score:
            target_score.comment = score["comment"]

        if "activityProgress" in score:
            target_score.activityProgress = score["activityProgress"]

        if "gradingProgress" in score:
            target_score.gradingProgress = score["gradingProgress"]

        if "submission" in score:
            submission = score["submission"]
            if "startedAt" in submission:
                target_score.submissionStartedAt = submission["startedAt"]
            if "endedAt" in submission:
                target_score.submissionEndedAt = submission["endedAt"]

        target_score.save()

        if is_new:
            return UpdateScoreStatus.CREATED
        else:
            return UpdateScoreStatus.SUCCESS

    def get_results(
        self, line_item_id: str, page: int, limit: int, user_id: t.Optional[str] = None
    ) -> TPage:
        line_item = self.find_lineitem_by_id(line_item_id)
        scores = Score.objects.filter(lineItem=line_item)

        if user_id:
            scores = scores.filter(userId=user_id)

        scores = scores.all()
        paginator = Paginator(scores, limit)
        page = paginator.get_page(page)

        results = []
        for score in page.object_list:
            user_id = score.userId
            result_id = (
                get_url(reverse("ags_result", kwargs={"lineitem_id": line_item_id}))
                + f"/{user_id}"
            )
            score_of = get_url(
                reverse("ags_lineitem", kwargs={"lineitem_id": line_item_id})
            )
            result_maximum = 1 if score.scoreMaximum <= 0 else score.scoreMaximum
            result_score = score.scoreGiven

            results.append(
                {
                    "id": result_id,
                    "userId": user_id,
                    "scoreOf": score_of,
                    "resultScore": result_score,
                    "resultMaximum": result_maximum,
                }
            )

        return {"content": results, "next": page.has_next()}
