from django.shortcuts import render
from lti1p3platform.message_launch import MessageLaunchAbstract

class DjangoLTI1P3MessageLaunch(MessageLaunchAbstract):
    def get_preflight_response(self) -> dict:
        return self._request.GET or self._request.POST
    
    def render_launch_form(self, launch_data, template):
        return render(self._request, template, launch_data)
