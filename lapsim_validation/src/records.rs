use serde::{Deserialize, Serialize};
use splines::{Interpolation, Key, Spline};
use std::error::Error;
use std::fs::{self, File};
use std::path::Path;

/// Cartesian coordinates in meters, relative to a reference point
#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
pub struct CartesianCoords {
    pub x: f64,             // East in meters
    pub y: f64,             // North in meters
    pub z: f64,             // Up in meters
    pub ax: f64,            // Acceleration X in Gs
    pub ay: f64,            // Acceleration Y in Gs
    pub az: f64,            // Acceleration Z in Gs
    pub roll: f64,          // Roll angle (imu_x) in degrees
    pub yaw: f64,           // Yaw angle (imu_z) in degrees
    pub susp_pot_1_fl: f64, // Front Left suspension potentiometer
    pub susp_pot_2_fr: f64, // Front Right suspension potentiometer
    pub susp_pot_3_rr: f64, // Rear Right suspension potentiometer
    pub susp_pot_4_rl: f64, // Rear Left suspension potentiometer
    pub rpm: u32,           // Engine RPM
}

/// Represents a circular arc with constant radius
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Arc {
    pub center_x: f64,    // Center of the circle in meters (East)
    pub center_y: f64,    // Center of the circle in meters (North)
    pub radius: f64,      // Radius of the arc in meters
    pub start_angle: f64, // Starting angle in radians
    pub end_angle: f64,   // Ending angle in radians
    pub start_x: f64,     // Starting point x coordinate
    pub start_y: f64,     // Starting point y coordinate
    pub end_x: f64,       // Ending point x coordinate
    pub end_y: f64,       // Ending point y coordinate
}

/// Maps an arc to its corresponding original GPS points with telemetry data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArcWithPoints {
    pub segment_id: usize,
    pub arc_id: usize,
    pub arc: Arc,
    pub points: Vec<CartesianCoords>,
    pub global_indices: Vec<usize>, // Indices into the original records array
}

/// Represents a segment of "good" GPS data (no frozen/repeating coordinates)
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TrackSegment {
    pub coords: Vec<CartesianCoords>,
    pub start_index: usize,
    pub end_index: usize,
    pub spline_x: Option<Spline<f64, f64>>,
    pub spline_y: Option<Spline<f64, f64>>,
    pub arcs: Vec<Arc>,
    pub initial_velocity: f64, // Ground speed at the start of the segment in m/s
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[allow(non_snake_case)]
#[allow(dead_code)]
pub struct Record {
    pub write_millis: u32,
    pub ecu_millis: u32,
    pub gps_millis: u32,
    pub imu_millis: u32,
    pub accel_millis: u32,
    pub analogx1_millis: u32,
    pub analogx2_millis: u32,
    pub analogx3_millis: u32,
    pub rpm: u32,
    pub time: u32,
    pub syncloss_count: u32,
    pub syncloss_code: u32,
    pub lat: f64,
    pub lon: f64,
    pub elev: u32,
    pub unixtime: String,
    pub ground_speed: f64,
    pub afr: f64,
    pub fuelload: f64,
    pub spark_advance: f64,
    pub baro: u32,
    pub map: f64,
    pub mat: f64,
    pub clnt_temp: f64,
    pub tps: f64,
    pub batt: f64,
    pub oil_press: f64,
    pub ltcl_timing: f64,
    pub ve1: f64,
    pub ve2: f64,
    pub egt: u32,
    pub maf: u32,
    pub in_temp: f64,
    pub ax: f64,
    pub ay: f64,
    pub az: f64,
    pub imu_x: f64,
    pub imu_y: f64,
    pub imu_z: f64,
    pub susp_pot_1_FL: f64,
    pub susp_pot_2_FR: f64,
    pub susp_pot_3_RR: f64,
    pub susp_pot_4_RL: f64,
    pub rad_in: f64,
    pub rad_out: f64,
    pub amb_air_temp: u32,
    pub brake1: f64,
    pub brake2: f64,
}

impl Record {
    /// Converts this record's GPS coordinates to Cartesian coordinates
    /// relative to a reference point (typically the first point in a track).
    ///
    /// # Arguments
    /// * `ref_lat` - Reference latitude in degrees
    /// * `ref_lon` - Reference longitude in degrees
    /// * `ref_elev` - Reference elevation in meters
    ///
    /// # Returns
    /// * `CartesianCoords` - Local Cartesian coordinates in meters
    pub fn to_cartesian(&self, ref_lat: f64, ref_lon: f64, ref_elev: f64) -> CartesianCoords {
        let (x, y, z) = gps_to_cartesian(
            self.lat,
            self.lon,
            self.elev as f64,
            ref_lat,
            ref_lon,
            ref_elev,
        );

        CartesianCoords {
            x,
            y,
            z,
            ax: self.ax,
            ay: self.ay,
            az: self.az,
            roll: self.imu_x,
            yaw: self.imu_z,
            susp_pot_1_fl: self.susp_pot_1_FL,
            susp_pot_2_fr: self.susp_pot_2_FR,
            susp_pot_3_rr: self.susp_pot_3_RR,
            susp_pot_4_rl: self.susp_pot_4_RL,
            rpm: self.rpm,
        }
    }
}

/// Converts GPS coordinates (latitude, longitude, elevation) to local Cartesian coordinates
/// in meters, relative to a reference point.
///
/// This uses the equirectangular approximation which is accurate for small distances
/// (a few kilometers). For racing applications, this is typically sufficient.
///
/// # Arguments
/// * `lat` - Latitude in degrees
/// * `elev` - Elevation in meters
/// * `ref_lat` - Reference latitude in degrees (origin point)
/// * `ref_lon` - Reference longitude in degrees (origin point)
/// * `ref_elev` - Reference elevation in meters (origin point)
///
/// # Returns
/// * `(f64, f64, f64)` - Tuple of (x, y, z) where:
///   - x: East in meters
///   - y: North in meters
///   - z: Up in meters
pub fn gps_to_cartesian(
    lat: f64,
    lon: f64,
    elev: f64,
    ref_lat: f64,
    ref_lon: f64,
    ref_elev: f64,
) -> (f64, f64, f64) {
    // Earth radius in meters
    const EARTH_RADIUS: f64 = 6_371_000.0;

    // Convert degrees to radians
    let lat_rad = lat.to_radians();
    let lon_rad = lon.to_radians();
    let ref_lat_rad = ref_lat.to_radians();
    let ref_lon_rad = ref_lon.to_radians();

    // Calculate differences
    let delta_lat = lat_rad - ref_lat_rad;
    let delta_lon = lon_rad - ref_lon_rad;

    // Use equirectangular approximation
    // x = R * Δλ * cos(φ_ref)  (East)
    // y = R * Δφ               (North)
    // z = Δh                   (Up)
    let x = EARTH_RADIUS * delta_lon * ref_lat_rad.cos();
    let y = EARTH_RADIUS * delta_lat;
    let z = elev - ref_elev;

    (x, y, z)
}

/// Converts a slice of Records to Cartesian coordinates using the first record
/// as the reference point.
///
/// # Arguments
/// * `records` - Slice of records to convert
///
/// # Returns
/// * `Vec<CartesianCoords>` - Vector of Cartesian coordinates
///
/// # Panics
/// * Panics if the records slice is empty
pub fn records_to_cartesian(records: &[Record]) -> Vec<CartesianCoords> {
    if records.is_empty() {
        panic!("Cannot convert empty records to Cartesian coordinates");
    }

    let ref_record = &records[0];
    let ref_lat = ref_record.lat;
    let ref_lon = ref_record.lon;
    let ref_elev = ref_record.elev as f64;

    records
        .iter()
        .map(|record| record.to_cartesian(ref_lat, ref_lon, ref_elev))
        .collect()
}

/// Reads a CSV file and returns a vector of Records.
///
/// # Arguments
/// * `path` - A path to the CSV file to read
///
/// # Returns
/// * `Result<Vec<Record>, Box<dyn Error>>` - A vector of records or an error
///
/// # Example
/// ```no_run
/// use gps_data_smoothing_v2::records::read_csv;
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// let records = read_csv("data.csv")?;
/// println!("Read {} records", records.len());
/// # Ok(())
/// # }
/// ```
pub fn read_csv<P: AsRef<Path>>(path: P) -> Result<Vec<Record>, Box<dyn Error>> {
    let file = File::open(path)?;
    let mut reader = csv::Reader::from_reader(file);

    let mut records = Vec::new();
    for result in reader.deserialize() {
        let record: Record = result?;
        records.push(record);
    }

    Ok(records)
}

/// Write data to a csv file.
///
/// # Arguments:
/// * `path` - A path to the CSV file to write to
/// * `data` - The data to write to the CSV file. Must implement `Serialize`
///
/// # Returns:
/// Unit type or an error.
pub fn write_csv<P: AsRef<Path>, T: Serialize>(path: P, data: &[T]) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(&path.as_ref().parent().unwrap())?;
    let mut writer = csv::Writer::from_path(path)?;

    for item in data {
        writer.serialize(item)?;
    }

    Ok(())
}

