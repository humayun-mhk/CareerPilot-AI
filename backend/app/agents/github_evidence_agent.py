from ..utils.github_scanner import scan_github_evidence


def _merge_github_text(report: dict) -> str:
    lines = []
    for project in report.get("projects", []):
        skills = ", ".join(project.get("detected_skills", []))
        lines.append(
            f"{project.get('repo_name', '')}: {project.get('project_type', '')}; "
            f"skills: {skills}; evidence: {project.get('readme_summary', '')}"
        )
    return "\n".join(lines)


def run_github_evidence_agent(state: dict) -> dict:
    github_input = state.get("github_url") or state.get("github_input") or ""
    if not github_input:
        return {
            "github_evidence_report": {
                "username": "",
                "repositories_scanned": 0,
                "projects": [],
                "skill_evidence_summary": {},
                "errors": ["No GitHub username or URL was provided."],
            },
            "github_evidence_text": state.get("github_evidence_text", ""),
            "current_step": "github_evidence_agent",
        }
    report = scan_github_evidence(github_input)
    return {
        "github_evidence_report": report,
        "github_evidence_text": _merge_github_text(report),
        "current_step": "github_evidence_agent",
    }
