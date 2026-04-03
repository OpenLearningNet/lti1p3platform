"""
LTI 1.3 Advantage Services - Assignments and Grades Service (AGS) Implementation

Assignments and Grades Service (AGS):
====================================
AGS allows tools (like homework/quiz platforms) to:
1. Create grading items (assignments/assessments) in the LMS
2. Submit student grades/results back to the LMS
3. Query existing grades and assignments

Real-World Example:
- Student uses external quiz tool to take quiz
- Quiz tool submits grade back to platform
- Platform records grade in gradebook
- Instructor can see student's quiz grade in LMS gradebook
- Tool can integrate with platform's grading system

Security:
- Tool must request specific OAuth scopes for AGS
- Platform validates scopes before allowing API calls
- All API calls use access_token (JWT Bearer token)
- Scopes control what tool can do:
  * lineitem.readonly: See assignments only
  * score: Submit new grades (recommended for quiz tools)
  * result.readonly: See grades only
  * lineitem: Create/delete assignments (for creation tools)
  * result: Modify grades (broader than score)

Reference: https://www.imsglobal.org/spec/lti-ags/v2p0/
"""
from __future__ import annotations

import typing as t


class LtiAgs:
    """
    LTI 1.3 Advantage Services - Assignments and Grades Service Configuration
    
    AGS provides three main APIs:
    
    1. LineItem API (Assignment Management API):
       - GET /lineitems: List all grading items (assignments)
       - POST /lineitems: Create new grading item (if allowed)
       - GET /lineitems/{id}: Get specific grading item details
       - PUT /lineitems/{id}: Update grading item
       - DELETE /lineitems/{id}: Delete grading item
       
       Scopes required:
       - lineitem.readonly: View only
       - lineitem: Create/modify/delete
    
    2. Score API (Grade Submission API):
       - POST /lineitems/{id}/scores: Submit student grade
       - Scopes: score (most restrictive, recommended)
       - Allows tool to submit grades without modifying items
    
    3. Result API (Detailed Grade Query API):
       - GET /lineitems/{id}/results: Retrieve all results for an item
       - GET /lineitems/{id}/results/{user_id}: Get specific student's result
       - Scopes: result.readonly (view) or result (modify)
    
    This class configures which AGS capabilities are available to tools.
    
    Parameters:
    - lineitems_url: Platform's API endpoint for listing/creating assignments
    - lineitem_url: Template URL for accessing specific assignment (contains {id})
    - allow_creating_lineitems: If False, tool can only see existing items (not create)
    - results_service_enabled: If True, tool can query student results
    - scores_service_enabled: If True, tool can submit grades
    
    Platform Security Considerations:
    - Only enable services actually used by this tool
    - Restrict scopes to minimum needed
    - Monitor tool's API usage for suspicious patterns
    - Default: conservative (results=true, scores=true, creation=false)
    
    Reference: https://www.imsglobal.org/spec/lti-ags/v2p0/
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        lineitems_url: t.Optional[str] = None,
        lineitem_url: t.Optional[str] = None,
        allow_creating_lineitems: bool = False,
        results_service_enabled: bool = True,
        scores_service_enabled: bool = True,
    ) -> None:
        """
        Initialize AGS configuration for a tool integration
        
        Parameters:
            lineitems_url: Platform's API endpoint for line item list/creation
                - Format: "https://platform.edu/lti/ags/lineitems"
                - Tool makes GET/POST requests to this endpoint
                - Required if scores/results services enabled
            
            lineitem_url: Template URL for accessing individual line item
                - Format: "https://platform.edu/lti/ags/lineitems/123"
                - Contains {id} placeholder replaced with item ID
                - Required if scores/results services enabled
            
            allow_creating_lineitems: Allow tool to create new assignments
                - Default: False (tool can only use existing items)
                - Set True for content creation tools
                - False prevents tool from cluttering gradebook
            
            results_service_enabled: Allow tool to query student results
                - Default: True (most tools need this)
                - Disabled if tool only submits grades (no results lookup)
                - Results API requires 'result.readonly' or 'result' scope
            
            scores_service_enabled: Allow tool to submit grades/scores
                - Default: True (most tools need this)
                - Disabled if tool is view-only
                - Scores API requires 'score' scope
        """
        # If the platform allows creating lineitems, set this
        # to True. This allows tools like content creators to add
        # new assignments to the platform's gradebook.
        self.allow_creating_lineitems = allow_creating_lineitems

        # Result and scores services
        # These indicate which AGS APIs the platform supports
        self.results_service_enabled = results_service_enabled
        self.scores_service_enabled = scores_service_enabled

        # Lineitems urls
        # These are the API endpoints where tool makes requests
        self.lineitems_url = lineitems_url
        self.lineitem_url = lineitem_url

    def get_available_scopes(self) -> t.List[str]:
        """
        Retrieves list of available OAuth 2.0 scopes for this AGS configuration
        
        OAuth 2.0 Scopes determine what the tool is allowed to do on the platform.
        Scopes are included in the access_token JWT and validated by the platform.
        
        Available AGS Scopes:
        - https://purl.imsglobal.org/spec/lti-ags/scope/lineitem
          * Create/modify/delete line items (assignments)
          * Requires: allow_creating_lineitems=True
          * Only included if tool needs to create items
        
        - https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly
          * View line items only, cannot modify
          * Less restrictive than lineitem
          * Default for tools that don't create items
        
        - https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly
          * View student results/grades only
          * Cannot modify or change grades
          * Safest scope for read-only tools
        
        - https://purl.imsglobal.org/spec/lti-ags/scope/result
          * View and modify student results/grades
          * More permissive than result.readonly
          * Used by tools that need full result access
        
        - https://purl.imsglobal.org/spec/lti-ags/scope/score
          * Submit grades for students
          * Most restrictive scope (RECOMMENDED!)
          * Used by quiz/homework tools
          * Cannot view other students' scores
        
        Scope Selection Best Practice:
        - Use 'score' if only submitting grades (quiz tools, most secure)
        - Use 'lineitem.readonly' if only viewing assignments
        - Use 'result.readonly' if only viewing grades
        - Use 'result' only if truly needing result modification
        - Use 'lineitem' only for content creation tools
        
        Returns:
            List of scope URIs the platform will provide tokens for
        
        Reference:
        - Scope descriptions: https://www.imsglobal.org/spec/lti-ags/v2p0/#scopes
        - OAuth 2.0 Scopes: https://tools.ietf.org/html/rfc6749#section-3.3
        """
        scopes = []

        if self.allow_creating_lineitems:
            # Tool can fully managed its line items, including adding and removing line items
            scopes.append("https://purl.imsglobal.org/spec/lti-ags/scope/lineitem")
        else:
            # Tool can query the line items, no modification is allowed
            scopes.append(
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
            )

        if self.results_service_enabled:
            scopes.append(
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
            )

        if self.scores_service_enabled:
            scopes.append("https://purl.imsglobal.org/spec/lti-ags/scope/score")

        return scopes

    def get_lti_ags_launch_claim(self) -> t.Dict[str, t.Any]:
        """
        Returns LTI AGS Claim to be injected in the LTI launch message.
        """

        claim_values: t.Dict[str, t.Any] = {
            "scope": self.get_available_scopes(),
        }

        if self.lineitem_url:
            # link has no line item (or many), tool can query and add line items
            claim_values["lineitem"] = self.lineitem_url

            if not self.lineitems_url:
                # link has a single line item, tool can only POST score
                for scope in claim_values["scope"]:
                    if scope != "https://purl.imsglobal.org/spec/lti-ags/scope/score":
                        claim_values["scope"].remove(scope)

        if self.lineitems_url:
            # link has a single line item, tool can only POST score
            claim_values["lineitems"] = self.lineitems_url

        return {
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": claim_values,
        }