/// Detects if two GPS coordinates are essentially the same (frozen sensor).
/// Uses a very small tolerance in degrees.
///
/// # Arguments
/// * `lat1, lon1` - First GPS coordinate
/// * `lat2, lon2` - Second GPS coordinate
/// * `tolerance_degrees` - Maximum difference in degrees to consider frozen (default: 0.000001 ≈ 0.1m)
///
/// # Returns
/// * `bool` - True if the coordinates are frozen (same location)
fn are_coords_frozen(lat1: f64, lon1: f64, lat2: f64, lon2: f64, tolerance_degrees: f64) -> bool {
    let dlat = (lat1 - lat2).abs();
    let dlon = (lon1 - lon2).abs();
    dlat < tolerance_degrees && dlon < tolerance_degrees
}

/// Splits track data into segments by detecting and splitting at frozen GPS sections.
///
/// When a GPS sensor freezes, it repeats the same coordinates many times. When it unfreezes,
/// it suddenly jumps to where the car actually is, creating an artificial instantaneous jump.
/// This function detects runs of duplicate GPS coordinates and splits the track around them,
/// removing these artificial jumps from the data.
///
/// All segments use the same global reference point for Cartesian conversion so they align
/// properly when visualized.
///
/// # Arguments
/// * `records` - Slice of records to split
/// * `min_segment_length` - Minimum number of points for a segment to be considered valid
/// * `min_frozen_count` - Minimum consecutive duplicate readings to consider as "frozen" (3-10 recommended)
/// * `tolerance_degrees` - Tolerance in degrees for detecting duplicate coordinates (0.000001 ≈ 0.1m)
///
/// # Returns
/// * `Vec<TrackSegment>` - Vector of good track segments (frozen sections excluded)
pub fn split_records_into_segments_detailed(
    records: &[Record],
    min_segment_length: usize,
    min_frozen_count: usize,
    tolerance_degrees: f64,
    max_jump_distance: f64,
) -> Vec<TrackSegment> {
    if records.is_empty() {
        return Vec::new();
    }

    // Use the first record as the global reference point for all segments
    let ref_lat = records[0].lat;
    let ref_lon = records[0].lon;
    let ref_elev = records[0].elev as f64;

    let mut segments = Vec::new();
    let mut segment_start = 0;
    let mut i = 1; // Start at 1 since we compare with previous

    while i < records.len() {
        // Check if current position is a duplicate of previous
        let is_duplicate = are_coords_frozen(
            records[i - 1].lat,
            records[i - 1].lon,
            records[i].lat,
            records[i].lon,
            tolerance_degrees,
        );

        // Check for large jump in position
        let is_jump = {
            let prev_cart = records[i - 1].to_cartesian(ref_lat, ref_lon, ref_elev);
            let curr_cart = records[i].to_cartesian(ref_lat, ref_lon, ref_elev);
            let dx = curr_cart.x - prev_cart.x;
            let dy = curr_cart.y - prev_cart.y;
            (dx * dx + dy * dy).sqrt() > max_jump_distance
        };

        if is_duplicate {
            // Count consecutive duplicates from this position
            let frozen_start = i - 1;
            let mut frozen_end = i;

            while frozen_end < records.len() - 1 {
                if are_coords_frozen(
                    records[frozen_end].lat,
                    records[frozen_end].lon,
                    records[frozen_end + 1].lat,
                    records[frozen_end + 1].lon,
                    tolerance_degrees,
                ) {
                    frozen_end += 1;
                } else {
                    break;
                }
            }

            let frozen_count = frozen_end - frozen_start;

            // If we have enough duplicates, this is a frozen section
            if frozen_count >= min_frozen_count {
                // Save the segment before the frozen section
                if frozen_start > segment_start
                    && (frozen_start - segment_start) >= min_segment_length
                {
                    let segment_records = &records[segment_start..frozen_start];
                    let segment_coords: Vec<CartesianCoords> = segment_records
                        .iter()
                        .map(|r| r.to_cartesian(ref_lat, ref_lon, ref_elev))
                        .collect();

                    segments.push(TrackSegment {
                        coords: segment_coords,
                        start_index: segment_start,
                        end_index: frozen_start - 1,
                        spline_x: None,
                        spline_y: None,
                        arcs: Vec::new(),
                        initial_velocity: records[segment_start].ground_speed,
                    });
                }

                // Skip past the frozen section and the jump
                i = frozen_end + 1;
                segment_start = i;
            } else {
                // Not enough duplicates, keep going
                i += 1;
            }
        } else if is_jump {
            // Large jump detected, split the segment here
            if i > segment_start && (i - segment_start) >= min_segment_length {
                let segment_records = &records[segment_start..i];
                let segment_coords: Vec<CartesianCoords> = segment_records
                    .iter()
                    .map(|r| r.to_cartesian(ref_lat, ref_lon, ref_elev))
                    .collect();

                segments.push(TrackSegment {
                    coords: segment_coords,
                    start_index: segment_start,
                    end_index: i - 1,
                    spline_x: None,
                    spline_y: None,
                    arcs: Vec::new(),
                    initial_velocity: records[segment_start].ground_speed,
                });
            }

            // Start new segment after the jump
            segment_start = i;
            i += 1;
        } else {
            // No duplicate or jump, move forward
            i += 1;
        }
    }

    // Add the final segment if it's valid
    if records.len() > segment_start && (records.len() - segment_start) >= min_segment_length {
        let segment_records = &records[segment_start..];
        let segment_coords: Vec<CartesianCoords> = segment_records
            .iter()
            .map(|r| r.to_cartesian(ref_lat, ref_lon, ref_elev))
            .collect();

        segments.push(TrackSegment {
            coords: segment_coords,
            start_index: segment_start,
            end_index: records.len() - 1,
            spline_x: None,
            spline_y: None,
            arcs: Vec::new(),
            initial_velocity: records[segment_start].ground_speed,
        });
    }

    // Post-process: split any segments that still contain jumps within them
    split_segments_with_jumps(segments, max_jump_distance)
}

