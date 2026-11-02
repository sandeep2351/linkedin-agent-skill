"""Roadmap posts for a DevOps and applied-AI profile.

Each board is one LinkedIn GIF plus the caption under it.
The facts about my work come from the resume. The roadmaps teach the mechanism.
"""

FOOTER = (
    "\n\nI work these paths in production: Jenkins, Docker, Kubernetes, Terraform, "
    "and AWS, Azure, and GCP.\n\n"
    "Save this roadmap for the next system you take past a demo."
)


BOARDS = [
    {
        "id": "ai-demo-to-production",
        "keywords": ["ai", "llm", "demo", "production", "rag"],
        "category": "ai",
        "title": "HOW AI GOES FROM\nDEMO TO PRODUCTION",
        "stages": [
            {
                "name": "Prototype",
                "title": "Start with a clear goal",
                "points": [
                    "Name the use case and the number that means it worked.",
                    "Pick the model and the limit you will accept.",
                    "Build the first version in a notebook or an LLM API.",
                ],
                "tools": ["Jupyter", "OpenAI API"],
                "callout": "The demo trap: 10 happy prompts are not 10,000 real users.",
            },
            {
                "name": "Data",
                "title": "Connect real information",
                "points": [
                    "Ingest the documents, rows, and APIs the job actually uses.",
                    "Chunk, embed, and index. Keep the source on every chunk.",
                    "Retrieve with filters, not with a dump of the whole corpus.",
                ],
                "tools": ["Airflow", "pgvector", "Qdrant"],
            },
            {
                "name": "Build",
                "title": "Orchestrate the workflow",
                "points": [
                    "Plan the steps, call the tools, and ground the answer.",
                    "Put a gateway in front: routing, fallback, and a rate limit.",
                    "Check what goes in and what comes out.",
                ],
                "tools": ["LangGraph", "LiteLLM", "Guardrails"],
            },
            {
                "name": "Evaluate",
                "title": "Test before you deploy",
                "points": [
                    "Keep a golden set of real questions and the expected answers.",
                    "Score faithfulness, relevance, and hallucinations.",
                    "Run a red team, then a human review, then ship only if the score holds.",
                ],
                "tools": ["Ragas", "DeepEval", "Promptfoo"],
            },
            {
                "name": "Operate",
                "title": "Watch it in production",
                "points": [
                    "Track latency, cost per request, and the failure rate.",
                    "Trace the prompt, the retrieval, and the tool call.",
                    "Roll out with a flag. Every bad answer becomes a new test.",
                ],
                "tools": ["Langfuse", "Grafana", "OpenTelemetry"],
            },
        ],
        "post": """The first 10 AI responses might impress your team.
The next 10,000 will test the whole system.

A demo runs on a few prompts you chose. Production meets messy documents, odd requests, a security review, a cost line, and a latency target.

That is where AI engineering becomes a DevOps problem.

Here is the roadmap I use, in 5 stages.

1. Prototype: start with a clear goal
Before the notebook, write the business problem and the number that means it worked.

Name the use case and the KPI.
Choose the model and the limit you will accept.
Build one working path with a notebook or an LLM API.

The point of the prototype is to learn if the idea is real. It is not the production design.

2. Data and context: connect real information
A folder of sample PDFs will not survive the first real user.

Ingest from the documents, databases, and APIs the team already trusts.
Chunk, embed, and keep the source attached to the chunk.
Store and filter that context in a vector database.

Tools I reach for on this stage: an orchestrated pipeline, then pgvector, Qdrant, or a managed vector store.

3. Build and orchestrate: make one reliable workflow
Connect the model, the retrieval, and the tools the answer is allowed to call.

Use RAG when the answer has to come from your data.
Put a gateway in front for routing, fallback, and rate limits.
Add guardrails for what may enter the prompt and what may leave the model.

4. Evaluate: a fluent answer can still be the wrong answer
Build a set of real questions with the answer you expect.
Measure faithfulness, relevance, and hallucinations.
Red-team the prompt. Then let a person who knows the domain review the misses.
Ship only when the score stays at or above the baseline.

5. Deploy and operate: earn the right to stay up
Track latency, cost, and the rate of bad answers.
Trace the request through retrieval and the model.
Collect the thumbs-down and turn it into the next test case.
Release behind a flag, not to every user on minute one.

The bigger picture:

A prototype proves that a model can answer.
Production engineering proves it can answer again, safely, at a cost you can explain.
The hard part is not the first good response. It is the next thousand, under real traffic.

I have taken one version of this path from a product idea to a running app: SensAI, an LLM career coach on React, Node.js, and the OpenAI API, with streaming responses and prompt pipelines. The same production habits apply as on any service I deploy: a pipeline, a rollback, and a dashboard."""
        + FOOTER
        + "\n\n#AIEngineering #LLMOps #DevOps\n",
        "comment": "Portfolio, with the project notes: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "jenkins-commit-to-production",
        "keywords": ["jenkins", "cicd", "ci/cd", "pipeline"],
        "category": "devops",
        "title": "HOW A COMMIT\nREACHES PRODUCTION",
        "stages": [
            {
                "name": "Commit",
                "title": "The pipeline starts in Git",
                "points": [
                    "One branch policy. Review before the main line moves.",
                    "A webhook starts the job. Nobody deploys from a laptop.",
                    "The Jenkinsfile lives next to the code.",
                ],
                "tools": ["Git", "GitHub", "Jenkins"],
            },
            {
                "name": "Build",
                "title": "Produce one artifact",
                "points": [
                    "Install dependencies from a lock, not from 'latest'.",
                    "Build the Docker image and tag it with the commit.",
                    "Push it to a registry you can scan.",
                ],
                "tools": ["Docker", "ACR"],
            },
            {
                "name": "Verify",
                "title": "Fail the build in CI",
                "points": [
                    "Unit and integration tests run on every commit.",
                    "A security scan blocks a known-bad image.",
                    "A stage gate stops the line if the check is red.",
                ],
                "tools": ["Jenkins", "QA gates"],
            },
            {
                "name": "Deploy",
                "title": "Ship the same artifact",
                "points": [
                    "Dev, stage, then production. Same image, different config.",
                    "Approval sits on the production stage, not in a chat thread.",
                    "Health checks decide if the new tasks may take traffic.",
                ],
                "tools": ["Kubernetes", "Helm"],
            },
            {
                "name": "Rollback",
                "title": "The previous version still starts",
                "points": [
                    "Keep the last good image.",
                    "Practice the rollback on purpose, not during the incident.",
                    "Write down what the pipeline failed to catch.",
                ],
                "tools": ["Jenkins", "Registry"],
            },
        ],
        "post": """A deploy that starts on someone's laptop will fail the day that person is offline.

The reliable version is boring, and that is the point. A commit enters Git. Jenkins does the rest. The same artifact moves through dev, stage, and production. If production misbehaves, the previous image still starts.

Here is the roadmap, in 5 stages.

1. Commit
The Jenkinsfile is in the repo. A webhook starts the job. Main does not move without a review.

2. Build
Dependencies come from a lock file. Docker builds the image. The tag is the commit, so you can point at the exact bits later.

3. Verify
Tests run in the pipeline, not after the release. A security scan can fail the job. A red stage does not continue.

4. Deploy
One image, three environments, config kept apart from the build. Production has an approval gate and a health check before it takes traffic.

5. Rollback
Keep the last good image. Run the rollback when nothing is on fire, so the steps are real. Then add the check the pipeline missed.

At SproutsAI this shape cut deployment time by 80% and supports 10+ production releases a day, with tests, scanning, and a rollback on the pipeline. A personal Jenkins project drives 20+ repos from commit to a Kubernetes deploy on Azure.

If the team cannot draw the path from commit to rollback, the YAML is ahead of them."""
        + FOOTER
        + "\n\n#CICD #Jenkins #DevOps\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "kubernetes-to-service",
        "keywords": ["kubernetes", "k8s", "pod", "helm"],
        "category": "kubernetes",
        "title": "HOW KUBERNETES\nRUNS A SERVICE",
        "stages": [
            {
                "name": "Image",
                "title": "A container is the unit you built",
                "points": [
                    "The image holds the app, the libraries, and the start command.",
                    "One process per container unless two must share a pod.",
                    "The registry is the source of truth, not a folder on a VM.",
                ],
                "tools": ["Docker", "ACR"],
            },
            {
                "name": "Pod",
                "title": "Kubernetes schedules pods",
                "points": [
                    "A pod is the smallest thing the cluster runs.",
                    "Containers in one pod share the network and can share a disk.",
                    "A sidecar belongs there only if it serves that one process.",
                ],
                "tools": ["Kubernetes"],
            },
            {
                "name": "Deploy",
                "title": "Ask for a count, not a server",
                "points": [
                    "A Deployment keeps the desired number of pods.",
                    "A rolling update replaces them one step at a time.",
                    "Readiness decides when a pod may receive traffic.",
                ],
                "tools": ["Deployment", "Probes"],
            },
            {
                "name": "Expose",
                "title": "Give the pods one address",
                "points": [
                    "A Service load-balances across ready pods.",
                    "Ingress or a cloud load balancer is the front door.",
                    "DNS points at that door, not at a single pod IP.",
                ],
                "tools": ["Service", "Ingress", "NGINX"],
            },
            {
                "name": "Operate",
                "title": "Scale, heal, and watch",
                "points": [
                    "Autoscale on a real signal, not on hope.",
                    "A failed pod is replaced. That is not a root-cause report.",
                    "Metrics and logs tell you why it was replaced.",
                ],
                "tools": ["HPA", "Prometheus", "Grafana"],
            },
        ],
        "post": """Kubernetes does not replace a careful design. It replaces the hand work of starting the next copy.

A container is the box you built. A pod is where that box runs. A Deployment keeps the count. A Service gives the ready pods one address. The cluster will restart a dead pod. It will not explain the bug. That part is still yours.

Here is the roadmap, in 5 stages.

1. Image
Docker packs the app and the start command. Tag it with the commit and store it in a registry you can scan.

2. Pod
This is the smallest thing Kubernetes runs. Put two containers in one pod only when they must share localhost or a volume. A log sidecar qualifies. A second product does not.

3. Deploy
Tell the cluster how many pods you want, how to roll them, and when a pod is ready for traffic. A readiness probe is the difference between a restart and an outage you caused yourself.

4. Expose
A Service balances across ready pods. Ingress, a cloud load balancer, or NGINX is the door users hit. Point DNS at the door.

5. Operate
Autoscale on CPU, latency, or queue depth. Alert on the symptom a person can act on. Pair the cluster with Prometheus and Grafana, or you will learn about failures from the user.

I have containerized 20+ production services and deployed Docker images onto Kubernetes across dev, stage, and production. The cluster is the scheduler. The roadmap above is the part you still have to mean."""
        + FOOTER
        + "\n\n#Kubernetes #Docker #DevOps\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "terraform-plan-to-apply",
        "keywords": ["terraform", "iac", "infrastructure"],
        "category": "terraform",
        "title": "HOW TERRAFORM\nCHANGES REACH CLOUD",
        "stages": [
            {
                "name": "Write",
                "title": "Describe the end state",
                "points": [
                    "Resources live in Git, next to a short README.",
                    "Names, tags, and owners are part of the code.",
                    "Secrets stay in a vault. They do not sit in the repo.",
                ],
                "tools": ["Terraform", "Git"],
            },
            {
                "name": "Plan",
                "title": "Read the diff before you apply",
                "points": [
                    "plan shows create, change, and destroy.",
                    "A destroy line stops the review.",
                    "If you cannot explain the plan, you do not apply it.",
                ],
                "tools": ["terraform plan"],
            },
            {
                "name": "Review",
                "title": "A second person sees the plan",
                "points": [
                    "The plan output is the pull request.",
                    "State is remote and locked.",
                    "One workspace per environment.",
                ],
                "tools": ["Remote state", "PR"],
            },
            {
                "name": "Apply",
                "title": "The pipeline applies, not a laptop",
                "points": [
                    "CI runs apply after the review.",
                    "The same version of the code created the plan.",
                    "A failed apply is read before anyone retries it.",
                ],
                "tools": ["CI", "terraform apply"],
            },
            {
                "name": "Drift",
                "title": "The console is not the source of truth",
                "points": [
                    "A click in the console becomes drift by tomorrow.",
                    "Schedule a plan that is expected to be empty.",
                    "Fix drift in code, then plan again.",
                ],
                "tools": ["Terraform", "Tags"],
            },
        ],
        "post": """The cloud console is a convenient way to make a change you cannot repeat.

Terraform is the opposite habit. You describe the end state. plan tells you what will be created, changed, and destroyed. A person reads that diff. Then apply runs from CI, against remote state, with a lock.

Here is the roadmap, in 5 stages.

1. Write
Resources, names, and tags live in Git. Secrets live in a vault. The README says which account this folder owns.

2. Plan
Read every destroy line. If the plan surprises you, the code is not ready.

3. Review
The plan is the pull request. State is remote. Dev, stage, and production do not share one state file.

4. Apply
The pipeline applies the plan you reviewed, not a newer plan nobody saw. If apply fails, read it before you run it again.

5. Drift
A change made in the console will show up as drift. The fix goes back into code. A clean scheduled plan is the proof.

I keep multi-cloud resources on GCP, Azure, and AWS in version control, including a move of application infrastructure from Azure to GCP. The tool is Terraform and the related automation. The discipline is the plan review."""
        + FOOTER
        + "\n\n#Terraform #InfrastructureAsCode #Cloud\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "request-path",
        "keywords": ["network", "traffic", "vpc", "dns", "load balancer"],
        "category": "network",
        "title": "HOW A REQUEST\nREACHES YOUR SERVICE",
        "stages": [
            {
                "name": "DNS",
                "title": "The name has to resolve",
                "points": [
                    "The public name points at the load balancer, not a pod.",
                    "TTL is short during a cutover and calm after it.",
                    "A health check belongs on the record when the provider allows it.",
                ],
                "tools": ["Route 53", "DNS"],
            },
            {
                "name": "Edge",
                "title": "Terminate and balance",
                "points": [
                    "TLS ends at a place you control.",
                    "The load balancer only sends traffic to healthy targets.",
                    "NGINX can route by path when one domain serves several apps.",
                ],
                "tools": ["ALB", "NLB", "NGINX"],
            },
            {
                "name": "Network",
                "title": "Put the service in a real network",
                "points": [
                    "VPC, subnets, and routes decide who can talk.",
                    "Private subnets for data. Public subnets for the door.",
                    "A security group is a allow-list, written down.",
                ],
                "tools": ["VPC", "Subnets", "SG"],
            },
            {
                "name": "Service",
                "title": "The app sees a local port",
                "points": [
                    "The process listens on the port the probe expects.",
                    "Upstream timeouts are shorter than the user's patience.",
                    "A 200 from the app is not a 200 from the dependency.",
                ],
                "tools": ["Kubernetes", "Health checks"],
            },
            {
                "name": "Proof",
                "title": "Trace one request",
                "points": [
                    "Pick one request id and follow it.",
                    "Latency at the edge, at the service, and at the database.",
                    "If you cannot draw the path, you cannot debug the outage.",
                ],
                "tools": ["Grafana", "ELK", "Traces"],
            },
        ],
        "post": """When a service is slow, the argument usually starts in the wrong layer.

Someone blames the model, or Kubernetes, or the database. The request still had to resolve a name, pass a load balancer, cross a subnet, satisfy a security group, and reach a process that is actually ready.

Here is the path, in 5 stages.

1. DNS
The name points at the load balancer. During a cutover the TTL is short. After the cutover you let it rest.

2. Edge
TLS terminates where you can renew it. The balancer sends traffic only to healthy targets. NGINX is enough when you need path routing in front of a few services.

3. Network
VPC and subnets are the map. Data stays private. The door stays small. Security groups name the ports you meant to open, and no others.

4. Service
The process listens on the port the probe uses. Timeouts are explicit. A healthy app in front of a dead database is still a failed request.

5. Proof
Take one request id. Find it at the edge, in the app log, and at the dependency. Latency belongs on a dashboard before it belongs in a war room.

On AWS that map is Route 53, a load balancer, VPC, and security groups. In front of the apps I have used NGINX. The picture is the same on Azure and GCP. The product names change. The path does not."""
        + FOOTER
        + "\n\n#CloudNetworking #AWS #DevOps\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "observability-loop",
        "keywords": ["observability", "prometheus", "grafana", "sre", "monitoring"],
        "category": "sre",
        "title": "HOW YOU NOTICE\nA FAILURE IN TIME",
        "stages": [
            {
                "name": "Metrics",
                "title": "A number with a job",
                "points": [
                    "Latency, error rate, saturation, and traffic.",
                    "Scrape the service. Do not wait for a user to graph it.",
                    "A dashboard matches the question an on-call will ask.",
                ],
                "tools": ["Prometheus", "Grafana"],
            },
            {
                "name": "Logs",
                "title": "One line you can search",
                "points": [
                    "A request id on every line that belongs to that request.",
                    "Structured fields beat a paragraph.",
                    "Retention has a cost. Keep what you will query.",
                ],
                "tools": ["ELK", "Loki"],
            },
            {
                "name": "Traces",
                "title": "Where the time went",
                "points": [
                    "A trace crosses the gateway, the app, and the dependency.",
                    "Use it when the metric says slow and the log says nothing.",
                    "Sample enough to trust the picture.",
                ],
                "tools": ["OpenTelemetry"],
            },
            {
                "name": "Alerts",
                "title": "Page a person who can act",
                "points": [
                    "Alert on symptoms, with the first dashboard linked.",
                    "A warning that fires all week will be muted.",
                    "Route the page to the team that owns the service.",
                ],
                "tools": ["Alertmanager"],
            },
            {
                "name": "Review",
                "title": "Close the loop",
                "points": [
                    "Every page ends with what the alert missed.",
                    "Tune the threshold or fix the system. Do one of those.",
                    "The next dashboard should make this page shorter.",
                ],
                "tools": ["On-call notes"],
            },
        ],
        "post": """An alert with no next step is noise. A dashboard nobody opens during an incident is decoration.

Observability is the loop: a metric says something changed, a log or a trace says where, a person does one thing, and the alert gets sharper because of what you learned.

Here is the roadmap, in 5 stages.

1. Metrics
Latency, errors, saturation, and traffic. Prometheus scrapes them. Grafana shows the question the on-call will actually ask.

2. Logs
Put a request id on the lines that belong together. Structure the fields. Keep the retention you can afford to search.

3. Traces
When the graph says slow and the log is quiet, follow one request across the gateway, the service, and the dependency.

4. Alerts
Page on a symptom. Link the first dashboard in the alert. If it fires every day and nobody acts, the threshold is wrong or the alert should not exist.

5. Review
After the page, write the gap. Either the system gets a fix or the alert gets a tighter rule.

I have run this with Prometheus, Grafana, and the ELK stack, and routed alerts through Alertmanager. That work reduced MTTR by 60%. The tools matter less than the loop. A graph that does not change the next action is a poster."""
        + FOOTER
        + "\n\n#Observability #SRE #Prometheus\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "blue-green-release",
        "keywords": ["release", "blue", "green", "deploy", "migration"],
        "category": "devops",
        "title": "HOW A RELEASE\nAVOIDS A BIG BANG",
        "stages": [
            {
                "name": "Artifact",
                "title": "Build once",
                "points": [
                    "The image that passed CI is the image you promote.",
                    "Config and secrets are injected, not baked in for one environment only.",
                    "You can name the commit from the running task.",
                ],
                "tools": ["Docker", "CI"],
            },
            {
                "name": "Stage",
                "title": "Stand up the next color",
                "points": [
                    "Blue keeps serving. Green comes up beside it.",
                    "Migrations are expandable. Old and new can run together.",
                    "Smoke tests hit green before any user does.",
                ],
                "tools": ["Blue-green"],
            },
            {
                "name": "Shift",
                "title": "Move a slice of traffic",
                "points": [
                    "Start with an internal user or a small percent.",
                    "Watch errors and latency, not just the deploy log.",
                    "The load balancer is the switch.",
                ],
                "tools": ["ALB", "Ingress"],
            },
            {
                "name": "Decide",
                "title": "Stay or go back",
                "points": [
                    "A written line says what 'bad' means.",
                    "Rollback is a switch, not a rebuild.",
                    "The previous color stays warm until you trust the new one.",
                ],
                "tools": ["Health checks"],
            },
            {
                "name": "Finish",
                "title": "Retire the old color",
                "points": [
                    "Drain connections. Then remove the old tasks.",
                    "Note the migration step that cannot be reversed.",
                    "The next release uses the same switch.",
                ],
                "tools": ["Runbook"],
            },
        ],
        "post": """A release plan that only works if nothing goes wrong is not a release plan.

Blue-green means the current version keeps serving while the next one starts. You test the new color. You move a slice of traffic. You keep the old color warm until the numbers say you can turn it off.

Here is the roadmap, in 5 stages.

1. Artifact
Promote the image CI already built. Do not rebuild it on the production laptop and hope it matches.

2. Stage
Green comes up beside blue. Database changes have to tolerate both versions for the length of the cutover.

3. Shift
Internal traffic first, or a small share of users. Watch the error rate and the latency. The deploy log only tells you that the process started.

4. Decide
Agree the failure line before you start. If you cross it, the switch goes back. Rollback is not a new project.

5. Finish
Drain, then remove the old color. Write down the one step you cannot undo.

I used this pattern for a zero-downtime move from Azure to GCP, including 500GB+ of databases and the container workloads in front of them. The same idea sits on ordinary app releases. Two colors. One switch. A number that tells you which color deserves the traffic."""
        + FOOTER
        + "\n\n#DevOps #SRE #Cloud\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
    {
        "id": "mlops-after-the-demo",
        "keywords": ["ml", "mlops", "model", "machine learning"],
        "category": "ml",
        "title": "HOW A MODEL\nSTAYS USEFUL",
        "stages": [
            {
                "name": "Question",
                "title": "Decide what the model is for",
                "points": [
                    "One decision the model should improve.",
                    "The label, or the preference, you will score later.",
                    "A baseline that is allowed to be simple.",
                ],
                "tools": ["KPI", "Baseline"],
            },
            {
                "name": "Data",
                "title": "The examples are the product",
                "points": [
                    "Train and test do not peek at each other.",
                    "Record where each row came from.",
                    "A prompt pipeline needs the same care as a training set.",
                ],
                "tools": ["Versioned sets"],
            },
            {
                "name": "Ship",
                "title": "The model is a service",
                "points": [
                    "Package it. Put it behind the same pipeline as the app.",
                    "A fallback exists when the model times out.",
                    "Cost per call is a metric, not a surprise.",
                ],
                "tools": ["Docker", "CI", "Gateway"],
            },
            {
                "name": "Score",
                "title": "Offline score, then online score",
                "points": [
                    "A golden set runs before the deploy.",
                    "Production logs the input, the output, and the user correction.",
                    "Hallucinations and drift are different failures. Name which one you saw.",
                ],
                "tools": ["Eval set", "Traces"],
            },
            {
                "name": "Tend",
                "title": "Promote the next version on purpose",
                "points": [
                    "A new prompt or a new model is a release.",
                    "Compare it with the current version on the same questions.",
                    "Roll forward only when the score holds.",
                ],
                "tools": ["Flags", "Grafana"],
            },
        ],
        "post": """A model that impressed the room is not a model you can leave running.

Machine learning in production has the same shape as any other service, plus one extra duty: you have to notice when the answers get worse while the process is still up.

Here is the roadmap, in 5 stages.

1. Question
Write the decision the model is supposed to improve, and the simple baseline it has to beat.

2. Data
Keep training rows and later evaluation rows apart. For an LLM product, the prompt pipeline and the retrieved context are part of that data. Treat a prompt change like a code change.

3. Ship
The model or the API call sits in a container, behind CI, with a timeout and a fallback. Cost per request belongs on the dashboard.

4. Score
Run a fixed set of questions before you deploy. In production, keep the input, the output, and the correction. A fluent wrong answer is a product bug.

5. Tend
The next prompt, the next model, and the next index are releases. Compare them on the same questions. Move traffic when the score holds.

I have built that first mile on SensAI: an LLM career coach with React and Node.js, streaming responses, and prompt pipelines aimed at a consistent answer. The rest of the roadmap is the same production work I do for any service. Package it, gate it, watch it, and keep a way back."""
        + FOOTER
        + "\n\n#MLOps #AIEngineering #DevOps\n",
        "comment": "Portfolio: https://sandeepkalyan-portfolio.vercel.app",
    },
]
