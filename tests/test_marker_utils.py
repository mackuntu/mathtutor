import pytest

from src.utils.marker_utils import MarkerUtils


@pytest.fixture
def setup_data():
    """Fixture to set up sample data for tests."""
    pdf_rois = [
        (400, 500, 500, 540),
        (400, 460, 500, 500),
        (400, 420, 500, 460),
        (400, 380, 500, 420),
    ]
    image_markers = [
        (100, 100),  # Bottom-left
        (100, 900),  # Top-left
        (900, 100),  # Bottom-right
        (900, 900),  # Top-right
    ]
    image_dimensions = (1000, 1000)
    return pdf_rois, image_markers, image_dimensions


def test_map_pdf_to_image_space_y_axis_reversal(setup_data):
    """Ensure transformed ROIs correctly map and eliminate Y-axis reversal bugs."""
    pdf_rois, image_markers, image_dimensions = setup_data
    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        pdf_rois, image_markers, image_dimensions
    )

    # Validate the number of transformed ROIs
    assert len(transformed_rois) == len(pdf_rois)

    # Validate Y-axis and X-axis values in transformed ROIs
    for original, transformed in zip(pdf_rois, transformed_rois):
        x1, y1, x2, y2 = transformed
        assert y1 <= y2, f"Y-axis reversed in ROI: {transformed}"
        assert x1 <= x2, f"X-axis reversed in ROI: {transformed}"

    print("Transformed ROIs:")
    for roi in transformed_rois:
        print(roi)


def test_invalid_image_markers(setup_data):
    """Test with invalid image markers (e.g., collinear or insufficient points)."""
    pdf_rois, _, image_dimensions = setup_data
    invalid_markers = [(100, 100), (100, 200)]  # Only 2 points
    with pytest.raises(ValueError):
        MarkerUtils.map_pdf_to_image_space(pdf_rois, invalid_markers, image_dimensions)


def test_collinear_image_markers(setup_data):
    """Test with collinear image markers."""
    pdf_rois, _, image_dimensions = setup_data
    collinear_markers = [(100, 100), (200, 200), (300, 300), (400, 400)]
    with pytest.raises(ValueError):
        MarkerUtils.map_pdf_to_image_space(
            pdf_rois, collinear_markers, image_dimensions
        )


def test_y_axis_reversal_correction(setup_data):
    """Validate that Y-axis reversal is corrected in transformed ROIs."""
    pdf_rois, image_markers, image_dimensions = setup_data
    transformed_rois = MarkerUtils.map_pdf_to_image_space(
        pdf_rois, image_markers, image_dimensions
    )

    for roi in transformed_rois:
        x1, y1, x2, y2 = roi
        assert y1 <= y2, f"Y-coordinates reversed in ROI: {roi}"
        assert x1 <= x2, f"X-coordinates reversed in ROI: {roi}"


def test_warning_for_invalid_rois(setup_data, caplog):
    """Test warnings for invalid ROIs (e.g., Y1 > Y2)."""
    invalid_rois = [(400, 300, 500, 200)]  # Invalid because y1 > y2
    _, image_markers, image_dimensions = setup_data
    with caplog.at_level("WARNING"):
        transformed_rois = MarkerUtils.map_pdf_to_image_space(
            invalid_rois, image_markers, image_dimensions
        )
        assert "Invalid transformed ROI" in caplog.text
        assert len(transformed_rois) == 0