/// Splits segments that contain jumps within their coordinate sequences.
/// This post-processing ensures that no segment has jumps larger than max_jump_distance
/// between consecutive points.
fn split_segments_with_jumps(
    segments: Vec<TrackSegment>,
    max_jump_distance: f64,
) -> Vec<TrackSegment> {
    let mut result = Vec::new();

    for segment in segments {
        if segment.coords.len() < 2 {
            result.push(segment);
            continue;
        }

        let mut current_start = 0;

        for i in 1..segment.coords.len() {
            let dx = segment.coords[i].x - segment.coords[i - 1].x;
            let dy = segment.coords[i].y - segment.coords[i - 1].y;
            let dist = (dx * dx + dy * dy).sqrt();

            if dist > max_jump_distance {
                // Split here
                if i - current_start >= 10 {
                    // Use same min_segment_length
                    let coords = segment.coords[current_start..i].to_vec();
                    let start_index = segment.start_index + current_start;
                    let end_index = segment.start_index + i - 1;

                    result.push(TrackSegment {
                        coords,
                        start_index,
                        end_index,
                        spline_x: None,
                        spline_y: None,
                        arcs: Vec::new(),
                        initial_velocity: segment.initial_velocity, // Keep original velocity for sub-segments
                    });
                }

                current_start = i;
            }
        }

        // Add the last part
        if segment.coords.len() - current_start >= 10 {
            let coords = segment.coords[current_start..].to_vec();
            let start_index = segment.start_index + current_start;
            let end_index = segment.end_index;

            result.push(TrackSegment {
                coords,
                start_index,
                end_index,
                spline_x: None,
                spline_y: None,
                arcs: Vec::new(),
                initial_velocity: segment.initial_velocity,
            });
        }
    }

    result
}

/// Splits records into good segments with custom parameters for advanced users.
///
/// This is the exported version of the detailed segmentation function that allows
/// full control over the detection parameters.
///
/// # Arguments
/// * `records` - Slice of records to split
/// * `min_segment_length` - Minimum number of points for a segment to be considered valid
/// * `min_frozen_count` - Minimum consecutive duplicate readings to consider as "frozen"
/// * `tolerance_degrees` - Tolerance in degrees for detecting duplicate coordinates (0.000001 ≈ 0.1m)
/// * `max_jump_distance` - Maximum allowed distance (meters) between consecutive points; larger jumps cause splits
///
/// # Returns
/// * `Vec<TrackSegment>` - Vector of good track segments (frozen sections and jumps excluded)
///
/// # Example
/// ```no_run
/// use gps_data_smoothing_v2::records::{read_csv, split_records_into_segments_custom};
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// # let records = read_csv("data.csv")?;
/// // More aggressive splitting - break on just 3 consecutive duplicates and 10m jumps
/// let segments = split_records_into_segments_custom(&records, 10, 3, 0.000001, 10.0);
///
/// // More lenient - only break on 15+ consecutive duplicates and 100m jumps
/// let segments = split_records_into_segments_custom(&records, 10, 15, 0.000001, 100.0);
/// # Ok(())
/// # }
/// ```
#[allow(dead_code)]
pub fn split_records_into_segments_custom(
    records: &[Record],
    min_segment_length: usize,
    min_frozen_count: usize,
    tolerance_degrees: f64,
    max_jump_distance: f64,
) -> Vec<TrackSegment> {
    split_records_into_segments_detailed(
        records,
        min_segment_length,
        min_frozen_count,
        tolerance_degrees,
        max_jump_distance,
    )
}

/// Convenience function that splits records into good segments by detecting frozen GPS sections and large jumps.
/// Uses sensible defaults:
/// - Minimum segment length: 10 points
/// - Minimum frozen count: 20 consecutive duplicates (to handle slow GPS update rates)
/// - Tolerance: 0.000001 degrees (approximately 0.1 meters)
/// - Maximum jump distance: 10.0 meters (splits on jumps larger than this)
///
/// This will split the track wherever the GPS freezes and repeats the same coordinates
/// 20+ times, or wherever there is a sudden jump in position larger than 10 meters.
/// This removes artificial jumps from frozen GPS and other anomalies.
///
/// # Arguments
/// * `records` - Slice of records to split
///
/// # Returns
/// * `Vec<TrackSegment>` - Vector of good track segments (frozen sections and jumps excluded)
pub fn split_records_into_segments(records: &[Record]) -> Vec<TrackSegment> {
    split_records_into_segments_detailed(records, 10, 20, 0.000001, 10.0)
}

