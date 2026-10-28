import json
import re
from pathlib import Path

from careermail.career.latex_compiler import (
    compile_pdf,
    load_master_profile,
    render_latex,
)
from careermail.core import paths
from careermail.core.observability import record_event


def detect_best_track(jd_text: str, available_tracks: dict) -> str:
    """Analyze job description keywords to pick the best matching role track."""
    low_jd = jd_text.lower()
    scores = {}

    for track_id, track_data in available_tracks.items():
        score = 0
        title = track_data.get("display_title", "").lower()
        # Check title overlap
        for word in title.split():
            if len(word) > 2 and word in low_jd:
                score += 3

        # Check skills overlap
        skills_map = track_data.get("skills_categories", {})
        for cat_skills in skills_map.values():
            for skill in re.split(r"[,/|()]", cat_skills):
                s = skill.strip().lower()
                if s and len(s) > 1 and s in low_jd:
                    score += 1

        scores[track_id] = score

    # Return track with highest score, fallback to first track
    if not scores or max(scores.values()) == 0:
        return next(iter(available_tracks.keys()))
    return max(scores, key=scores.get)


def tailor_cv(
    jd_text: str,
    target_track: str | None = None,
    company_name: str = "Company",
    template_name: str = "classic",
) -> tuple[Path, str, str]:
    """
    Select best track based on JD (or user override), render LaTeX, and compile to PDF.
    Returns: (output_pdf_path, selected_track_id, track_display_title)
    """
    profile = load_master_profile()
    tracks = profile.get("tracks", {})
    if not tracks:
        raise ValueError("Profile không chứa danh sách tracks nào.")

    # 1. Determine Track
    if target_track and target_track in tracks:
        chosen_track = target_track
    else:
        chosen_track = detect_best_track(jd_text, tracks)

    track_info = tracks.get(chosen_track, {})
    display_title = track_info.get("display_title", chosen_track)

    record_event(
        "INFO",
        "career",
        f"Lựa chọn track '{chosen_track}' ({display_title}) cho công ty {company_name}",
    )

    # 2. Render LaTeX
    tex_content = render_latex(profile, track_id=chosen_track, template_name=template_name)

    # 3. Compile to PDF
    safe_company = re.sub(r"[^\w\-]", "_", company_name.strip()) or "Tailored"
    personal = profile.get("personal_info", {})
    safe_name = re.sub(r"[^\w\-]", "", personal.get("name", "Applicant").replace(" ", ""))
    pdf_filename = f"CV_{safe_name}_{safe_company}.pdf"

    output_dir = paths.data_dir() / "generated_cvs"
    output_pdf_path = output_dir / pdf_filename

    final_pdf_path = compile_pdf(
        tex_content=tex_content,
        output_pdf_path=output_pdf_path,
        template_name=template_name,
    )

    return final_pdf_path, chosen_track, display_title
