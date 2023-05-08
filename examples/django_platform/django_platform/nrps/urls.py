from django.urls import path
from .views import (
    get_membership,
)

urlpatterns = [path("<str:context_id>", get_membership, name="nrps")]
