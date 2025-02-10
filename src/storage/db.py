"""Database management module."""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and operations."""

    def __init__(self, db_path: str = "data/worksheets.db"):
        """Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._ensure_data_dir()
        self.initialize_database()

    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection.

        Raises:
            sqlite3.Error: If connection fails.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def initialize_database(self) -> None:
        """Initialize database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create worksheets table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS worksheets (
                    id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    data BLOB NOT NULL,
                    template_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    graded_at TIMESTAMP,
                    grade TEXT,
                    total_correct INTEGER,
                    total_questions INTEGER
                )
            """
            )

            # Create ROI templates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS roi_templates (
                    id TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create problems table for better querying
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worksheet_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    student_answer TEXT,
                    confidence REAL,
                    roi_x1 INTEGER,
                    roi_y1 INTEGER,
                    roi_x2 INTEGER,
                    roi_y2 INTEGER,
                    FOREIGN KEY (worksheet_id) REFERENCES worksheets(id)
                )
            """
            )

    def save_worksheet(
        self,
        worksheet_id: str,
        version: str,
        data: bytes,
        template_id: str,
        grade: Optional[str] = None,
        total_correct: Optional[int] = None,
        total_questions: Optional[int] = None,
    ) -> None:
        """Save worksheet data to database.

        Args:
            worksheet_id: Unique identifier for worksheet.
            version: Version string.
            data: Serialized worksheet data.
            template_id: ID of ROI template used.
            grade: Optional grade (if graded).
            total_correct: Optional count of correct answers.
            total_questions: Optional total number of questions.

        Raises:
            sqlite3.Error: If database operation fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO worksheets 
                (id, version, data, template_id, grade, total_correct, total_questions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    worksheet_id,
                    version,
                    data,
                    template_id,
                    grade,
                    total_correct,
                    total_questions,
                ),
            )

    def fetch_worksheet(
        self, worksheet_id: str, version: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch worksheet data from database.

        Args:
            worksheet_id: Unique identifier for worksheet.
            version: Version string.

        Returns:
            Dictionary containing worksheet data if found, None otherwise.

        Raises:
            sqlite3.Error: If database operation fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM worksheets 
                WHERE id = ? AND version = ?
                """,
                (worksheet_id, version),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_roi_template(self, template_id: str, rois: bytes) -> None:
        """Save ROI template to database.

        Args:
            template_id: Unique identifier for template.
            rois: Serialized ROI data.

        Raises:
            sqlite3.Error: If database operation fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO roi_templates (id, data)
                VALUES (?, ?)
                """,
                (template_id, rois),
            )

    def fetch_roi_template(self, template_id: str) -> Optional[bytes]:
        """Fetch ROI template from database.

        Args:
            template_id: Unique identifier for template.

        Returns:
            Serialized ROI data if found, None otherwise.

        Raises:
            sqlite3.Error: If database operation fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM roi_templates WHERE id = ?", (template_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def get_worksheet_statistics(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about graded worksheets.

        Args:
            start_date: Optional start date for filtering (YYYY-MM-DD).
            end_date: Optional end date for filtering (YYYY-MM-DD).

        Returns:
            Dictionary containing statistics.

        Raises:
            sqlite3.Error: If database operation fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build query with optional date filtering
            query = """
                SELECT 
                    COUNT(*) as total_worksheets,
                    COUNT(grade) as graded_worksheets,
                    AVG(CASE WHEN grade IS NOT NULL 
                        THEN CAST(total_correct AS FLOAT) / total_questions 
                        ELSE NULL END) as average_score,
                    SUM(CASE WHEN grade = 'A' THEN 1 ELSE 0 END) as a_grades,
                    SUM(CASE WHEN grade = 'B' THEN 1 ELSE 0 END) as b_grades,
                    SUM(CASE WHEN grade = 'C' THEN 1 ELSE 0 END) as c_grades,
                    SUM(CASE WHEN grade = 'D' THEN 1 ELSE 0 END) as d_grades,
                    SUM(CASE WHEN grade = 'F' THEN 1 ELSE 0 END) as f_grades
                FROM worksheets
            """
            params = []
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append("created_at >= ?")
                    params.append(start_date)
                if end_date:
                    conditions.append("created_at <= ?")
                    params.append(end_date)
                if conditions:
                    query += f" WHERE {' AND '.join(conditions)}"

            cursor.execute(query, params)
            return dict(cursor.fetchone())
