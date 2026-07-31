"""
Handles all writes to the target GitHub repo:
- committing a solved problem's source file + a companion README under
  solutions/<difficulty>/<zero-padded-id>-<slug>/
- regenerating the root README.md with an up-to-date stats table
"""
import logging
from typing import Any

from github import Github, GithubException

logger = logging.getLogger("leetcode_sync.github_sync")

DIFFICULTY_EMOJI = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}


def _pad_id(problem_id: str) -> str:
    """Zero-pads to 4 digits so folders sort correctly (0001, 0002, ... 0056,
    not 1, 10, 100, 2, ...)."""
    try:
        return f"{int(problem_id):04d}"
    except (TypeError, ValueError):
        return str(problem_id)


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
        """Commits one solved problem's code file + companion README. Returns the folder path."""
        raw_id = question.get("questionFrontendId", "0")
        padded_id = _pad_id(raw_id)
        slug = submission["titleSlug"]
        difficulty = question.get("difficulty", "Unknown")
        title = submission["title"]
        tags = [t["name"] for t in question.get("topicTags", [])]

        folder = f"solutions/{difficulty.lower()}/{padded_id}-{slug}"
        code_path = f"{folder}/solution.{extension}"
        readme_path = f"{folder}/README.md"

        # Code file: just enough to link back, so the header stays valid
        # syntax in every language without needing per-language field lists.
        header = self._comment_header(extension, slug)
        content = header + (details.get("code") or "")

        message = f"Sync: {raw_id}. {title} ({difficulty})"
        self._commit_file(code_path, content, message)
        self._commit_file(
            readme_path,
            self._problem_readme(raw_id, title, slug, difficulty, tags, details, submission["lang"]),
            message,
        )
        return folder

    @staticmethod
    def _comment_header(ext: str, slug: str) -> str:
        link = f"https://leetcode.com/problems/{slug}/"
        if ext in ("py", "sh"):
            wrapped = f"# {link}"
        elif ext == "sql":
            wrapped = f"-- {link}"
        else:
            wrapped = f"// {link}"
        return wrapped + "\n\n"

    @staticmethod
    def _problem_readme(problem_id: str, title: str, slug: str, difficulty: str,
                         tags: list[str], details: dict[str, Any], lang: str) -> str:
        emoji = DIFFICULTY_EMOJI.get(difficulty, "")
        lines = [
            f"# {problem_id}. {title}",
            "",
            f"{emoji} **{difficulty}** &nbsp;·&nbsp; "
            f"[View on LeetCode](https://leetcode.com/problems/{slug}/)",
            "",
        ]
        if tags:
            lines += [f"**Tags:** {', '.join(tags)}", ""]
        lines += [
            f"**Language:** `{lang}` &nbsp;·&nbsp; "
            f"**Runtime:** {details.get('runtimeDisplay', 'n/a')} &nbsp;·&nbsp; "
            f"**Memory:** {details.get('memoryDisplay', 'n/a')}",
            "",
        ]
        return "\n".join(lines)

    def update_readme(self, synced: dict[str, Any]) -> None:
        total = len(synced)
        by_difficulty = {"Easy": 0, "Medium": 0, "Hard": 0}
        rows = []
        for _, rec in sorted(synced.items(), key=lambda kv: int(kv[1].get("problem_id", 0))):
            diff = rec.get("difficulty", "Unknown")
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
            padded = _pad_id(rec.get("problem_id", "0"))
            slug = rec.get("slug")
            folder_link = f"solutions/{diff.lower()}/{padded}-{slug}"
            rows.append(
                f"| {rec.get('problem_id')} | [{rec.get('title')}]({folder_link}) "
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