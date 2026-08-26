"""
Generates the synthetic identity, service-account, asset, and vendor
inventories for Veridian LegalTech (fictional company — see docs/company-profile.md).

Deterministic: fixed seed + fixed reference date, so re-running this script
produces byte-identical CSV output every time.

Usage: python data/generate_inventory.py
"""

import csv
import os
import random
from datetime import date, timedelta

from faker import Faker

SEED = 42
AS_OF = date(2026, 8, 26)  # fixed "today" so output never drifts with real time

random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

DEPARTMENTS = [
    "Engineering", "Product", "Sales", "Customer Success", "Marketing",
    "Finance", "Legal & Compliance", "People/HR", "IT/Security", "Support",
]

TITLES_BY_DEPT = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "Staff Engineer", "Engineering Manager", "Platform Engineer", "DevOps Engineer"],
    "Product": ["Product Manager", "Senior Product Manager", "Product Designer"],
    "Sales": ["Account Executive", "Sales Development Rep", "Sales Director"],
    "Customer Success": ["Customer Success Manager", "Onboarding Specialist"],
    "Marketing": ["Marketing Manager", "Content Marketer", "Demand Gen Specialist"],
    "Finance": ["Financial Analyst", "Accounts Payable Specialist", "Controller"],
    "Legal & Compliance": ["Compliance Analyst", "Paralegal", "General Counsel"],
    "People/HR": ["HR Business Partner", "Recruiter", "HRIS Administrator"],
    "IT/Security": ["IT Support Specialist", "Security Engineer", "Identity & Access Engineer", "IT Manager"],
    "Support": ["Support Engineer", "Support Team Lead"],
}

PRIVILEGED_TITLES = {
    "Staff Engineer", "Engineering Manager", "Platform Engineer", "DevOps Engineer",
    "Security Engineer", "Identity & Access Engineer", "IT Manager",
    "Controller", "HRIS Administrator", "IT Support Specialist",
}
ADMIN_TITLES = {
    "Platform Engineer", "DevOps Engineer", "Security Engineer",
    "Identity & Access Engineer", "IT Manager", "HRIS Administrator",
}

TOTAL_EMPLOYEES = 195
NUM_TERMINATED = 15
NUM_OFFBOARDING_GAPS = 4  # terminated but still Active in Okta
WINDOW_START = AS_OF - timedelta(days=18 * 30)  # 18-month growth window
COMPANY_START = WINDOW_START - timedelta(days=5 * 365)  # a handful of long-tenured founders


def random_date(start, end):
    delta_days = (end - start).days
    if delta_days < 0:
        raise ValueError(f"random_date: start ({start}) is after end ({end})")
    return start + timedelta(days=random.randint(0, delta_days))


def gen_hire_date(index, total):
    """Skews hires later in the window, matching a 90 -> 180 growth curve."""
    if index < 90:
        # the original ~90 employees, hired before the growth window
        return random_date(COMPANY_START, WINDOW_START)
    # remaining ~105 hired during the 18-month growth window, weighted toward recent
    progress = (index - 90) / max(total - 90, 1)
    weighted_progress = progress ** 0.6  # convex: more hires as time goes on
    day_offset = int(weighted_progress * (AS_OF - WINDOW_START).days)
    return WINDOW_START + timedelta(days=day_offset)


