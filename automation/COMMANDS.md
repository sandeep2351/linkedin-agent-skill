# LinkedIn commands

The API listens on http://127.0.0.1:8787. Start it first. Each block below is the purpose, then the request.

Start the API. It serves the profile, the GIF posts, and the prepared job applications.

automation/.venv/bin/python -m automation.server

List every endpoint and its purpose. Use this when you forget which path does what.

curl -s http://127.0.0.1:8787/

Check that the API process is up.

curl -s http://127.0.0.1:8787/health

Enhance the LinkedIn profile from the resume. Writes the headline, about, and experience, then uploads those files to the Google Drive folder named Sandeep LinkedIn Profile.

curl -s -X POST http://127.0.0.1:8787/profile/enhance

Create the next roadmap GIF and caption, then upload post.gif, preview.png, and post.txt to the Google Drive folder named Sandeep LinkedIn Posts.

curl -s -X POST http://127.0.0.1:8787/posts/create

Upload a post folder that already exists on disk to the Sandeep LinkedIn Posts Drive folder. Omit folder to upload the newest post.gif.

curl -s -X POST http://127.0.0.1:8787/posts/upload -H 'Content-Type: application/json' -d '{"folder":"automation/output/HOW-AI-GOES-FROM-DEMO-TO-PRODUCTION"}'

Run the whole job pass in one request. It collects 0-3 year roles that match DevOps, cloud, SRE, platform, Kubernetes, observability, and MLOps from RemoteOK, Jobicy, Remotive, and Arbeitnow. Claude ranks them. For each match it writes a two-page resume from the original resume (three roles, all skills, projects, certifications, and leadership), adds role keywords that already appear on that resume, saves Company - Job Title.pdf, uploads that PDF to the Google Drive folder Sandeep Job Applications, and checks the apply link. submitted is true only when an employer career form accepts the PDF. The links from Jobicy and RemoteOK are board pages, not the career form. Jobicy asks for an account first. RemoteOK does not publish the employer apply URL. Those applications stay not_submitted. Open apply_url and attach the PDF. LinkedIn entries in the reply are search links, not apply buttons. limit defaults to 8 and is capped at 8. The same reply includes LinkedIn search links (Entry level and Associate, India, past week, remote).

curl -s -X POST http://127.0.0.1:8787/jobs -H 'Content-Type: application/json' -d '{"limit":8}'

Pull Naukri jobs in the 0-3 year band and apply with a tailored resume. Naukri does not return a job list or an apply form unless you are logged in, so count stays 0 and nothing is sent. search_url is the page to open yourself.

curl -s -X POST http://127.0.0.1:8787/jobs/naukri -H 'Content-Type: application/json' -d '{"limit":3}'

Pull Wellfound jobs in the 0-3 year band and apply with a tailored resume. Wellfound stops on a Cloudflare check, so count stays 0 and nothing is sent.

curl -s -X POST http://127.0.0.1:8787/jobs/wellfound -H 'Content-Type: application/json' -d '{"limit":3}'

Pull Simplify jobs in the 0-3 year band and apply with a tailored resume. Simplify does not publish the job list or an apply form to an unsigned request, so count stays 0 and nothing is sent.

curl -s -X POST http://127.0.0.1:8787/jobs/simplify -H 'Content-Type: application/json' -d '{"limit":3}'

Pull Indeed jobs in the 0-3 year band and apply with a tailored resume. Indeed refuses the unsigned request, so count stays 0 and nothing is sent.

curl -s -X POST http://127.0.0.1:8787/jobs/indeed -H 'Content-Type: application/json' -d '{"limit":3}'

Pull Instahyre entry-level roles whose titles match the resume, write a two-page tailored resume for each, and upload it to Sandeep Job Applications. Instahyre accepts the application only from a logged-in candidate profile, so submitted_count stays 0. limit defaults to 3 and is capped at 5.

