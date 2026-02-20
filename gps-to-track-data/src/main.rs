//! GPS Data Analysis and Visualization Pipeline
//!
//! This tool processes GPS track data from CSV files, detects frozen GPS readings,
//! converts coordinates to Cartesian space, fits splines, generates racing arcs,
//! and creates interactive 2D visualizations using Plotly.

mod plotting;
mod records;

use clap::Parser;
use colored::Colorize;
use plotting::{
    plot_2d_track, plot_arc_points_detailed, plot_arcs, plot_segmented_track, plot_splines,
};
use records::{
    CartesianCoords, TrackSegment, convert_splines_to_arcs, fit_splines_to_segments,
    map_arcs_to_points, read_csv, records_to_cartesian, split_records_into_segments,
};
use std::fs::File;
use std::io::Write;

/// CLI Arguments for GPS data analysis pipeline
#[derive(Parser, Debug)]
#[command(name = "GPS Data Analysis")]
#[command(about = "Process and visualize GPS racing track data", long_about = None)]
struct Args {
    /// Path to input CSV file containing GPS/telemetry data
    #[arg(short, long, value_name = "FILE")]
    input: Option<String>,

    /// Directory for output files (plots and CSV exports)
    #[arg(short, long, value_name = "DIR", default_value = "./output")]
    output_dir: String,

    /// Directory for output plot files (HTML visualizations)
    #[arg(short, long, value_name = "DIR", default_value = ".")]
    plot_dir: String,
}

impl Args {
    /// Get the default input file path if none provided
    fn get_input_path(&self) -> String {
        self.input
            .clone()
            .unwrap_or_else(|| "drive_days/10-4-2025/Eric/5.csv".to_string())
    }
}

fn main() {
    let args = Args::parse();

    println!(
        "{}",
        "=== GPS Data Analysis Pipeline ===".bright_cyan().bold()
    );

    // Display configuration
    println!("{}", "Configuration:".bright_white().bold());
    println!("  {} {}", "Input:".bright_black(), args.get_input_path());
    println!("  {} {}", "Output data:".bright_black(), args.output_dir);
    println!("  {} {}", "Output plots:".bright_black(), args.plot_dir);

    match read_csv(&args.get_input_path()) {
        Ok(records) => {
            println!(
                "\n{} {}",
                "✓".green().bold(),
                format!("Loaded {} records", records.len()).bright_white()
            );

            // Step 1: GPS to Cartesian Conversion
            process_step_1_cartesian_conversion(&records, &args.output_dir, &args.plot_dir);

            // Step 2: Segment Detection
            let mut segments = process_step_2_segment_detection(&records, &args.output_dir);

            // Step 3: Spline Fitting
            process_step_3_spline_fitting(&mut segments, &args.output_dir, &args.plot_dir);

            // Step 4: Arc Conversion
            process_step_4_arc_conversion(&mut segments, &args.output_dir, &args.plot_dir);

            // Step 5: Velocity Analysis & Export Arc Points
            process_step_5_velocity_and_exports(
                &segments,
                &records,
                &args.output_dir,
                &args.plot_dir,
            );

            // Final Summary
            println!("\n{}", "=== Pipeline Complete ===".bright_cyan().bold());
            println!(
                "  {} Multiple plot files generated",
                "Plots:".bright_white()
            );
            println!("  {} {}/", "Data:".bright_white(), args.output_dir);
        }
        Err(e) => {
            print_error(&format!("CSV read failed: {}", e));
        }
    }
}

