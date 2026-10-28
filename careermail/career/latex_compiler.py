import json
import os
import shutil
import subprocess
from pathlib import Path

from careermail.core import paths
from careermail.core.observability.errors import CareerError
from careermail.core.observability.events import record_event


def load_master_profile() -> dict:
    """Load master profile JSON from the data directory. Auto-initializes from example if missing."""
    profile_path = paths.data_dir() / "master_profile.json"
    if not profile_path.is_file():
        # Fallback to project root data directory if not in runtime data_dir
        root_data_file = paths.app_root() / "data" / "master_profile.json"
        if root_data_file.is_file():
            profile_path = root_data_file

    if not profile_path.is_file():
        # Check for example template file to auto-initialize
        example_file = paths.app_root() / "master_profile.example.json"
        if example_file.is_file():
            dest = paths.data_dir() / "master_profile.json"
            shutil.copy2(example_file, dest)
            record_event(
                "INFO",
                "career",
                "Chưa có master_profile.json, đã tự động khởi tạo từ master_profile.example.json",
            )
            profile_path = dest
        else:
            raise CareerError(
                "Không tìm thấy file data/master_profile.json.\n"
                "Vui lòng tạo file hồ sơ của bạn theo hướng dẫn chi tiết tại docs/PROFILE_GENERATOR.md."
            )

    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _format_address(personal_info: dict) -> str:
    parts = []
    if personal_info.get("location"):
        parts.append(personal_info["location"])
    if personal_info.get("phone"):
        parts.append(personal_info["phone"])
    if personal_info.get("email"):
        email = personal_info["email"]
        parts.append(f"\\href{{mailto:{email}}}{{{email}}}")
    if personal_info.get("github"):
        gh = personal_info["github"]
        gh_display = gh.replace("https://", "").rstrip("/")
        parts.append(f"\\faGithub\\ \\href{{{gh}}}{{{gh_display}}}")
    if personal_info.get("linkedin"):
        li = personal_info["linkedin"]
        parts.append(f"\\faLinkedin\\ \\href{{{li}}}{{LinkedIn}}")
    return " $\\cdot$ ".join(parts)


def render_latex(profile: dict, track_id: str | None = None, template_name: str = "classic") -> str:
    """Generate .tex string from profile data according to the selected track."""
    template_dir = paths.resource_path("templates", template_name)
    template_file = template_dir / "cv_template.tex"
    if not template_file.is_file():
        raise CareerError(f"Template '{template_name}' không tồn tại tại {template_file}")

    with open(template_file, "r", encoding="utf-8") as f:
        tex_raw = f.read()

    personal = profile.get("personal_info", {})
    name = personal.get("name", "Applicant Name")
    address_line = _format_address(personal)

    # Resolve track
    tracks = profile.get("tracks", {})
    default_track_id = profile.get("default_track")
    if not track_id or track_id not in tracks:
        track_id = default_track_id if default_track_id in tracks else (next(iter(tracks.keys())) if tracks else None)

    track_data = tracks.get(track_id, {}) if track_id else {}

    # Profile Section
    summary = track_data.get("summary") or personal.get("summary", "")
    profile_section = ""
    if summary:
        profile_section = f"""\\begin{{rSection}}{{Profile}}
{summary}
\\end{{rSection}}"""

    # Education Section
    edu = profile.get("education", {})
    edu_section = ""
    if edu:
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        period = edu.get("period", "")
        details = edu.get("details", "")
        edu_section = f"""\\begin{{rSection}}{{Education}}
{{\\bf {degree}}} ({institution}) \\hfill {{{period}}} 
\\\\
{{\\bf Academic Standing:}} {details}
\\end{{rSection}}"""

    # Skills Section
    skills_map = track_data.get("skills_categories") or profile.get("skills_categories", {})
    skills_section = ""
    if skills_map:
        lines = []
        for cat_name, cat_val in skills_map.items():
            lines.append(f"\\textbf{{{cat_name}:}} {cat_val}")
        body = " \\\\\n".join(lines)
        skills_section = f"""\\begin{{rSection}}{{Skills}}
{body}
\\end{{rSection}}"""

    # Experience Section
    exps = profile.get("experiences", [])
    exp_section = ""
    if exps:
        subsections = []
        for exp in exps:
            company = exp.get("company", "")
            period = exp.get("period", "")
            role = exp.get("role", "")
            loc = exp.get("location", "")
            bullets = "\n".join(f"\\item {b}" for b in exp.get("bullet_points", []))
            subsections.append(f"""\\begin{{rSubsection}}{{{company}}}{{{period}}}{{{role}}}{{{loc}}}
{bullets}
\\end{{rSubsection}}""")
        exp_body = "\n\n".join(subsections)
        exp_section = f"""\\begin{{rSection}}{{Experience}}
{exp_body}
\\end{{rSection}}"""

    # Projects Section
    all_projects = {p.get("id"): p for p in profile.get("all_projects", []) if p.get("id")}
    selected_ids = track_data.get("selected_project_ids")
    if selected_ids:
        active_projects = [all_projects[pid] for pid in selected_ids if pid in all_projects]
    else:
        active_projects = list(all_projects.values())

    proj_section = ""
    if active_projects:
        subsections = []
        for proj in active_projects:
            p_name = proj.get("name", "")
            p_period = proj.get("period", "")
            p_role = proj.get("role", "")
            p_github = proj.get("github", "")

            role_line = p_role
            if p_github:
                role_line += f" | \\faGithub\\ \\href{{{p_github}}}{{GitHub}}"

            bullets = "\n".join(f"\\item {b}" for b in proj.get("bullet_points", []))
            subsections.append(f"""\\begin{{rSubsection}}{{{p_name}}}{{{p_period}}}{{{role_line}}}{{}}
{bullets}
\\end{{rSubsection}}""")
        proj_body = "\n\n".join(subsections)
        proj_section = f"""\\begin{{rSection}}{{Projects}}
{proj_body}
\\end{{rSection}}"""

    # Certificate Section
    certs = profile.get("certifications", [])
    cert_section = ""
    if certs:
        cert_text = ", ".join(certs)
        cert_section = f"""\\begin{{rSection}}{{Certificates}} \\itemsep -3pt 
{{\\textbf{{Languages \\& Certs:}}}} {cert_text}
\\end{{rSection}}"""

    # Replace placeholders
    rendered = tex_raw
    replacements = {
        "<<NAME>>": name,
        "<<ADDRESS_LINE>>": address_line,
        "<<PROFILE_SECTION>>": profile_section,
        "<<EDUCATION_SECTION>>": edu_section,
        "<<SKILLS_SECTION>>": skills_section,
        "<<EXPERIENCE_SECTION>>": exp_section,
        "<<PROJECTS_SECTION>>": proj_section,
        "<<CERTIFICATE_SECTION>>": cert_section,
    }
    for tag, val in replacements.items():
        rendered = rendered.replace(tag, val)

    return rendered


