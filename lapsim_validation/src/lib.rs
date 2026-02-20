pub mod plotting;
pub mod records;

// Re-export commonly used types and functions for convenience
pub use records::{
    Arc, ArcWithPoints, CartesianCoords, Record, TrackSegment, convert_splines_to_arcs,
    convert_splines_to_arcs_custom, fit_splines_to_segments, map_arcs_to_points, read_csv,
    records_to_cartesian, split_records_into_segments, split_records_into_segments_custom,
};
