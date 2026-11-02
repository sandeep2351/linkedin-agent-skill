"""Write the LinkedIn profile copy from the resume. Recruiters skim this in a few seconds.

The numbers are the ones on the resume. Nothing new is added.
Two overlapping SproutsAI titles are collapsed into one current role so the profile does not look duplicated.

The dry run reads that same record, rewrites it as objects, and saves a JSON file.
It does not log into LinkedIn and it does not upload anything.
"""

import json
from pathlib import Path

from .resume_facts import (
    CERTIFICATIONS,
    CONTACT,
    EDUCATION,
    EXPERIENCES,
    LEADERSHIP,
    PROJECTS,
    SKILL_GROUPS,
    SUMMARY,
)

HEADLINE = (
    "DevOps Engineer | Jenkins CI/CD, Kubernetes, Terraform, AWS, Azure, GCP | "
    "I take a release from hours to minutes and keep production observable"
)

ABOUT = """If you are hiring for DevOps, cloud, SRE, or platform engineering, the proof you usually need is simple: a pipeline that ships, infrastructure you can rebuild, and a system you can see when it fails.

That is the work I do.

At SproutsAI, a US-based startup, I design Jenkins pipelines that cut deployment time by 80% and support 10+ production releases a day, with tests, security scanning, and rollback. I led a zero-downtime move from Azure to GCP, including 500GB+ of databases and container workloads, using blue-green deployment. Prometheus, Grafana, and the ELK stack reduced MTTR by 60%.

I also build the applications I deploy. React, Next.js, and Node.js, plus SensAI, an LLM career coach on the OpenAI API with streaming responses and prompt pipelines. The pipeline is better when you understand the app.

Open to DevOps, Cloud, SRE, and platform roles.
B.Tech in Information Technology, Vishnu Institute of Technology. GPA 8.89/10.
ServiceNow CSA and CAD.

Portfolio: sandeepkalyan-portfolio.vercel.app
"""

EXPERIENCE = """CURRENT ROLE  (use one LinkedIn entry, not two)

DevOps Engineer
SproutsAI · Remote
Apr 2025 – Present

The resume lists a second title at the same company for the same dates (Full Stack AI Engineer & DevOps Engineer). Put that work in the bullets and in About. Two current cards with the same dates read as a duplicate.

- Designed Jenkins CI/CD that reduced deployment time by 80% and supports 10+ production releases a day, with automated tests, security scanning, and rollback
- Led a zero-downtime migration from Azure to GCP for 500GB+ of databases and container workloads, using blue-green deployment
- Built Prometheus, Grafana, and ELK monitoring that reduced MTTR by 60%
- Containerized 20+ production services with Docker, including autoscaling, load balancing, and health checks
- Administered Azure and AWS (EC2, S3, Route 53, VPC, IAM, load balancers) and GCP, and cut cloud cost by 30% through right-sizing and scheduling
- Wrote Python automation for log analysis, backups, and health checks, cutting manual operational effort by 85%
- Built and deployed React, Next.js, and Node.js services on that same pipeline, including RBAC and Grafana dashboards with tracing

PREVIOUS ROLE

Software Developer & DevOps Engineer
Techin IT
Jun 2024 – Dec 2024

- Built React, Node.js, and Express applications and REST APIs on PostgreSQL and MongoDB
- Replaced manual releases with CI/CD for build, test, and deploy
- Containerized services with Docker on AWS and fronted them with NGINX
- Added monitoring, logging, and Bash/Python automation for backups and environment setup

EDUCATION

Bachelor of Technology, Information Technology
Vishnu Institute of Technology, Bhimavaram
Dec 2023 – Apr 2026
GPA 8.89/10

Diploma in Computer Engineering
Smt. B. Seetha Polytechnic, Bhimavaram
Jun 2020 – Jul 2023

FEATURED  (three items)

1. Portfolio: https://sandeepkalyan-portfolio.vercel.app
2. The latest roadmap GIF from automation/output (pin the post after you publish it)
3. SensAI, the LLM career coach, or the Jenkins pipeline project. One proof, not both, if you only have three slots.

BANNER

One line, high contrast, your name small in the corner:
DevOps Engineer · CI/CD · Kubernetes · Multi-cloud · Observability

SKILLS  (pin these first, in this order)

Kubernetes
Terraform
CI/CD
Docker
AWS
Jenkins
Prometheus
Linux
Python
Azure

Then GCP, Helm, GitHub Actions, Ansible, ELK, NGINX, React, Node.js.

HEADLINE TO RETIRE

Anything that is only the job title, and any line that starts with "passionate about".

CONTACT

Keep the email and phone already on the profile.
Custom URL: linkedin.com/in/sandeep-kalyan
Add the portfolio under Contact info and in Featured.
Open to work: DevOps Engineer, Cloud Engineer, SRE, Platform Engineer. On-site, hybrid, and remote.

PHOTO

Face large in the frame, recent, plain background. Recruiters decide on the headline and the photo before they read About.
"""


