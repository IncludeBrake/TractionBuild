"""
SQLite-based budget store with ACID compliance and audit trail.
Provides robust usage tracking and cost control for LLM operations.
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class UsageRecord:
    """Usage record for LLM operations."""
    id: Optional[int] = None
    scope: str = ""
    model: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    is_cache_hit: bool = False
    provider: str = ""
    created_at: Optional[str] = None
    source: str = "api"  # api, import, migration
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BudgetStore:
    """SQLite-based budget store with ACID compliance."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the budget store."""
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', '..', 'data', 'budget.db'
            )
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Migrate existing JSON data if present
        self._migrate_json_data()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for ACID
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety vs performance
        conn.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        return conn
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            # Usage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_input INTEGER NOT NULL DEFAULT 0,
                    tokens_output INTEGER NOT NULL DEFAULT 0,
                    cost_usd REAL NOT NULL DEFAULT 0.0,
                    is_cache_hit BOOLEAN NOT NULL DEFAULT 0,
                    provider TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'api',
                    UNIQUE(scope, model, created_at, source)
                )
            """)
            
            # Rate limiting table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit (
                    scope TEXT NOT NULL,
                    ts_utc TEXT NOT NULL,
                    tokens INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (scope, ts_utc)
                )
            """)
            
            # Audit table for tamper evidence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_utc TEXT NOT NULL,
                    event TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    sha_prev TEXT NOT NULL,
                    sha_curr TEXT NOT NULL
                )
            """)
            
            # Budget configuration table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budget_config (
                    scope TEXT PRIMARY KEY,
                    daily_budget_usd REAL NOT NULL DEFAULT 10.0,
                    monthly_budget_usd REAL NOT NULL DEFAULT 100.0,
                    rate_limit_tokens_per_minute INTEGER NOT NULL DEFAULT 10000,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_scope_created ON usage(scope, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_model_created ON usage(model, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_scope_ts ON rate_limit(scope, ts_utc)")
            
            conn.commit()
    
    def _migrate_json_data(self):
        """Migrate existing JSON usage data to SQLite."""
        json_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'data', 'token_usage.json'
        )
        
        if not os.path.exists(json_path):
            return
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            migrated_count = 0
            with self._get_connection() as conn:
                for date, usage_data in data.items():
                    # Parse the date
                    try:
                        dt = datetime.strptime(date, "%Y-%m-%d")
                        created_at = dt.isoformat()
                    except ValueError:
                        logger.warning(f"Invalid date format in JSON: {date}")
                        continue
                    
                    # Insert usage records
                    conn.execute("""
                        INSERT OR IGNORE INTO usage 
                        (scope, model, tokens_input, tokens_output, cost_usd, is_cache_hit, 
                         provider, created_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "global",  # Default scope for migrated data
                        "unknown",
                        usage_data.get("tokens_used", 0),
                        0,  # Assume all tokens are input for migrated data
                        usage_data.get("cost_usd", 0.0),
                        False,
                        "unknown",
                        created_at,
                        "import"
                    ))
                    migrated_count += 1
                
                conn.commit()
            
            logger.info(f"Migrated {migrated_count} usage records from JSON to SQLite")
            
            # Backup the original JSON file
            backup_path = json_path + ".backup"
            os.rename(json_path, backup_path)
            logger.info(f"Backed up original JSON to {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to migrate JSON data: {e}")
    
    def record_usage(self, record: UsageRecord) -> bool:
        """
        Record usage and check budget limits.
        
        Args:
            record: UsageRecord to insert
            
        Returns:
            True if within budget, False if budget exceeded
        """
        if not record.created_at:
            record.created_at = datetime.now(timezone.utc).isoformat()
        
        try:
            with self._get_connection() as conn:
                # Check budget before inserting
                if not self._check_budget(conn, record.scope, record.cost_usd):
                    return False
                
                # Insert usage record
                conn.execute("""
                    INSERT INTO usage 
                    (scope, model, tokens_input, tokens_output, cost_usd, is_cache_hit, 
                     provider, created_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.scope, record.model, record.tokens_input, record.tokens_output,
                    record.cost_usd, record.is_cache_hit, record.provider, 
                    record.created_at, record.source
                ))
                
                # Record audit event
                self._audit_event(conn, "usage_recorded", {
                    "scope": record.scope,
                    "model": record.model,
                    "cost_usd": record.cost_usd,
                    "is_cache_hit": record.is_cache_hit
                })
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate usage record: {e}")
            return True  # Assume it's a duplicate, not a budget breach
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return False
    
    def _check_budget(self, conn: sqlite3.Connection, scope: str, cost_usd: float) -> bool:
        """Check if the operation would exceed budget limits."""
        # Get budget configuration
        conn.execute("""
            INSERT OR IGNORE INTO budget_config (scope, daily_budget_usd, monthly_budget_usd, 
                                                rate_limit_tokens_per_minute, created_at, updated_at)
            VALUES (?, 10.0, 100.0, 10000, ?, ?)
        """, (scope, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()))
        
        config = conn.execute("""
            SELECT daily_budget_usd, monthly_budget_usd FROM budget_config WHERE scope = ?
        """, (scope,)).fetchone()
        
        if not config:
            return True  # No budget configured, allow
        
        daily_budget, monthly_budget = config
        
        # Check daily budget
        today = datetime.now(timezone.utc).date().isoformat()
        daily_usage = conn.execute("""
            SELECT COALESCE(SUM(cost_usd), 0) FROM usage 
            WHERE scope = ? AND date(created_at) = ?
        """, (scope, today)).fetchone()[0]
        
        if daily_usage + cost_usd > daily_budget:
            logger.warning(f"Daily budget exceeded for {scope}: ${daily_usage + cost_usd:.2f} > ${daily_budget}")
            return False
        
        # Check monthly budget
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        monthly_usage = conn.execute("""
            SELECT COALESCE(SUM(cost_usd), 0) FROM usage 
            WHERE scope = ? AND strftime('%Y-%m', created_at) = ?
        """, (scope, month)).fetchone()[0]
        
        if monthly_usage + cost_usd > monthly_budget:
            logger.warning(f"Monthly budget exceeded for {scope}: ${monthly_usage + cost_usd:.2f} > ${monthly_budget}")
            return False
        
        return True
    
    def _audit_event(self, conn: sqlite3.Connection, event: str, meta: Dict[str, Any]):
        """Record an audit event with tamper evidence."""
        meta_json = json.dumps(meta, sort_keys=True)
        ts_utc = datetime.now(timezone.utc).isoformat()
        
        # Get previous hash
        prev_hash = conn.execute("""
            SELECT sha_curr FROM audit ORDER BY id DESC LIMIT 1
        """).fetchone()
        
        sha_prev = prev_hash[0] if prev_hash else "0" * 64
        
        # Calculate current hash
        row_data = f"{ts_utc}:{event}:{meta_json}:{sha_prev}"
        sha_curr = hashlib.sha256(row_data.encode()).hexdigest()
        
        conn.execute("""
            INSERT INTO audit (ts_utc, event, meta_json, sha_prev, sha_curr)
            VALUES (?, ?, ?, ?, ?)
        """, (ts_utc, event, meta_json, sha_prev, sha_curr))
    
    def get_usage_summary(self, scope: str = "global") -> Dict[str, Any]:
        """Get usage summary for a scope."""
        with self._get_connection() as conn:
            today = datetime.now(timezone.utc).date().isoformat()
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            
            # Get daily usage
            daily_usage = conn.execute("""
                SELECT 
                    COALESCE(SUM(tokens_input + tokens_output), 0) as tokens_used,
                    COALESCE(SUM(cost_usd), 0) as cost_usd,
                    COUNT(*) as requests_made,
                    SUM(CASE WHEN is_cache_hit THEN 1 ELSE 0 END) as cache_hits
                FROM usage 
                WHERE scope = ? AND date(created_at) = ?
            """, (scope, today)).fetchone()
            
            # Get monthly usage
            monthly_usage = conn.execute("""
                SELECT 
                    COALESCE(SUM(tokens_input + tokens_output), 0) as tokens_used,
                    COALESCE(SUM(cost_usd), 0) as cost_usd,
                    COUNT(*) as requests_made,
                    SUM(CASE WHEN is_cache_hit THEN 1 ELSE 0 END) as cache_hits
                FROM usage 
                WHERE scope = ? AND strftime('%Y-%m', created_at) = ?
            """, (scope, month)).fetchone()
            
            # Get budget configuration
            config = conn.execute("""
                SELECT daily_budget_usd, monthly_budget_usd FROM budget_config WHERE scope = ?
            """, (scope,)).fetchone()
            
            daily_budget = config[0] if config else 10.0
            monthly_budget = config[1] if config else 100.0
            
            return {
                "today": {
                    "tokens_used": daily_usage[0],
                    "cost_usd": daily_usage[1],
                    "requests_made": daily_usage[2],
                    "cache_hits": daily_usage[3],
                    "budget_remaining": max(0, daily_budget - daily_usage[1])
                },
                "month": {
                    "tokens_used": monthly_usage[0],
                    "cost_usd": monthly_usage[1],
                    "requests_made": monthly_usage[2],
                    "cache_hits": monthly_usage[3],
                    "budget_remaining": max(0, monthly_budget - monthly_usage[1])
                },
                "budgets": {
                    "daily_usd": daily_budget,
                    "monthly_usd": monthly_budget
                }
            }
    
    def reset_usage(self, scope: str = "global", period: str = "today"):
        """Reset usage for a scope and period."""
        with self._get_connection() as conn:
            if period == "today":
                today = datetime.now(timezone.utc).date().isoformat()
                conn.execute("""
                    DELETE FROM usage WHERE scope = ? AND date(created_at) = ?
                """, (scope, today))
            elif period == "month":
                month = datetime.now(timezone.utc).strftime("%Y-%m")
                conn.execute("""
                    DELETE FROM usage WHERE scope = ? AND strftime('%Y-%m', created_at) = ?
                """, (scope, month))
            
            self._audit_event(conn, "usage_reset", {"scope": scope, "period": period})
            conn.commit()
            logger.info(f"Reset usage for {scope} ({period})")

# Global instance
budget_store = BudgetStore()
