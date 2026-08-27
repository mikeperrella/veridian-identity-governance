"""Read-only CISO Assistant API client for the dashboard.

Reuses the exact auth/TLS/pagination pattern established in
scripts/risk_scoring.py (Stage 5): `Authorization: Token <PAT>` header,
PAT from the CISO_ASSISTANT_PAT environment variable, self-signed-cert
verification disabled, DRF-style {"results": [...], "next": ...} pagination.

Unlike risk_scoring.py, every function here is read-only (GET only, no
PATCH) and returns None instead of raising on failure, so the dashboard
can degrade one section at a time if CISO Assistant is unreachable rather
than crashing the whole page.
"""

import os

import requests
import urllib3

from constants import CISO_ASSISTANT_BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CisoAssistantUnavailable(Exception):
    """Raised internally when the PAT is missing; callers see None, not this."""


def _session():
    pat = os.environ.get("CISO_ASSISTANT_PAT")
    if not pat:
        raise CisoAssistantUnavailable("CISO_ASSISTANT_PAT environment variable is not set.")
    session = requests.Session()
    session.headers.update({"Authorization": f"Token {pat}"})
    return session


def _get_all_pages(session, path, params=None):
    results = []
    url = f"{CISO_ASSISTANT_BASE_URL}{path}"
    while url:
        resp = session.get(url, params=params, verify=False, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        results.extend(payload["results"])
        url = payload.get("next")
        params = None  # `next` already encodes any query params from the first request
    return results


def _safe_get_all_pages(path, params=None):
    try:
        session = _session()
        return _get_all_pages(session, path, params=params)
    except (requests.RequestException, CisoAssistantUnavailable):
        return None


def get_risk_scenarios():
    return _safe_get_all_pages("/api/risk-scenarios/")


def get_findings():
    return _safe_get_all_pages("/api/findings/")


def get_requirement_assessments():
    """Returns only the rows this project actually tested (result != not_assessed) --
    ~12 points of focus out of the ~375 rows in the full imported SOC 2 framework."""
    rows = _safe_get_all_pages("/api/requirement-assessments/")
    if rows is None:
        return None
    return [r for r in rows if r.get("result") not in (None, "", "not_assessed")]