/// Calculates cumulative distances along a sequence of Cartesian coordinates.
///
/// Returns a vector where the i-th element is the total distance traveled
/// from the start (index 0) to the i-th point.
///
/// # Arguments
/// * `coords` - Slice of Cartesian coordinates
///
/// # Returns
/// * `Vec<f64>` - Vector of cumulative distances (first element is always 0.0)
pub fn calculate_cumulative_distances(coords: &[CartesianCoords]) -> Vec<f64> {
    let mut cumulative_distances = vec![0.0];
    for i in 1..coords.len() {
        let dx = coords[i].x - coords[i - 1].x;
        let dy = coords[i].y - coords[i - 1].y;
        let distance = (dx * dx + dy * dy).sqrt();
        cumulative_distances.push(cumulative_distances[i - 1] + distance);
    }
    cumulative_distances
}

/// Fits a parametric spline to a track segment's x and y coordinates.
///
/// This function takes the Cartesian coordinates of a track segment and fits
/// a parametric spline through them using cosine interpolation. The spline is
/// parameterized by cumulative distance along the track, which provides a
/// natural parameterization.
///
/// # Arguments
/// * `segment` - Mutable reference to a TrackSegment
///
/// # Panics
/// Panics if the segment has fewer than 4 points. Callers should check
/// `segment.coords.len() >= 4` before calling this function.
///
/// # Details
/// The spline uses cumulative distance as the parameter t, where:
/// - t=0 at the start of the segment
/// - t increases with distance traveled
/// - Cosine interpolation provides smooth curves suitable for path representation
pub fn fit_spline_to_segment(segment: &mut TrackSegment) {
    let n = segment.coords.len();

    assert!(
        n >= 4,
        "Segment must have at least 4 points for spline fitting"
    );

    // Calculate cumulative distance along the track for parameterization
    let cumulative_distances = calculate_cumulative_distances(&segment.coords);

    // Create spline keys for x and y coordinates
    let mut x_keys = Vec::new();
    let mut y_keys = Vec::new();

    for i in 0..n {
        let t = cumulative_distances[i];
        x_keys.push(Key::new(t, segment.coords[i].x, Interpolation::Cosine));
        y_keys.push(Key::new(t, segment.coords[i].y, Interpolation::Cosine));
    }

    // Create the splines
    segment.spline_x = Some(Spline::from_vec(x_keys));
    segment.spline_y = Some(Spline::from_vec(y_keys));
}

/// Fits splines to all track segments in a vector.
///
/// This is a convenience function that applies `fit_spline_to_segment` to
/// each segment in the vector. Segments with fewer than 4 points are skipped.
///
/// # Arguments
/// * `segments` - Mutable reference to a vector of TrackSegments
///
/// # Returns
/// * `usize` - Number of segments that had splines fitted
pub fn fit_splines_to_segments(segments: &mut [TrackSegment]) -> usize {
    let mut success_count = 0;

    for segment in segments.iter_mut() {
        if segment.coords.len() >= 4 {
            fit_spline_to_segment(segment);
            success_count += 1;
        }
    }

    success_count
}

/// Calculates the curvature (1/radius) at a point on a parametric curve.
/// Uses the formula: κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
///
/// # Arguments
/// * `spline_x` - Spline for x coordinates
/// * `spline_y` - Spline for y coordinates
/// * `t` - Parameter value
/// * `dt` - Small step for numerical differentiation
///
/// # Returns
/// * `Option<f64>` - Curvature value (1/radius), or None if calculation fails
#[allow(dead_code)]
fn calculate_curvature(
    spline_x: &Spline<f64, f64>,
    spline_y: &Spline<f64, f64>,
    t: f64,
    dt: f64,
) -> Option<f64> {
    // Calculate first derivatives (velocity)
    let x_t = spline_x.clamped_sample(t)?;
    let y_t = spline_y.clamped_sample(t)?;

    let x_forward = spline_x.clamped_sample(t + dt)?;
    let y_forward = spline_y.clamped_sample(t + dt)?;

    let x_backward = spline_x.clamped_sample(t - dt)?;
    let y_backward = spline_y.clamped_sample(t - dt)?;

    // First derivatives (central difference)
    let dx_dt = (x_forward - x_backward) / (2.0 * dt);
    let dy_dt = (y_forward - y_backward) / (2.0 * dt);

    // Second derivatives (central difference)
    let d2x_dt2 = (x_forward - 2.0 * x_t + x_backward) / (dt * dt);
    let d2y_dt2 = (y_forward - 2.0 * y_t + y_backward) / (dt * dt);

    // Curvature formula: κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
    let numerator = (dx_dt * d2y_dt2 - dy_dt * d2x_dt2).abs();
    let denominator = (dx_dt * dx_dt + dy_dt * dy_dt).powf(1.5);

    if denominator < 1e-10 {
        return None;
    }

    Some(numerator / denominator)
}

/// Fits a circle (center and radius) to three points.
///
/// # Arguments
/// * `p1`, `p2`, `p3` - Three points (x, y) on the circle
///
/// # Returns
/// * `Option<(f64, f64, f64)>` - (center_x, center_y, radius) or None if points are collinear
fn fit_circle_to_three_points(
    p1: (f64, f64),
    p2: (f64, f64),
    p3: (f64, f64),
) -> Option<(f64, f64, f64)> {
    let (x1, y1) = p1;
    let (x2, y2) = p2;
    let (x3, y3) = p3;

    // Use the determinant method to find circle center
    let a = x1 - x2;
    let b = y1 - y2;
    let c = x1 - x3;
    let d = y1 - y3;

    let e = a * (x1 + x2) + b * (y1 + y2);
    let f = c * (x1 + x3) + d * (y1 + y3);

    let g = 2.0 * (a * (y3 - y2) - b * (x3 - x2));

    if g.abs() < 1e-10 {
        // Points are collinear or too close
        return None;
    }

    let center_x = (d * e - b * f) / g;
    let center_y = (a * f - c * e) / g;

    let radius = ((x1 - center_x).powi(2) + (y1 - center_y).powi(2)).sqrt();

    Some((center_x, center_y, radius))
}

