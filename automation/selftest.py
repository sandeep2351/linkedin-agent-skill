"""Offline checks for the scorer, the week plan, and the sample post."""

import json
import tempfile
import unittest
from pathlib import Path

from automation.audit_math import load_rows, rank_rows
from automation.carousel_pdf import build_slides, render_html
from automation.config import Config
from automation.jobs import run_jobs
from automation.profile_score import score_profile
from automation.tasks import keyword_bucket, load_engage, week_plan
from automation.textutil import limit_hashtags


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "automation" / "examples"


class LinkedInRunnerTest(unittest.TestCase):
    def test_profile_sample_stays_low(self) -> None:
        rows = score_profile((EXAMPLES / "profile-sample.txt").read_text(encoding="utf-8"))
        total = sum(row["points"] for row in rows)
        headline = next(row for row in rows if row["id"] == "headline")
        self.assertLess(total, 50)
        self.assertLessEqual(headline["points"], 3)
        self.assertEqual(sum(row["max"] for row in rows), 100)

    def test_audit_ranks_by_engagement_rate(self) -> None:
        ranked = rank_rows(load_rows(EXAMPLES / "analytics-sample.csv"))
        self.assertIn("Jenkins", ranked[0]["text"])
        # (90 + 20 + 5) / 1200
        self.assertAlmostEqual(ranked[0]["engagement_rate"], 115 / 1200)

    def test_inbox_keywords_name_the_tell(self) -> None:
        bucket, tell = keyword_bucket("Quick question. Book a time at calendly.com/example")
        self.assertEqual(bucket, "SPAM")
        self.assertTrue(tell)

    def test_hashtags_stop_at_three(self) -> None:
        text = limit_hashtags("Hello\n\n#One #Two #Three #Four")
        self.assertNotIn("#Four", text)
        self.assertIn("#Three", text)

    def test_week_plan_does_not_invent_people(self) -> None:
        config = Config()
        config.engage_path = Path(tempfile.gettempdir()) / "missing-engage.txt"
        code = week_plan(config, draft=False)
        self.assertEqual(code, 0)
        plan = config.plan_path.read_text(encoding="utf-8")
        self.assertIn("PROOF", plan)
        self.assertIn("OPINION", plan)
        self.assertIn("TEACH", plan)
        self.assertIn("Names are not invented", plan)
        self.assertIn("STORY skipped", plan)

    def test_engage_file_parses_real_rows_only(self) -> None:
        path = EXAMPLES.parent / "engage.example.txt"
        people = load_engage(path)
        self.assertEqual(people, [])

    def test_carousel_html_has_one_section_per_slide(self) -> None:
        slides = build_slides(
            {
                "cover": {"headline": "Read the plan", "promise": "Then decide."},
                "stake": "A destroy line is the whole risk.",
                "slides": [{"headline": f"Step {index}", "body": "One check."} for index in range(1, 7)],
                "recap": ["Read the plan", "Stop on destroy"],
                "cta": "Run plan before apply.",
            }
        )
        self.assertGreaterEqual(len(slides), 8)
        self.assertLessEqual(len(slides), 12)
        html = render_html(slides)
        self.assertEqual(html.count("<section>"), len(slides))
        self.assertIn("1080px", html)

    def test_year_floor_reads_ranges(self) -> None:
        from automation.sources import year_floor

        self.assertEqual(year_floor("5-9 years of experience"), 5)
        self.assertEqual(year_floor("0-2 years"), 0)
        self.assertEqual(year_floor("6+ years in production"), 6)
        self.assertIsNone(year_floor("entry level, no figure given"))

    def test_senior_roles_are_dropped(self) -> None:
        from automation.openroles import too_senior

        self.assertTrue(too_senior("Senior DevOps Engineer", ""))
        self.assertTrue(too_senior("DevOps Engineer", "We need 5+ years of production ownership."))
        self.assertFalse(too_senior("DevOps Engineer", "1-3 years. Kubernetes and Jenkins."))

    def test_tailored_resume_uses_real_facts_only(self) -> None:
        from automation.config import Config
        from automation.openroles import tailor, write_application

        resume = tailor(
            Config(),
            "Northwind",
            "Site Reliability Engineer",
            "Prometheus Grafana Kubernetes on-call entry level",
        )
        blob = resume["summary"] + "\n" + "\n".join(resume["roles"][0]["bullets"])
        self.assertIn("60%", blob)
        self.assertNotIn("5 years", resume["summary"].lower())
        self.assertEqual(len(resume["roles"]), 3)
        self.assertIn("Full Stack AI Engineer", resume["roles"][1]["title"])
        self.assertIn("Techin IT", resume["roles"][2]["company"])
        self.assertNotEqual(resume["roles"][0]["title"], "Site Reliability Engineer")
        self.assertIn("Prometheus", resume["keywords"])
        record = write_application(Config(), resume)
        pdf_bytes = Path(record["pdf"]).read_bytes()
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertIn("Northwind", Path(record["pdf"]).name)
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertEqual(len(reader.pages), 2)
        self.assertNotIn("Prepared for", text)
        self.assertNotIn("<br", text)
        self.assertIn("ServiceNow", text)
        self.assertIn("DO IT Club", text)

    def test_profile_kit_is_recruiter_copy(self) -> None:
        from automation.profile_kit import HEADLINE, ABOUT, write_profile_kit

        self.assertIn("DevOps Engineer", HEADLINE)
        self.assertIn("Kubernetes", HEADLINE)
        self.assertNotIn("passionate", ABOUT.lower())
        folder = write_profile_kit(ROOT / "automation" / "output" / "profile")
        self.assertTrue((folder / "headline.txt").exists())
        self.assertTrue((folder / "about.txt").exists())

    def test_gif_roadmap_renders(self) -> None:
        import tempfile

        from automation.boards import BOARDS
        from automation.gifboard import write_gif

        folder = Path(tempfile.mkdtemp())
        write_gif(BOARDS[0], folder / "post.gif", folder / "preview.png")
        self.assertGreater((folder / "post.gif").stat().st_size, 1000)
        self.assertIn("Prototype", BOARDS[0]["post"])
        self.assertNotIn("—", BOARDS[0]["post"])

    def test_demo_post_is_saved(self) -> None:
        config = Config()
        code = run_jobs(config, only=None, demo=True, count=1, concept=None)
        self.assertEqual(code, 0)
        folders = list(config.output_dir.glob("A-container-is-a-packed-lunch*"))
        self.assertTrue(folders)
        post = (folders[-1] / "post.txt").read_text(encoding="utf-8")
        meta = json.loads((folders[-1] / "meta.json").read_text(encoding="utf-8"))
        self.assertIn("packed lunch", post)
        self.assertIn(meta["verdict"], {"PASS", "REVIEW", "FLAGGED"})
        self.assertGreater(meta["overall"], 0)


if __name__ == "__main__":
    unittest.main()
