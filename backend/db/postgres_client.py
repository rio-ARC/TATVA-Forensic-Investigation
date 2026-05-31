"""
Supabase PostgreSQL client for TATVA Forensic Investigation.

Stores persistent user data:
  - Cases (investigation metadata)
  - Investigation notes / annotations
  - Evidence upload records
  - Query / search history
  - Audit log of user actions
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, Column, String, Text, Float, DateTime,
    Integer, JSON, Boolean, ForeignKey, UniqueConstraint, text
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("SUPABASE_DB_URL", "")

if not DATABASE_URL:
    print("[PostgreSQL] WARNING: SUPABASE_DB_URL not set in .env")

# ── SQLAlchemy Setup ──────────────────────────────────────────
Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


# ── ORM Models ────────────────────────────────────────────────

class Case(Base):
    """A forensic investigation case."""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    investigator = Column(String(128), default="")
    status = Column(String(32), default="open")  # open, in_progress, closed
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    metadata_json = Column(JSON, default=dict)

    # Relationships
    notes = relationship("Note", back_populates="case", cascade="all, delete-orphan")
    evidence_files = relationship("EvidenceFile", back_populates="case", cascade="all, delete-orphan")
    queries = relationship("QueryLog", back_populates="case", cascade="all, delete-orphan")


class Note(Base):
    """Investigation notes / annotations attached to a case."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    author = Column(String(128), default="system")
    content = Column(Text, nullable=False)
    entity_ref = Column(String(128), default=None)  # optional link to a graph entity
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    case = relationship("Case", back_populates="notes")


class EvidenceFile(Base):
    """Record of an uploaded / processed evidence file."""
    __tablename__ = "evidence_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(64), default="csv")  # csv, json, image, pdf
    file_hash = Column(String(128), default="")
    record_count = Column(Integer, default=0)
    status = Column(String(32), default="uploaded")  # uploaded, processing, processed, error
    processed_at = Column(DateTime(timezone=True), default=None)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    metadata_json = Column(JSON, default=dict)

    case = relationship("Case", back_populates="evidence_files")
    raw_content = relationship(
        "RawEvidenceContent",
        back_populates="evidence",
        uselist=False,
        cascade="all, delete-orphan",
    )


class RawEvidenceContent(Base):
    """Raw user-uploaded evidence content stored in Supabase PostgreSQL."""
    __tablename__ = "raw_evidence_contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_id = Column(Integer, ForeignKey("evidence_files.id"), nullable=False, unique=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(64), default="")
    content_encoding = Column(String(32), default="utf-8")
    content_text = Column(Text, nullable=False)
    file_hash = Column(String(128), default="")
    size_bytes = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    evidence = relationship("EvidenceFile", back_populates="raw_content")


