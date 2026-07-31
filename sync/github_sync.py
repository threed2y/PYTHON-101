"""
Handles all writes to the target GitHub repo:
- committing a solved problem's source file under solutions/<difficulty>/<id>-<slug>/
- regenerating the root README.md with an up-to-date stats table
"""
import logging
from typing import Any

from github import Github, GithubException

logger = logging.getLogger("leetcode_sync.github_sync")

DIFFICULTY_EMOJI = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}


class GitHubSync:
    def __init__(self, token: str, repo_full_name: str, branch: str,
                 author_name: str, author_email: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_full_name)
        self.branch = branch
        self.author_name = author_name
        self.author_email = author_email

    def _commit_file(self, path: str, content: str, message: str) -> None:
        try:
            existing = self.repo.get_contents(path, ref=self.branch)
            self.repo.update_file(
                path=path,
                message=message,
                content=content,
                sha=existing.sha,
                branch=self.branch,
            )
            logger.info("Updated %s", path)
        except GithubException as exc:
            if exc.status == 404:
                self.repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=self.branch,
                )
                logger.info("Created %s", path)
            else:
                raise

    def sync_solution(self, submission: dict[str, Any], details: dict[str, Any],
                       question: dict[str, Any], extension: str) -> str:
        """Commits one solved problem's code file. Returns the repo path used."""
        problem_id = question.get("questionFrontendId", "0")
        slug = submission["titleSlug"]
        difficulty = question.get("difficulty", "Unknown")
        title = submission["title"]

        folder = f"solutions/{difficulty.lower()}/{problem_id}-{slug}"
        code_path = f"{folder}/solution.{extension}"

        tags = ", ".join(t["name"] for t in question.get("topicTags", []))
        header = self._comment_header(extension, title, problem_id, slug, difficulty, tags, details)
        content = header + (details.get("code") or "")

        message = f"Sync: {problem_id}. {title} ({difficulty})"
        self._commit_file(code_path, content, message)
        return folder

    @staticmethod
    def _comment_header(ext: str, title: str, problem_id: str, slug: str,
                         difficulty: str, tags: str, details: dict[str, Any]) -> str:
        lines = [
            f"Problem: {problem_id}. {title}",
            f"Difficulty: {difficulty}",
            f"Link: https://leetcode.com/problems/{slug}/",
            f"Tags: {tags}" if tags else None,
            f"Runtime: {details.get('runtimeDisplay', 'n/a')} | Memory: {details.get('memoryDisplay', 'n/a')}",
        ]
        lines = [l for l in lines if l]
        # Use a comment style that's valid in most languages; SQL/shell get '--'/'#'.
        if ext in ("py", "sh"):
            wrapped = "\n".join(f"# {l}" for l in lines)
        elif ext == "sql":
            wrapped = "\n".join(f"-- {l}" for l in lines)
        else:
            wrapped = "/*\n" + "\n".join(lines) + "\n*/"
        return wrapped + "\n\n"

    def update_readme(self, synced: dict[str, Any]) -> None:
        total = len(synced)
        by_difficulty = {"Easy": 0, "Medium": 0, "Hard": 0}
        rows = []
        for _, rec in sorted(synced.items(), key=lambda kv: int(kv[1].get("problem_id", 0))):
            diff = rec.get("difficulty", "Unknown")
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
            rows.append(
                f"| {rec.get('problem_id')} | [{rec.get('title')}]"
                f"(https://leetcode.com/problems/{rec.get('slug')}/) "
                f"| {DIFFICULTY_EMOJI.get(diff, '')} {diff} | `{rec.get('lang')}` |"
            )

        content = [
            "# LeetCode Solutions",
            "",
            "_Automatically synced from LeetCode via "
            "[leetcode-github-sync](.)._",
            "",
            f"**Total solved:** {total} "
            f"(🟢 {by_difficulty.get('Easy', 0)} Easy · "
            f"🟡 {by_difficulty.get('Medium', 0)} Medium · "
            f"🔴 {by_difficulty.get('Hard', 0)} Hard)",
            "",
            "| # | Title | Difficulty | Lang |",
            "|---|-------|------------|------|",
            *rows,
            "",
        ]
        self._commit_file("README.md", "\n".join(content), "Sync: update stats README")
