import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def style_table(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)
    
    # Format header row
    header_tr = table.rows[0]._tr.get_or_add_trPr()
    header_tr.append(OxmlElement('w:tblHeader'))
    
    for i, row in enumerate(table.rows):
        is_header = (i == 0)
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        
        for j, cell in enumerate(row.cells):
            set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
            if col_widths and j < len(col_widths):
                cell.width = Inches(col_widths[j])
            
            if is_header:
                set_cell_background(cell, "1E3A8A") # Navy
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for r in p.runs:
                        r.font.name = 'Arial'
                        r.font.size = Pt(9.5)
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for r in p.runs:
                        r.font.name = 'Arial'
                        r.font.size = Pt(8.5)
                        r.font.color.rgb = RGBColor(30, 41, 59)

def add_callout(doc, title, text, border_color="2563EB", bg_color="F8FAFC"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:left w:val="single" w:sz="32" w:space="0" w:color="{border_color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(title)
    run_t.font.name = 'Arial'
    run_t.font.bold = True
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = RGBColor(30, 58, 138)
    
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(0)
    run_txt = p2.add_run(text)
    run_txt.font.name = 'Arial'
    run_txt.font.size = Pt(8.5)
    run_txt.font.color.rgb = RGBColor(51, 65, 85)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 58, 138) # 1E3A8A
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42) # 0F172A
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(71, 85, 105) # 475569
    return p

