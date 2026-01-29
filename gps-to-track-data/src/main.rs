mod plotting;
mod records;

use colored::Colorize;
use plotting::{plot_2d_track, plot_arcs, plot_segmented_track, plot_splines};
use records::{
    CartesianCoords, TrackSegment, convert_splines_to_arcs, fit_splines_to_segments, read_csv,
    records_to_cartesian, split_records_into_segments,
};
use std::fs::File;
use std::io::Write;

fn main() {
    println!(
        "{}",
        "=== GPS Data Analysis Pipeline ===".bright_cyan().bold()
    );

    match read_csv("drive_days/10-4-2025/Eric/5.csv") {
        Ok(records) => {
            println!(
                "\n{} {}",
                "✓".green().bold(),
                format!("Loaded {} records", records.len()).bright_white()
            );

            // Step 1: Convert GPS coordinates to Cartesian coordinates
            print_step(1, "GPS → Cartesian Conversion");
            let cartesian_coords = records_to_cartesian(&records);

            let total_distance = calculate_distance(&cartesian_coords);
            println!("  {} {:.2} m", "Distance:".bright_white(), total_distance);

            // Export raw Cartesian coordinates
            if let Err(e) =
                export_cartesian_coords(&cartesian_coords, "./output/01_cartesian_coords.csv")
            {
                print_error(&format!("Failed to export Cartesian coords: {}", e));
            } else {
                println!(
                    "  {} ./output/01_cartesian_coords.csv",
                    "Exported:".bright_black()
                );
            }

            // Generate 2D track plot
            if let Err(e) = plot_2d_track(&cartesian_coords, "./track_2d.html") {
                print_error(&format!("Plot generation failed: {}", e));
            }

            // Step 2: Segment Detection
            print_step(2, "GPS Segment Detection");
            let mut segments = split_records_into_segments(&records);

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

            // Export segment summary
            if let Err(e) = export_segments_summary(&segments, "./output/02_segments.csv") {
                print_error(&format!("Failed to export segments: {}", e));
            } else {
                println!("  {} ./output/02_segments.csv", "Exported:".bright_black());
            }

            if let Err(e) = plot_segmented_track(&segments, "./track_segmented.html") {
                print_error(&format!("Segmented plot failed: {}", e));
            }

            // Step 3: Spline Fitting
            print_step(3, "Spline Fitting");
            let spline_count = fit_splines_to_segments(&mut segments);
            println!(
                "  {} {} / {}",
                "Fitted:".bright_white(),
                spline_count,
                segments.len()
            );

            // Export spline points
            if let Err(e) = export_spline_points(&segments, "./output/03_spline_points.csv") {
                print_error(&format!("Failed to export splines: {}", e));
            } else {
                println!(
                    "  {} ./output/03_spline_points.csv",
                    "Exported:".bright_black()
                );
            }

            if let Err(e) = plot_splines(&segments, "./track_splines.html") {
                print_error(&format!("Spline plot failed: {}", e));
            }

            // Step 4: Arc Conversion
            print_step(4, "Arc Conversion");
            let arc_count = convert_splines_to_arcs(&mut segments);
            let total_arcs: usize = segments.iter().map(|s| s.arcs.len()).sum();
            println!(
                "  {} {} segments → {} arcs",
                "Converted:".bright_white(),
                arc_count,
                total_arcs
            );

            // Arc statistics
            let mut arc_radii = Vec::new();
            for segment in segments.iter() {
                for arc in segment.arcs.iter() {
                    arc_radii.push(arc.radius);
                }
            }

            if !arc_radii.is_empty() {
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

            // Export arcs
            if let Err(e) = export_arcs(&segments, "./output/04_arcs.csv") {
                print_error(&format!("Failed to export arcs: {}", e));
            } else {
                println!("  {} ./output/04_arcs.csv", "Exported:".bright_black());
            }

            // Step 5: Velocity Analysis
            print_step(5, "Velocity Analysis");
            let mut segment_velocities = Vec::new();
            for segment in segments.iter() {
                if !segment.arcs.is_empty() {
                    segment_velocities.push(segment.initial_velocity);
                }
            }

            if !segment_velocities.is_empty() {
                let min_v = segment_velocities
                    .iter()
                    .min_by(|a, b| a.partial_cmp(b).unwrap())
                    .unwrap();
                let max_v = segment_velocities
                    .iter()
                    .max_by(|a, b| a.partial_cmp(b).unwrap())
                    .unwrap();
                let avg_v =
                    segment_velocities.iter().sum::<f64>() / segment_velocities.len() as f64;

                println!(
                    "  {} {:.1} - {:.1} mph (avg: {:.1} mph)",
                    "Range:".bright_white(),
                    min_v * 2.23694,
                    max_v * 2.23694,
                    avg_v * 2.23694
                );

                // Export velocities
                if let Err(e) = export_velocities(&segments, "./output/05_velocities.csv") {
                    print_error(&format!("Failed to export velocities: {}", e));
                } else {
                    println!(
                        "  {} ./output/05_velocities.csv",
                        "Exported:".bright_black()
                    );
                }
            }

            if let Err(e) = plot_arcs(&segments, "./track_arcs.html") {
                print_error(&format!("Arc plot failed: {}", e));
            }

            // Final Summary
            println!("\n{}", "=== Pipeline Complete ===".bright_cyan().bold());
            println!(
                "  {} track_2d.html, track_segmented.html, track_splines.html, track_arcs.html",
                "Plots:".bright_white()
            );
            println!("  {} ./output/", "Data:".bright_white());
        }
        Err(e) => {
            print_error(&format!("CSV read failed: {}", e));
        }
    }
}

fn print_step(step: u8, description: &str) {
    println!(
        "\n{} {}",
        format!("[{}]", step).bright_blue().bold(),
        description.bright_white().bold()
    );
}

fn print_error(msg: &str) {
    println!("  {} {}", "✗".red().bold(), msg.red());
}

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

fn export_cartesian_coords(coords: &[CartesianCoords], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(file, "index,x_m,y_m,z_m")?;
    for (i, coord) in coords.iter().enumerate() {
        writeln!(file, "{},{:.6},{:.6},{:.6}", i, coord.x, coord.y, coord.z)?;
    }
    Ok(())
}

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

fn export_spline_points(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(file, "segment_id,sample_index,x_m,y_m")?;

    for (seg_idx, segment) in segments.iter().enumerate() {
        if segment.spline_x.is_some() && segment.spline_y.is_some() {
            let spline_x = segment.spline_x.as_ref().unwrap();
            let spline_y = segment.spline_y.as_ref().unwrap();

            // Sample 100 points along the spline
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

fn export_arcs(segments: &[TrackSegment], path: &str) -> std::io::Result<()> {
    std::fs::create_dir_all("./output")?;
    let mut file = File::create(path)?;
    writeln!(
        file,
        "segment_id,arc_id,center_x_m,center_y_m,radius_m,start_angle_rad,end_angle_rad,start_x_m,start_y_m,end_x_m,end_y_m,arc_length_m"
    )?;

    for (seg_idx, segment) in segments.iter().enumerate() {
        for (arc_idx, arc) in segment.arcs.iter().enumerate() {
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