/// STEP 1: Convert GPS records to Cartesian coordinates and generate initial visualization
fn process_step_1_cartesian_conversion(
    records: &[records::Record],
    output_dir: &str,
    plot_dir: &str,
) {
    print_step(1, "GPS → Cartesian Conversion");

    // Convert GPS latitude/longitude to local Cartesian coordinates (East, North, Up)
    let cartesian_coords = records_to_cartesian(records);
    let total_distance = calculate_distance(&cartesian_coords);

    println!("  {} {:.2} m", "Distance:".bright_white(), total_distance);

    // Export raw Cartesian coordinates to CSV for inspection
    let output_file = format!("{}/01_cartesian_coords.csv", output_dir);
    match export_cartesian_coords(&cartesian_coords, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export Cartesian coords: {}", e)),
    }

    // Generate 2D track visualization showing all GPS data points
    let plot_file = format!("{}/track_2d.html", plot_dir);
    if let Err(e) = plot_2d_track(&cartesian_coords, &plot_file) {
        print_error(&format!("Plot generation failed: {}", e));
    }
}

/// STEP 2: Detect GPS segments by identifying and filtering frozen GPS readings
fn process_step_2_segment_detection(
    records: &[records::Record],
    output_dir: &str,
) -> Vec<TrackSegment> {
    print_step(2, "GPS Segment Detection");

    // Split records into valid segments, excluding frozen GPS periods and artificial jumps
    let segments = split_records_into_segments(records);

    // Calculate segment statistics
    let total_segment_points: usize = segments.iter().map(|s| s.coords.len()).sum();
    let excluded_points = records.len() - total_segment_points;
    let percentage_good = (total_segment_points as f64 / records.len() as f64) * 100.0;

    println!("  {} {}", "Segments:".bright_white(), segments.len());
    println!(
        "  {} {} / {} ({:.1}%)",
        "Valid:".green(),
        total_segment_points,
        records.len(),
        percentage_good
    );
    println!(
        "  {} {} ({:.1}%)",
        "Excluded:".red(),
        excluded_points,
        100.0 - percentage_good
    );

    // Export segment summary to CSV
    let output_file = format!("{}/02_segments.csv", output_dir);
    match export_segments_summary(&segments, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export segments: {}", e)),
    }

    // Generate segmented visualization showing data quality
    if let Err(e) = plot_segmented_track(&segments, "./track_segmented.html") {
        print_error(&format!("Segmented plot failed: {}", e));
    }

    segments
}

/// STEP 3: Fit smooth parametric splines to each segment
fn process_step_3_spline_fitting(segments: &mut [TrackSegment], output_dir: &str, plot_dir: &str) {
    print_step(3, "Spline Fitting");

    // Fit cosine interpolation splines to each segment's x, y coordinates
    let spline_count = fit_splines_to_segments(segments);

    println!(
        "  {} {} / {}",
        "Fitted:".bright_white(),
        spline_count,
        segments.len()
    );

    // Export spline sample points to CSV for analysis
    let output_file = format!("{}/03_spline_points.csv", output_dir);
    match export_spline_points(segments, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export splines: {}", e)),
    }

    // Generate visualization with splines overlaid on original data points
    if let Err(e) = plot_splines(segments, "./track_splines.html") {
        print_error(&format!("Spline plot failed: {}", e));
    }
}

/// STEP 4: Convert splines to constant-radius circular arcs for racing analysis
fn process_step_4_arc_conversion(segments: &mut [TrackSegment], output_dir: &str, plot_dir: &str) {
    print_step(4, "Arc Conversion");

    // Fit circular arcs to splines for constant-radius approximation
    let arc_count = convert_splines_to_arcs(segments);
    let total_arcs: usize = segments.iter().map(|s| s.arcs.len()).sum();

    println!(
        "  {} {} segments → {} arcs",
        "Converted:".bright_white(),
        arc_count,
        total_arcs
    );

    // Calculate arc statistics for track characterization
    let mut arc_radii = Vec::new();
    for segment in segments.iter() {
        for arc in segment.arcs.iter() {
            arc_radii.push(arc.radius);
        }
    }

    if !arc_radii.is_empty() {
        // Find min/max/average arc radius
        let min_r = arc_radii
            .iter()
            .min_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap();
        let max_r = arc_radii
            .iter()
            .max_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap();
        let avg_r = arc_radii.iter().sum::<f64>() / arc_radii.len() as f64;

        println!(
            "  {} {:.1}m - {:.1}m (avg: {:.1}m)",
            "Radius:".bright_white(),
            min_r,
            max_r,
            avg_r
        );

        // Classify arcs by cornering difficulty
        let tight = arc_radii.iter().filter(|&&r| r < 30.0).count();
        let medium = arc_radii.iter().filter(|&&r| r >= 30.0 && r < 80.0).count();
        let fast = arc_radii.iter().filter(|&&r| r >= 80.0).count();

        println!(
            "  {} {}  {} {}  {} {}",
            "Tight (<30m):".yellow(),
            tight,
            "Medium (30-80m):".bright_yellow(),
            medium,
            "Fast (>80m):".green(),
            fast
        );
    }

    // Export arc definitions to CSV
    let output_file = format!("{}/04_arcs.csv", output_dir);
    match export_arcs(segments, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export arcs: {}", e)),
    }
}

