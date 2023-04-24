"""django_platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include

from .views import preflight_lti_1p3_launch, authorization, access_token, get_jwks

urlpatterns = [
    path("login", preflight_lti_1p3_launch, name="platform-login"),
    path("authorization", authorization, name="platform-authorization"),
    path("access_token", access_token, name="platform-access-token"),
    path("jwks", get_jwks, name="platform-jwk"),
    path("lineitems/", include("django_platform.ags.urls")),
]
