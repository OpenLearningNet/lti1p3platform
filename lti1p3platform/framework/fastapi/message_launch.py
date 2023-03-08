from lti1p3platform.message_launch import MessageLaunchAbstract

class FastapiMessageLaunch(MessageLaunchAbstract):
    def get_preflight_response(self) -> dict:
        pass

    def template_data(self, launch_data):
        raise NotImplementedError
    
    def render_launch_form(self, launch_data, template, launch_url_name=None):
        pass