# Sections a caller may send. Anything else in the body is ignored so a stray key cannot become profile copy.
PROFILE_FIELDS = (
    "headline",
    "about",
    "experience",
    "education",
    "skills",
    "featured",
    "banner",
    "contact",
    "projects",
    "certifications",
    "leadership",
    "photo",
    "activity",
    "recommendations",
)


def source_profile() -> dict:
    """The full record already on the resume, shaped like a LinkedIn profile."""
    # Skills stay as named groups so the JSON is a list of objects, not one long string.
    skills = [{"name": name, "detail": detail} for name, detail in SKILL_GROUPS]
    return {
        "headline": "",
        "about": SUMMARY.strip(),
        "banner": "",
        "featured": [],
        "photo": "",
        "experience": [dict(role) for role in EXPERIENCES],
        "education": [dict(school) for school in EDUCATION],
        "skills": skills,
        "projects": [dict(project) for project in PROJECTS],
        "certifications": list(CERTIFICATIONS),
        "leadership": [dict(item) for item in LEADERSHIP],
        "contact": dict(CONTACT),
        "activity": "",
        "recommendations": "",
    }


def read_posted_profile(body: dict | None) -> dict:
    """Start from the resume, then overlay the LinkedIn sections the caller sent."""
    profile = source_profile()
    if not body:
        return profile
    # A nested profile object is the full paste. A flat body is accepted the same way.
    incoming = body.get("profile") if isinstance(body.get("profile"), dict) else body
    for field in PROFILE_FIELDS:
        value = incoming.get(field)
        if value in (None, "", [], {}):
            continue
        profile[field] = value
    return profile


