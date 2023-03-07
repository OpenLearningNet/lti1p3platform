from django.shortcuts import render
from lti1p3platform.message_launch import MessageLaunchAbstract

class DjangoLTI1P3MessageLaunch(MessageLaunchAbstract):
    def get_preflight_response(self) -> dict:
        return self._request.GET or self._request.POST
    
    def set_launch_url(self, launch_data, launch_url_name):
        launch_data[launch_url_name] = self._registration.get_launch_url()

    def render_launch_form(self, launch_data, template, launch_url_name=None):
        if launch_url_name:
            self.set_launch_url(launch_data, launch_url_name)
        else:
            self.set_launch_url(launch_data, 'tool_launch_url')

        return render(self._request, template, launch_data)
