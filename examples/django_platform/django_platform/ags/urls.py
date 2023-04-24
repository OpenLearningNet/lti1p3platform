from django.urls import path
from .views import (
    LineItemView,
    LineItemsView,
    get_results,
    update_scores,
)

urlpatterns = [
    path("<str:lineitem_id>", LineItemView.as_view(), name="ags-lineitem"),
    path("", LineItemsView.as_view(), name="ags-lineitems"),
    path("<str:lineitem_id>/results", get_results, name="ags-results"),
    path("<str:lineitem_id>/scores", update_scores, name="ags-scores"),
]
