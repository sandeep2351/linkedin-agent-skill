"""Facts taken from the original two-page resume. Tailoring may reorder keywords. It may not add new ones."""

import re

CONTACT = {
    "name": "P. SANDEEP KALYAN",
    "location": "Bhimavaram, Andhra Pradesh, India",
    "phone": "+91 8367331109",
    "phone_display": "(+91) 8367331109",
    "email": "sandeepkalyan299@gmail.com",
    "linkedin": "linkedin.com/in/sandeep-kalyan",
    "portfolio": "sandeepkalyan-portfolio.vercel.app",
}

# Strings that are allowed to appear as proof. A tailored resume may not invent a new figure.
ALLOWED_NUMBERS = (
    "80%",
    "60%",
    "10+",
    "500GB+",
    "20+",
    "30%",
    "85%",
    "99.9%",
    "8.89",
    "15+",
    "40%",
    "50+",
    "6",
    "3",
    "24-hour",
)

SUMMARY = (
    "DevOps Engineer with hands-on, production experience architecting CI/CD pipelines, "
    "multi-cloud infrastructure (AWS, Azure, GCP), and observability platforms that cut "
    "deployment time by up to 80%, reduce MTTR by 60%, and drive measurable cost savings at scale. "
    "Brings a complementary full-stack and applied AI engineering background, building production "
    "React, Next.js, and Node.js applications and LLM-powered tools, which gives a sharper, "
    "systems-level understanding of the applications being deployed, scaled, and monitored. "
    "Focused on applying automation, infrastructure-as-code, and reliability engineering practices "
    "to help engineering teams ship faster and more reliably."
)

# Three LinkedIn entries. The two SproutsAI titles share dates and stay separate, as on the original resume.
EXPERIENCES = [
    {
        "title": "DevOps Engineer",
        "company": "SproutsAI (US-based Startup)",
        "when": "Apr 2025 – Present",
        "where": "Remote",
        "bullets": [
            "Designed and implemented end-to-end CI/CD pipelines using Jenkins, reducing deployment time by 80% and enabling 10+ daily production releases with automated testing, security scanning, and rollback mechanisms.",
            "Managed multi-cloud infrastructure across GCP and Azure using configuration management tools and automation scripts, maintaining 50+ version-controlled cloud resources.",
            "Led a zero-downtime migration of the entire application infrastructure from Azure to GCP, moving 500GB+ of databases, container workloads, and network configurations using a blue-green deployment strategy.",
            "Built a monitoring and alerting stack using Prometheus, Grafana, and the ELK Stack, reducing MTTR by 60% and preventing 15+ potential production outages through proactive monitoring.",
            "Containerized microservice applications with Docker, implementing auto-scaling, load balancing, and health monitoring for 20+ production services.",
            "Integrated automated QA testing (unit, integration, security, performance) into CI/CD pipelines, achieving zero production defects while maintaining 99.9% system uptime.",
            "Developed Python automation scripts for log analysis, backup verification, and system health checks, cutting manual operational effort by 85%.",
            "Administered Azure (ACR, Key Vault, VMs, Storage) and AWS (EC2, S3, Route 53, Load Balancers, VPC, IAM) resources, optimizing cloud costs by 30% through right-sizing and scheduling.",
            "Established centralized container image management on Azure Container Registry with retention policies, security scanning, and version control.",
            "Configured declarative Jenkins pipelines with automated builds, tests, and deployments, including stage gates and approval workflows.",
        ],
    },
    {
        "title": "Full Stack AI Engineer & DevOps Engineer",
        "company": "SproutsAI (US-based Startup)",
        "when": "Apr 2025 – Present",
        "where": "Remote",
        "bullets": [
            "Developed and deployed cloud-native applications using React, Next.js, Node.js, and Express.js on containerized infrastructure, with CI/CD pipelines for automated builds and deployments.",
            "Designed and deployed automated release strategies, including blue-green deployments, to minimize downtime during production rollouts.",
            "Built Grafana monitoring dashboards and integrated APM with distributed tracing to identify bottlenecks and optimize system performance.",
            "Implemented an enterprise-grade RBAC system with secure authentication, enforcing least-privilege access controls across cloud platforms.",
            "Automated database backup and disaster recovery procedures, including restoration testing, to meet RPO/RTO targets for production databases.",
            "Partnered with development teams to optimize performance and enforce security best practices across production services.",
        ],
    },
    {
        "title": "Software Developer & DevOps Engineer",
        "company": "Techin IT",
        "when": "Jun 2024 – Dec 2024",
        "where": "",
        "bullets": [
            "Developed and maintained full-stack web applications using React, Node.js, and Express.js, delivering new features and bug fixes in collaboration with a cross-functional team.",
            "Built and maintained REST APIs with PostgreSQL and MongoDB backends, applying code reviews and Git-based workflows to improve code quality and release consistency.",
            "Set up CI/CD pipelines to automate build, test, and deployment stages, replacing manual releases and reducing deployment effort.",
            "Containerized applications with Docker and deployed them to cloud environments (AWS), managing environment configuration and NGINX reverse proxy setups.",
            "Implemented basic monitoring, logging, and alerting to track application health and speed up troubleshooting of production issues.",
            "Wrote Bash and Python scripts to automate routine operational tasks such as backups, log cleanup, and environment provisioning.",
        ],
    },
]

