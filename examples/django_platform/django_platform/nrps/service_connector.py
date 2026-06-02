import typing as t
from math import ceil

from lti1p3platform.membership import Context
from lti1p3platform.service_connector import NamesRoleProvisioningService, TPage

from ..views import get_user_data


class NRPS(NamesRoleProvisioningService):
    _MEMBERS = [
        {
            "user_id": "user_id",
            "roles": ["http://purl.imsglobal.org/vocab/lis/v2/system/person#User"],
            "name": "John Doe",
            "status": "Active",
            "changed_at": 1717230000,
        },
        {
            "user_id": "former_user_id",
            "roles": ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"],
            "name": "Former Student",
            "status": "Deleted",
            "changed_at": 1717230500,
        },
    ]

    def get_member_data_page(
        self,
        page: int = 1,
        limit: t.Optional[int] = None,
        role: t.Optional[str] = None,
        since: t.Optional[str] = None,
    ) -> TPage:
        user_data = get_user_data()
        members = []

        try:
            since_value = int(since) if since is not None else None
        except (TypeError, ValueError):
            since_value = None

        try:
            page_index = max(1, int(page))
        except (TypeError, ValueError):
            page_index = 1

        try:
            page_size = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            page_size = None

        for member in self._MEMBERS:
            # Keep user data in sync with the launch demo account.
            if member["user_id"] == user_data["user_id"]:
                member = {
                    **member,
                    "roles": user_data["lis_roles"],
                    "name": user_data["full_name"],
                }

            if since_value is None and member.get("status") == "Deleted":
                continue

            if (
                since_value is not None
                and int(member.get("changed_at", 0)) <= since_value
            ):
                continue

            if role and role not in member.get("roles", []):
                continue

            members.append(
                {
                    "user_id": member["user_id"],
                    "roles": member["roles"],
                    "name": member["name"],
                    "status": member["status"],
                }
            )

        members.sort(key=lambda item: item["user_id"])

        page_size = page_size or len(members) or 1
        start = (page_index - 1) * page_size
        end = start + page_size
        total_pages = ceil(len(members) / page_size) if members else 1

        return {
            "content": members[start:end],
            "has_next": page_index < total_pages,
        }

    def get_context_by_id(self) -> Context:
        return Context(id="context_id", label="Test Course", title="Test Course")