/// STEP 5: Analyze velocities and export detailed arc-to-point mappings
fn process_step_5_velocity_and_exports(
    segments: &[TrackSegment],
    records: &[records::Record],
    output_dir: &str,
    plot_dir: &str,
) {
    print_step(5, "Velocity Analysis");

    // Collect initial velocities from segments that have arcs
    let segment_velocities: Vec<f64> = segments
        .iter()
        .filter(|s| !s.arcs.is_empty())
        .map(|s| s.initial_velocity)
        .collect();

    if !segment_velocities.is_empty() {
        // Calculate velocity statistics
        let min_v = segment_velocities
            .iter()
            .min_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap();
        let max_v = segment_velocities
            .iter()
            .max_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap();
        let avg_v = segment_velocities.iter().sum::<f64>() / segment_velocities.len() as f64;

        println!(
            "  {} {:.1} - {:.1} mph (avg: {:.1} mph)",
            "Range:".bright_white(),
            min_v * 2.23694,
            max_v * 2.23694,
            avg_v * 2.23694
        );

        // Export velocity summary for lap simulation setup
        let output_file = format!("{}/05_velocities.csv", output_dir);
        match export_velocities(segments, &output_file) {
            Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
            Err(e) => print_error(&format!("Failed to export velocities: {}", e)),
        }
    }

    // Export detailed arc-to-point mapping with arc metadata for analysis
    let output_file = format!("{}/06_arc_points_detailed.csv", output_dir);
    match export_arc_points_detailed(segments, records, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export detailed arc points: {}", e)),
    }

    // Export simplified arc-to-point mapping
    let output_file = format!("{}/06_arc_points.csv", output_dir);
    match export_arc_points(segments, records, &output_file) {
        Ok(_) => println!("  {} {}", "Exported:".bright_black(), output_file),
        Err(e) => print_error(&format!("Failed to export arc points: {}", e)),
    }

    // Generate arc visualizations
    if let Err(e) = plot_arcs(segments, "./track_arcs.html") {
        print_error(&format!("Arc plot failed: {}", e));
    }

    if let Err(e) = plot_arc_points_detailed(segments, records, "./track_arc_points_detailed.html")
    {
        print_error(&format!("Arc points detailed plot failed: {}", e));
    }
}

/// Print a formatted section header for pipeline steps
fn print_step(step: u8, description: &str) {
    println!(
        "\n{} {}",
        format!("[{}]", step).bright_blue().bold(),
        description.bright_white().bold()
    );
}

/// Print a formatted error message
fn print_error(msg: &str) {
    println!("  {} {}", "✗".red().bold(), msg.red());
}

/// Calculate total Euclidean distance traveled through all coordinates
fn calculate_distance(coords: &[CartesianCoords]) -> f64 {
    if coords.len() < 2 {
        return 0.0;
    }

    let mut total_distance = 0.0;
    for i in 1..coords.len() {
        let dx = coords[i].x - coords[i - 1].x;
        let dy = coords[i].y - coords[i - 1].y;
        let dz = coords[i].z - coords[i - 1].z;
        total_distance += (dx * dx + dy * dy + dz * dz).sqrt();
    }
    total_distance
}