PROJECTS = [
    {
        "title": "Jenkins CI/CD Pipeline Automation",
        "meta": "DevOps · Personal Project",
        "bullets": [
            "Built and maintained automated Jenkins CI/CD pipelines driving 20+ projects from commit to production, cutting deployment time from hours to minutes.",
            "Automated Docker image builds and Kubernetes deployments across multi-environment (dev, stage, prod) setups on Azure, with webhook-triggered builds on every commit.",
            "Implemented secrets management and tested rollback procedures for every release, eliminating manual, error-prone deployment steps.",
            "Designed pipeline-as-code from the outset, enabling consistent, version-controlled, and repeatable deployments.",
        ],
    },
    {
        "title": "Observability Stack — Grafana & Prometheus Monitoring",
        "meta": "DevOps · Personal Project",
        "bullets": [
            "Deployed a Grafana and Prometheus monitoring stack for centralized logging, real-time metrics dashboards, and automated alert routing via Google Chat.",
            "Configured Prometheus scrape targets across distributed services and built custom Grafana dashboards aligned to on-call workflows.",
            "Tuned alert thresholds with Alertmanager to reduce alert fatigue while preserving fast incident detection.",
            "Delivered full-stack observability (logs, metrics, alerts) for production-style services running on Docker and Linux.",
        ],
    },
    {
        "title": "SensAI — AI Career Coach",
        "meta": "Full-Stack + AI · Personal Project",
        "bullets": [
            "Built an LLM-powered career coaching platform using React, Node.js, and the OpenAI API, delivering personalized career guidance, resume feedback, and skill-gap analysis.",
            "Engineered context-aware prompt pipelines to maintain conversational relevance while safeguarding user data across sessions.",
            "Implemented streaming LLM responses to reduce perceived latency and improve the real-time chat experience.",
            "Applied prompt-engineering best practices to ensure consistent, high-quality AI outputs across varied user inputs.",
        ],
    },
]

EDUCATION = [
    {
        "school": "Vishnu Institute of Technology, Bhimavaram, India",
        "when": "Dec 2023 – Apr 2026",
        "detail": "Bachelor of Technology in Information Technology — GPA: 8.89 / 10",
        "coursework": "Data Structures & Algorithms, Operating Systems, Computer Networks, Database Systems, Software Engineering, Cloud Computing, System Administration",
    },
    {
        "school": "Smt. B. Seetha Polytechnic, Bhimavaram, India",
        "when": "Jun 2020 – Jul 2023",
        "detail": "Diploma in Computer Engineering",
        "coursework": "Programming Fundamentals (C, C++, Python), Computer Networks, Operating Systems (Linux/Windows), Database Management, System Administration",
    },
]

SKILL_GROUPS = [
    ("Cloud Platforms", "AWS (EC2, S3, VPC, Route 53, ALB/NLB, IAM, CloudWatch, Lambda, RDS, Auto Scaling Groups); Azure (VMs, Container Registry, Key Vault, Storage Accounts, Virtual Networks); GCP"),
    ("Containerization & Orchestration", "Docker, Docker Compose, Kubernetes, Helm, Container Registry Management"),
    ("CI/CD, Version Control & GitOps", "Jenkins, GitHub Actions, GitLab CI, ArgoCD, Azure DevOps Pipelines, Git, GitHub, GitLab"),
    ("Infrastructure as Code", "Terraform, Ansible, YAML"),
    ("Monitoring & Observability", "Prometheus, Grafana, ELK Stack (Elasticsearch, Logstash, Kibana), CloudWatch, Azure Monitor"),
    ("Scripting & Automation", "Python, Bash, Shell Scripting"),
    ("Operating Systems & Networking", "Linux (Ubuntu), Windows Server, VPC, Subnets, Security Groups, Load Balancing, DNS, VPN"),
    ("Databases", "PostgreSQL, MongoDB, MySQL, Redis, Elasticsearch, RabbitMQ"),
    ("Security", "SSL/TLS, Key Management, Secret Management, RBAC"),
    ("Web Servers & Deployment", "NGINX, Reverse Proxy Configuration, Blue-Green Deployment, Rolling Deployment"),
    ("Full-Stack Development", "React, Next.js, Node.js, Express.js, TypeScript, REST APIs, GraphQL, WebSockets, Tailwind CSS"),
    ("AI & LLM Engineering", "LLMs, Prompt Engineering, OpenAI API, RAG (Retrieval-Augmented Generation), Vector Search / Embeddings, AWS Textract, Resume Parsing & OCR"),
    ("Methodologies", "Agile/Scrum, DevOps, GitOps, CI/CD"),
]

