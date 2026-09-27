"""Neo4j graph correlation — optional dependency.
If Neo4j driver is not installed or server is unavailable, all functions
return empty/no-op gracefully so the rest of the app still works."""

import logging

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False
    logger.info("neo4j driver not installed — graph correlation features disabled.")

from app.config import settings

_driver = None


def get_driver():
    global _driver
    if not _NEO4J_AVAILABLE:
        return None
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def ensure_constraints():
    driver = get_driver()
    if driver is None:
        return
    with driver.session() as session:
        session.run("CREATE CONSTRAINT email_case_id IF NOT EXISTS FOR (e:Email) REQUIRE e.case_id IS UNIQUE")
        session.run("CREATE CONSTRAINT domain_value IF NOT EXISTS FOR (d:Domain) REQUIRE d.value IS UNIQUE")
        session.run("CREATE CONSTRAINT ip_value IF NOT EXISTS FOR (i:IP) REQUIRE i.value IS UNIQUE")
        session.run("CREATE CONSTRAINT url_value IF NOT EXISTS FOR (u:URL) REQUIRE u.value IS UNIQUE")


def upsert_case_graph(case_id: str, subject: str, sender_domain: str, risk_score: float,
                       verdict: str, ips: list, domains: list, urls: list):
    driver = get_driver()
    if driver is None:
        return
    with driver.session() as session:
        session.run(
            """
            MERGE (e:Email {case_id: $case_id})
            SET e.subject = $subject, e.sender_domain = $sender_domain,
                e.risk_score = $risk_score, e.verdict = $verdict
            """,
            case_id=case_id, subject=subject, sender_domain=sender_domain,
            risk_score=risk_score, verdict=verdict,
        )
        if sender_domain:
            session.run(
                """
                MERGE (d:Domain {value: $domain})
                WITH d
                MATCH (e:Email {case_id: $case_id})
                MERGE (e)-[:SENT_FROM_DOMAIN]->(d)
                """,
                domain=sender_domain, case_id=case_id,
            )
        for ip in ips:
            session.run(
                """
                MERGE (i:IP {value: $ip})
                WITH i
                MATCH (e:Email {case_id: $case_id})
                MERGE (e)-[:ORIGINATED_FROM]->(i)
                """,
                ip=ip, case_id=case_id,
            )
        for domain in domains:
            session.run(
                """
                MERGE (d:Domain {value: $domain})
                WITH d
                MATCH (e:Email {case_id: $case_id})
                MERGE (e)-[:REFERENCES_DOMAIN]->(d)
                """,
                domain=domain, case_id=case_id,
            )
        for url in urls:
            session.run(
                """
                MERGE (u:URL {value: $url})
                WITH u
                MATCH (e:Email {case_id: $case_id})
                MERGE (e)-[:CONTAINS_URL]->(u)
                """,
                url=url, case_id=case_id,
            )


def find_related_cases(case_id: str) -> list:
    """Cases that share at least one IP, domain, or URL with this case —
    this is the 'campaign correlation' the slides describe."""
    driver = get_driver()
    if driver is None:
        return []
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e1:Email {case_id: $case_id})-[]->(shared)<-[]-(e2:Email)
            WHERE e2.case_id <> $case_id
            RETURN DISTINCT e2.case_id AS case_id, e2.subject AS subject,
                   e2.verdict AS verdict, e2.risk_score AS risk_score,
                   labels(shared)[0] AS shared_type, shared.value AS shared_value
            LIMIT 50
            """,
            case_id=case_id,
        )
        return [dict(r) for r in result]


def get_case_subgraph(case_id: str) -> dict:
    """Nodes/edges for the given case, for the frontend graph view."""
    driver = get_driver()
    if driver is None:
        return {"nodes": [], "edges": []}
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Email {case_id: $case_id})-[r]->(n)
            RETURN e, r, n
            """,
            case_id=case_id,
        )
        nodes = {}
        edges = []
        for record in result:
            e = record["e"]
            n = record["n"]
            r = record["r"]
            e_id = f"email:{e['case_id']}"
            nodes[e_id] = {"id": e_id, "label": e.get("subject", "email")[:40], "type": "Email"}
            n_type = list(n.labels)[0]
            n_id = f"{n_type.lower()}:{n.get('value')}"
            nodes[n_id] = {"id": n_id, "label": n.get("value"), "type": n_type}
            edges.append({"source": e_id, "target": n_id, "type": r.type})
        return {"nodes": list(nodes.values()), "edges": edges}