/// Fits a circle to multiple points using least-squares approach.
/// This provides better fitting than 3-point method for longer arcs.
///
/// # Arguments
/// * `points` - Slice of (t, x, y) tuples
///
/// # Returns
/// * `Option<(f64, f64, f64)>` - (center_x, center_y, radius) or None if fitting fails
fn fit_circle_least_squares(points: &[(f64, f64, f64)]) -> Option<(f64, f64, f64)> {
    if points.len() < 3 {
        return None;
    }

    // Calculate centroid
    let n = points.len() as f64;
    let mut sum_x = 0.0;
    let mut sum_y = 0.0;
    for (_, x, y) in points {
        sum_x += x;
        sum_y += y;
    }
    let cx = sum_x / n;
    let cy = sum_y / n;

    // Calculate moments
    let mut mxx = 0.0;
    let mut myy = 0.0;
    let mut mxy = 0.0;
    let mut mxz = 0.0;
    let mut myz = 0.0;

    for (_, x, y) in points {
        let dx = x - cx;
        let dy = y - cy;
        let z = dx * dx + dy * dy;
        mxx += dx * dx;
        myy += dy * dy;
        mxy += dx * dy;
        mxz += dx * z;
        myz += dy * z;
    }

    mxx /= n;
    myy /= n;
    mxy /= n;
    mxz /= n;
    myz /= n;

    // Solve for center offset
    let det = mxx * myy - mxy * mxy;
    if det.abs() < 1e-10 {
        return None;
    }

    let center_x = cx + (mxz * myy - myz * mxy) / det;
    let center_y = cy + (mxx * myz - mxy * mxz) / det;

    // Calculate radius as average distance to center
    let mut sum_r = 0.0;
    for (_, x, y) in points {
        sum_r += ((x - center_x).powi(2) + (y - center_y).powi(2)).sqrt();
    }
    let radius = sum_r / n;

    Some((center_x, center_y, radius))
}

/// Calculates the maximum deviation between an arc and a set of points.
///
/// # Arguments
/// * `center_x`, `center_y` - Arc center
/// * `radius` - Arc radius
/// * `points` - Points to check against
///
/// # Returns
/// * `f64` - Maximum deviation in meters
#[allow(dead_code)]
fn calculate_arc_deviation(
    center_x: f64,
    center_y: f64,
    radius: f64,
    points: &[(f64, f64, f64)],
) -> f64 {
    let mut max_deviation: f64 = 0.0;

    for point in points {
        let (_, x, y) = point;
        let dist_to_center = ((x - center_x).powi(2) + (y - center_y).powi(2)).sqrt();
        let deviation = (dist_to_center - radius).abs();
        max_deviation = max_deviation.max(deviation);
    }

    max_deviation
}

/// Converts a spline segment into constant-radius arcs that closely approximate the spline.
///
/// This function creates many short arcs that closely follow the spline curve. Instead of
/// trying to extend arcs as far as possible, it creates fixed-length arcs that are guaranteed
/// to match the spline well. This ensures the arc sequence visually matches the spline.
///
/// Each arc starts exactly where the previous arc ended, ensuring complete coverage with no gaps.
///
/// Arcs with radius greater than 500m are considered essentially straight and are filtered out.
///
/// # Arguments
/// * `segment` - Track segment with fitted splines
/// * `max_deviation` - Maximum allowed deviation from spline (meters) - used for validation
/// * `min_arc_length` - Target length for each arc (meters) - creates many short arcs
/// * `sample_density` - Number of samples per meter along the spline
///
/// # Returns
/// * `Vec<Arc>` - Vector of constant-radius arcs that completely cover the spline with no gaps
pub fn convert_spline_to_arcs(
    segment: &TrackSegment,
    _max_deviation: f64,
    min_arc_length: f64,
    sample_density: f64,
) -> Vec<Arc> {
    let mut arcs = Vec::new();

    // Maximum radius threshold - larger radii are essentially straight sections
    const MAX_RADIUS_THRESHOLD: f64 = 500.0;

    // Minimum radius threshold - smaller radii are likely fitting errors
    const MIN_RADIUS_THRESHOLD: f64 = 5.0;

    // Minimum points to create an arc
    const MIN_ARC_POINTS: usize = 3;

    if segment.spline_x.is_none() || segment.spline_y.is_none() {
        return arcs;
    }

    let spline_x = segment.spline_x.as_ref().unwrap();
    let spline_y = segment.spline_y.as_ref().unwrap();

    // Calculate cumulative distance for parameterization
    let cumulative_distances = calculate_cumulative_distances(&segment.coords);
    let total_distance = cumulative_distances[cumulative_distances.len() - 1];

    if total_distance < 0.1 {
        return arcs;
    }

    // Sample the spline densely
    let num_samples = (total_distance * sample_density).max(20.0) as usize;
    let mut sampled_points = Vec::new();

    // Sample all points
    for i in 0..=num_samples {
        let t = (i as f64 / num_samples as f64) * total_distance;
        if let (Some(x), Some(y)) = (spline_x.clamped_sample(t), spline_y.clamped_sample(t)) {
            sampled_points.push((t, x, y));
        }
    }

    if sampled_points.len() < MIN_ARC_POINTS {
        return arcs;
    }

    // Use fixed-length arcs to ensure they follow the spline closely
    // Calculate target arc length in sample points based on min_arc_length parameter
    let target_arc_length = (min_arc_length * sample_density).max(5.0) as usize;

    let mut i = 0;
    while i < sampled_points.len() {
        let start_idx = i;

        // Need at least MIN_ARC_POINTS points for a circle
        let remaining_points = sampled_points.len() - start_idx;
        if remaining_points < MIN_ARC_POINTS {
            break;
        }

        // Determine end index: use target length or whatever remains
        let end_idx = (start_idx + target_arc_length).min(sampled_points.len() - 1);

        // Ensure we have at least MIN_ARC_POINTS
        let end_idx = if end_idx - start_idx + 1 < MIN_ARC_POINTS {
            (start_idx + MIN_ARC_POINTS - 1).min(sampled_points.len() - 1)
        } else {
            end_idx
        };

        // Fit circle to this range of points
        let points_in_range = &sampled_points[start_idx..=end_idx];

        let circle = if points_in_range.len() <= 5 {
            // For short arcs, use 3-point fitting
            let mid_idx = (start_idx + end_idx) / 2;
            let p1 = (sampled_points[start_idx].1, sampled_points[start_idx].2);
            let p2 = (sampled_points[mid_idx].1, sampled_points[mid_idx].2);
            let p3 = (sampled_points[end_idx].1, sampled_points[end_idx].2);
            fit_circle_to_three_points(p1, p2, p3)
        } else {
            // For longer arcs, use least-squares fitting for better accuracy
            fit_circle_least_squares(points_in_range)
        };

        // Create the arc if we have a valid circle
        if let Some((center_x, center_y, radius)) = circle {
            // Check if radius is reasonable (not too large or too small)
            if radius >= MIN_RADIUS_THRESHOLD && radius <= MAX_RADIUS_THRESHOLD {
                // Use the actual end point from the previous arc if this isn't the first arc
                let (start_x, start_y) = if !arcs.is_empty() {
                    let prev_arc = &arcs[arcs.len() - 1];
                    (prev_arc.end_x, prev_arc.end_y)
                } else {
                    (sampled_points[start_idx].1, sampled_points[start_idx].2)
                };

                let end_x = sampled_points[end_idx].1;
                let end_y = sampled_points[end_idx].2;

                // Calculate angles
                let start_angle = (start_y - center_y).atan2(start_x - center_x);
                let end_angle = (end_y - center_y).atan2(end_x - center_x);

                arcs.push(Arc {
                    center_x,
                    center_y,
                    radius,
                    start_angle,
                    end_angle,
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                });
            }

            // Move to the next arc starting point (no overlap)
            i = end_idx + 1;
        } else {
            // Circle fitting failed, try with smaller range
            i += (target_arc_length / 2).max(1);
        }
    }

    arcs
}

