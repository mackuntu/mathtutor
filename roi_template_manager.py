import hashlib

from db_handler import DatabaseHandler


class ROITemplateManager:

    @staticmethod
    def calculate_hash(rois):
        """
        Calculate a hash for the given ROI list.
        """
        serialized = ",".join(map(str, rois))  # Serialize the ROI list
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def calculate_rois(
        problems, x_positions, y_positions, row_spacing, answer_width, answer_height
    ):
        """
        Calculate ROIs for the given problems based on layout configuration.
        """
        return [
            ROITemplateManager._calculate_single_roi(
                column,
                problems_list,
                i,
                x_positions,
                y_positions,
                row_spacing,
                answer_width,
                answer_height,
            )
            for column, problems_list in problems.items()
            for i, _ in enumerate(problems_list)
        ]

    @staticmethod
    def _calculate_single_roi(
        column,
        problems_list,
        index,
        x_positions,
        y_positions,
        row_spacing,
        answer_width,
        answer_height,
    ):
        """
        Helper function to calculate a single ROI.
        """
        x1 = x_positions[column] + 20  # Offset for problem number
        y1 = y_positions[column] - index * row_spacing - answer_height // 2
        x2 = x1 + answer_width
        y2 = y1 + answer_height
        return (x1, y1, x2, y2)

    @staticmethod
    def find_or_create_template(rois):
        """
        Find or create a template by its hash.
        """
        roi_hash = ROITemplateManager.calculate_hash(rois)

        if ROITemplateManager._template_exists(roi_hash):
            return roi_hash

        return ROITemplateManager._create_template(roi_hash, rois)

    @staticmethod
    def _template_exists(roi_hash):
        """
        Check if a template exists by its hash.
        """
        try:
            existing_rois = DatabaseHandler.fetch_roi_template(roi_hash)
            return existing_rois is not None
        except Exception as e:
            print(f"Error fetching ROI template: {e}")
            return False

    @staticmethod
    def _create_template(roi_hash, rois):
        """
        Create a new template and save it.
        """
        try:
            return DatabaseHandler.save_roi_template(roi_hash, rois)
        except Exception as e:
            raise ValueError(f"Error saving new ROI template: {e}")
