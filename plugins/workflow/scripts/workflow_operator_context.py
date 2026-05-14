#!/usr/bin/env python3
"""Workflow operator subagent detection helpers.

Operator-specific detection is shared by hook adapters. Hosting it here keeps a
single home for operator matching so hook scripts do not import each other.
"""

from __future__ import annotations

WORKFLOW_OPERATOR_AGENT_NAME = "workflow-operator"


def agent_name_matches_operator(name: str | None) -> bool:
    return bool(name) and name.strip() == WORKFLOW_OPERATOR_AGENT_NAME