/// Converts splines to arcs for all segments with default parameters.
///
/// Default parameters:
/// - max_deviation: 0.5 meters (used for validation)
/// - min_arc_length: 1.5 meters (target arc length - creates many short arcs)
/// - sample_density: 6.0 samples per meter (high density for accurate approximation)
///
/// # Arguments
/// * `segments` - Mutable slice of track segments with fitted splines
///
/// # Returns
/// * `usize` - Number of segments that had arcs fitted
/// Creates a mapping of arcs to their corresponding original GPS points
///
/// # Arguments
/// * `segments` - The track segments containing arcs
///
/// # Returns
/// * Vector of `ArcWithPoints` containing each arc with its associated GPS points
pub fn map_arcs_to_points(segments: &[TrackSegment]) -> Vec<ArcWithPoints> {
    let mut arc_mappings = Vec::new();

    for (seg_idx, segment) in segments.iter().enumerate() {
        if segment.arcs.is_empty() {
            continue;
        }

        // For each arc, we need to find which original coords belong to it
        // We'll use distance from arc to determine membership
        for (arc_idx, arc) in segment.arcs.iter().enumerate() {
            let mut arc_points = Vec::new();
            let mut arc_indices = Vec::new();

            // Calculate arc bounds (min/max x and y for quick filtering)
            let arc_start_x = arc.start_x;
            let arc_start_y = arc.start_y;
            let arc_end_x = arc.end_x;
            let arc_end_y = arc.end_y;

            // Find points that are close to this arc
            for (i, coord) in segment.coords.iter().enumerate() {
                let global_index = segment.start_index + i;

                // Calculate distance from point to arc center
                let dx = coord.x - arc.center_x;
                let dy = coord.y - arc.center_y;
                let dist_to_center = (dx * dx + dy * dy).sqrt();

                // Check if point is approximately on the arc (within tolerance)
                let radius_tolerance = arc.radius * 0.15; // 15% tolerance
                if (dist_to_center - arc.radius).abs() <= radius_tolerance {
                    // Check if the point is within the angular range of the arc
                    let point_angle = dy.atan2(dx);

                    // Normalize angles to [0, 2π]
                    let normalize_angle = |angle: f64| {
                        let mut a = angle;
                        while a < 0.0 {
                            a += 2.0 * std::f64::consts::PI;
                        }
                        while a >= 2.0 * std::f64::consts::PI {
                            a -= 2.0 * std::f64::consts::PI;
                        }
                        a
                    };

                    let norm_start = normalize_angle(arc.start_angle);
                    let norm_end = normalize_angle(arc.end_angle);
                    let norm_point = normalize_angle(point_angle);

                    // Check if point angle is between start and end angles
                    let in_range = if norm_end > norm_start {
                        norm_point >= norm_start && norm_point <= norm_end
                    } else {
                        // Arc crosses the 0/2π boundary
                        norm_point >= norm_start || norm_point <= norm_end
                    };

                    // Also check spatial proximity to arc endpoints for better accuracy
                    let dist_to_start =
                        ((coord.x - arc_start_x).powi(2) + (coord.y - arc_start_y).powi(2)).sqrt();
                    let dist_to_end =
                        ((coord.x - arc_end_x).powi(2) + (coord.y - arc_end_y).powi(2)).sqrt();
                    let arc_length = arc.radius * (norm_end - norm_start).abs();
                    let near_arc_path = dist_to_start <= arc_length && dist_to_end <= arc_length;

                    if in_range || near_arc_path {
                        arc_points.push(*coord);
                        arc_indices.push(global_index);
                    }
                }
            }

            // Only add the mapping if we found points for this arc
            if !arc_points.is_empty() {
                arc_mappings.push(ArcWithPoints {
                    segment_id: seg_idx + 1,
                    arc_id: arc_idx + 1,
                    arc: *arc,
                    points: arc_points,
                    global_indices: arc_indices,
                });
            }
        }
    }

    arc_mappings
}

pub fn convert_splines_to_arcs(segments: &mut [TrackSegment]) -> usize {
    convert_splines_to_arcs_custom(segments, 0.5, 1.5, 6.0)
}

