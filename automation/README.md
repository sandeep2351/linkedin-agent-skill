# AIOrbit Lab LinkedIn runner

Eleven skills decide what good LinkedIn writing looks like. This folder runs them.

## Brief

The default run does not read a voice file and does not make a short video. It builds one roadmap GIF and the caption under it. A new topic is due every 2 days: AI, DevOps, ML, cloud, Kubernetes, Terraform, network traffic, and observability. `--profile-kit` rewrites the headline, about, and experience from the resume.

| You ask for | You get |
| --- | --- |
| A post | `post.gif` plus `post.txt`, ready to upload |
| The week | Tuesday proof, Thursday opinion, Friday teach, plus who to engage with |
| A comment | Two comments of different types on someone else's post |
| Your replies | Comments under your post sorted, then the replies worth sending |
| Your profile | A score out of 100 and rewrites for the weak sections |
| A carousel | Slide copy and a PDF |
| A long asset | Up to four standalone posts from one transcript |
| A DM | An invite note under 200 characters, a first message, and two follow-ups |
| The inbox | Lead, recruiter, peer, ask, and spam, with the tell named |
| An audit | Your posts ranked by engagement rate, not by impressions |
| A cleanup | Invisible characters, slop words, and a five-check score removed or shown |

You paste every draft. The runner has no LinkedIn login. A personal profile has no open posting API, and automating the site breaks LinkedIn's User Agreement.

## Detailed

### Post (`python3 -m automation.run`)

Reads the voice profile and `skills/li-post/hooks.json`. Picks an unused topic from `automation/topics.json`, or uses the idea you pass with `--concept`. Writes three hook options from the 21 formulas, drafts the post on the strongest one, then runs `humanize.py` and `detect.py`.

The shape it aims for: line 1 under 140 characters, line 2 pays that line off, short paragraphs, 900 to 1,300 characters, at most three hashtags, no link in the body. A personal number that is not in the voice profile stays as `{{your number}}`.

Stages, in order: `pick-topic`, `hooks`, `draft`, `humanize`, `save`, `mark-used`. A `--concept` run skips the bank. `--demo` skips the model and humanizes a local sample.

Saved next to the post: `hooks.txt`, `detect.txt`, `receipt.txt`, `meta.json`. The hook and the first line are appended to `automation/state/log.md`.

### Week (`--week`)

Three posts, not seven. Tuesday is proof, Thursday is an opinion, Friday teaches one mechanism. Monday and Wednesday are for 20 minutes of comments. Saturday is empty. Sunday's story slot stays empty until you add a real scene to the proof list in the voice profile. The runner will not invent a client story to fill it.

Times are local, written for an India audience. The plan says so, and it also says the first line matters more than the clock.

Names come only from `automation/engage.txt`, one person per line: `reach | Name | why`. The working mix is 5 reach, 3 peers, 2 buyers. Missing names are left missing.

`--week --draft` then writes the three posts into `automation/output/week-YYYY-MM-DD/`.

### Comment (`--comment --file post.txt`)

Reads the other person's post from the file. Picks two of the nine comment types and writes both. It will not open with "Great post", "Love this", "So true", or "This resonates". Both go through the humanizer. You paste the one you mean.

### Replies (`--reply --file comments.txt`)

Separate comments with a line of `---`. Sorts them into lead, substance, peer, support, and noise. Lead and substance get a real answer. Support gets a few words. Noise gets nothing. The answer stays in the thread.

### Profile (`--profile --file profile.txt`)

Scores twelve sections against `skills/li-profile/rubric.json`. The points are computed in `profile_score.py` from the paste. A section you leave out scores zero. With the Bedrock key set, sections under half their points get a rewrite of the headline, about, and current role. Employers and numbers are not invented.

Label the paste if you can:

```
Headline: ...
About: ...
Role: ...
Featured: ...
Banner: ...
Photo: ...
Experience: ...
Skills: ...
Recommendations: ...
Activity: ...
Contact: ...
```

### Carousel (`--carousel --concept "How a Jenkins pipeline works"`)

Cover, why it matters, one idea per slide, a recap, and one action. The cover is the hook. The feed still needs two or three lines, saved above the slides. Chrome writes `slides.pdf` at 1080 by 1350 when Chrome is installed. You upload the PDF.

### Repurpose (`--repurpose --file transcript.txt`)

Reads the whole source, counts claims, numbers, stories, mechanisms, mistakes, and quotable lines, then writes up to four posts that each stand alone. A number in a post has to be in the source. A thin source comes back with fewer than four posts and a note that says so.

### DM (`--dm --who "..." --reason "..." --want "..."`)

The invite is one specific reference, one line on who you are, and no ask. The character count is printed and must be 200 or under. Then the first message, then two follow-ups. The reason has to be real. "They fit my niche" is not a reason, and the command refuses to run without one.

### Inbox (`--inbox --file messages.txt`)

Separate messages with `---`. Sorts into lead, recruiter, peer, ask, and spam, and names the phrase that decided it. Spam gets no reply. With the Bedrock key, the sort is checked and the replies worth sending are drafted. Without the key, the keyword sort still runs.

### Audit (`--audit --file analytics.csv`)

You export the CSV from LinkedIn. The runner computes engagement rate `(reactions + comments + reposts) / impressions`, comment ratio `comments / reactions`, and reach multiple `impressions / followers` when that column exists. It ranks by engagement rate. Impressions alone do not win. Fewer than three scored rows is reported as a hint, not a pattern.

### Humanizer (`--human --file draft.txt`)

This one is local. `skills/li-human/humanize.py` removes invisible characters, fixes typography, and swaps the slop lexicon. `detect.py` scores burstiness, specificity, slop density, fingerprint, and voice from 0 to 100. Higher is more human. The verdict weights the average at 60% and the weakest check at 40%. PASS needs 70 overall and no check under 55. Structural tells are flagged for you to rewrite. The scripts do not call a detector API.

### Voice

`automation/voice.md` is the AIOrbit Lab profile: P. Sandeep Kalyan, writing for engineering students and early-career developers, on AI, machine learning, MLOps, DevOps, SRE, and cloud architecture. The proof list is empty. Fill it before you want a personal number in a post. If `~/.claude/linkedin/voice.md` exists, that file wins.

### Schedule

```bash
python3 -m automation.run --schedule
python3 -m automation.run --unschedule
```

Tuesday 8:15, Thursday 8:00, and Friday 8:30, on the Mac clock. Each run writes the next post to `automation/output/`. The Mac has to be on. LinkedIn is not opened.

## Setup

```bash
cd /Users/sandeepsmac/Documents/automations/linkedin-agent-skill
python3 -m automation.run --check
python3 -m automation.run --demo
```

A model draft needs `AWS_BEARER_TOKEN_BEDROCK` in `automation/.env`. If that file is absent, the runner uses the key already stored for the YouTube automation. Copy `automation/.env.example` when you want a separate key.

The command list is in `automation/COMMANDS.md`.
