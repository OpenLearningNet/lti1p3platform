"""
LTI 1.3 Advantage Services - Names and Role Provisioning Service (NRPS)

Names and Role Provisioning Service (NRPS):
===========================================
NRPS allows tools to fetch a list of users (students, instructors) in a course
and their roles, without needing separate user management integrations like LDAP/Active Directory.

Real-World Example:
- Grade book tool wants to display all students in a course
- Rather than syncing via separate directory service
- Tool calls platform's NRPS API: /memberships?context_id=course-123
- Platform returns list of users with roles in that course
- Tool can display students, instructors, TAs, etc.

Use Cases:
- Roster synchronization: Get current class list
- Permission management: Know which users are instructors vs students
- Context-aware features: Show appropriate features based on role
- Gradebook setup: Know which students to create grade columns for
- Bulk operations: Process grades for all students at once

API Details:
- Context Membership Service: Get members (users) in a course/context
  * Endpoint: /memberships?context_id=<id>&role=<role>&limit=<limit>&offset=<offset>
  * Returns: List of users with their roles in the context
  * Pagination supported via limit/offset

Scopes:
- contextmembership.readonly: Can only read/fetch the member list
- (No write scope - NRPS is read-only by design)

Security:
- Tool authenticates with access_token (OAuth 2.0 Bearer)
- Platform controls who can access roster data
- Scope-based access control
- Can filter by role (students only, instructors only, etc.)
- Data includes: user_id, roles, names (based on privacy settings)

Privacy Considerations:
- Tools should only request scope when needed
- Platform may limit PII (Personally Identifiable Information) shared
- Instructor may control if students can see class roster
- Names/emails may be redacted based on privacy policies

Reference: https://www.imsglobal.org/spec/lti-nrps/v2p0/
"""
from __future__ import annotations

import typing as t


class LtiNrps:
    """
    LTI 1.3 Advantage Services - Names and Role Provisioning Service Configuration
    
    NRPS (Names and Role Provisioning Service) Overview:
    ====================================================
    
    Purpose:
    - Enables tools to query course membership information from the platform
    - Alternative to separate directory integrations (LDAP, AD, etc.)
    - Dynamically fetches roster without pre-synced data
    
    Context Membership Service:
    - Provides list of users enrolled in a course/context
    - Includes user identifiers and role information
    - Supports pagination for large courses (thousands of students)
    
    Platform Role Examples:
    - http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor
    - http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student
    - http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner
    - http://purl.imsglobal.org/vocab/lis/v2/membership#Administrator
    
    Tool Security Considerations:
    - Cache data locally if possible (reduce API calls)
    - Respect privacy settings and role filtering
    - Use appropriate scopes
    - Handle pagination for large courses
    - Handle errors gracefully if roster API unavailable
    
    This class configures NRPS access for a tool integration.
    
    Reference: https://www.imsglobal.org/spec/lti-nrps/v2p0/
    """

    def __init__(
        self,
        context_memberships_url: str,
    ):
        """
        Initialize NRPS configuration for a tool integration
        
        Parameters:
            context_memberships_url: Platform's API endpoint for roster/memberships
                - Format: "https://platform.edu/lti/nrps/memberships"
                - Tool makes GET requests to query course members
                - URL provided by platform in the launch message
                - Actual member retrieval happens when tool calls this API
        """
        self.context_memberships_url = context_memberships_url

    def get_available_scopes(self) -> t.List[str]:
        """
        Retrieves list of available OAuth 2.0 scopes for NRPS
        
        OAuth 2.0 Scopes for NRPS:
        
        - https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly
          * Access permission for Context Membership Service
          * Read-only: can only fetch roster data
          * Cannot modify/delete members (NRPS is read-only)
          * Included in access_token if enabled
        
        Scope Usage:
        - Platform includes this scope in access_token if NRPS enabled for tool
        - Tool includes this scope in token request when calling APIs
        - Platform validates token has required scope before returning roster
        
        No 'write' Scope:
        - NRPS is intentionally read-only
        - Tools cannot add/remove/modify course members via NRPS
        - Member management handled through platform UI
        - Prevents accidental/malicious roster changes from tools
        
        Typical Scope in Access Token (JWT):
        {
            "scope": "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem
                      https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
            ...
        }
        
        Returns:
            List containing the NRPS contextmembership.readonly scope URI
        
        Reference:
        - Scope specification: https://www.imsglobal.org/spec/lti-nrps/v2p0/#scopes
        """

        return [
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ]

    def get_lti_nrps_launch_claim(self) -> t.Dict[str, t.Any]:
        """
        Generate NRPS Launch Claim for LTI message
        
        This claim is included in the LTI launch message to tell the tool
        where to call to fetch the course roster (member list).
        
        Claim Structure:
        {
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
                "context_memberships_url": "<api-endpoint>",
                "service_versions": ["2.0"]
            }
        }
        
        Usage:
        1. Tool receives launch message with NRPS claim
        2. Tool extracts context_memberships_url from claim
        3. Tool calls API: GET context_memberships_url?context_id=<course>
        4. Platform returns JSON list of members with roles
        5. Tool processes roster data for its features
        
        API Call Example:
        GET /lti/nrps/memberships?context_id=course-123&limit=50&offset=0
        With Authorization: Bearer <access_token>
        
        API Response Example:
        {
            "context": {
                "id": "course-123",
                "label": "Biology 101"
            },
            "members": [
                {
                    "status": "Active",
                    "name": "Jane Instructor",
                    "picture": "https://...",
                    "given_name": "Jane",
                    "family_name": "Instructor",
                    "email": "jane@university.edu",
                    "user_id": "user-456",
                    "roles": [
                        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor"
                    ]
                },
                {
                    "status": "Active",
                    "name": "John Student",
                    "user_id": "user-789",
                    "roles": [
                        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student"
                    ]
                }
            ],
            "pageNumber": 1,
            "pageSize": 50,
            "pageCount": 1
        }
        
        Pagination:
        - pageNumber: Current page (1-indexed)
        - pageSize: Number of members per page
        - pageCount: Total number of pages
        - Control pagination via ?limit=50&offset=0 parameters
        
        Returns:
            dict: The namesroleservice claim to inject into LTI launch message
        
        Reference:
                - Context Membership Service:  # pylint: disable=line-too-long
                    https://www.imsglobal.org/spec/lti-nrps/v2p0/#context-memberships-service
        """

        return {
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
                "context_memberships_url": self.context_memberships_url,
                "service_versions": ["2.0"],
            }
        }