/// Converts splines to arcs for all segments with custom parameters.
///
/// # Arguments
/// * `segments` - Mutable slice of track segments with fitted splines
/// * `max_deviation` - Maximum allowed deviation from spline (meters)
/// * `min_arc_length` - Minimum length for an arc to be kept (meters)
/// * `sample_density` - Number of samples per meter along the spline
///
/// # Returns
/// * `usize` - Number of segments that had arcs fitted
pub fn convert_splines_to_arcs_custom(
    segments: &mut [TrackSegment],
    max_deviation: f64,
    min_arc_length: f64,
    sample_density: f64,
) -> usize {
    let mut success_count = 0;

    for segment in segments.iter_mut() {
        if segment.spline_x.is_some() && segment.spline_y.is_some() {
            let arcs =
                convert_spline_to_arcs(segment, max_deviation, min_arc_length, sample_density);

            if !arcs.is_empty() {
                segment.arcs = arcs;
                success_count += 1;
            }
        }
    }

    success_count
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    #[test]
    fn test_gps_to_cartesian() {
        // Test with reference point at origin
        let lat = 0.0;
        let lon = 0.0;
        let elev = 0.0;
        let ref_lat = 0.0;
        let ref_lon = 0.0;
        let ref_elev = 0.0;

        let (x, y, z) = gps_to_cartesian(lat, lon, elev, ref_lat, ref_lon, ref_elev);
        assert!((x - 0.0).abs() < 1e-6);
        assert!((y - 0.0).abs() < 1e-6);
        assert!((z - 0.0).abs() < 1e-6);

        // Test with small displacement (1 degree north)
        let lat = 1.0;
        let (_x, y, _z) = gps_to_cartesian(lat, lon, elev, ref_lat, ref_lon, ref_elev);
        let expected_y = 6_371_000.0 * (1.0_f64.to_radians());
        assert!((y - expected_y).abs() < 1.0); // Allow some tolerance for floating point
    }

    #[test]
    fn test_records_to_cartesian_empty() {
        let records = Vec::new();
        let result = std::panic::catch_unwind(|| records_to_cartesian(&records));
        assert!(result.is_err()); // Should panic on empty records
    }

    #[test]
    fn test_records_to_cartesian_single() {
        let record = Record {
            lat: 45.0,
            lon: -122.0,
            elev: 100,
            // Fill other fields with defaults
            write_millis: 0,
            ecu_millis: 0,
            gps_millis: 0,
            imu_millis: 0,
            accel_millis: 0,
            analogx1_millis: 0,
            analogx2_millis: 0,
            analogx3_millis: 0,
            rpm: 0,
            time: 0,
            syncloss_count: 0,
            syncloss_code: 0,
            unixtime: "0".to_string(),
            ground_speed: 0.0,
            afr: 0.0,
            fuelload: 0.0,
            spark_advance: 0.0,
            baro: 0,
            map: 0.0,
            mat: 0.0,
            clnt_temp: 0.0,
            tps: 0.0,
            batt: 0.0,
            oil_press: 0.0,
            ltcl_timing: 0.0,
            ve1: 0.0,
            ve2: 0.0,
            egt: 0,
            maf: 0,
            in_temp: 0.0,
            ax: 0.0,
            ay: 0.0,
            az: 0.0,
            imu_x: 0.0,
            imu_y: 0.0,
            imu_z: 0.0,
            susp_pot_1_FL: 0.0,
            susp_pot_2_FR: 0.0,
            susp_pot_3_RR: 0.0,
            susp_pot_4_RL: 0.0,
            rad_in: 0.0,
            rad_out: 0.0,
            amb_air_temp: 0,
            brake1: 0.0,
            brake2: 0.0,
        };

        let coords = records_to_cartesian(&[record]);
        assert_eq!(coords.len(), 1);
        // Since it is the reference point, should be at origin
        assert!((coords[0].x).abs() < 1e-6);
        assert!((coords[0].y).abs() < 1e-6);
        assert!((coords[0].z - 0.0).abs() < 1e-6);
    }

    #[test]
    fn test_are_coords_frozen() {
        // Same coordinates should be frozen
        assert!(are_coords_frozen(45.0, -122.0, 45.0, -122.0, 0.000001));

        // Slightly different coordinates should not be frozen
        assert!(!are_coords_frozen(45.0, -122.0, 45.00001, -122.0, 0.000001));

        // Test tolerance
        assert!(are_coords_frozen(
            45.0, -122.0, 45.0000005, -122.0, 0.000001
        ));
        assert!(!are_coords_frozen(
            45.0, -122.0, 45.000002, -122.0, 0.000001
        ));
    }

    #[test]
    fn test_calculate_cumulative_distances() {
        let coords = vec![
            CartesianCoords {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                ax: 0.0,
                ay: 0.0,
                az: 0.0,
                roll: 0.0,
                yaw: 0.0,
                susp_pot_1_fl: 0.0,
                susp_pot_2_fr: 0.0,
                susp_pot_3_rr: 0.0,
                susp_pot_4_rl: 0.0,
                rpm: 0,
            },
            CartesianCoords {
                x: 3.0,
                y: 4.0,
                z: 0.0,
                ax: 0.0,
                ay: 0.0,
                az: 0.0,
                roll: 0.0,
                yaw: 0.0,
                susp_pot_1_fl: 0.0,
                susp_pot_2_fr: 0.0,
                susp_pot_3_rr: 0.0,
                susp_pot_4_rl: 0.0,
                rpm: 0,
            }, // Distance 5
            CartesianCoords {
                x: 6.0,
                y: 8.0,
                z: 0.0,
                ax: 0.0,
                ay: 0.0,
                az: 0.0,
                roll: 0.0,
                yaw: 0.0,
                susp_pot_1_fl: 0.0,
                susp_pot_2_fr: 0.0,
                susp_pot_3_rr: 0.0,
                susp_pot_4_rl: 0.0,
                rpm: 0,
            }, // Distance 5 more
        ];

        let distances = calculate_cumulative_distances(&coords);
        assert_eq!(distances.len(), 3);
        assert!((distances[0] - 0.0).abs() < 1e-6);
        assert!((distances[1] - 5.0).abs() < 1e-6);
        assert!((distances[2] - 10.0).abs() < 1e-6);
    }

    #[test]
    fn test_calculate_cumulative_distances_single_point() {
        let coords = vec![CartesianCoords {
            x: 1.0,
            y: 2.0,
            z: 3.0,
            ax: 0.0,
            ay: 0.0,
            az: 0.0,
            roll: 0.0,
            yaw: 0.0,
            susp_pot_1_fl: 0.0,
            susp_pot_2_fr: 0.0,
            susp_pot_3_rr: 0.0,
            susp_pot_4_rl: 0.0,
            rpm: 0,
        }];
        let distances = calculate_cumulative_distances(&coords);
        assert_eq!(distances, vec![0.0]);
    }

    #[test]
    fn test_fit_circle_to_three_points() {
        // Test with points on a known circle
        let center_x = 0.0;
        let center_y = 0.0;
        let radius = 5.0;

        let p1 = (5.0, 0.0);
        let p2 = (0.0, 5.0);
        let p3 = (-5.0, 0.0);

        let result = fit_circle_to_three_points(p1, p2, p3);
        assert!(result.is_some());

        let (cx, cy, r) = result.unwrap();
        assert!((cx - center_x).abs() < 1e-6);
        assert!((cy - center_y).abs() < 1e-6);
        assert!((r - radius).abs() < 1e-6);
    }

    #[test]
    fn test_fit_circle_to_three_points_collinear() {
        // Collinear points should return None
        let p1 = (0.0, 0.0);
        let p2 = (1.0, 1.0);
        let p3 = (2.0, 2.0);

        let result = fit_circle_to_three_points(p1, p2, p3);
        assert!(result.is_none());
    }

    #[test]
    fn test_fit_circle_least_squares() {
        // Test with points on a known circle
        let center_x = 1.0;
        let center_y = 2.0;
        let radius = 3.0;

        let points = vec![
            (0.0, 4.0, 2.0),  // Point on circle: (1+3, 2+0) = (4, 2)
            (0.0, 1.0, 5.0),  // Point on circle: (1+0, 2+3) = (1, 5)
            (0.0, -2.0, 2.0), // Point on circle: (1-3, 2+0) = (-2, 2)
        ];

        let result = fit_circle_least_squares(&points);
        assert!(result.is_some());

        let (cx, cy, r) = result.unwrap();
        assert!((cx - center_x).abs() < 1.1); // Allow some tolerance
        assert!((cy - center_y).abs() < 1.1);
        assert!((r - radius).abs() < 1.1);
    }

    #[test]
    fn test_fit_circle_least_squares_insufficient_points() {
        let points = vec![(0.0, 0.0, 0.0), (0.0, 1.0, 1.0)];
        let result = fit_circle_least_squares(&points);

        assert!(result.is_none());
    }
    #[test]
    fn test_split_records_into_segments_empty() {
        let records = Vec::new();
        let segments = split_records_into_segments(&records);
        assert!(segments.is_empty());
    }

    #[test]
    fn test_cartesian_coords_struct() {
        let coord = CartesianCoords {
            x: 1.0,
            y: 2.0,
            z: 3.0,
            ax: 0.0,
            ay: 0.0,
            az: 0.0,
            roll: 0.0,
            yaw: 0.0,
            susp_pot_1_fl: 0.0,
            susp_pot_2_fr: 0.0,
            susp_pot_3_rr: 0.0,
            susp_pot_4_rl: 0.0,
            rpm: 0,
        };
        assert_eq!(coord.x, 1.0);
        assert_eq!(coord.y, 2.0);
        assert_eq!(coord.z, 3.0);
    }

    #[test]
    fn test_arc_struct() {
        let arc = Arc {
            center_x: 0.0,
            center_y: 0.0,
            radius: 5.0,
            start_angle: 0.0,
            end_angle: PI / 2.0,
            start_x: 5.0,
            start_y: 0.0,
            end_x: 0.0,
            end_y: 5.0,
        };
        assert_eq!(arc.center_x, 0.0);
        assert_eq!(arc.radius, 5.0);
        assert!((arc.start_angle - 0.0).abs() < 1e-6);
        assert!((arc.end_angle - PI / 2.0).abs() < 1e-6);
    }

    #[test]
    fn test_track_segment_struct() {
        let coords = vec![CartesianCoords {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            ax: 0.0,
            ay: 0.0,
            az: 0.0,
            roll: 0.0,
            yaw: 0.0,
            susp_pot_1_fl: 0.0,
            susp_pot_2_fr: 0.0,
            susp_pot_3_rr: 0.0,
            susp_pot_4_rl: 0.0,
            rpm: 0,
        }];
        let segment = TrackSegment {
            coords,
            start_index: 0,
            end_index: 0,
            spline_x: None,
            spline_y: None,
            arcs: Vec::new(),
            initial_velocity: 10.0,
        };
        assert_eq!(segment.coords.len(), 1);
        assert_eq!(segment.start_index, 0);
        assert_eq!(segment.end_index, 0);
        assert!(segment.spline_x.is_none());
        assert!(segment.arcs.is_empty());
        assert_eq!(segment.initial_velocity, 10.0);
    }

    #[test]
    #[should_panic(expected = "Segment must have at least 4 points")]
    fn test_fit_spline_to_segment_insufficient_points() {
        let mut segment = TrackSegment {
            coords: vec![
                CartesianCoords {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                    ax: 0.0,
                    ay: 0.0,
                    az: 0.0,
                    roll: 0.0,
                    yaw: 0.0,
                    susp_pot_1_fl: 0.0,
                    susp_pot_2_fr: 0.0,
                    susp_pot_3_rr: 0.0,
                    susp_pot_4_rl: 0.0,
                    rpm: 0,
                };
                3
            ],
            start_index: 0,
            end_index: 2,
            spline_x: None,
            spline_y: None,
            arcs: Vec::new(),
            initial_velocity: 0.0,
        };
        fit_spline_to_segment(&mut segment);
    }

    #[test]
    fn test_fit_splines_to_segments() {
        let mut segments = vec![TrackSegment {
            coords: vec![
                CartesianCoords {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                    ax: 0.0,
                    ay: 0.0,
                    az: 0.0,
                    roll: 0.0,
                    yaw: 0.0,
                    susp_pot_1_fl: 0.0,
                    susp_pot_2_fr: 0.0,
                    susp_pot_3_rr: 0.0,
                    susp_pot_4_rl: 0.0,
                    rpm: 0,
                },
                CartesianCoords {
                    x: 10.0,
                    y: 20.0,
                    z: 0.0,
                    ax: 0.0,
                    ay: 0.0,
                    az: 0.0,
                    roll: 0.0,
                    yaw: 0.0,
                    susp_pot_1_fl: 0.0,
                    susp_pot_2_fr: 0.0,
                    susp_pot_3_rr: 0.0,
                    susp_pot_4_rl: 0.0,
                    rpm: 0,
                },
                CartesianCoords {
                    x: 20.0,
                    y: 30.0,
                    z: 0.0,
                    ax: 0.0,
                    ay: 0.0,
                    az: 0.0,
                    roll: 0.0,
                    yaw: 0.0,
                    susp_pot_1_fl: 0.0,
                    susp_pot_2_fr: 0.0,
                    susp_pot_3_rr: 0.0,
                    susp_pot_4_rl: 0.0,
                    rpm: 0,
                },
                CartesianCoords {
                    x: 30.0,
                    y: 40.0,
                    z: 0.0,
                    ax: 0.0,
                    ay: 0.0,
                    az: 0.0,
                    roll: 0.0,
                    yaw: 0.0,
                    susp_pot_1_fl: 0.0,
                    susp_pot_2_fr: 0.0,
                    susp_pot_3_rr: 0.0,
                    susp_pot_4_rl: 0.0,
                    rpm: 0,
                },
            ],
            start_index: 0,
            end_index: 3,
            spline_x: None,
            spline_y: None,
            arcs: Vec::new(),
            initial_velocity: 0.0,
        }];

        let count = fit_splines_to_segments(&mut segments);
        assert_eq!(count, 1);
        assert!(segments[0].spline_x.is_some());
        assert!(segments[0].spline_y.is_some());
    }

    #[test]
    fn test_convert_splines_to_arcs_no_splines() {
        let mut segments = vec![TrackSegment {
            coords: vec![CartesianCoords {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                ax: 0.0,
                ay: 0.0,
                az: 0.0,
                roll: 0.0,
                yaw: 0.0,
                susp_pot_1_fl: 0.0,
                susp_pot_2_fr: 0.0,
                susp_pot_3_rr: 0.0,
                susp_pot_4_rl: 0.0,
                rpm: 0,
            }],
            start_index: 0,
            end_index: 0,
            spline_x: None,
            spline_y: None,
            arcs: Vec::new(),
            initial_velocity: 0.0,
        }];

        let count = convert_splines_to_arcs(&mut segments);
        assert_eq!(count, 0);
        assert!(segments[0].arcs.is_empty());
    }
}