/// Export raw Cartesian coordinates to CSV file
///
/// Writes all converted GPS coordinates in Cartesian space (East, North, Up)
/// for inspection and debugging of coordinate conversion.
fn export_cartesian_coords(coords: &[CartesianCoords], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(file, "index,x_m,y_m,z_m")?;
    for (i, coord) in coords.iter().enumerate() {
        writeln!(file, "{},{:.6},{:.6},{:.6}", i, coord.x, coord.y, coord.z)?;
    }
    Ok(())
}

/// Export a summary of each detected GPS segment
///
/// Includes segment boundaries, point counts, and initial velocity for lap simulation setup.
fn export_segments_summary(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(
        file,
        "segment_id,start_index,end_index,point_count,initial_velocity_mps,initial_velocity_mph"
    )?;
    for (i, segment) in segments.iter().enumerate() {
        writeln!(
            file,
            "{},{},{},{},{:.6},{:.3}",
            i + 1,
            segment.start_index,
            segment.end_index,
            segment.coords.len(),
            segment.initial_velocity,
            segment.initial_velocity * 2.23694
        )?;
    }
    Ok(())
}

/// Export sampled spline points for visualization and validation
///
/// Samples 100 points along each segment's fitted spline to show smooth path approximation.
fn export_spline_points(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(file, "segment_id,sample_index,x_m,y_m")?;

    for (seg_idx, segment) in segments.iter().enumerate() {
        if segment.spline_x.is_some() && segment.spline_y.is_some() {
            let spline_x = segment.spline_x.as_ref().unwrap();
            let spline_y = segment.spline_y.as_ref().unwrap();

            // Sample 100 evenly-spaced points along the spline
            for i in 0..100 {
                let t = i as f64 / 99.0;
                if let (Some(x), Some(y)) = (spline_x.sample(t), spline_y.sample(t)) {
                    writeln!(file, "{},{},{:.6},{:.6}", seg_idx + 1, i, x, y)?;
                }
            }
        }
    }
    Ok(())
}

/// Export arc definitions with geometric properties for racing analysis
///
/// Contains center coordinates, radius, angles, and arc length for each constant-radius arc.
/// Useful for corner speed calculations and track characterization.
fn export_arcs(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(
        file,
        "segment_id,arc_id,center_x_m,center_y_m,radius_m,start_angle_rad,end_angle_rad,start_x_m,start_y_m,end_x_m,end_y_m,arc_length_m"
    )?;

    for (seg_idx, segment) in segments.iter().enumerate() {
        for (arc_idx, arc) in segment.arcs.iter().enumerate() {
            // Calculate arc length from radius and angle difference
            let mut angle_diff = arc.end_angle - arc.start_angle;
            if angle_diff < 0.0 {
                angle_diff += 2.0 * std::f64::consts::PI;
            }
            let arc_length = arc.radius * angle_diff;

            writeln!(
                file,
                "{},{},{:.6},{:.6},{:.3},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.3}",
                seg_idx + 1,
                arc_idx + 1,
                arc.center_x,
                arc.center_y,
                arc.radius,
                arc.start_angle,
                arc.end_angle,
                arc.start_x,
                arc.start_y,
                arc.end_x,
                arc.end_y,
                arc_length
            )?;
        }
    }
    Ok(())
}

/// Export initial velocities for each segment with arc information
///
/// Used to set up lap simulation with actual starting speeds from telemetry data.
fn export_velocities(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(
        file,
        "segment_id,initial_velocity_mps,initial_velocity_mph,initial_velocity_kmh,arc_count"
    )?;

    for (seg_idx, segment) in segments.iter().enumerate() {
        if !segment.arcs.is_empty() {
            writeln!(
                file,
                "{},{:.6},{:.3},{:.3},{}",
                seg_idx + 1,
                segment.initial_velocity,
                segment.initial_velocity * 2.23694,
                segment.initial_velocity * 3.6,
                segment.arcs.len()
            )?;
        }
    }
    Ok(())
}