def enhanced_profile() -> dict:
    """Recruiter-facing sections as objects. Same facts as the text kit, nothing invented."""
    current = EXPERIENCES[0]
    previous = EXPERIENCES[2]
    # Shortened from the resume so a recruiter can skim one card. The second SproutsAI title shares these dates.
    current_bullets = [
        "Designed Jenkins CI/CD that reduced deployment time by 80% and supports 10+ production releases a day, with automated tests, security scanning, and rollback",
        "Led a zero-downtime migration from Azure to GCP for 500GB+ of databases and container workloads, using blue-green deployment",
        "Built Prometheus, Grafana, and ELK monitoring that reduced MTTR by 60%",
        "Containerized 20+ production services with Docker, including autoscaling, load balancing, and health checks",
        "Administered Azure and AWS (EC2, S3, Route 53, VPC, IAM, load balancers) and GCP, and cut cloud cost by 30% through right-sizing and scheduling",
        "Wrote Python automation for log analysis, backups, and health checks, cutting manual operational effort by 85%",
        "Built and deployed React, Next.js, and Node.js services on that same pipeline, including RBAC and Grafana dashboards with tracing",
    ]
    return {
        "headline": HEADLINE,
        "about": ABOUT.strip(),
        "banner": "DevOps Engineer · CI/CD · Kubernetes · Multi-cloud · Observability",
        "open_to_work": [
            "DevOps Engineer",
            "Cloud Engineer",
            "Site Reliability Engineer",
            "Platform Engineer",
        ],
        "experience": [
            {
                "current": True,
                "title": "DevOps Engineer",
                "company": "SproutsAI",
                "location": current["where"],
                "start": "Apr 2025",
                "end": "Present",
                "note": (
                    "Use one LinkedIn entry. The Full Stack AI Engineer title covers the same dates, "
                    "so that work stays in these bullets and in About."
                ),
                "bullets": current_bullets,
            },
            {
                "current": False,
                "title": previous["title"],
                "company": previous["company"],
                "location": previous["where"],
                "start": "Jun 2024",
                "end": "Dec 2024",
                "bullets": [
                    "Built React, Node.js, and Express applications and REST APIs on PostgreSQL and MongoDB",
                    "Replaced manual releases with CI/CD for build, test, and deploy",
                    "Containerized services with Docker on AWS and fronted them with NGINX",
                    "Added monitoring, logging, and Bash/Python automation for backups and environment setup",
                ],
            },
        ],
        "education": [
            {
                "school": "Vishnu Institute of Technology, Bhimavaram",
                "degree": "Bachelor of Technology, Information Technology",
                "start": "Dec 2023",
                "end": "Apr 2026",
                "detail": "GPA 8.89/10",
            },
            {
                "school": "Smt. B. Seetha Polytechnic, Bhimavaram",
                "degree": "Diploma in Computer Engineering",
                "start": "Jun 2020",
                "end": "Jul 2023",
                "detail": "",
            },
        ],
        "skills": {
            "pin_first": [
                "Kubernetes",
                "Terraform",
                "CI/CD",
                "Docker",
                "AWS",
                "Jenkins",
                "Prometheus",
                "Linux",
                "Python",
                "Azure",
            ],
            "then": ["GCP", "Helm", "GitHub Actions", "Ansible", "ELK", "NGINX", "React", "Node.js"],
        },
        "featured": [
            {"title": "Portfolio", "url": "https://sandeepkalyan-portfolio.vercel.app"},
            {"title": "Latest roadmap GIF", "url": ""},
            {"title": "SensAI or the Jenkins pipeline", "url": ""},
        ],
        "contact": {
            "keep_existing_email_and_phone": True,
            "custom_url": CONTACT["linkedin"],
            "portfolio": CONTACT["portfolio"],
        },
        "photo": "Face large in the frame, recent, plain background.",
        "headline_to_retire": "Anything that is only the job title, and any line that starts with passionate about.",
    }


def write_profile_dry_run(folder: Path, source: dict) -> dict:
    """Save the source profile and the enhanced objects. Nothing is sent to LinkedIn or Drive."""
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "dry_run": True,
        "linkedin_changed": False,
        "drive_uploaded": False,
        "apply_manually": True,
        "source": source,
        "enhanced": enhanced_profile(),
    }
    path = folder / "dry-run.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["file"] = str(path)
    return payload


def write_profile_kit(folder: Path) -> Path:
    """Write the sections in the order you paste them into LinkedIn."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "headline.txt").write_text(HEADLINE + "\n", encoding="utf-8")
    (folder / "about.txt").write_text(ABOUT, encoding="utf-8")
    (folder / "experience.txt").write_text(EXPERIENCE, encoding="utf-8")
    order = (
        "PASTE ORDER\n"
        "1. Photo, if the current one is older than two years or the face is small.\n"
        "2. Banner, using the line in experience.txt.\n"
        "3. headline.txt\n"
        "4. about.txt\n"
        "5. One current SproutsAI role, with the bullets in experience.txt.\n"
        "6. Techin IT, then education.\n"
        "7. Pin the skills in the order listed.\n"
        "8. Featured: portfolio, then one project, then your newest roadmap post.\n"
        "9. Open to work for DevOps, Cloud, SRE, and platform roles.\n"
        "\n"
        "This file is the profile. Update LinkedIn from it when a role or a number changes.\n"
        "The runner does not log into LinkedIn.\n"
    )
    (folder / "PASTE-ORDER.txt").write_text(order, encoding="utf-8")
    return folder