curl -s -X POST http://127.0.0.1:8787/jobs/instahyre -H 'Content-Type: application/json' -d '{"limit":3}'

Drive folders, kept separate on purpose:

Sandeep LinkedIn Posts holds GIF posts.
Sandeep Job Applications holds Company - Job Title.pdf files.
Sandeep LinkedIn Profile holds the headline, about, and experience text.

# Local commands, without the API


Run these from the linkedin-agent-skill folder.
Use the venv Python so the GIF renderer can import Pillow.

automation/.venv/bin/python -m automation.run

Each block is the purpose, then the command.
The runner writes post.gif and post.txt. You upload the GIF and paste the caption. It does not log into LinkedIn.

Check that GIF posts can be built, and whether the optional model key is present.

automation/.venv/bin/python -m automation.run --check

Build the next roadmap. Topics rotate through AI, DevOps, Kubernetes, Terraform, network traffic, observability, releases, and ML. This marks the topic used so the next run is a different subject.

automation/.venv/bin/python -m automation.run

Build the demo-to-production GIF once, without marking the topic used.

automation/.venv/bin/python -m automation.run --demo

Build two unused roadmaps in one run.

automation/.venv/bin/python -m automation.run --count 2

Build the roadmap that matches an idea you type. Kubernetes, Terraform, Jenkins, network, observability, and ML are in the bank.

automation/.venv/bin/python -m automation.run --concept "Kubernetes"
automation/.venv/bin/python -m automation.run --concept "Terraform"
automation/.venv/bin/python -m automation.run --concept "how a request reaches a service"

Write the recruiter profile from the resume: headline, about, one current role, previous role, skills, featured, and banner. Paste the sections in the order in PASTE-ORDER.txt.

automation/.venv/bin/python -m automation.run --profile-kit

Score a profile you already pasted, when you want a number out of 100 before editing.

automation/.venv/bin/python -m automation.run --profile --file automation/examples/profile-sample.txt

Install the Mac schedule. It wakes at 08:15 every day and writes a new GIF only when the previous one is at least 2 days old.

automation/.venv/bin/python -m automation.run --schedule

Remove that schedule.

automation/.venv/bin/python -m automation.run --unschedule

The same two-day check the schedule uses. Safe to run by hand.

automation/.venv/bin/python -m automation.run --scheduled

Clean a draft and print the five-check human score. No model call.

automation/.venv/bin/python -m automation.run --human --file automation/output/profile/about.txt

Rank a CSV you exported from LinkedIn. Engagement rate, not raw impressions.

automation/.venv/bin/python -m automation.run --audit --file automation/examples/analytics-sample.csv

Sort pasted inbox messages into lead, recruiter, peer, ask, and spam.

automation/.venv/bin/python -m automation.run --inbox --file automation/examples/inbox-sample.txt

Write two comments on someone else's post.

automation/.venv/bin/python -m automation.run --comment --file automation/examples/comment-sample.txt

Draft replies under your own post. Separate the comments with a line of ---.

automation/.venv/bin/python -m automation.run --reply --file automation/examples/reply-sample.txt

Write the week plan for topics and posting times.

automation/.venv/bin/python -m automation.run --week

Turn one transcript into several standalone posts. Needs the Bedrock key.

automation/.venv/bin/python -m automation.run --repurpose --file automation/examples/transcript-sample.txt

Write an invite note under 200 characters, a first message, and two follow-ups. Needs the Bedrock key.

automation/.venv/bin/python -m automation.run --dm --who "Hiring manager, platform team" --reason "They posted about a Kubernetes migration" --want "a conversation about the role"

What each output file is for, after a GIF run:

post.gif is the image you upload.
preview.png is a still of the same roadmap, for a quick look.
post.txt is the caption you paste.
first-comment.txt is the portfolio link, pasted after the post is live so the link is not inside the caption.
detect.txt is the local human score.
HOW-TO-POST.txt is the upload order.