/// Export arc-to-original-point mapping with full telemetry data
///
/// Maps each GPS point to its assigned arc, allowing correlation of telemetry
/// (acceleration, suspension, etc.) with specific track sections.
fn export_arc_points(
    segments: &[TrackSegment],
    records: &[records::Record],
    path: &str,
) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;

    // Write header with telemetry fields
    writeln!(
        file,
        "segment_id,arc_id,global_index,time_s,x_m,y_m,z_m,ax_g,ay_g,az_g,roll_deg,yaw_deg,susp_fl,susp_fr,susp_rr,susp_rl,rpm"
    )?;

    // Get arc-to-point mappings
    let arc_mappings = map_arcs_to_points(segments);

    // Write each point with its arc association
    for mapping in arc_mappings.iter() {
        // Use the segment's start time as t=0 for relative timing
        let segment = &segments[mapping.segment_id - 1];
        let first_gps_millis = records[segment.start_index].gps_millis;

        for (i, point) in mapping.points.iter().enumerate() {
            let global_idx = mapping.global_indices[i];
            let gps_millis = records[global_idx].gps_millis;
            let time_s = (gps_millis - first_gps_millis) as f64 / 1000.0;

            writeln!(
                file,
                "{},{},{},{:.3},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{}",
                mapping.segment_id,
                mapping.arc_id,
                global_idx,
                time_s,
                point.x,
                point.y,
                point.z,
                point.ax,
                point.ay,
                point.az,
                point.roll,
                point.yaw,
                point.susp_pot_1_fl,
                point.susp_pot_2_fr,
                point.susp_pot_3_rr,
                point.susp_pot_4_rl,
                point.rpm
            )?;
        }
    }

    Ok(())
}

/// Export arc-to-point mapping with detailed arc metadata
///
/// Includes arc geometry (center, radius, angles) alongside telemetry data
/// for advanced analysis combining track geometry with vehicle dynamics.
fn export_arc_points_detailed(
    segments: &[TrackSegment],
    records: &[records::Record],
    path: &str,
) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;

    // Write header including arc geometry and point telemetry
    writeln!(
        file,
        "segment_id,arc_id,global_index,time_s,arc_center_x_m,arc_center_y_m,arc_radius_m,arc_start_angle_rad,arc_end_angle_rad,point_x_m,point_y_m,point_z_m,ax_g,ay_g,az_g,roll_deg,yaw_deg,susp_fl,susp_fr,susp_rr,susp_rl,rpm"
    )?;

    // Get arc-to-point mappings
    let arc_mappings = map_arcs_to_points(segments);

    // Write each point with its arc association and complete arc metadata
    for mapping in arc_mappings.iter() {
        // Use the segment's start time as t=0 for relative timing
        let segment = &segments[mapping.segment_id - 1];
        let first_gps_millis = records[segment.start_index].gps_millis;

        for (i, point) in mapping.points.iter().enumerate() {
            let global_idx = mapping.global_indices[i];
            let gps_millis = records[global_idx].gps_millis;
            let time_s = (gps_millis - first_gps_millis) as f64 / 1000.0;

            writeln!(
                file,
                "{},{},{},{:.3},{:.6},{:.6},{:.3},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{}",
                mapping.segment_id,
                mapping.arc_id,
                global_idx,
                time_s,
                mapping.arc.center_x,
                mapping.arc.center_y,
                mapping.arc.radius,
                mapping.arc.start_angle,
                mapping.arc.end_angle,
                point.x,
                point.y,
                point.z,
                point.ax,
                point.ay,
                point.az,
                point.roll,
                point.yaw,
                point.susp_pot_1_fl,
                point.susp_pot_2_fr,
                point.susp_pot_3_rr,
                point.susp_pot_4_rl,
                point.rpm
            )?;
        }
    }

    Ok(())
}