def find_latex_compiler() -> tuple[str, list[str]]:
    """Detect available LaTeX compiler (bundled Tectonic, system tectonic, or pdflatex)."""
    # 1. Check bundled tectonic.exe in bin/
    bundled_tectonic = paths.app_root() / "bin" / ("tectonic.exe" if os.name == "nt" else "tectonic")
    if bundled_tectonic.is_file():
        return "tectonic", [str(bundled_tectonic)]

    # 2. Check system tectonic
    system_tectonic = shutil.which("tectonic")
    if system_tectonic:
        return "tectonic", [system_tectonic]

    # 3. Check system pdflatex or xelatex
    for engine in ("xelatex", "pdflatex"):
        found = shutil.which(engine)
        if found:
            return engine, [found, "-interaction=nonstopmode"]

    raise CareerError(
        "Không tìm thấy trình biên dịch LaTeX.\n"
        "Giải pháp nhanh nhất: Tải file 'tectonic.exe' (~30MB) từ "
        "https://github.com/tectonic-typesetting/tectonic/releases và đặt vào thư mục 'bin/' của dự án."
    )


def compile_pdf(
    tex_content: str,
    output_pdf_path: str | Path,
    template_name: str = "classic",
) -> Path:
    """Compile LaTeX source text into a PDF file."""
    out_pdf = Path(output_pdf_path).resolve()
    out_dir = out_pdf.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    build_dir = out_dir / ".tex_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Copy template class files (such as resume.cls) into build directory
    template_dir = paths.resource_path("templates", template_name)
    if template_dir.is_dir():
        for item in template_dir.iterdir():
            if item.suffix in (".cls", ".sty", ".ttf", ".otf"):
                shutil.copy2(item, build_dir / item.name)

    tex_file = build_dir / "resume.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(tex_content)

    compiler_type, cmd = find_latex_compiler()
    try:
        if compiler_type == "tectonic":
            # Tectonic compiles directly to PDF
            full_cmd = cmd + [str(tex_file), "--outdir", str(build_dir)]
            subprocess.run(full_cmd, check=True, capture_output=True, text=True)
            generated_pdf = build_dir / "resume.pdf"
        else:
            # pdflatex / xelatex
            full_cmd = cmd + ["-output-directory", str(build_dir), str(tex_file)]
            subprocess.run(full_cmd, check=True, capture_output=True, text=True)
            generated_pdf = build_dir / "resume.pdf"

        if not generated_pdf.is_file():
            raise CareerError("Biên dịch LaTeX hoàn tất nhưng không tìm thấy file PDF đầu ra.")

        shutil.move(generated_pdf, out_pdf)
        record_event("INFO", "latex", f"Xuất file PDF thành công: {out_pdf.name}")
        return out_pdf

    except subprocess.CalledProcessError as exc:
        record_event("ERROR", "latex", f"Lỗi biên dịch LaTeX: {exc.stderr or exc.stdout}", exc=exc)
        raise CareerError(f"Lỗi khi biên dịch LaTeX sang PDF:\n{(exc.stderr or exc.stdout or str(exc))[:500]}")
    finally:
        # Clean build directory
        shutil.rmtree(build_dir, ignore_errors=True)
