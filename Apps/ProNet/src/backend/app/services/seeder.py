"""Deterministic database seeder populating 10 personas, 15 connections, 12 posts, and 8 jobs."""
import json
import logging
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import hash_password
from app.models.schema import (
    User, Profile, Experience, Education, Skill, UserSkill,
    Connection, Post, PostReaction, Comment, Job, JobApplication,
    Message, Notification
)

logger = logging.getLogger("pronet.seeder")


async def seed_database(db: AsyncSession, force: bool = False) -> bool:
    """Populate database with deterministic initial state if users table is empty."""
    user_count_res = await db.execute(select(func.count(User.id)))
    existing_users = user_count_res.scalar() or 0

    if existing_users > 0 and not force:
        logger.info("Database already contains data; skipping seeder.")
        return False

    logger.info("Starting deterministic database seeding...")
    now = datetime.now(timezone.utc)
    base_pwd_hash = hash_password("Password123!")

    # --------------------------------------------------------------------------
    # 1. SKILLS CATALOG
    # --------------------------------------------------------------------------
    skills_data = [
        ("skl_python", "Python", "Engineering"),
        ("skl_dist_sys", "Distributed Systems", "Engineering"),
        ("skl_pytorch", "PyTorch", "AI/ML"),
        ("skl_cpp", "C++", "Engineering"),
        ("skl_sqlalchemy", "SQLAlchemy", "Engineering"),
        ("skl_fastapi", "FastAPI", "Engineering"),
        ("skl_k8s", "Kubernetes", "DevOps"),
        ("skl_terraform", "Terraform", "DevOps"),
        ("skl_go", "Go", "Engineering"),
        ("skl_aws", "AWS", "Cloud"),
        ("skl_docker", "Docker", "DevOps"),
        ("skl_eng_lead", "Engineering Leadership", "Management"),
        ("skl_arch", "Architecture", "Engineering"),
        ("skl_prod_strat", "Product Strategy", "Product"),
        ("skl_agile", "Agile", "Management"),
        ("skl_react", "React", "Frontend"),
        ("skl_ts", "TypeScript", "Frontend"),
        ("skl_tailwind", "Tailwind CSS", "Frontend"),
        ("skl_prod_des", "Product Design", "Design"),
        ("skl_ui_ux", "UI/UX", "Design"),
        ("skl_des_sys", "Design Systems", "Design"),
        ("skl_figma", "Figma", "Design"),
        ("skl_frontend", "Frontend Engineering", "Frontend"),
        ("skl_tech_rec", "Technical Recruiting", "HR"),
        ("skl_talent", "Talent Acquisition", "HR"),
        ("skl_exec_search", "Executive Search", "HR"),
        ("skl_hiring", "Hiring Strategy", "HR"),
        ("skl_linux", "Linux", "Systems"),
        ("skl_ebpf", "eBPF", "Systems"),
        ("skl_prom", "Prometheus", "DevOps"),
        ("skl_kafka", "Apache Kafka", "Data"),
        ("skl_flink", "Flink", "Data"),
        ("skl_sql", "SQL", "Data"),
        ("skl_prod_mgmt", "Product Management", "Product"),
        ("skl_api_des", "API Design", "Engineering"),
        ("skl_saas", "Enterprise SaaS", "Product"),
        ("skl_crypto", "Cryptography", "Security"),
        ("skl_identity", "Identity Management", "Security"),
        ("skl_oauth2", "OAuth2", "Security"),
        ("skl_appsec", "AppSec", "Security"),
    ]

    skill_entities = {}
    for sid, sname, scat in skills_data:
        skill = Skill(id=sid, name=sname, category=scat, created_at=now)
        db.add(skill)
        skill_entities[sname] = skill

    await db.flush()

    # --------------------------------------------------------------------------
    # 2. 10 PERSONAS (USERS & PROFILES)
    # --------------------------------------------------------------------------
    personas = [
        {
            "id": "usr_elena_rostova",
            "email": "elena.rostova@pronet.local",
            "full_name": "Elena Rostova",
            "headline": "Staff AI Systems Engineer | Distributed LLM Training & Kernel Optimization",
            "location": "San Francisco, CA",
            "bio": "Architecting high-throughput distributed tensor pipelines and low-latency inference runtimes. Passionate about local-first systems and deterministic software design.",
            "avatar_url": "/uploads/avatars/usr_elena_rostova.png",
            "connections_count": 4,
            "experiences": [
                ("exp_01_1", "NeuralMesh AI", "Staff AI Systems Engineer", "San Francisco, CA", date(2022, 3, 1), None, True, "Engineered zero-copy memory transfer layer for multi-node LLM training."),
                ("exp_01_2", "Databox Labs", "Senior Distributed Systems Engineer", "Mountain View, CA", date(2018, 6, 1), date(2022, 2, 28), False, "Architected distributed key-value store handling 5M QPS at p99 < 4ms.")
            ],
            "educations": [
                ("edu_01_1", "University of California, Berkeley", "M.S.", "Computer Science", 2016, 2018),
                ("edu_01_2", "University of Washington", "B.S.", "Computer Engineering", 2012, 2016)
            ],
            "skills": ["Python", "Distributed Systems", "PyTorch", "C++", "SQLAlchemy", "FastAPI"]
        },
        {
            "id": "usr_alex_chen",
            "email": "alex.chen@pronet.local",
            "full_name": "Alex Chen",
            "headline": "Principal Cloud Infrastructure Architect | Kubernetes & High-Resilience Systems",
            "location": "Seattle, WA",
            "bio": "Dedicated to zero-trust cloud architectures, infrastructure-as-code automation, and sub-second failover orchestration across hybrid cloud environments.",
            "avatar_url": "/uploads/avatars/usr_alex_chen.png",
            "connections_count": 3,
            "experiences": [
                ("exp_02_1", "HyperScale Networks", "Principal Cloud Architect", "Seattle, WA", date(2021, 1, 1), None, True, "Leading 40-engineer cloud platform modernization initiative."),
                ("exp_02_2", "CloudNative Technologies", "Staff Infrastructure Engineer", "Redmond, WA", date(2016, 9, 1), date(2020, 12, 31), False, "Maintained 10,000-node Kubernetes clusters with 99.999% availability.")
            ],
            "educations": [
                ("edu_02_1", "University of Washington", "B.S.", "Software Engineering", 2012, 2016)
            ],
            "skills": ["Kubernetes", "Terraform", "Go", "AWS", "Distributed Systems", "Docker"]
        },
        {
            "id": "usr_marcus_vance",
            "email": "marcus.vance@pronet.local",
            "full_name": "Marcus Vance",
            "headline": "VP of Engineering & Platform Scalability | Building High-Velocity Orgs",
            "location": "Austin, TX",
            "bio": "Executive engineering leader scaling teams from Seed to IPO. Champion of developer ergonomics, psychological safety, and metric-driven architecture.",
            "avatar_url": "/uploads/avatars/usr_marcus_vance.png",
            "connections_count": 4,
            "experiences": [
                ("exp_03_1", "Nexus Cloud Systems", "VP of Engineering", "Austin, TX", date(2020, 4, 1), None, True, "Overseeing 120+ engineers across platform, product, and QA."),
                ("exp_03_2", "ScaleStream", "Director of Platform Engineering", "Austin, TX", date(2015, 2, 1), date(2020, 3, 31), False, "Built engineering culture focused on continuous delivery and automated QA.")
            ],
            "educations": [
                ("edu_03_1", "University of Texas at Austin", "B.S.", "Computer Science", 2007, 2011)
            ],
            "skills": ["Engineering Leadership", "Architecture", "Distributed Systems", "Product Strategy", "Agile"]
        },
        {
            "id": "usr_priya_sharma",
            "email": "priya.sharma@pronet.local",
            "full_name": "Priya Sharma",
            "headline": "Lead Full-Stack Engineer | React 18 & Async Python Architecture",
            "location": "New York, NY",
            "bio": "Crafting pixel-perfect, accessible client applications backed by lightning-fast async ASGI backends. Open source contributor and tech conference speaker.",
            "avatar_url": "/uploads/avatars/usr_priya_sharma.png",
            "connections_count": 3,
            "experiences": [
                ("exp_04_1", "FinEdge Systems", "Lead Full-Stack Engineer", "New York, NY", date(2022, 7, 1), None, True, "Directing design system implementation and TanStack Query state caching layer."),
                ("exp_04_2", "MetroMedia", "Senior Frontend Engineer", "Brooklyn, NY", date(2019, 3, 1), date(2022, 6, 30), False, "Reduced client bundle sizes by 58% utilizing code splitting and Vite.")
            ],
            "educations": [
                ("edu_04_1", "Columbia University", "B.S.", "Computer Science", 2015, 2019)
            ],
            "skills": ["React", "TypeScript", "Python", "FastAPI", "Tailwind CSS", "SQLAlchemy"]
        },
        {
            "id": "usr_devon_taylor",
            "email": "devon.taylor@pronet.local",
            "full_name": "Devon Taylor",
            "headline": "Head of Product Design | Design Systems & Cognitive Ergonomics",
            "location": "San Francisco, CA",
            "bio": "Focused on human-centered computing, enterprise design tokens, and eliminating cognitive friction in complex data workflows.",
            "avatar_url": "/uploads/avatars/usr_devon_taylor.png",
            "connections_count": 2,
            "experiences": [
                ("exp_05_1", "CanvasLogic", "Head of Product Design", "San Francisco, CA", date(2021, 8, 1), None, True, "Standardized multi-brand component design system across 4 products."),
                ("exp_05_2", "StudioEight", "Principal UI/UX Designer", "San Francisco, CA", date(2017, 5, 1), date(2021, 7, 31), False, "Led enterprise user research and high-fidelity prototyping.")
            ],
            "educations": [
                ("edu_05_1", "Stanford University", "B.A.", "Product Design & HCI", 2013, 2017)
            ],
            "skills": ["Product Design", "UI/UX", "Design Systems", "Figma", "Frontend Engineering"]
        },
        {
            "id": "usr_sarah_jenkins",
            "email": "sarah.jenkins@pronet.local",
            "full_name": "Sarah Jenkins",
            "headline": "Principal Technical Talent Partner | Executive Tech Recruiter",
            "location": "Boston, MA",
            "bio": "Connecting elite engineering leaders and specialized systems architects with venture-backed, high-growth technology companies.",
            "avatar_url": "/uploads/avatars/usr_sarah_jenkins.png",
            "connections_count": 2,
            "experiences": [
                ("exp_06_1", "Apex Executive Search", "Principal Talent Partner", "Boston, MA", date(2019, 1, 1), None, True, "Placed 65+ senior staff engineers and VP leaders in Series A-D startups."),
                ("exp_06_2", "TechTalent Global", "Senior Technical Recruiter", "Cambridge, MA", date(2015, 6, 1), date(2018, 12, 31), False, "Scaled engineering org from 15 to 140 developers in 18 months.")
            ],
            "educations": [
                ("edu_06_1", "Boston College", "B.A.", "Communications & Psychology", 2011, 2015)
            ],
            "skills": ["Technical Recruiting", "Talent Acquisition", "Executive Search", "Hiring Strategy"]
        },
        {
            "id": "usr_liam_patel",
            "email": "liam.patel@pronet.local",
            "full_name": "Liam Patel",
            "headline": "Senior Site Reliability Engineer | eBPF & Kernel Telemetry",
            "location": "Chicago, IL",
            "bio": "Obsessed with sub-millisecond network tracing, eBPF instrumentation, and bulletproof disaster recovery pipelines.",
            "avatar_url": "/uploads/avatars/usr_liam_patel.png",
            "connections_count": 2,
            "experiences": [
                ("exp_07_1", "CloudWatch Systems", "Senior SRE", "Chicago, IL", date(2021, 9, 1), None, True, "Authored eBPF probes reducing distributed tracing overhead by 80%."),
                ("exp_07_2", "Midwest Data Hub", "Systems Administrator", "Chicago, IL", date(2017, 8, 1), date(2021, 8, 31), False, "Managed high-availability bare-metal Linux clusters.")
            ],
            "educations": [
                ("edu_07_1", "University of Illinois Urbana-Champaign", "B.S.", "Computer Engineering", 2013, 2017)
            ],
            "skills": ["Linux", "Kubernetes", "Go", "eBPF", "Prometheus", "Docker"]
        },
        {
            "id": "usr_zack_kowalski",
            "email": "zack.kowalski@pronet.local",
            "full_name": "Zack Kowalski",
            "headline": "Staff Data Platform Engineer | Apache Kafka & Flink Streaming",
            "location": "Denver, CO",
            "bio": "High-throughput streaming data architectures, event-driven microservices, and exactly-once processing pipelines.",
            "avatar_url": "/uploads/avatars/usr_zack_kowalski.png",
            "connections_count": 2,
            "experiences": [
                ("exp_08_1", "StreamLine Dynamics", "Staff Data Engineer", "Denver, CO", date(2020, 11, 1), None, True, "Processed 100B daily events with real-time stream aggregation."),
                ("exp_08_2", "Rocky Mountain Analytics", "Senior Big Data Developer", "Boulder, CO", date(2016, 10, 1), date(2020, 10, 31), False, "Maintained petabyte-scale data lakes and real-time Kafka topologies.")
            ],
            "educations": [
                ("edu_08_1", "Colorado School of Mines", "B.S.", "Applied Mathematics & CS", 2012, 2016)
            ],
            "skills": ["Apache Kafka", "Flink", "Python", "SQL", "Distributed Systems"]
        },
        {
            "id": "usr_aisha_diop",
            "email": "aisha.diop@pronet.local",
            "full_name": "Aisha Diop",
            "headline": "Director of Product Management | Developer Platforms & Enterprise APIs",
            "location": "New York, NY",
            "bio": "Transforming developer experience through intuitive APIs, SDKs, and developer-first platform ecosystems.",
            "avatar_url": "/uploads/avatars/usr_aisha_diop.png",
            "connections_count": 1,
            "experiences": [
                ("exp_09_1", "APIPlatform Corp", "Director of Product", "New York, NY", date(2021, 3, 1), None, True, "Driving product roadmap for enterprise API developer tooling."),
                ("exp_09_2", "CloudServices Inc", "Senior Product Manager", "New York, NY", date(2017, 2, 1), date(2021, 2, 28), False, "Grew developer platform ecosystem from 5k to 120k monthly active developers.")
            ],
            "educations": [
                ("edu_09_1", "Harvard University", "B.A.", "Economics & Computer Science", 2012, 2016)
            ],
            "skills": ["Product Management", "API Design", "Product Strategy", "Enterprise SaaS"]
        },
        {
            "id": "usr_jordan_mendez",
            "email": "jordan.mendez@pronet.local",
            "full_name": "Jordan Mendez",
            "headline": "Cybersecurity & Identity Architect | Zero-Trust & Cryptographic Infrastructure",
            "location": "San Jose, CA",
            "bio": "Protecting critical digital assets through threat modeling, zero-trust network access, and end-to-end cryptographic key management.",
            "avatar_url": "/uploads/avatars/usr_jordan_mendez.png",
            "connections_count": 1,
            "experiences": [
                ("exp_10_1", "CyberShield Defense", "Identity Infrastructure Architect", "San Jose, CA", date(2020, 5, 1), None, True, "Deployed enterprise-wide WebAuthn and cryptographic token services."),
                ("exp_10_2", "SecureBay Networks", "Security Operations Lead", "Sunnyvale, CA", date(2016, 4, 1), date(2020, 4, 30), False, "Led penetration testing and automated vulnerability scanning programs.")
            ],
            "educations": [
                ("edu_10_1", "San Jose State University", "B.S.", "Software Engineering & Cybersecurity", 2012, 2016)
            ],
            "skills": ["Cryptography", "Identity Management", "OAuth2", "AppSec", "Linux"]
        }
    ]

    for p in personas:
        user = User(
            id=p["id"],
            email=p["email"],
            hashed_password=base_pwd_hash,
            full_name=p["full_name"],
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)

        profile = Profile(
            id=f"prf_{p['id']}",
            user_id=p["id"],
            headline=p["headline"],
            bio=p["bio"],
            location=p["location"],
            avatar_url=p["avatar_url"],
            connections_count=p["connections_count"],
            created_at=now,
            updated_at=now,
        )
        db.add(profile)

        for eid, comp, title, loc, sdate, edate, curr, desc in p["experiences"]:
            exp = Experience(
                id=eid,
                user_id=p["id"],
                company=comp,
                title=title,
                location=loc,
                start_date=sdate,
                end_date=edate,
                is_current=curr,
                description=desc,
                created_at=now,
            )
            db.add(exp)

        for eduid, inst, deg, field, syear, eyear in p["educations"]:
            edu = Education(
                id=eduid,
                user_id=p["id"],
                institution=inst,
                degree=deg,
                field_of_study=field,
                start_year=syear,
                end_year=eyear,
                created_at=now,
            )
            db.add(edu)

        for sname in p["skills"]:
            if sname in skill_entities:
                us = UserSkill(
                    id=f"us_{p['id']}_{skill_entities[sname].id}",
                    user_id=p["id"],
                    skill_id=skill_entities[sname].id,
                    created_at=now,
                )
                db.add(us)

    await db.flush()

    # --------------------------------------------------------------------------
    # 3. 15 CONNECTIONS GRAPH
    # --------------------------------------------------------------------------
    connections_blueprint = [
        ("conn_01", "usr_elena_rostova", "usr_alex_chen", "ACCEPTED", "Great collaborating on the distributed systems panel!"),
        ("conn_02", "usr_marcus_vance", "usr_elena_rostova", "ACCEPTED", "Elena, let's catch up on platform architecture."),
        ("conn_03", "usr_elena_rostova", "usr_priya_sharma", "ACCEPTED", "Excited to connect regarding the React & ASGI stack!"),
        ("conn_04", "usr_devon_taylor", "usr_elena_rostova", "ACCEPTED", "Love your insights on local-first application UI."),
        ("conn_05", "usr_alex_chen", "usr_marcus_vance", "ACCEPTED", "Marcus, would love to exchange notes on org scaling."),
        ("conn_06", "usr_liam_patel", "usr_alex_chen", "ACCEPTED", "Connecting from the SRE and Kubernetes summit."),
        ("conn_07", "usr_marcus_vance", "usr_sarah_jenkins", "ACCEPTED", "Looking forward to partnering on upcoming staff hires."),
        ("conn_08", "usr_aisha_diop", "usr_marcus_vance", "ACCEPTED", "Aligning on engineering platform requirements."),
        ("conn_09", "usr_priya_sharma", "usr_devon_taylor", "ACCEPTED", "Let's review the design token sync workflow."),
        ("conn_10", "usr_priya_sharma", "usr_zack_kowalski", "ACCEPTED", "Checking in on the streaming API frontend bridge."),
        ("conn_11", "usr_sarah_jenkins", "usr_jordan_mendez", "ACCEPTED", "Jordan, keeping you in mind for top security roles."),
        ("conn_12", "usr_zack_kowalski", "usr_liam_patel", "ACCEPTED", "Telemetry and Kafka metrics integration."),
        ("conn_13", "usr_elena_rostova", "usr_sarah_jenkins", "PENDING", "Hi Sarah, would love to connect and follow talent updates."),
        ("conn_14", "usr_aisha_diop", "usr_elena_rostova", "PENDING", "Elena, saw your post on SQLite WAL mode—let's connect!"),
        ("conn_15", "usr_jordan_mendez", "usr_devon_taylor", "IGNORED", "Let's connect regarding identity design."),
    ]

    for cid, init, recip, status, note in connections_blueprint:
        u_low = min(init, recip)
        u_high = max(init, recip)
        conn = Connection(
            id=cid,
            user_low_id=u_low,
            user_high_id=u_high,
            initiator_id=init,
            recipient_id=recip,
            status=status,
            note=note,
            created_at=now - timedelta(hours=12),
            updated_at=now - timedelta(hours=12),
        )
        db.add(conn)

    await db.flush()

    # --------------------------------------------------------------------------
    # 4. 12 RICH ACTIVITY FEED POSTS, REACTIONS & THREADED COMMENTS
    # --------------------------------------------------------------------------
    posts_data = [
        (
            "post_01", "usr_elena_rostova",
            "Why we chose SQLite in WAL mode for ProNet: Zero cloud dependencies, sub-millisecond local reads via memory mapping, and zero database locks when PRAGMA busy_timeout is set properly. Here is our async session engine setup:",
            "engine = create_async_engine('sqlite+aiosqlite:///pronet.db')\n# PRAGMA journal_mode=WAL;\n# PRAGMA busy_timeout=5000;",
            "python", None, 18, 7, 14, 4, 30
        ),
        (
            "post_02", "usr_alex_chen",
            "Production-ready zero-trust network ingress requires end-to-end cryptographic verification at the API gateway layer. Here is our typed middleware hook for Bearer token introspection:",
            "export const verifyJwtToken = (header: string): TokenPayload => {\n  const token = header.replace('Bearer ', '');\n  return jwt.verify(token, SECRET_KEY) as TokenPayload;\n};",
            "typescript", None, 12, 4, 9, 2, 28
        ),
        (
            "post_03", "usr_devon_taylor",
            "Thrilled to share our new design system tokens for ProNet! We focused on high-contrast typography, crisp borders, and subtle elevation hierarchies that eliminate visual clutter.",
            None, None, "/uploads/posts/post_devon_design.png", 24, 15, 6, 3, 26
        ),
        (
            "post_04", "usr_marcus_vance",
            "Engineering leadership is not about managing tickets; it's about engineering the environment so that talented people can ship deterministic, high-quality software without bureaucratic friction.",
            None, None, None, 31, 22, 19, 5, 24
        ),
        (
            "post_05", "usr_priya_sharma",
            "Eliminating feed re-render lag in React 18: By combining TanStack Query's optimistic updates with cursor pagination, our feed navigation remains buttery smooth at 60 FPS:",
            "const { data, fetchNextPage } = useInfiniteQuery({\n  queryKey: ['feed', mode],\n  queryFn: ({ pageParam }) => fetchFeed(mode, pageParam),\n  getNextPageParam: (lastPage) => lastPage.next_cursor,\n});",
            "typescript", None, 16, 5, 11, 2, 22
        ),
        (
            "post_06", "usr_sarah_jenkins",
            "We are officially hiring 3 Staff Backend Engineers and a Principal Cloud Architect at TechCorp! All roles are 100% remote with competitive compensation ($160k - $240k). Apply directly through our ProNet job board!",
            None, None, None, 28, 19, 8, 4, 20
        ),
        (
            "post_07", "usr_liam_patel",
            "Tracing Linux kernel network drops with eBPF: Here is a minimal program measuring socket packet latency directly inside kernel space:",
            "SEC(\"kprobe/tcp_v4_connect\")\nint kprobe_tcp_connect(struct pt_regs *ctx) {\n    u64 ts = bpf_ktime_get_ns();\n    // record timestamp\n    return 0;\n}",
            "go", None, 15, 3, 16, 3, 18
        ),
        (
            "post_08", "usr_zack_kowalski",
            "The power of recursive Common Table Expressions (CTEs) in SQLite: You don't need a heavy graph database to compute 2nd-degree social connections. A single indexed SQL self-join computes mutuals in < 8ms:",
            "WITH viewer_edges AS (\n  SELECT CASE WHEN user_low_id = ? THEN user_high_id ELSE user_low_id END AS friend_id\n  FROM connections WHERE status = 'ACCEPTED'\n)\nSELECT friend_id FROM viewer_edges;",
            "sql", None, 22, 8, 21, 4, 16
        ),
        (
            "post_09", "usr_aisha_diop",
            "Great developer products are born from ruthless simplification. If an engineer cannot understand your API contract within 60 seconds of reading your documentation, your abstractions are leaking.",
            None, None, None, 25, 11, 17, 3, 14
        ),
        (
            "post_10", "usr_jordan_mendez",
            "PSA: Passwords should never be hashed with plain SHA-256 or MD5. Bcrypt with cost factor 12 provides the right balance of security and deterministic local hashing (~250ms per hash).",
            None, None, None, 19, 6, 14, 2, 12
        ),
        (
            "post_11", "usr_elena_rostova",
            "Architecture diagram for our local-first full-duplex WebSocket direct messaging pipeline. 1st-degree connection guards are enforced at the transport handshake!",
            None, None, "/uploads/posts/post_elena_arch.png", 35, 18, 29, 6, 10
        ),
        (
            "post_12", "usr_alex_chen",
            "Infrastructure as Code (IaC) is only as good as your automated linting and plan verification in CI. Catch misconfigured security groups before they ever touch cloud APIs.",
            None, None, None, 14, 5, 8, 1, 8
        ),
    ]

    for pid, aid, cont, code, lang, img, lk, cl, ins, cmt, h_ago in posts_data:
        p_time = now - timedelta(hours=h_ago)
        post = Post(
            id=pid,
            author_id=aid,
            content=cont,
            code_snippet=code,
            code_language=lang,
            image_url=img,
            like_count=lk,
            celebrate_count=cl,
            insightful_count=ins,
            comment_count=cmt,
            created_at=p_time,
            updated_at=p_time,
        )
        db.add(post)

    await db.flush()

    # Seed comments on Post 01
    cmt_time = now - timedelta(hours=29)
    cmt_01 = Comment(
        id="cmt_01",
        post_id="post_01",
        author_id="usr_alex_chen",
        parent_id=None,
        content="The WAL concurrency model is unmatched for single-host deployments. Did you benchmark busy_timeout contention under 50 concurrent writes?",
        created_at=cmt_time,
        updated_at=cmt_time,
    )
    db.add(cmt_01)
    await db.flush()

    cmt_01_01 = Comment(
        id="cmt_01_01",
        post_id="post_01",
        author_id="usr_elena_rostova",
        parent_id="cmt_01",
        content="Yes! With synchronous=NORMAL and busy_timeout=5000ms, 50 parallel workers sustained 0 lock errors over 1,000 transactions.",
        created_at=cmt_time + timedelta(minutes=15),
        updated_at=cmt_time + timedelta(minutes=15),
    )
    db.add(cmt_01_01)

    cmt_02 = Comment(
        id="cmt_02",
        post_id="post_01",
        author_id="usr_priya_sharma",
        parent_id=None,
        content="Super clean SQLAlchemy async setup. Love how you handled the engine lifespan hooks.",
        created_at=cmt_time + timedelta(hours=1),
        updated_at=cmt_time + timedelta(hours=1),
    )
    db.add(cmt_02)
    await db.flush()

    cmt_02_01 = Comment(
        id="cmt_02_01",
        post_id="post_01",
        author_id="usr_devon_taylor",
        parent_id="cmt_02",
        content="Seconded! Makes UI testing and local prototyping effortless.",
        created_at=cmt_time + timedelta(hours=1, minutes=20),
        updated_at=cmt_time + timedelta(hours=1, minutes=20),
    )
    db.add(cmt_02_01)

    # Post Reactions for Post 01
    db.add(PostReaction(id="react_01", post_id="post_01", user_id="usr_alex_chen", reaction_type="INSIGHTFUL", created_at=now))
    db.add(PostReaction(id="react_02", post_id="post_01", user_id="usr_priya_sharma", reaction_type="CELEBRATE", created_at=now))
    db.add(PostReaction(id="react_03", post_id="post_01", user_id="usr_devon_taylor", reaction_type="LIKE", created_at=now))

    # --------------------------------------------------------------------------
    # 5. 8 JOB LISTINGS & CANDIDATE ATS PIPELINE
    # --------------------------------------------------------------------------
    jobs_blueprint = [
        ("job_01", "usr_marcus_vance", "Staff Backend Engineer (Async Systems)", "TechCorp Systems", "REMOTE", "United States", 160000, 210000, "Join our core async platform team engineering high-throughput backend services.", ["Python", "FastAPI", "SQLAlchemy", "Distributed Systems"], "OPEN", 3),
        ("job_02", "usr_sarah_jenkins", "Principal Cloud Infrastructure Architect", "CloudScale Global", "REMOTE", "Seattle, WA", 190000, 240000, "Lead multi-region Kubernetes cloud automation and zero-trust mesh ingress.", ["Kubernetes", "AWS", "Terraform", "Go"], "OPEN", 2),
        ("job_03", "usr_marcus_vance", "Senior Full-Stack Product Engineer", "Nexus Enterprise", "HYBRID", "Austin, TX", 145000, 185000, "Build user-facing enterprise workflows across React 18 and FastAPI backends.", ["React", "TypeScript", "Python", "Tailwind CSS"], "OPEN", 1),
        ("job_04", "usr_sarah_jenkins", "Staff AI / ML Systems Engineer", "DeepCognition Labs", "HYBRID", "San Francisco, CA", 180000, 235000, "Optimize inference kernels and tensor streaming runtimes for foundation models.", ["PyTorch", "Python", "C++", "Distributed Systems"], "OPEN", 1),
        ("job_05", "usr_sarah_jenkins", "Lead Site Reliability Engineer", "Apex Data Networks", "ON_SITE", "Boston, MA", 155000, 195000, "Architect 99.999% uptime bare-metal telemetry and Linux kernel observability pipelines.", ["Linux", "Kubernetes", "eBPF", "Prometheus"], "OPEN", 0),
        ("job_06", "usr_aisha_diop", "Director of Enterprise Product Management", "Horizon Platform", "REMOTE", "New York, NY", 175000, 220000, "Drive strategy and roadmaps for next-generation developer tooling platforms.", ["Product Management", "API Design", "Product Strategy", "Enterprise SaaS"], "OPEN", 1),
        ("job_07", "usr_sarah_jenkins", "Principal Security & Identity Architect", "CyberShield Defense", "ON_SITE", "San Jose, CA", 170000, 215000, "Design cryptographic authentication architectures and zero-trust identity frameworks.", ["Cryptography", "Identity Management", "OAuth2", "AppSec"], "OPEN", 0),
        ("job_08", "usr_marcus_vance", "Senior Staff Distributed Data Engineer", "StreamLine Analytics", "REMOTE", "Denver, CO", 165000, 210000, "Lead petabyte-scale event stream processing with Kafka and Flink topologies.", ["Apache Kafka", "Flink", "Python", "SQL"], "OPEN", 0),
    ]

    for jid, pid, title, comp, work, loc, smin, smax, desc, req_sk, status, app_cnt in jobs_blueprint:
        job = Job(
            id=jid,
            poster_id=pid,
            title=title,
            company_name=comp,
            workplace_type=work,
            location=loc,
            salary_min=smin,
            salary_max=smax,
            description=desc,
            required_skills=json.dumps(req_sk),
            status=status,
            application_count=app_cnt,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2),
        )
        db.add(job)

    await db.flush()

    # Candidate applications
    apps_data = [
        ("app_01", "job_01", "usr_priya_sharma", "SHORTLISTED", "Experienced in FastAPI and high-concurrency async backends.", "/uploads/resumes/priya_resume.pdf", "Lead Full-Stack Engineer | React 18 & Async Python Architecture", ["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy"]),
        ("app_02", "job_01", "usr_zack_kowalski", "REVIEWING", "Passionate about high-throughput streaming systems.", "/uploads/resumes/zack_resume.pdf", "Staff Data Platform Engineer | Apache Kafka & Flink Streaming", ["Python", "Apache Kafka", "SQL", "Distributed Systems"]),
        ("app_03", "job_01", "usr_jordan_mendez", "APPLIED", "Bringing identity security to backend services.", "/uploads/resumes/jordan_resume.pdf", "Cybersecurity & Identity Architect | Zero-Trust & Cryptographic Infrastructure", ["Cryptography", "Identity Management", "Linux"]),
        ("app_04", "job_02", "usr_alex_chen", "SHORTLISTED", "Over 8 years scaling multi-tenant Kubernetes clusters.", "/uploads/resumes/alex_resume.pdf", "Principal Cloud Infrastructure Architect | Kubernetes & High-Resilience Systems", ["Kubernetes", "AWS", "Terraform", "Go"]),
        ("app_05", "job_02", "usr_liam_patel", "REVIEWING", "Specialized in SRE and eBPF observability.", "/uploads/resumes/liam_resume.pdf", "Senior Site Reliability Engineer | eBPF & Kernel Telemetry", ["Linux", "Kubernetes", "Go", "eBPF"]),
        ("app_06", "job_04", "usr_elena_rostova", "SHORTLISTED", "Excited to bring low-latency inference architectures to DeepCognition.", "/uploads/resumes/elena_resume.pdf", "Staff AI Systems Engineer | Distributed LLM Training & Kernel Optimization", ["Python", "Distributed Systems", "PyTorch", "C++", "FastAPI"]),
        ("app_07", "job_03", "usr_priya_sharma", "APPLIED", "Love building design systems and React SPAs.", "/uploads/resumes/priya_resume.pdf", "Lead Full-Stack Engineer | React 18 & Async Python Architecture", ["React", "TypeScript", "Tailwind CSS", "Python"]),
        ("app_08", "job_06", "usr_devon_taylor", "REJECTED", "Transitioning product design leadership to enterprise product strategy.", "/uploads/resumes/devon_resume.pdf", "Head of Product Design | Design Systems & Cognitive Ergonomics", ["Product Design", "Product Strategy", "UI/UX"]),
    ]

    for aid, jid, app_id, st, note, res_url, head, sk_list in apps_data:
        app = JobApplication(
            id=aid,
            job_id=jid,
            applicant_id=app_id,
            status=st,
            cover_note=note,
            resume_url=res_url,
            profile_headline_snapshot=head,
            skills_snapshot=json.dumps(sk_list),
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        )
        db.add(app)

    # --------------------------------------------------------------------------
    # 6. SEED DIRECT MESSAGES & NOTIFICATIONS
    # --------------------------------------------------------------------------
    # Conversation between Elena and Alex
    msg_01 = Message(
        id="msg_101",
        sender_id="usr_alex_chen",
        recipient_id="usr_elena_rostova",
        content="Hey Elena, let me know when you review the WAL benchmark results.",
        read_at=None,
        created_at=now - timedelta(minutes=45),
    )
    msg_02 = Message(
        id="msg_102",
        sender_id="usr_elena_rostova",
        recipient_id="usr_alex_chen",
        content="Just checked it! The p95 latency is down to 42ms. Incredible work.",
        read_at=now - timedelta(minutes=30),
        created_at=now - timedelta(minutes=35),
    )
    db.add(msg_01)
    db.add(msg_02)

    # Notifications for Elena
    notif_01 = Notification(
        id="notif_01",
        user_id="usr_elena_rostova",
        actor_id="usr_aisha_diop",
        notification_type="CONNECTION_REQUEST",
        title="Connection Request",
        content="Aisha Diop sent you a connection request.",
        reference_id="conn_14",
        reference_type="CONNECTION",
        is_read=False,
        created_at=now - timedelta(hours=1),
    )
    notif_02 = Notification(
        id="notif_02",
        user_id="usr_elena_rostova",
        actor_id="usr_priya_sharma",
        notification_type="POST_REACTION",
        title="New Reaction",
        content="Priya Sharma celebrated your post.",
        reference_id="post_01",
        reference_type="POST",
        is_read=False,
        created_at=now - timedelta(hours=2),
    )
    notif_03 = Notification(
        id="notif_03",
        user_id="usr_elena_rostova",
        actor_id="usr_alex_chen",
        notification_type="POST_COMMENT",
        title="New Comment",
        content="Alex Chen commented on your post.",
        reference_id="post_01",
        reference_type="POST",
        is_read=True,
        created_at=now - timedelta(hours=3),
    )
    db.add(notif_01)
    db.add(notif_02)
    db.add(notif_03)

    await db.commit()
    logger.info("Deterministic database seeding complete in single atomic transaction.")
    return True
