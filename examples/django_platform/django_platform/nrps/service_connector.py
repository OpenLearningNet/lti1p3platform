import typing as t

from lti1p3platform.membership import Context
from lti1p3platform.service_connector import NamesRoleProvisioningService, TPage

from ..views import get_user_data


class NRPS(NamesRoleProvisioningService):
    def get_member_data_page(
        self,
        page: int = 1,
        limit: t.Optional[int] = None,
        role: t.Optional[str] = None,
        since: t.Optional[str] = None,
    ) -> TPage:
        user_data = get_user_data()
        return {
            "content": [
                {
                    "user_id": user_data["user_id"],
                    "roles": user_data["lis_roles"],
                    "name": user_data["full_name"],
                }
            ],
            "has_next": False,
        }

    def get_context_by_id(self) -> Context:
        return Context(id="context_id", label="Test Course", title="Test Course")
