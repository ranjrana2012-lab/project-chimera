"""Policy management routes for Safety Filter service."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime

from ....main import handler


router = APIRouter()


@router.get("/")
async def get_policies() -> Dict[str, Any]:
    """Get current safety policies.

    Returns all configured policy rules including their
    enabled status, thresholds, and actions.

    Returns:
        Dictionary with policy rules, default action, and metadata
    """
    try:
        policies = handler.get_policies()
        return {
            "policies": policies["rules"],
            "default_action": policies["default_action"],
            "default_strictness": policies["default_strictness"],
            "category_weights": policies["category_weights"],
            "active_rule_count": policies["active_rule_count"],
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get policies: {str(e)}"
        )


@router.put("/")
async def update_policies(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update safety policies.

    Update policy rules and default action. All rules are replaced
    with the provided list.

    Request body:
        rules: List of policy rule dictionaries
        default_action: New default action (optional)
        version: Optional version identifier

    Returns:
        Updated policy configuration

    Raises:
        HTTPException: If policy update fails
    """
    try:
        rules = request.get("rules", [])
        default_action = request.get("default_action")
        version = request.get("version")

        if not rules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one rule is required"
            )

        # Validate rules
        for rule in rules:
            if "name" not in rule or "category" not in rule or "action" not in rule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each rule must have name, category, and action"
                )

        # Update policies
        updated = handler.update_policies(rules, default_action)

        # Log policy update (async)
        # await handler.audit_logger.log_policy_update(version, rules)

        return {
            "policies": updated["rules"],
            "default_action": updated["default_action"],
            "default_strictness": updated["default_strictness"],
            "category_weights": updated["category_weights"],
            "active_rule_count": updated["active_rule_count"],
            "version": version or f"v{int(datetime.now().timestamp())}",
            "updated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update policies: {str(e)}"
        )


@router.get("/categories")
async def get_categories() -> Dict[str, Any]:
    """Get available content categories.

    Returns all content categories that can be checked,
    along with their weights and descriptions.

    Returns:
        Dictionary with category information
    """
    categories = {
        "profanity": {
            "description": "Profanity and offensive language",
            "weight": 0.5
        },
        "hate_speech": {
            "description": "Hate speech and discriminatory content",
            "weight": 1.0
        },
        "sexual_content": {
            "description": "Sexual content and explicit material",
            "weight": 0.95
        },
        "violence": {
            "description": "Violent content and threats",
            "weight": 0.9
        },
        "harassment": {
            "description": "Harassment and bullying",
            "weight": 0.85
        },
        "self_harm": {
            "description": "Self-harm and suicide related content",
            "weight": 1.0
        },
        "misinformation": {
            "description": "Misinformation and false claims",
            "weight": 0.7
        },
        "spam": {
            "description": "Spam and unsolicited content",
            "weight": 0.3
        }
    }

    return {
        "categories": categories,
        "total_count": len(categories)
    }


@router.get("/strictness-levels")
async def get_strictness_levels() -> Dict[str, Any]:
    """Get available strictness levels.

    Returns all strictness levels with their descriptions
    and threshold configurations.

    Returns:
        Dictionary with strictness level information
    """
    return {
        "strictness_levels": {
            "permissive": {
                "description": "Most lenient filtering - only block severe content",
                "thresholds": {
                    "block": 0.95,
                    "flag": 0.85,
                    "warn": 0.70
                }
            },
            "moderate": {
                "description": "Balanced filtering - recommended for general use",
                "thresholds": {
                    "block": 0.85,
                    "flag": 0.70,
                    "warn": 0.55
                }
            },
            "strict": {
                "description": "Most aggressive filtering - flag borderline content",
                "thresholds": {
                    "block": 0.70,
                    "flag": 0.55,
                    "warn": 0.40
                }
            }
        },
        "default": "moderate"
    }
