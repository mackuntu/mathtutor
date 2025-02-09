import hashlib
import json

from ..db_handler import DatabaseHandler


class ROITemplateManager:
    @staticmethod
    def _hash_rois(rois):
        """Generate a unique hash for a list of ROIs."""
        # Convert ROIs to a JSON string for consistent hashing
        rois_json = json.dumps(rois, sort_keys=True)
        return hashlib.sha256(rois_json.encode()).hexdigest()

    @staticmethod
    def find_or_create_template(rois):
        """Find an existing ROI template or create a new one."""
        # Generate hash for the ROIs
        template_hash = ROITemplateManager._hash_rois(rois)

        try:
            # Try to fetch existing template
            DatabaseHandler.fetch_roi_template(template_hash)
        except ValueError:
            # Template doesn't exist, create new one
            DatabaseHandler.save_roi_template(template_hash, rois)

        return template_hash