CERTIFICATIONS = [
    "ServiceNow Certified System Administrator (CSA) — ServiceNow Learning, Jul 2025",
    "ServiceNow Certified Application Developer (CAD) — ServiceNow Learning, Jul 2025",
    "SQL for Data Science — Coursera, Jul 2024",
    "JavaScript Essentials — Scaler Academy, Jul 2024",
]

LEADERSHIP = [
    {
        "title": "Web Development Lead — DO IT Club, Vishnu Institute of Technology",
        "bullets": [
            "Led a team of 6 developers in deploying a cloud-based departmental coordination tool on AWS, implementing automated CI/CD pipelines and infrastructure monitoring.",
            "Organized 3 technical workshops on DevOps practices, Docker containerization, and cloud infrastructure management.",
            "Established Git workflow standards, code review processes, and automated testing practices, reducing deployment failures by 40%.",
        ],
    },
    {
        "title": "Top 5 Finalist — Internal Hackathon, Vishnu Institute of Technology",
        "bullets": [
            "Developed a cloud-native solution with an automated deployment pipeline and infrastructure monitoring using a containerized microservices architecture.",
            "Implemented a complete DevOps workflow from code commit to production deployment within a 24-hour constraint.",
        ],
    },
]

ADDITIONAL = [
    "Availability: Open to night shift operations and 24/7 on-call rotations for production support.",
    "Strengths: Strong troubleshooting skills, infrastructure monitoring expertise, automation mindset, collaborative team player.",
    "Learning focus: Kubernetes advanced patterns, service mesh (Istio), and observability practices.",
]

# Display order for ATS keywords. A phrase is used only when the job text contains it and the original resume already lists it.
KEYWORD_ORDER = [
    "CI/CD",
    "Jenkins",
    "GitHub Actions",
    "GitLab CI",
    "ArgoCD",
    "GitOps",
    "Terraform",
    "Ansible",
    "Docker",
    "Kubernetes",
    "Helm",
    "AWS",
    "Azure",
    "GCP",
    "Prometheus",
    "Grafana",
    "ELK",
    "Linux",
    "Python",
    "Bash",
    "NGINX",
    "PostgreSQL",
    "MongoDB",
    "RBAC",
    "Key Vault",
    "blue-green",
    "observability",
    "infrastructure as code",
    "site reliability",
    "on-call",
    "OpenAI",
    "RAG",
    "React",
    "Node.js",
    "Next.js",
    "TypeScript",
    "REST",
    "CloudWatch",
    "IAM",
    "VPC",
    "Terraform",
]

SKILLS = "; ".join(f"{name}: {body}" for name, body in SKILL_GROUPS)

# Kept so older imports still resolve. The PDF uses SUMMARY and EXPERIENCES.
CURRENT = EXPERIENCES[0]
PREVIOUS = EXPERIENCES[2]

SEARCH_TITLES = [
    "DevOps Engineer",
    "Cloud Engineer",
    "Site Reliability Engineer",
    "Platform Engineer",
    "CI/CD Engineer",
    "Kubernetes Engineer",
    "Observability Engineer",
    "MLOps Engineer",
    "AWS DevOps Engineer",
    "Azure DevOps Engineer",
    "GCP Cloud Engineer",
]

SUMMARIES = {"devops": SUMMARY}


def family(title: str) -> str:
    """Which summary family the job title belongs to. The PDF uses the original summary either way."""
    low = title.lower()
    if "sre" in low or "reliability" in low:
        return "sre"
    if "sec" in low:
        return "devsecops"
    if "observ" in low or "monitor" in low:
        return "observability"
    if "kubernetes" in low or "container" in low:
        return "k8s"
    if "mlops" in low or "llm" in low or "machine learning" in low:
        return "mlops"
    if "platform" in low or "gitops" in low:
        return "platform"
    if "aws" in low:
        return "aws"
    if "azure" in low:
        return "azure"
    if "gcp" in low or "google cloud" in low:
        return "gcp"
    return "devops"


def matched_keywords(description: str) -> list[str]:
    """Job words that already appear on the original resume, in a stable order."""
    low = re.sub(r"[^a-z0-9+.#/ ]+", " ", (description or "").lower())
    low = f" {low} "
    found = []
    seen = set()
    for phrase in KEYWORD_ORDER:
        key = phrase.lower()
        if key in seen:
            continue
        # Whole phrase, so "git" does not light up inside an unrelated word.
        if f" {key} " in low or key in low:
            # Require the phrase itself, not a accidental substring like "rest" inside "restore".
            if re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", low):
                found.append(phrase)
                seen.add(key)
    return found


def source_text() -> str:
    """Every allowed sentence, used to reject invented claims."""
    parts = [SUMMARY, SKILLS]
    for role in EXPERIENCES:
        parts.extend(role["bullets"])
    for project in PROJECTS:
        parts.append(project["title"])
        parts.extend(project["bullets"])
    for school in EDUCATION:
        parts.append(school["detail"])
    parts.extend(CERTIFICATIONS)
    for item in LEADERSHIP:
        parts.extend(item["bullets"])
    parts.extend(ADDITIONAL)
    return "\n".join(parts)
