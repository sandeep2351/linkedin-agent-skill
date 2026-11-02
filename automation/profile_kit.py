"""Write the LinkedIn profile copy from the resume. Recruiters skim this in a few seconds.

The numbers are the ones on the resume. Nothing new is added.
Two overlapping SproutsAI titles are collapsed into one current role so the profile does not look duplicated.
"""

from pathlib import Path

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
