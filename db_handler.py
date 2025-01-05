import sqlite3
from worksheet_pb2 import Worksheet, ROITemplate


class DatabaseHandler:
    @staticmethod
    def initialize_database():
        """
        Initialize the database and create tables if they don't exist.
        """
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        # Create worksheets table
        c.execute(
            """CREATE TABLE IF NOT EXISTS worksheets (
                id TEXT PRIMARY KEY, 
                version TEXT, 
                data BLOB
            )"""
        )

        # Create ROI templates table
        c.execute(
            """CREATE TABLE IF NOT EXISTS roi_templates (
                id TEXT PRIMARY KEY,
                data BLOB
            )"""
        )

        conn.commit()
        conn.close()

    @staticmethod
    def save_worksheet(worksheet_id, version, problems, answers, template_id):
        """
        Save a worksheet as a serialized Protobuf object.
        """
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        # Create Protobuf object
        worksheet = Worksheet()
        worksheet.worksheet_id = worksheet_id
        worksheet.version = version

        # Ensure all problems and answers are strings
        worksheet.problems.extend(map(str, problems))
        worksheet.answers.extend(map(str, answers))  # Convert answers to strings

        worksheet.template_id = template_id

        # Serialize to Protobuf binary
        serialized_data = worksheet.SerializeToString()

        # Save to SQLite
        c.execute(
            "INSERT OR REPLACE INTO worksheets (id, version, data) VALUES (?, ?, ?)",
            (worksheet_id, version, serialized_data),
        )

        conn.commit()
        conn.close()

    @staticmethod
    def fetch_worksheet(worksheet_id, version):
        """
        Fetch and deserialize a worksheet from the database.
        """
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        c.execute(
            "SELECT data FROM worksheets WHERE id = ? AND version = ?",
            (worksheet_id, version),
        )
        result = c.fetchone()
        conn.close()

        if result:
            serialized_data = result[0]
            worksheet = Worksheet()
            worksheet.ParseFromString(serialized_data)
            return worksheet
        else:
            raise ValueError("Worksheet not found.")

    @staticmethod
    def save_roi_template(roi_hash, rois):
        """
        Save an ROI template as a serialized Protobuf object.
        """
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        # Generate Protobuf object
        template = ROITemplate()
        template.id = roi_hash
        for x1, y1, x2, y2 in rois:
            roi = template.rois.add()
            roi.x1 = x1
            roi.y1 = y1
            roi.x2 = x2
            roi.y2 = y2

        # Serialize to Protobuf binary
        serialized_data = template.SerializeToString()

        # Save to SQLite
        c.execute(
            "INSERT OR IGNORE INTO roi_templates (id, data) VALUES (?, ?)",
            (roi_hash, serialized_data),
        )

        conn.commit()
        conn.close()

        return roi_hash

    @staticmethod
    def fetch_roi_template(roi_hash):
        """
        Fetch and deserialize an ROI template from the database.
        """
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        c.execute("SELECT data FROM roi_templates WHERE id = ?", (roi_hash,))
        result = c.fetchone()
        conn.close()

        if result:
            serialized_data = result[0]
            template = ROITemplate()
            template.ParseFromString(serialized_data)

            # Extract ROI tuples
            return [(roi.x1, roi.y1, roi.x2, roi.y2) for roi in template.rois]
        else:
            raise ValueError("ROI Template not found.")