class QueryLog(Base):
    """Log of user queries / searches against the knowledge graph."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(64), default="search")  # search, cypher, filter, insight
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    user = Column(String(128), default="analyst")

    case = relationship("Case", back_populates="queries")


class AuditLog(Base):
    """Audit trail of important system actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(128), nullable=False)  # e.g. "case_created", "evidence_uploaded", "graph_imported"
    entity_type = Column(String(64), default="")  # e.g. "case", "note", "evidence"
    entity_id = Column(String(128), default="")
    user = Column(String(128), default="system")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class EntityAssessment(Base):
    """
    Investigator assessment of a graph entity.
    Stored ONLY in PostgreSQL — Neo4j data is never modified.
    Supports: ACTIVE | CLEARED | PERSON_OF_INTEREST | PRIORITY_TARGET
    """
    __tablename__ = "entity_assessments"
    __table_args__ = (
        UniqueConstraint("case_id", "entity_id", name="uq_entity_assessment"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE | CLEARED | PERSON_OF_INTEREST | PRIORITY_TARGET
    reason = Column(Text, default=None)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ── Client Class ──────────────────────────────────────────────

class PostgresClient:
    """Manages the Supabase PostgreSQL connection and table operations."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = None
        self.Session = None
        self._connect()

    def _connect(self):
        if not self.db_url:
            print("[PostgreSQL] No database URL configured. Falling back to SQLite.")
            self._fallback_to_sqlite()
            return

        try:
            self.engine = create_engine(
                self.db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # auto-reconnect on stale connections
                connect_args={"options": "-c timezone=utc"}
            )
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.Session = sessionmaker(bind=self.engine)
            print(f"[PostgreSQL] Connected to Supabase successfully.")
        except Exception as e:
            print(f"[PostgreSQL] Connection failed: {e}")
            self._fallback_to_sqlite()

    def _fallback_to_sqlite(self):
        try:
            db_path = Path(__file__).parent.parent / "tatva_local.db"
            self.db_url = f"sqlite:///{db_path}"
            self.engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False}
            )
            self.Session = sessionmaker(bind=self.engine)
            print(f"[SQLite] Falling back to local SQLite database: {db_path}")
        except Exception as ex:
            print(f"[SQLite] Local fallback initialization failed: {ex}")
            self.engine = None
            self.Session = None

    def create_tables(self):
        """Create all tables if they don't exist."""
        if not self.engine:
            print("[PostgreSQL] No engine available.")
            return False
        Base.metadata.create_all(self.engine)
        print("[PostgreSQL] All tables created / verified.")
        return True

    def get_session(self):
        """Return a new SQLAlchemy session."""
        if not self.Session:
            raise RuntimeError("PostgreSQL client is not connected.")
        return self.Session()

    # ── Case Operations ───────────────────────────────────────

    def create_case(self, case_id: str, title: str, description: str = "",
                    investigator: str = "", metadata: dict = None) -> dict:
        session = self.get_session()
        try:
            case = Case(
                case_id=case_id, title=title, description=description,
                investigator=investigator, metadata_json=metadata or {}
            )
            session.add(case)
            session.commit()
            self._audit(session, "case_created", "case", case_id, details={"title": title})
            session.commit()
            print(f"[PostgreSQL] Case '{case_id}' created.")
            return {"case_id": case_id, "title": title, "status": "open"}
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error creating case: {e}")
            raise
        finally:
            session.close()

    def list_cases(self, status: str = None) -> list:
        session = self.get_session()
        try:
            query = session.query(Case)
            if status:
                query = query.filter(Case.status == status)
            cases = query.order_by(Case.created_at.desc()).all()
            return [
                {
                    "case_id": c.case_id, "title": c.title,
                    "status": c.status, "investigator": c.investigator,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in cases
            ]
        finally:
            session.close()

    def get_case(self, case_id: str) -> dict | None:
        session = self.get_session()
        try:
            case = session.query(Case).filter(Case.case_id == case_id).first()
            if not case:
                return None
            return {
                "case_id": case.case_id, "title": case.title,
                "description": case.description, "status": case.status,
                "investigator": case.investigator,
                "metadata": case.metadata_json,
                "created_at": case.created_at.isoformat() if case.created_at else None,
                "updated_at": case.updated_at.isoformat() if case.updated_at else None,
                "note_count": len(case.notes),
                "evidence_count": len(case.evidence_files),
            }
        finally:
            session.close()

    def update_case_status(self, case_id: str, status: str) -> bool:
        session = self.get_session()
        try:
            case = session.query(Case).filter(Case.case_id == case_id).first()
            if not case:
                return False
            case.status = status
            self._audit(session, "case_status_updated", "case", case_id, details={"new_status": status})
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error updating case: {e}")
            return False
        finally:
            session.close()

    # ── Note Operations ───────────────────────────────────────

    def add_note(self, case_id: str, content: str, author: str = "analyst",
                 entity_ref: str = None, tags: list = None) -> dict:
        session = self.get_session()
        try:
            note = Note(
                case_id=case_id, content=content, author=author,
                entity_ref=entity_ref, tags=tags or []
            )
            session.add(note)
            self._audit(session, "note_added", "note", str(note.id), details={"case_id": case_id})
            session.commit()
            return {"id": note.id, "case_id": case_id, "content": content}
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error adding note: {e}")
            raise
        finally:
            session.close()

    def get_notes(self, case_id: str) -> list:
        session = self.get_session()
        try:
            notes = session.query(Note).filter(Note.case_id == case_id)\
                .order_by(Note.created_at.desc()).all()
            return [
                {
                    "id": n.id, "content": n.content, "author": n.author,
                    "entity_ref": n.entity_ref, "tags": n.tags,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                }
                for n in notes
            ]
        finally:
            session.close()

    # ── Evidence File Operations ──────────────────────────────

    def add_evidence(self, case_id: str, filename: str, file_type: str = "csv",
                     file_hash: str = "", record_count: int = 0, metadata: dict = None) -> dict:
        session = self.get_session()
        try:
            ev = EvidenceFile(
                case_id=case_id, filename=filename, file_type=file_type,
                file_hash=file_hash, record_count=record_count,
                metadata_json=metadata or {}
            )
            session.add(ev)
            self._audit(session, "evidence_uploaded", "evidence", filename,
                        details={"case_id": case_id, "type": file_type})
            session.commit()
            return {"id": ev.id, "filename": filename, "status": "uploaded"}
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error adding evidence: {e}")
            raise
        finally:
            session.close()

    def update_evidence_status(self, evidence_id: int, status: str, record_count: int = None):
        session = self.get_session()
        try:
            ev = session.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
            if ev:
                ev.status = status
                if record_count is not None:
                    ev.record_count = record_count
                if status == "processed":
                    ev.processed_at = _utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error updating evidence: {e}")
        finally:
            session.close()

    def add_raw_evidence_content(
        self,
        evidence_id: int,
        case_id: str,
        filename: str,
        file_type: str,
        content_text: str,
        content_encoding: str,
        file_hash: str,
        size_bytes: int,
        metadata: dict = None,
    ) -> dict:
        """Store raw uploaded evidence content in Supabase."""
        session = self.get_session()
        try:
            row = session.query(RawEvidenceContent)\
                .filter(RawEvidenceContent.evidence_id == evidence_id).first()
            if not row:
                row = RawEvidenceContent(
                    evidence_id=evidence_id,
                    case_id=case_id,
                    filename=filename,
                    file_type=file_type,
                )
                session.add(row)

            row.content_encoding = content_encoding
            row.content_text = content_text
            row.file_hash = file_hash
            row.size_bytes = size_bytes
            row.metadata_json = metadata or {}

            self._audit(
                session,
                "raw_evidence_stored",
                "evidence",
                str(evidence_id),
                details={
                    "case_id": case_id,
                    "filename": filename,
                    "file_type": file_type,
                    "encoding": content_encoding,
                    "size_bytes": size_bytes,
                },
            )
            session.commit()
            return {
                "id": row.id,
                "evidence_id": evidence_id,
                "filename": filename,
                "content_encoding": content_encoding,
                "size_bytes": size_bytes,
                "status": "stored",
            }
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error storing raw evidence content: {e}")
            raise
        finally:
            session.close()

    def get_evidence(self, case_id: str) -> list:
        session = self.get_session()
        try:
            files = session.query(EvidenceFile).filter(EvidenceFile.case_id == case_id)\
                .order_by(EvidenceFile.created_at.desc()).all()
            return [
                {
                    "id": f.id, "filename": f.filename, "file_type": f.file_type,
                    "status": f.status, "record_count": f.record_count,
                    "raw_stored": f.raw_content is not None,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "processed_at": f.processed_at.isoformat() if f.processed_at else None,
                }
                for f in files
            ]
        finally:
            session.close()

    # ── Query Log Operations ──────────────────────────────────

    def log_query(self, query_text: str, query_type: str = "search",
                  result_count: int = 0, execution_time_ms: float = 0.0,
                  case_id: str = None, user: str = "analyst") -> dict:
        session = self.get_session()
        try:
            ql = QueryLog(
                case_id=case_id, query_text=query_text, query_type=query_type,
                result_count=result_count, execution_time_ms=execution_time_ms,
                user=user
            )
            session.add(ql)
            session.commit()
            return {"id": ql.id, "query": query_text, "results": result_count}
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error logging query: {e}")
            return {}
        finally:
            session.close()

    def get_query_history(self, case_id: str = None, limit: int = 50) -> list:
        session = self.get_session()
        try:
            query = session.query(QueryLog)
            if case_id:
                query = query.filter(QueryLog.case_id == case_id)
            logs = query.order_by(QueryLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": q.id, "query": q.query_text, "type": q.query_type,
                    "results": q.result_count, "time_ms": q.execution_time_ms,
                    "user": q.user,
                    "created_at": q.created_at.isoformat() if q.created_at else None
                }
                for q in logs
            ]
        finally:
            session.close()

    # ── Audit Log ─────────────────────────────────────────────

    def _audit(self, session, action: str, entity_type: str = "",
               entity_id: str = "", user: str = "system", details: dict = None):
        log = AuditLog(
            action=action, entity_type=entity_type, entity_id=entity_id,
            user=user, details=details or {}
        )
        session.add(log)

    def get_audit_log(self, limit: int = 100) -> list:
        session = self.get_session()
        try:
            logs = session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "action": l.action, "entity_type": l.entity_type,
                    "entity_id": l.entity_id, "user": l.user,
                    "details": l.details,
                    "created_at": l.created_at.isoformat() if l.created_at else None
                }
                for l in logs
            ]
        finally:
            session.close()

    # ── Entity Assessment Operations ──────────────────────────

    def upsert_entity_assessment(self, case_id: str, entity_id: str,
                                  status: str, reason: str = None) -> dict:
        """
        Insert or update an investigator assessment for a graph entity.
        Upserts by (case_id, entity_id) — one assessment per entity per case.
        Does NOT touch Neo4j or master_entities.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(EntityAssessment)
                .filter(
                    EntityAssessment.case_id == case_id,
                    EntityAssessment.entity_id == entity_id,
                )
                .first()
            )
            if existing:
                existing.status = status
                existing.reason = reason
                existing.updated_at = _utcnow()
            else:
                existing = EntityAssessment(
                    case_id=case_id,
                    entity_id=entity_id,
                    status=status,
                    reason=reason,
                )
                session.add(existing)
            session.commit()
            return {
                "case_id": case_id,
                "entity_id": entity_id,
                "status": status,
                "reason": reason,
                "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
            }
        except Exception as e:
            session.rollback()
            print(f"[PostgreSQL] Error upserting entity assessment: {e}")
            raise
        finally:
            session.close()

    def get_entity_assessments(self, case_id: str) -> dict:
        """
        Return all assessments for a case as a dict keyed by entity_id.
        Example: { "P001": { "status": "CLEARED", "reason": "Verified alibi" } }
        """
        session = self.get_session()
        try:
            rows = (
                session.query(EntityAssessment)
                .filter(EntityAssessment.case_id == case_id)
                .all()
            )
            return {
                r.entity_id: {
                    "status": r.status,
                    "reason": r.reason,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            }
        finally:
            session.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
            print("[PostgreSQL] Connection pool closed.")


# ── Standalone Test ───────────────────────────────────────────
if __name__ == "__main__":
    client = PostgresClient()
    if client.engine:
        client.create_tables()
        print("\n[PostgreSQL] Schema ready. Tables:")
        from sqlalchemy import inspect
        inspector = inspect(client.engine)
        for table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            print(f"  -> {table}: {cols}")
        client.close()