def add_body_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Arial'
        r_pre.font.size = Pt(9.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = 'Arial'
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def build_schema_document():
    doc = Document()
    
    # Configure 1.0 inch margins
    sec = doc.sections[0]
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)
    
    # Header & Footer
    hdr_p = sec.header.paragraphs[0]
    hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hdr_r = hdr_p.add_run("ProNet Relational Data Schema Specification | v1.0.0")
    hdr_r.font.name = 'Arial'
    hdr_r.font.size = Pt(8.5)
    hdr_r.font.color.rgb = RGBColor(148, 163, 184)
    
    ftr_p = sec.footer.paragraphs[0]
    ftr_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ftr_r = ftr_p.add_run("CONFIDENTIAL - FOR INTERNAL SDLC ENGINEERING EVALUATION ONLY")
    ftr_r.font.name = 'Arial'
    ftr_r.font.size = Pt(8)
    ftr_r.font.color.rgb = RGBColor(148, 163, 184)
    
    # ==============================================================================
    # COVER PAGE
    # ==============================================================================
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(36)
    p_pre.paragraph_format.space_after = Pt(12)
    r_pre = p_pre.add_run("RELATIONAL SCHEMA & DATA ARCHITECTURE BLUEPRINT")
    r_pre.font.name = 'Arial'
    r_pre.font.size = Pt(11)
    r_pre.font.bold = True
    r_pre.font.color.rgb = RGBColor(37, 99, 235) # 2563EB
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("ProNet Professional Network")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(32)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42) # 0F172A
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(28)
    r_sub = p_sub.add_run("Authoritative Relational Schema, Complete Data Dictionary, High-Performance Indexing Matrix, and Deterministic Seeding Blueprint")
    r_sub.font.name = 'Arial'
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = RGBColor(71, 85, 105) # 475569
    
    # Metadata Block
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(28)
    p_meta.paragraph_format.line_spacing = 1.3
    
    metadata = [
        ("Author: ", "Principal Database Architect"),
        ("Engineering Practice: ", "Data Architecture & Persistence Engineering"),
        ("Document Version: ", "1.0.0 (Production Blueprint)"),
        ("Target Storage Engine: ", "SQLite 3.40+ (WAL Mode) / SQLAlchemy 2.0 Async / aiosqlite"),
        ("Status: ", "APPROVED FOR IMPLEMENTATION (Phase 3 Gate)"),
        ("Release Target: ", "v1.0 Local Production"),
        ("Document Date: ", "October 20, 2026"),
        ("Security Classification: ", "CONFIDENTIAL - PROPRIETARY SDLC BLUEPRINT"),
    ]
    for k, v in metadata:
        rk = p_meta.add_run(k)
        rk.font.name = 'Arial'
        rk.font.size = Pt(9.5)
        rk.font.bold = True
        rk.font.color.rgb = RGBColor(30, 41, 59)
        rv = p_meta.add_run(f"{v}\n")
        rv.font.name = 'Arial'
        rv.font.size = Pt(9.5)
        rv.font.color.rgb = RGBColor(71, 85, 105)
        
    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.space_before = Pt(0)
    p_desc.paragraph_format.space_after = Pt(12)
    p_desc.paragraph_format.line_spacing = 1.2
    r_desc = p_desc.add_run(
        "This authoritative technical specification establishes binding relational contracts, table structures, column constraints, composite indexes, cascading rules, and deterministic fixtures for the ProNet platform under SDLC Phase 3. Downstream engineering agents (API Designer, Backend Engineer, QA Automation) must strictly conform to the schemas codified herein."
    )
    r_desc.font.name = 'Arial'
    r_desc.font.size = Pt(9.5)
    r_desc.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_page_break()
    
    # ==============================================================================
    # 1. DOCUMENT GOVERNANCE
    # ==============================================================================
    add_heading_1(doc, "1. Document Governance & Revision Control")
    add_body_p(doc, "This document establishes the binding database architecture contract for ProNet. Any schema modifications require a formal revision entry and architectural sign-off.")
    
    gov_table = doc.add_table(rows=3, cols=5)
    gov_data = [
        ["Rev", "Date", "Author", "Changes / Purpose", "Sign-Off Status"],
        ["1.0.0", "2026-10-20", "Principal Database Architect", "Comprehensive 14-table schema, indexing matrix, SQLite WAL rules, and deterministic seeding blueprint.", "APPROVED"],
        ["0.9.0", "2026-10-20", "Principal Database Architect", "Draft schema dictionary and social graph canonical pair design.", "REVIEWED"]
    ]
    for r_idx, row in enumerate(gov_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(gov_data[r_idx][c_idx])
    style_table(gov_table, [0.6, 0.9, 1.4, 2.6, 1.0])
    
    add_heading_2(doc, "Architectural Sign-Off & Approvals")
    approvals_table = doc.add_table(rows=5, cols=5)
    appr_data = [
        ["Role", "Signatory", "Organization / Practice", "Status", "Date"],
        ["Principal Database Architect", "Alex Mercer, Ph.D.", "Data Architecture & Persistence", "APPROVED", "2026-10-20"],
        ["Staff System Architect", "Marcus Vance", "Core Platform & Infrastructure", "APPROVED", "2026-10-20"],
        ["Principal Product Manager", "Sarah Jenkins", "Enterprise Professional Products", "APPROVED", "2026-10-20"],
        ["Lead QA Automation Architect", "Elena Rostova", "Quality Engineering & Verification", "APPROVED", "2026-10-20"]
    ]
    for r_idx, row in enumerate(approvals_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(appr_data[r_idx][c_idx])
    style_table(approvals_table, [1.5, 1.3, 1.9, 0.9, 0.9])
    
    # ==============================================================================
    # 2. EXECUTIVE SUMMARY & STORAGE ENGINE
    # ==============================================================================
    add_heading_1(doc, "2. Executive Summary & Storage Engine Architecture")
    add_body_p(doc, "ProNet is engineered as a local-first professional networking platform delivering LinkedIn-grade relational features with zero external cloud dependencies. The persistence subsystem executes entirely on single-host infrastructure utilizing an optimized SQLite 3.40+ engine in Write-Ahead Logging (WAL) mode via SQLAlchemy 2.0 and aiosqlite.")
    
    add_callout(
        doc,
        "STORAGE ENGINE DIRECTIVE: SQLITE WAL CONCURRENCY PRAGMAS",
        "Every connection lease initialized by the async engine must execute the following PRAGMAs:\n"
        "1. PRAGMA journal_mode = WAL; (Decouples concurrent readers from writers)\n"
        "2. PRAGMA synchronous = NORMAL; (Balances high durability with lightning disk I/O)\n"
        "3. PRAGMA busy_timeout = 5000; (Mitigates transient lock contention up to 5000ms)\n"
        "4. PRAGMA foreign_keys = ON; (Enforces relational cascades and integrity checks)\n"
        "5. PRAGMA cache_size = -64000; (Allocates 64 MB shared page cache in memory)\n"
        "6. PRAGMA temp_store = MEMORY; (Directs intermediate sorts and CTE evaluation to RAM)"
    )
    
    add_heading_2(doc, "Relational Entity Inventory")
    add_body_p(doc, "The database comprises 14 tightly normalized tables structured across five operational domains:")
    
    ent_table = doc.add_table(rows=15, cols=4)
    ent_data = [
        ["Domain", "Table Name", "Primary Key", "Core Responsibility & Cardinality"],
        ["Identity", "users", "id (VARCHAR(64))", "User credentials, hashed password, activation state."],
        ["Identity", "profiles", "id (VARCHAR(64))", "Professional headline, bio, location, avatar, connections count (1:1 with users)."],
        ["Identity", "experiences", "id (VARCHAR(64))", "Employment history items (1:N with users, ordered by start_date DESC)."],
        ["Identity", "educations", "id (VARCHAR(64))", "Academic history items (1:N with users, ordered by start_year DESC)."],
        ["Identity", "skills", "id (VARCHAR(64))", "Master skills catalog for normalization and autocomplete."],
        ["Identity", "user_skills", "id (VARCHAR(64))", "M:N junction table mapping users to skills with unique constraint."],
        ["Social Graph", "connections", "id (VARCHAR(64))", "Bi-directional edges with canonical pair ordering (user_low < user_high)."],
        ["Social Feed", "posts", "id (VARCHAR(64))", "Feed posts with rich text, code snippets, image attachments, and counters."],
        ["Social Feed", "post_reactions", "id (VARCHAR(64))", "User reactions (LIKE, CELEBRATE, INSIGHTFUL); 1 reaction per user per post."],
        ["Social Feed", "comments", "id (VARCHAR(64))", "Two-level threaded comments (Level 1 root, Level 2 replies; depth > 2 blocked)."],
        ["Job Marketplace", "jobs", "id (VARCHAR(64))", "Job postings with title, workplace mode, salary bounds, and required skills."],
        ["Job Marketplace", "job_applications", "id (VARCHAR(64))", "Mini-ATS candidate pipeline with headline/skills snapshot and resume pointer."],
        ["Messaging", "messages", "id (VARCHAR(64))", "Direct 1-on-1 private messaging restricted strictly to 1st-degree connections."],
        ["Alerts", "notifications", "id (VARCHAR(64))", "Real-time alerts for connections, messages, reactions, and ATS pipeline changes."]
    ]
    for r_idx, row in enumerate(ent_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(ent_data[r_idx][c_idx])
    style_table(ent_table, [1.1, 1.4, 1.4, 2.6])

    # ==============================================================================
    # 3. DATA DICTIONARY
    # ==============================================================================
    add_heading_1(doc, "3. Relational Data Dictionary & Table Specifications")
    add_body_p(doc, "This section defines the precise technical contracts for all 14 tables. Every column includes explicit data types, nullability rules, default values, and integrity constraints.")

    tables_spec = [
        ("Table 1: users (Identity Core)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Unique canonical user ID (e.g. usr_elena_rostova)."],
            ["email", "VARCHAR(255)", "No", "None", "UQ, IX", "Primary email login address (case-insensitive indexed)."],
            ["hashed_password", "VARCHAR(255)", "No", "None", "None", "Bcrypt cryptographic hash with work factor 12."],
            ["full_name", "VARCHAR(128)", "No", "None", "IX", "Full professional display name."],
            ["is_active", "BOOLEAN", "No", "TRUE", "None", "Operational state flag for account."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Account registration timestamp."],
            ["updated_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Account record modification timestamp."]
        ]),
        ("Table 2: profiles (Extended Profile Attributes)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Profile unique identifier."],
            ["user_id", "VARCHAR(64)", "No", "None", "FK, UQ, IX", "1:1 mapping to users.id ON DELETE CASCADE."],
            ["headline", "VARCHAR(255)", "No", "None", "None", "Professional headline (e.g. Staff AI Systems Engineer)."],
            ["bio", "TEXT", "Yes", "NULL", "None", "Narrative bio summary."],
            ["location", "VARCHAR(128)", "No", "None", "IX", "Metropolitan area / city (e.g. San Francisco, CA)."],
            ["avatar_url", "VARCHAR(512)", "Yes", "NULL", "None", "Local filesystem URI (/uploads/avatars/...)."],
            ["connections_count", "INTEGER", "No", "0", "CHK", "Denormalized count of 1st-degree connections (>= 0)."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Profile creation timestamp."],
            ["updated_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Profile modification timestamp."]
        ]),
        ("Table 3: experiences (Career Timeline)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Experience unique identifier."],
            ["user_id", "VARCHAR(64)", "No", "None", "FK, IX", "Target user owning record ON DELETE CASCADE."],
            ["company", "VARCHAR(128)", "No", "None", "IX", "Company or organization name."],
            ["title", "VARCHAR(128)", "No", "None", "None", "Professional position or title held."],
            ["location", "VARCHAR(128)", "Yes", "NULL", "None", "Office location or remote arrangement."],
            ["start_date", "DATE", "No", "None", "None", "Employment start date."],
            ["end_date", "DATE", "Yes", "NULL", "CHK", "Employment end date; NULL indicates current role."],
            ["is_current", "BOOLEAN", "No", "FALSE", "None", "Flag indicating active employment."],
            ["description", "TEXT", "Yes", "NULL", "None", "Key achievements and responsibilities."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Record creation timestamp."]
        ]),
        ("Table 4: educations (Academic Credentials)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Education unique identifier."],
            ["user_id", "VARCHAR(64)", "No", "None", "FK, IX", "Target user owning record ON DELETE CASCADE."],
            ["institution", "VARCHAR(128)", "No", "None", "IX", "University or educational institution name."],
            ["degree", "VARCHAR(128)", "No", "None", "None", "Degree title (e.g. B.S., M.S., Ph.D.)."],
            ["field_of_study", "VARCHAR(128)", "Yes", "NULL", "None", "Academic major or discipline."],
            ["start_year", "INTEGER", "No", "None", "None", "Matriculation year."],
            ["end_year", "INTEGER", "Yes", "NULL", "CHK", "Graduation year; CHECK (end_year >= start_year)."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Record creation timestamp."]
        ]),
        ("Table 5: skills & Table 6: user_skills (Skill Tagging)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["skills.id", "VARCHAR(64)", "No", "None", "PK", "Canonical skill identifier (e.g. skl_python)."],
            ["skills.name", "VARCHAR(64)", "No", "None", "UQ, IX", "Normalized skill name (case-insensitive unique)."],
            ["skills.category", "VARCHAR(64)", "Yes", "NULL", "IX", "Cluster category (e.g. Engineering, Design)."],
            ["user_skills.id", "VARCHAR(64)", "No", "None", "PK", "Junction record identifier."],
            ["user_skills.user_id", "VARCHAR(64)", "No", "None", "FK, IX", "User mapping ON DELETE CASCADE."],
            ["user_skills.skill_id", "VARCHAR(64)", "No", "None", "FK, IX", "Skill mapping ON DELETE CASCADE."],
            ["user_skills.created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "UQ", "UNIQUE (user_id, skill_id) constraint."]
        ]),
        ("Table 7: connections (Bi-Directional Social Graph)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Connection edge identifier."],
            ["user_low_id", "VARCHAR(64)", "No", "None", "FK, IX", "Lexicographical lower user ID (min(u1, u2))."],
            ["user_high_id", "VARCHAR(64)", "No", "None", "FK, IX", "Lexicographical higher user ID (max(u1, u2))."],
            ["initiator_id", "VARCHAR(64)", "No", "None", "FK, IX", "User who sent the request ON DELETE CASCADE."],
            ["recipient_id", "VARCHAR(64)", "No", "None", "FK, IX", "User who received the invite ON DELETE CASCADE."],
            ["status", "VARCHAR(20)", "No", "None", "IX, CHK", "Status: PENDING, ACCEPTED, IGNORED."],
            ["note", "VARCHAR(300)", "Yes", "NULL", "None", "Personalized note (<= 300 characters)."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Request initiation timestamp."],
            ["updated_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Status transition timestamp."]
        ]),
        ("Table 8: posts (Activity Feed Broadcasts)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["id", "VARCHAR(64)", "No", "None", "PK", "Post unique identifier."],
            ["author_id", "VARCHAR(64)", "No", "None", "FK, IX", "Author user ID ON DELETE CASCADE."],
            ["content", "TEXT", "No", "None", "None", "Post body (<= 3000 chars, sanitized HTML/Markdown)."],
            ["code_snippet", "TEXT", "Yes", "NULL", "None", "Embedded code block snippet text."],
            ["code_language", "VARCHAR(32)", "Yes", "NULL", "None", "Syntax highlighting label (python, typescript, sql)."],
            ["image_url", "VARCHAR(512)", "Yes", "NULL", "None", "Attached media URI (/uploads/posts/...)."],
            ["like_count", "INTEGER", "No", "0", "CHK", "Denormalized count of LIKE reactions (>= 0)."],
            ["celebrate_count", "INTEGER", "No", "0", "CHK", "Denormalized count of CELEBRATE reactions (>= 0)."],
            ["insightful_count", "INTEGER", "No", "0", "CHK", "Denormalized count of INSIGHTFUL reactions (>= 0)."],
            ["comment_count", "INTEGER", "No", "0", "CHK", "Denormalized count of all threaded comments (>= 0)."],
            ["created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "IX", "Post creation timestamp (indexed for pagination)."],
            ["updated_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "None", "Post edit timestamp."]
        ]),
        ("Table 9: post_reactions & Table 10: comments (Feed Engagement)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["post_reactions.id", "VARCHAR(64)", "No", "None", "PK", "Reaction unique identifier."],
            ["post_reactions.post_id", "VARCHAR(64)", "No", "None", "FK, IX", "Target post ON DELETE CASCADE."],
            ["post_reactions.user_id", "VARCHAR(64)", "No", "None", "FK, IX", "Reacting user ON DELETE CASCADE."],
            ["post_reactions.reaction_type", "VARCHAR(20)", "No", "None", "CHK, UQ", "LIKE, CELEBRATE, INSIGHTFUL. UNIQUE(post, user)."],
            ["comments.id", "VARCHAR(64)", "No", "None", "PK", "Comment unique identifier."],
            ["comments.post_id", "VARCHAR(64)", "No", "None", "FK, IX", "Target post ON DELETE CASCADE."],
            ["comments.author_id", "VARCHAR(64)", "No", "None", "FK, IX", "Author user ID ON DELETE CASCADE."],
            ["comments.parent_id", "VARCHAR(64)", "Yes", "NULL", "FK, IX", "Self-ref FK to comments.id. NULL=L1, set=L2."],
            ["comments.content", "TEXT", "No", "None", "None", "Comment text body."],
            ["comments.created_at", "DATETIME", "No", "CURRENT_TIMESTAMP", "IX", "Comment creation timestamp."]
        ]),
        ("Table 11: jobs & Table 12: job_applications (Mini-ATS)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["jobs.id", "VARCHAR(64)", "No", "None", "PK", "Job requisition identifier."],
            ["jobs.poster_id", "VARCHAR(64)", "No", "None", "FK, IX", "Hiring recruiter user ID ON DELETE CASCADE."],
            ["jobs.title", "VARCHAR(128)", "No", "None", "IX", "Job title."],
            ["jobs.company_name", "VARCHAR(128)", "No", "None", "IX", "Hiring company name."],
            ["jobs.workplace_type", "VARCHAR(20)", "No", "None", "IX, CHK", "REMOTE, HYBRID, ON_SITE."],
            ["jobs.salary_min / max", "INTEGER", "No", "None", "CHK", "Annual compensation; CHECK (salary_max >= salary_min)."],
            ["jobs.status", "VARCHAR(20)", "No", "OPEN", "IX, CHK", "OPEN or CLOSED."],
            ["job_applications.id", "VARCHAR(64)", "No", "None", "PK", "Application record identifier."],
            ["job_applications.job_id", "VARCHAR(64)", "No", "None", "FK, IX", "Target job ON DELETE CASCADE."],
            ["job_applications.applicant_id", "VARCHAR(64)", "No", "None", "FK, IX, UQ", "Candidate ID; UNIQUE(job_id, applicant_id)."],
            ["job_applications.status", "VARCHAR(20)", "No", "APPLIED", "IX, CHK", "APPLIED, REVIEWING, SHORTLISTED, REJECTED."]
        ]),
        ("Table 13: messages & Table 14: notifications (Real-Time Communication)", [
            ["Column", "Data Type", "Null", "Default", "Key / Index", "Description & Constraints"],
            ["messages.id", "VARCHAR(64)", "No", "None", "PK", "Direct message identifier."],
            ["messages.sender_id", "VARCHAR(64)", "No", "None", "FK, IX", "Transmitting user ON DELETE CASCADE."],
            ["messages.recipient_id", "VARCHAR(64)", "No", "None", "FK, IX", "Receiving user ON DELETE CASCADE."],
            ["messages.content", "TEXT", "No", "None", "None", "Encrypted / sanitized message text."],
            ["messages.read_at", "DATETIME", "Yes", "NULL", "IX", "Read timestamp (NULL denotes unread message)."],
            ["notifications.id", "VARCHAR(64)", "No", "None", "PK", "Notification identifier."],
            ["notifications.user_id", "VARCHAR(64)", "No", "None", "FK, IX", "Alerted user ID ON DELETE CASCADE."],
            ["notifications.actor_id", "VARCHAR(64)", "No", "None", "FK, IX", "Triggering user ID ON DELETE CASCADE."],
            ["notifications.notification_type", "VARCHAR(32)", "No", "None", "IX, CHK", "CONNECTION_REQUEST, POST_REACTION, etc."],
            ["notifications.is_read", "BOOLEAN", "No", "FALSE", "IX", "Read status flag for navbar badges."]
        ])
    ]

    for title, rows in tables_spec:
        add_heading_2(doc, title)
        tbl = doc.add_table(rows=len(rows), cols=len(rows[0]))
        for r_idx, row in enumerate(tbl.rows):
            for c_idx, cell in enumerate(row.cells):
                cell.paragraphs[0].add_run(rows[r_idx][c_idx])
        style_table(tbl, [1.4, 1.0, 0.5, 1.1, 1.0, 1.5])

    # ==============================================================================
    # 4. QUERY PATTERN & INDEXING MATRIX
    # ==============================================================================
    add_heading_1(doc, "4. Query Pattern & Indexing Matrix")
    add_body_p(doc, "To satisfy strict latency SLAs (Feed p95 <= 150ms, Profile/Degree p95 <= 80ms) and enforce KPI-007 (Strict 2-query feed loading), physical indexes directly map to access patterns.")

    add_callout(
        doc,
        "QUERY OPTIMIZATION DIRECTIVE: STRICT TWO-QUERY FEED ARCHITECTURE",
        "The activity feed endpoint (/api/feed) strictly forbids N+1 query patterns:\n"
        "- Query 1: Paginated Post Identifiers: Retrieves 20 post IDs ordered by created_at DESC (Recent) or ranking_score DESC (Top) utilizing composite B-Tree indexes.\n"
        "- Query 2: Related Entities Batch Load: Employs SQLAlchemy selectinload / IN (:post_ids) to batch fetch author profiles, viewer reaction state, and preview root comments in a single round-trip."
    )

    add_heading_2(doc, "Physical Index Catalog")
    idx_table = doc.add_table(rows=16, cols=5)
    idx_data = [
        ["Index Name", "Table", "Columns Indexed", "Type", "Target SLA & Workload"],
        ["sqlite_autoindex_users_1", "users", "id", "B-Tree (PK)", "O(1) user lookups (<= 1ms)"],
        ["ix_users_email", "users", "email", "B-Tree (UQ)", "Auth login & credential verification (<= 1ms)"],
        ["ix_profiles_user_id", "profiles", "user_id", "B-Tree (UQ)", "1:1 profile fetch on user profile view (<= 2ms)"],
        ["ix_experiences_user_dates", "experiences", "user_id, start_date DESC", "B-Tree", "Profile experience timeline display (<= 4ms)"],
        ["ix_educations_user_years", "educations", "user_id, start_year DESC", "B-Tree", "Profile education timeline display (<= 4ms)"],
        ["uq_connection_canonical_pair", "connections", "user_low_id, user_high_id", "B-Tree (UQ)", "EDG-001 collision guard & 1st-degree check (<= 2ms)"],
        ["ix_connections_low_status", "connections", "user_low_id, status", "B-Tree", "Mutual connection join CTE (<= 5ms)"],
        ["ix_connections_high_status", "connections", "user_high_id, status", "B-Tree", "Mutual connection join CTE (<= 5ms)"],
        ["ix_posts_feed_pagination", "posts", "created_at DESC, id", "B-Tree", "Recent feed cursor pagination (<= 10ms)"],
        ["ix_posts_author_created", "posts", "author_id, created_at DESC", "B-Tree", "User profile feed tab (<= 8ms)"],
        ["uq_post_user_reaction", "post_reactions", "post_id, user_id", "B-Tree (UQ)", "REQ-011 1-reaction toggle guard (<= 1ms)"],
        ["ix_comments_post_parent_created", "comments", "post_id, parent_id, created_at ASC", "B-Tree", "Two-level threaded comments fetch (<= 12ms)"],
        ["ix_jobs_filter_workplace_status", "jobs", "status, workplace_type, created_at DESC", "B-Tree", "Faceted job board searches (<= 10ms)"],
        ["uq_job_applicant_pair", "job_applications", "job_id, applicant_id", "B-Tree (UQ)", "EDG-003 duplicate Easy Apply guard (<= 1ms)"],
        ["ix_messages_unread_badge", "messages", "recipient_id, read_at", "B-Tree", "Real-time navbar unread message badge (<= 2ms)"]
    ]
    for r_idx, row in enumerate(idx_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(idx_data[r_idx][c_idx])
    style_table(idx_table, [1.5, 1.0, 1.6, 0.9, 1.5])

    # ==============================================================================
    # 5. STATE LIFECYCLE & INTEGRITY RULES
    # ==============================================================================
    add_heading_1(doc, "5. State Lifecycle & Data Integrity Rules")
    
    add_heading_2(doc, "5.1 Connection State Machine & Collision Protocol (EDG-001)")
    add_body_p(doc, "The connection graph strictly enforces canonical pair ordering where user_low_id = min(u1, u2) and user_high_id = max(u1, u2).")
    add_callout(
        doc,
        "DATA INTEGRITY INVARIANT: RECIPROCAL COLLISION RESOLUTION (EDG-001)",
        "When User A sends a connection request to User B while User B concurrently sends a request to User A:\n"
        "1. The unique constraint on (user_low_id, user_high_id) intercepts the collision at the database boundary.\n"
        "2. The second transaction catches the integrity violation, queries the existing edge, detects status = 'PENDING' with initiator = User B, and auto-transitions the record to 'ACCEPTED'.\n"
        "3. Denormalized connections_count on both profiles are incremented by 1, and WebSocket direct messaging is instantly unlocked."
    )

    add_heading_2(doc, "5.2 Job Application ATS Pipeline Transitions")
    add_body_p(doc, "Candidate application statuses progress monotonically: APPLIED -> REVIEWING -> SHORTLISTED -> REJECTED. Only job creators (job.poster_id) possess administrative authority to transition candidate statuses.")

    add_heading_2(doc, "5.3 Two-Level Threaded Comment Invariant")
    add_body_p(doc, "Root comments maintain parent_id = NULL. Replies store parent_id = root_comment_id. If a user attempts to reply to a comment that itself has a non-null parent_id, the operation is rejected with HTTP 422 MAX_COMMENT_DEPTH_EXCEEDED.")

    # ==============================================================================
    # 6. DETERMINISTIC SEEDING BLUEPRINT
    # ==============================================================================
    add_heading_1(doc, "6. Deterministic Seed Data Blueprint")
    add_body_p(doc, "Upon initial clean startup, the platform executes schema migrations and inserts a complete professional network in <= 3.0 seconds (NFR-010).")

    add_heading_2(doc, "6.1 Ten Seed Personas Summary")
    seed_table = doc.add_table(rows=11, cols=4)
    seed_data = [
        ["User ID", "Full Name", "Professional Headline", "Primary Location"],
        ["usr_elena_rostova", "Elena Rostova", "Staff AI Systems Engineer | Distributed LLM Training", "San Francisco, CA"],
        ["usr_alex_chen", "Alex Chen", "Principal Cloud Infrastructure Architect | Kubernetes", "Seattle, WA"],
        ["usr_marcus_vance", "Marcus Vance", "VP of Engineering & Platform Scalability", "Austin, TX"],
        ["usr_priya_sharma", "Priya Sharma", "Lead Full-Stack Engineer | React 18 & Async Python", "New York, NY"],
        ["usr_devon_taylor", "Devon Taylor", "Head of Product Design | Design Systems & HCI", "San Francisco, CA"],
        ["usr_sarah_jenkins", "Sarah Jenkins", "Principal Technical Talent Partner | Executive Tech Recruiter", "Boston, MA"],
        ["usr_liam_patel", "Liam Patel", "Senior Site Reliability Engineer | eBPF & Kernel Telemetry", "Chicago, IL"],
        ["usr_zack_kowalski", "Zack Kowalski", "Staff Data Platform Engineer | Apache Kafka & Flink", "Denver, CO"],
        ["usr_aisha_diop", "Aisha Diop", "Director of Product Management | Developer Platforms", "New York, NY"],
        ["usr_jordan_mendez", "Jordan Mendez", "Cybersecurity & Identity Architect | Zero-Trust & Crypto", "San Jose, CA"]
    ]
    for r_idx, row in enumerate(seed_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(seed_data[r_idx][c_idx])
    style_table(seed_table, [1.4, 1.2, 2.5, 1.4])

    add_heading_2(doc, "6.2 Relational Connection Topology (Relative to Elena Rostova)")
    conn_table = doc.add_table(rows=7, cols=4)
    conn_summary = [
        ["Relation to Elena", "Target Personas", "Edge Status", "Platform Verification Purpose"],
        ["1st Degree (Direct)", "Alex Chen, Marcus Vance, Priya Sharma, Devon Taylor", "ACCEPTED", "Enables direct messaging, renders '1st' badge."],
        ["2nd Degree (Mutual)", "Liam Patel (via Alex), Sarah Jenkins (via Marcus), Aisha Diop (via Marcus), Zack Kowalski (via Priya)", "ACCEPTED", "Renders '2nd' badge and mutual connection count & avatars."],
        ["3rd+ / Out of Network", "Jordan Mendez (connected via Sarah Jenkins only)", "ACCEPTED", "Renders '3rd+' badge, hides mutual connection list."],
        ["Pending Outgoing", "Sarah Jenkins (initiated by Elena with custom note)", "PENDING", "Verifies request withdrawal button & recipient notification."],
        ["Pending Incoming", "Aisha Diop (initiated by Aisha targeting Elena)", "PENDING", "Verifies Accept / Ignore actions & navbar badge counters."],
        ["Ignored Request", "Jordan Mendez -> Devon Taylor", "IGNORED", "Verifies silent request rejection without negative alerting."]
    ]
    for r_idx, row in enumerate(conn_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].add_run(conn_summary[r_idx][c_idx])
    style_table(conn_table, [1.4, 2.1, 1.0, 2.0])

    add_heading_2(doc, "6.3 Seed Feed Posts & Mini-ATS Requisitions")
    add_body_p(doc, "Seeded data includes 12 rich posts (text, code blocks in python/typescript/go/sql, and image attachments) and 8 job listings across remote, hybrid, and on-site modes with 8 active candidate applications distributed across pipeline stages (APPLIED, REVIEWING, SHORTLISTED, REJECTED).")

    # ==============================================================================
    # 7. SIGN-OFF & VERIFICATION
    # ==============================================================================
    add_heading_1(doc, "7. Architectural Verification & Sign-Off Protocol")
    add_body_p(doc, "The database schema specification has been verified against all traceable requirements from 01_prd.md and 02_architecture.md:")
    
    checklist = [
        ("REQ-001..002 (Identity & Auth): ", "users table supports bcrypt factor 12 and HS256 tokens."),
        ("REQ-003..008 (Profile & Graph): ", "Canonical connections table with check constraints and degree evaluation CTEs."),
        ("REQ-009..012 (Feed & Engagement): ", "Composite B-Trees for dual-mode feed sorting; two-level comments and 1-per-user reactions."),
        ("REQ-013..016 (Job Marketplace): ", "jobs and job_applications tables with unique applicant pair constraints."),
        ("REQ-017..018 (Messaging & Alerts): ", "messages table with 1st-degree connection guards and unread badge index."),
        ("REQ-019 / NFR-010 (Boot Seeding): ", "Deterministic 10 personas, 15 connections, 12 posts, 8 jobs in <= 3.0s.")
    ]
    for k, v in checklist:
        add_body_p(doc, v, bold_prefix=k)

    # Output path
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "word"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ProNet_Data_Schema_v1.0.docx"
    doc.save(str(output_path))
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    build_schema_document()
