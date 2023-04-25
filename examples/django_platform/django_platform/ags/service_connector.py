import typing as t

from dateutil import parser
from django.urls import reverse
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from lti1p3platform.service_connector import AssignmentsGradesService, TPage
from lti1p3platform.lineitem import TLineItem
from lti1p3platform.score import TScore, UpdateScoreStatus
from lti1p3platform.exceptions import LineItemNotFoundException

from .models import LineItem, Score
from ..helpers import get_url


class AGS(AssignmentsGradesService):
    def lineitem_serializer(self, lineitem: LineItem) -> TLineItem:
        return {
            "id": get_url(reverse("ags-lineitem", args=[lineitem.id])),
            "label": lineitem.label,
            "resourceId": lineitem.resource_id,
            "tag": lineitem.tag,
            "resourceLinkId": lineitem.resource_link_id,
            "scoreMaximum": lineitem.score_maximum,
            "startDateTime": lineitem.start_date_time,
            "endDateTime": lineitem.end_date_time,
        }

    # pylint: disable=too-many-arguments
    def find_lineitems(
        self,
        page: int = 1,
        limit: int = 10,
        line_item_id: t.Optional[str] = None,
        resource_link_id: t.Optional[str] = None,
        resource_id: t.Optional[str] = None,
        tag: t.Optional[str] = None,
    ) -> TPage:
        line_items = LineItem.objects  # pylint: disable=no-member
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
        lineitem = LineItem.objects.get(id=line_item_id)  # pylint: disable=no-member

        if lineitem is None:
            raise LineItemNotFoundException

        return lineitem

    def find_lineitem(self, line_item_id: str) -> TLineItem:
        lineitem = self.find_lineitem_by_id(line_item_id)

        return self.lineitem_serializer(lineitem)

    def create_lineitem(
        self,
        creation_data: TLineItem,
    ) -> TLineItem:
        line_item = LineItem(
            start_date_time=creation_data.get("startDateTime"),
            end_date_time=creation_data.get("endDateTime"),
            score_maximum=creation_data.get("scoreMaximum"),
            label=creation_data.get("label"),
            tag=creation_data.get("tag"),
            resource_link_id=creation_data.get("resourceLinkId"),
            resource_id=creation_data.get("resourceId"),
        )
        line_item.save()
        return self.lineitem_serializer(line_item)

    def update_lineitem(
        self,
        update_data: TLineItem,
    ) -> TLineItem:
        assert "lineItemId" in update_data
        line_item = self.find_lineitem_by_id(update_data["lineItemId"])

        if update_data.get("startDateTime"):
            line_item.start_date_time = parser.parse(update_data.get("startDateTime"))
        if update_data.get("endDateTime"):
            line_item.end_date_time = parser.parse(update_data.get("endDateTime"))
        if update_data.get("scoreMaximum"):
            line_item.score_maximum = update_data.get("scoreMaximum")
        if update_data.get("label"):
            line_item.label = update_data.get("label")
        if update_data.get("tag"):
            line_item.tag = update_data.get("tag")
        if update_data.get("resourceLinkId"):
            line_item.resource_link_id = update_data.get("resourceLinkId")
        if update_data.get("resourceId"):
            line_item.resource_id = update_data.get("resourceId")
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
            target_score = Score.objects.get(  # pylint: disable=no-member
                lineItem=line_item, userId=score["userId"]
            )
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

        target_score.score_given = score["scoreGiven"]
        target_score.score_maximum = score.get("scoreMaximum")
        target_score.comment = score.get("comment")
        target_score.activity_progress = score["activityProgress"]
        target_score.grading_progress = score["gradingProgress"]

        if "submission" in score:
            submission = score["submission"]
            if "startedAt" in submission:
                target_score.submission_started_at = submission["startedAt"]
            if "endedAt" in submission:
                target_score.submission_ended_at = submission["endedAt"]
        target_score.save()

        if is_new:
            return UpdateScoreStatus.CREATED

        return UpdateScoreStatus.SUCCESS

    def get_results(
        self, line_item_id: str, page: int, limit: int, user_id: t.Optional[str] = None
    ) -> TPage:
        line_item = self.find_lineitem_by_id(line_item_id)
        scores = Score.objects.filter(lineItem=line_item)  # pylint: disable=no-member

        if user_id:
            scores = scores.filter(userId=user_id)

        scores = scores.all()
        paginator = Paginator(scores, limit)
        page = paginator.get_page(page)

        results = []
        for score in page.object_list:
            user_id = score.userId
            result_id = (
                get_url(reverse("ags-results", kwargs={"lineitem_id": line_item_id}))
                + f"/{user_id}"
            )
            score_of = get_url(
                reverse("ags-lineitem", kwargs={"lineitem_id": line_item_id})
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