def gen_identity_inventory():
    rows = []
    terminated_indices = set(random.sample(range(TOTAL_EMPLOYEES), NUM_TERMINATED))
    offboarding_gap_indices = set(random.sample(sorted(terminated_indices), NUM_OFFBOARDING_GAPS))

    for i in range(TOTAL_EMPLOYEES):
        employee_id = f"EMP-{i + 1:04d}"
        department = random.choice(DEPARTMENTS)
        title = random.choice(TITLES_BY_DEPT[department])
        full_name = fake.name()
        email = f"{full_name.lower().replace(' ', '.')}@veridianlegaltech.example"
        employment_type = "Contractor" if random.random() < 0.12 else "FTE"
        hire_date = gen_hire_date(i, TOTAL_EMPLOYEES)

        is_terminated = i in terminated_indices
        if is_terminated:
            # For employees hired within 30 days of AS_OF, the usual 30-day
            # minimum tenure floor would exceed AS_OF and produce a future
            # date. Clamp the floor to AS_OF so termination is never dated
            # after "today" — this employee was simply terminated almost
            # immediately.
            term_date = random_date(min(hire_date + timedelta(days=30), AS_OF), AS_OF)
            status = "Terminated"
            okta_status = "Active" if i in offboarding_gap_indices else "Deprovisioned"
        else:
            term_date = ""
            status = "Active"
            okta_status = "Active" if random.random() > 0.03 else "Suspended"

        if title in ADMIN_TITLES and random.random() < 0.5:
            role_category = "Admin"
        elif title in PRIVILEGED_TITLES:
            role_category = "Privileged"
        else:
            role_category = "Standard"

        mfa_enrolled = "N" if (employment_type == "Contractor" and random.random() < 0.2) or random.random() < 0.04 else "Y"

        if role_category in ("Privileged", "Admin"):
            # most reviewed within the last ~120 days; a meaningful chunk are stale or never reviewed
            roll = random.random()
            if roll < 0.55:
                last_review = random_date(AS_OF - timedelta(days=120), AS_OF)
            elif roll < 0.85:
                last_review = random_date(AS_OF - timedelta(days=400), AS_OF - timedelta(days=180))
            else:
                last_review = ""
        else:
            last_review = random_date(AS_OF - timedelta(days=365), AS_OF) if random.random() < 0.6 else ""

        manager_id = f"EMP-{random.randint(1, i):04d}" if i >= 5 else ""

        rows.append({
            "employee_id": employee_id,
            "full_name": full_name,
            "email": email,
            "department": department,
            "title": title,
            "employment_type": employment_type,
            "manager_id": manager_id,
            "hire_date": hire_date.isoformat(),
            "term_date": term_date.isoformat() if term_date else "",
            "status": status,
            "okta_status": okta_status,
            "mfa_enrolled": mfa_enrolled,
            "role_category": role_category,
            "last_access_review_date": last_review.isoformat() if last_review else "",
        })
    return rows


SERVICE_ACCOUNT_DEFS = [
    ("SVC-Okta-Provisioning", "Okta", True, True),
    ("SVC-CI-Deploy-Prod", "GitHub / AWS", True, True),
    ("SVC-CI-Deploy-Staging", "GitHub / AWS", True, False),
    ("SVC-Backup-RDS", "AWS RDS", True, True),
    ("SVC-Monitoring-Datadog", "AWS", False, False),
    ("SVC-Salesforce-Sync", "Salesforce", True, False),
    ("SVC-Stripe-Billing", "Stripe", False, True),
    ("SVC-Slack-Bot-Ops", "Slack", True, False),
    ("SVC-S3-DocPipeline", "AWS S3", True, True),
    ("SVC-EKS-ClusterAdmin", "AWS EKS", True, True),
    ("SVC-Notion-Sync", "Notion", True, False),
    ("SVC-GitHub-Actions-Bot", "GitHub", True, False),
    ("SVC-Legacy-EDiscovery-App", "Internal App", True, True),
    ("SVC-HRIS-Integration", "HRIS", False, False),
    ("SVC-Zendesk-Support-Bot", "Support Tooling", False, False),
    ("SVC-Terraform-CloudOps", "AWS", True, True),
    ("SVC-VPN-Gateway", "Network", False, True),
    ("SVC-DB-Migration-Runner", "AWS RDS", True, False),
]


def gen_service_accounts(identity_rows):
    active_employee_ids = [r["employee_id"] for r in identity_rows if r["status"] == "Active"]
    rows = []
    for i, (name, system, shared, privileged) in enumerate(SERVICE_ACCOUNT_DEFS):
        account_id = f"SA-{i + 1:03d}"
        owner = "" if shared and random.random() < 0.4 else random.choice(active_employee_ids)
        created_date = random_date(COMPANY_START, AS_OF - timedelta(days=60))
        if random.random() < 0.35:
            last_reviewed = ""
        else:
            last_reviewed = random_date(AS_OF - timedelta(days=500), AS_OF)
        rows.append({
            "account_id": account_id,
            "account_name": name,
            "system": system,
            "owner_employee_id": owner,
            "shared": "Y" if shared else "N",
            "privileged": "Y" if privileged else "N",
            "created_date": created_date.isoformat(),
            "last_reviewed_date": last_reviewed.isoformat() if last_reviewed else "",
            "status": "Active",
        })
    return rows


ASSET_DEFS = [
    ("Okta", "Identity Provider", "IdP", "High", "SaaS", "IT/Security", "SSO + MFA enforcement for most connected apps"),
    ("AWS Production Account", "Cloud Infrastructure", "Cloud", "High", "AWS", "Engineering", "Hosts customer-facing production workloads"),
    ("AWS Staging Account", "Cloud Infrastructure", "Cloud", "Medium", "AWS", "Engineering", "Pre-production environment"),
    ("AWS Security/Logging Account", "Cloud Infrastructure", "Cloud", "High", "AWS", "IT/Security", "Centralized log aggregation and security tooling"),
    ("EKS Production Cluster", "Container Platform", "Cloud", "High", "AWS", "Engineering", "Runs primary application workloads"),
    ("S3 - Client Document Storage", "Object Storage", "Cloud", "High", "AWS", "Engineering", "Stores client matter documents and e-discovery artifacts"),
    ("RDS - Primary Application DB", "Database", "Cloud", "High", "AWS", "Engineering", "Stores matter metadata and application state"),
    ("Next.js Frontend", "Application", "App", "Medium", "AWS", "Engineering", "Customer-facing web application"),
    ("GitHub", "Source Control", "Repo", "High", "SaaS", "Engineering", "Source code and CI/CD pipeline definitions"),
    ("Slack", "Collaboration", "SaaS", "Medium", "SaaS", "IT/Security", "Internal communication; some client-related discussion occurs here"),
    ("Notion", "Knowledge Base", "SaaS", "Medium", "SaaS", "People/HR", "Internal documentation and process wiki"),
    ("Stripe", "Billing", "SaaS", "Medium", "SaaS", "Finance", "Subscription billing and payment processing"),
    ("Salesforce", "CRM", "SaaS", "Medium", "SaaS", "Sales", "Customer and pipeline records"),
    ("HRIS Platform", "HR System", "SaaS", "High", "SaaS", "People/HR", "Employee records, source of truth for joiner/mover/leaver events"),
    ("Legacy E-Discovery App", "Internal Application", "App", "High", "AWS", "Engineering", "Older service predating current SSO rollout; partial Okta integration"),
]


def gen_asset_inventory():
    rows = []
    for i, (name, atype, category, sensitivity, hosting, owner_dept, notes) in enumerate(ASSET_DEFS):
        rows.append({
            "asset_id": f"AST-{i + 1:03d}",
            "asset_name": name,
            "asset_type": atype,
            "category": category,
            "data_sensitivity": sensitivity,
            "hosting": hosting,
            "owner_department": owner_dept,
            "notes": notes,
        })
    return rows


VENDOR_DEFS = [
    ("Okta", "Identity provider (IdP)", "Okta tenant", "Y", "Admin"),
    ("GitHub", "Source control / CI-CD", "GitHub org", "N", "Admin"),
    ("Slack", "Team collaboration", "Slack workspace", "Y", "Admin"),
    ("Notion", "Internal documentation", "Notion workspace", "N", "Admin"),
    ("Stripe", "Payment processing", "Stripe account", "Y", "Standard"),
    ("Salesforce", "CRM", "Salesforce org", "Y", "Admin"),
    ("Amazon Web Services", "Cloud infrastructure", "AWS Organization", "Y", "Admin"),
    ("Gusto (Payroll Processor)", "Payroll and benefits administration", "HRIS integration", "N", "Standard"),
    ("Relativity (E-Discovery Subprocessor)", "E-discovery data processing for select customer matters", "S3, Legacy E-Discovery App", "Y", "Standard"),
    ("Datadog", "Monitoring and observability", "AWS accounts", "N", "Standard"),
    ("Zendesk", "Customer support tooling", "Support Tooling", "Y", "Standard"),
    ("DocuSign", "E-signature for contracts", "Salesforce integration", "N", "Standard"),
]


def gen_vendor_access():
    rows = []
    for i, (name, service, systems, accesses_client_data, access_level) in enumerate(VENDOR_DEFS):
        last_reviewed = "" if random.random() < 0.3 else random_date(AS_OF - timedelta(days=540), AS_OF)
        contract_status = "Active" if random.random() > 0.08 else "Renewal Pending"
        rows.append({
            "vendor_id": f"VEN-{i + 1:03d}",
            "vendor_name": name,
            "service_provided": service,
            "systems_accessed": systems,
            "accesses_client_data": accesses_client_data,
            "access_level": access_level,
            "last_reviewed_date": last_reviewed.isoformat() if last_reviewed else "",
            "contract_status": contract_status,
        })
    return rows


def write_csv(filename, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {path}")


def main():
    identity_rows = gen_identity_inventory()
    write_csv("identity_inventory.csv", identity_rows)
    write_csv("service_accounts.csv", gen_service_accounts(identity_rows))
    write_csv("asset_inventory.csv", gen_asset_inventory())
    write_csv("vendor_access.csv", gen_vendor_access())


if __name__ == "__main__":
    main()
