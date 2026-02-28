use crate::records::{
    CartesianCoords, Record, TrackSegment, calculate_cumulative_distances, map_arcs_to_points,
};
use plotly::{
    Plot, Scatter,
    common::{Line, Marker, Mode},
    configuration::Configuration,
    layout::{DragMode, Layout},
};
use std::fs;

/// Plots a 2D top-down view of the track (X-Y plane, looking down from above).
///
/// # Arguments
/// * `coords` - Slice of Cartesian coordinates to plot
/// * `filename` - Output HTML filename
///
/// # Returns
/// * `Result<(), Box<dyn std::error::Error>>` - Ok if successful
pub fn plot_2d_track(
    coords: &[CartesianCoords],
    filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let x: Vec<f64> = coords.iter().map(|c| c.x).collect();
    let y: Vec<f64> = coords.iter().map(|c| c.y).collect();

    let trace = Scatter::new(x, y)
        .mode(Mode::LinesMarkers)
        .name("Track Path")
        .line(Line::new().width(2.0))
        .marker(Marker::new().size(4))
        .web_gl_mode(true);

    let mut plot = Plot::new();
    plot.add_trace(trace);

    let layout = Layout::new().auto_size(true).drag_mode(DragMode::Pan);
    plot.set_layout(layout);

    let config = Configuration::new().scroll_zoom(true);
    plot.set_configuration(config);

    let html = plot.to_html();
    let modified_html = html
        .replace(
            "<head>",
            "<head><style>html, body { height: 100%; margin: 0; padding: 0; }</style>",
        )
        .replace(
            "style=\"height:100%; width:100%;\"",
            "style=\"position:absolute;top:0;left:0;width:100%;height:100%;\"",
        );
    fs::write(filename, modified_html).unwrap();

    println!("2D track plot saved to: {}", filename);
    Ok(())
}

/// Plots multiple track segments in different colors to visualize good vs bad GPS data.
/// Each segment is rendered in a different color for easy visual verification.
///
/// # Arguments
/// * `segments` - Slice of track segments to plot
/// * `filename` - Output HTML filename
///
/// # Returns
/// * `Result<(), Box<dyn std::error::Error>>` - Ok if successful
pub fn plot_segmented_track(
    segments: &[TrackSegment],
    filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut plot = Plot::new();

    let config = Configuration::new().scroll_zoom(true);
    plot.set_configuration(config);

    // Color palette for different segments
    let colors = vec![
        "rgb(31, 119, 180)",  // Blue
        "rgb(255, 127, 14)",  // Orange
        "rgb(44, 160, 44)",   // Green
        "rgb(214, 39, 40)",   // Red
        "rgb(148, 103, 189)", // Purple
        "rgb(140, 86, 75)",   // Brown
        "rgb(227, 119, 194)", // Pink
        "rgb(127, 127, 127)", // Gray
        "rgb(188, 189, 34)",  // Olive
        "rgb(23, 190, 207)",  // Cyan
    ];

    for (i, segment) in segments.iter().enumerate() {
        let x: Vec<f64> = segment.coords.iter().map(|c| c.x).collect();
        let y: Vec<f64> = segment.coords.iter().map(|c| c.y).collect();

        let color = colors[i % colors.len()];
        let trace = Scatter::new(x, y)
            .mode(Mode::LinesMarkers)
            .name(format!(
                "Segment {} ({}-{})",
                i + 1,
                segment.start_index,
                segment.end_index
            ))
            .line(Line::new().width(2.0).color(color))
            .marker(Marker::new().size(4).color(color))
            .web_gl_mode(true);

        plot.add_trace(trace);
    }

    let layout = Layout::new()
        .auto_size(true)
        .drag_mode(DragMode::Pan)
        .title(plotly::common::Title::with_text(format!(
            "Track with {} Good Segments",
            segments.len()
        )));
    plot.set_layout(layout);

    let html = plot.to_html();
    let modified_html = html
        .replace(
            "<head>",
            "<head><style>html, body { height: 100%; margin: 0; padding: 0; }</style>",
        )
        .replace(
            "style=\"height:100%; width:100%;\"",
            "style=\"position:absolute;top:0;left:0;width:100%;height:100%;\"",
        );
    fs::write(filename, modified_html).unwrap();

    println!(
        "Segmented track plot with {} segments saved to: {}",
        segments.len(),
        filename
    );
    Ok(())
}

/// Plots fitted splines for track segments alongside the original data points.
/// Original data points are shown as small markers, and the fitted splines are shown as smooth lines.
///
/// # Arguments
/// * `segments` - Slice of track segments with fitted splines
/// * `filename` - Output HTML filename
///
/// # Returns
/// * `Result<(), Box<dyn std::error::Error>>` - Ok if successful
pub fn plot_splines(
    segments: &[TrackSegment],
    filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut plot = Plot::new();

    let config = Configuration::new().scroll_zoom(true);
    plot.set_configuration(config);

    // Color palette for different segments
    let colors = vec![
        "rgb(31, 119, 180)",  // Blue
        "rgb(255, 127, 14)",  // Orange
        "rgb(44, 160, 44)",   // Green
        "rgb(214, 39, 40)",   // Red
        "rgb(148, 103, 189)", // Purple
        "rgb(140, 86, 75)",   // Brown
        "rgb(227, 119, 194)", // Pink
        "rgb(127, 127, 127)", // Gray
        "rgb(188, 189, 34)",  // Olive
        "rgb(23, 190, 207)",  // Cyan
    ];

    for (i, segment) in segments.iter().enumerate() {
        let color = colors[i % colors.len()];

        // Plot original data points
        let x_points: Vec<f64> = segment.coords.iter().map(|c| c.x).collect();
        let y_points: Vec<f64> = segment.coords.iter().map(|c| c.y).collect();

        let points_trace = Scatter::new(x_points, y_points)
            .mode(Mode::Markers)
            .name(format!("Segment {} data", i + 1))
            .marker(Marker::new().size(5).color(color))
            .web_gl_mode(true);

        plot.add_trace(points_trace);

        // Plot spline if available
        if let (Some(spline_x), Some(spline_y)) = (&segment.spline_x, &segment.spline_y) {
            // Calculate cumulative distance for parameterization
            let cumulative_distances = calculate_cumulative_distances(&segment.coords);
            let total_distance = cumulative_distances[cumulative_distances.len() - 1];

            // Sample the spline at many points for a smooth curve
            let num_samples = 200;
            let mut x_spline = Vec::new();
            let mut y_spline = Vec::new();

            for k in 0..=num_samples {
                let t = (k as f64 / num_samples as f64) * total_distance;
                if let Some(x_val) = spline_x.clamped_sample(t)
                    && let Some(y_val) = spline_y.clamped_sample(t)
                {
                    x_spline.push(x_val);
                    y_spline.push(y_val);
                }
            }

            let spline_trace = Scatter::new(x_spline, y_spline)
                .mode(Mode::Lines)
                .name(format!("Segment {} spline", i + 1))
                .line(Line::new().width(3.0).color(color))
                .web_gl_mode(true);

            plot.add_trace(spline_trace);
        }
    }

    let layout = Layout::new()
        .auto_size(true)
        .drag_mode(DragMode::Pan)
        .title(plotly::common::Title::with_text(format!(
            "Track Segments with Fitted Splines ({} segments)",
            segments.len()
        )));
    plot.set_layout(layout);

    let html = plot.to_html();
    let modified_html = html
        .replace(
            "<head>",
            "<head><style>html, body { height: 100%; margin: 0; padding: 0; }</style>",
        )
        .replace(
            "style=\"height:100%; width:100%;\"",
            "style=\"position:absolute;top:0;left:0;width:100%;height:100%;\"",
        );
    fs::write(filename, modified_html).unwrap();

    println!(
        "Spline plot with {} segments saved to: {}",
        segments.len(),
        filename
    );
    Ok(())
}

/// Plots constant-radius arcs fitted to track segments alongside the original splines.
/// This allows visual comparison of how well the arcs approximate the splines.
///
/// # Arguments
/// * `segments` - Slice of track segments with fitted splines and arcs
/// * `filename` - Output HTML filename
///
/// # Returns
/// * `Result<(), Box<dyn std::error::Error>>` - Ok if successful
pub fn plot_arcs(
    segments: &[TrackSegment],
    filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut plot = Plot::new();

    let config = Configuration::new().scroll_zoom(true);
    plot.set_configuration(config);

    // Color palette for different segments
    let colors = vec![
        "rgb(31, 119, 180)",  // Blue
        "rgb(255, 127, 14)",  // Orange
        "rgb(44, 160, 44)",   // Green
        "rgb(214, 39, 40)",   // Red
        "rgb(148, 103, 189)", // Purple
        "rgb(140, 86, 75)",   // Brown
        "rgb(227, 119, 194)", // Pink
        "rgb(127, 127, 127)", // Gray
        "rgb(188, 189, 34)",  // Olive
        "rgb(23, 190, 207)",  // Cyan
    ];

    let mut total_arcs = 0;

    for (seg_idx, segment) in segments.iter().enumerate() {
        let color = colors[seg_idx % colors.len()];

        // Plot the original spline first (if available) as a reference
        if let (Some(spline_x), Some(spline_y)) = (&segment.spline_x, &segment.spline_y) {
            let cumulative_distances = calculate_cumulative_distances(&segment.coords);
            let total_distance = cumulative_distances[cumulative_distances.len() - 1];

            let num_samples = 200;
            let mut x_spline = Vec::new();
            let mut y_spline = Vec::new();

            for k in 0..=num_samples {
                let t = (k as f64 / num_samples as f64) * total_distance;
                if let Some(x_val) = spline_x.clamped_sample(t)
                    && let Some(y_val) = spline_y.clamped_sample(t)
                {
                    x_spline.push(x_val);
                    y_spline.push(y_val);
                }
            }

            let spline_trace = Scatter::new(x_spline, y_spline)
                .mode(Mode::Lines)
                .name(format!("Seg {} spline (reference)", seg_idx + 1))
                .line(
                    Line::new()
                        .width(2.0)
                        .color(color)
                        .dash(plotly::common::DashType::Dash),
                )
                .opacity(0.4)
                .show_legend(true)
                .web_gl_mode(true);

            plot.add_trace(spline_trace);
        }

        // Plot the arcs
        for (arc_idx, arc) in segment.arcs.iter().enumerate() {
            total_arcs += 1;

            // Generate points along the arc
            let num_arc_points = 50;
            let mut x_arc = Vec::new();
            let mut y_arc = Vec::new();

            // Determine direction of arc (clockwise or counterclockwise)
            let mut angle_diff = arc.end_angle - arc.start_angle;

            // Normalize angle difference to [-π, π]
            while angle_diff > std::f64::consts::PI {
                angle_diff -= 2.0 * std::f64::consts::PI;
            }
            while angle_diff < -std::f64::consts::PI {
                angle_diff += 2.0 * std::f64::consts::PI;
            }

            for i in 0..=num_arc_points {
                let t = i as f64 / num_arc_points as f64;
                let angle = arc.start_angle + t * angle_diff;
                let x = arc.center_x + arc.radius * angle.cos();
                let y = arc.center_y + arc.radius * angle.sin();
                x_arc.push(x);
                y_arc.push(y);
            }

            let arc_trace_hover: Vec<String> = (0..num_arc_points)
                .into_iter()
                .map(|_| format!("Direction {}", arc.turn_direction().to_string()))
                .collect();

            let arc_trace = Scatter::new(x_arc, y_arc)
                .mode(Mode::Lines)
                .name(format!(
                    "Seg {} Arc {} (R={:.1}m)",
                    seg_idx + 1,
                    arc_idx + 1,
                    arc.radius
                ))
                .line(Line::new().width(3.0).color(color))
                .text_array(arc_trace_hover)
                .hover_info(plotly::common::HoverInfo::Text)
                .web_gl_mode(true);

            plot.add_trace(arc_trace);

            // Plot arc endpoints as markers
            let endpoints_trace =
                Scatter::new(vec![arc.start_x, arc.end_x], vec![arc.start_y, arc.end_y])
                    .mode(Mode::Markers)
                    .name(format!("Seg {} Arc {} endpoints", seg_idx + 1, arc_idx + 1))
                    .marker(Marker::new().size(6).color(color))
                    .show_legend(false)
                    .web_gl_mode(true);

            plot.add_trace(endpoints_trace);
        }
    }

    let layout = Layout::new()
        .auto_size(true)
        .drag_mode(DragMode::Pan)
        .title(plotly::common::Title::with_text(format!(
            "Arc Approximation of Splines ({} arcs) - Dashed lines are original splines",
            total_arcs
        )));
    plot.set_layout(layout);

    let html = plot.to_html();
    let modified_html = html
        .replace(
            "<head>",
            "<head><style>html, body { height: 100%; margin: 0; padding: 0; }</style>",
        )
        .replace(
            "style=\"height:100%; width:100%;\"",
            "style=\"position:absolute;top:0;left:0;width:100%;height:100%;\"",
        );
    fs::write(filename, modified_html).unwrap();

    println!(
        "Arc comparison plot with {} arcs across {} segments saved to: {}",
        total_arcs,
        segments.len(),
        filename
    );
    Ok(())
}

/// Plots arc points with detailed telemetry data from arc_points_detailed.csv.
/// Points are colored by arc and include hover information for telemetry data.
///
/// # Arguments
/// * `segments` - Slice of track segments with arc-to-point mappings
/// * `filename` - Output HTML filename
///
/// # Returns
/// * `Result<(), Box<dyn std::error::Error>>` - Ok if successful
pub fn plot_arc_points_detailed(
    segments: &[TrackSegment],
    records: &[Record],
    filename: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut plot = Plot::new();

    let config = Configuration::new().scroll_zoom(true);
    plot.set_configuration(config);

    // Color palette for different arcs
    let colors = vec![
        "rgb(31, 119, 180)",  // Blue
        "rgb(255, 127, 14)",  // Orange
        "rgb(44, 160, 44)",   // Green
        "rgb(214, 39, 40)",   // Red
        "rgb(148, 103, 189)", // Purple
        "rgb(140, 86, 75)",   // Brown
        "rgb(227, 119, 194)", // Pink
        "rgb(127, 127, 127)", // Gray
        "rgb(188, 189, 34)",  // Olive
        "rgb(23, 190, 207)",  // Cyan
    ];

    // Get arc-to-point mappings
    let arc_mappings = map_arcs_to_points(segments);
    let total_arcs = arc_mappings.len();

    // First, plot arc radius circles as background (initially hidden)
    for (arc_idx, mapping) in arc_mappings.iter().enumerate() {
        let color = colors[arc_idx % colors.len()];

        // Generate circle points for the arc radius
        let num_circle_points = 100;
        let mut circle_x = Vec::new();
        let mut circle_y = Vec::new();

        for i in 0..=num_circle_points {
            let angle = 2.0 * std::f64::consts::PI * (i as f64) / (num_circle_points as f64);
            let x = mapping.arc.center_x + mapping.arc.radius * angle.cos();
            let y = mapping.arc.center_y + mapping.arc.radius * angle.sin();
            circle_x.push(x);
            circle_y.push(y);
        }

        let circle_trace = Scatter::new(circle_x, circle_y)
            .mode(Mode::Lines)
            .name(format!(
                "Circle_Seg{}_Arc{}",
                mapping.segment_id + 1,
                mapping.arc_id + 1
            ))
            .line(
                Line::new()
                    .width(2.0)
                    .color(color)
                    .dash(plotly::common::DashType::Dot),
            )
            .opacity(0.5)
            .visible(plotly::common::Visible::False)
            .show_legend(false)
            .hover_info(plotly::common::HoverInfo::Skip)
            .web_gl_mode(true);

        plot.add_trace(circle_trace);
    }

    // Plot each arc's points (these come after circles in trace order)
    for (arc_idx, mapping) in arc_mappings.iter().enumerate() {
        let color = colors[arc_idx % colors.len()];

        // Extract x and y coordinates
        let x: Vec<f64> = mapping.points.iter().map(|p| p.x).collect();
        let y: Vec<f64> = mapping.points.iter().map(|p| p.y).collect();

        // Get the segment's start index to use as the time reference (t=0)
        let segment = &segments[mapping.segment_id - 1];
        let first_gps_millis = records[segment.start_index].gps_millis;

        // Calculate cumulative distances for the entire segment
        let segment_distances = calculate_cumulative_distances(&segment.coords);

        // Create hover text with telemetry data
        let hover_text: Vec<String> = mapping
            .points
            .iter()
            .enumerate()
            .map(|(i, p)| {
                let global_idx = mapping.global_indices[i];
                let gps_millis = records[global_idx].gps_millis;
                let time_s = (gps_millis - first_gps_millis) as f64 / 1000.0;

                // Get the distance from the segment start
                let point_index_in_segment = global_idx - segment.start_index;
                let distance_m = segment_distances[point_index_in_segment];

                format!(
                    "Arc: S{}-A{}<br>\
                Global Index: {}<br>\
                Time: {:.3}s<br>\
                Distance: {:.3}m<br>\
                Position: ({:.2}, {:.2})<br>\
                Elevation: {:.2}m<br>\
                Accel: ax={:.3}g, ay={:.3}g, az={:.3}g<br>\
                Roll: {:.2}°<br>\
                Yaw: {:.2}°<br>\
                Susp: FL={:.2}, FR={:.2}, RR={:.2}, RL={:.2}<br>\
                RPM: {}<br>\
                Arc Radius: {:.2}m",
                    mapping.segment_id + 1,
                    mapping.arc_id + 1,
                    global_idx,
                    time_s,
                    distance_m,
                    p.x,
                    p.y,
                    p.z,
                    p.ax,
                    p.ay,
                    p.az,
                    p.roll,
                    p.yaw,
                    p.susp_pot_1_fl,
                    p.susp_pot_2_fr,
                    p.susp_pot_3_rr,
                    p.susp_pot_4_rl,
                    p.rpm,
                    mapping.arc.radius
                )
            })
            .collect();

        let trace = Scatter::new(x, y)
            .mode(Mode::Markers)
            .name(format!(
                "Seg {} Arc {} (R={:.1}m, {} pts)",
                mapping.segment_id + 1,
                mapping.arc_id + 1,
                mapping.arc.radius,
                mapping.points.len()
            ))
            .marker(Marker::new().size(6).color(color))
            .text_array(hover_text)
            .hover_info(plotly::common::HoverInfo::Text)
            .web_gl_mode(true);

        plot.add_trace(trace);
    }

    let layout = Layout::new()
        .auto_size(true)
        .drag_mode(DragMode::Pan)
        .title(plotly::common::Title::with_text(format!(
            "Arc Points with Detailed Telemetry ({} arcs)",
            total_arcs
        )));
    plot.set_layout(layout);

    let html = plot.to_html();

    // Add custom JavaScript to show/hide arc circles on hover
    let custom_js = format!(
        r#"
<script>
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {{
        // Find the plotly div - it's the only div with a data-unformatted attribute or look for the plot container
        const plotDiv = document.querySelector('.plotly-graph-div') || document.querySelector('[id^="plotly"]') || document.getElementsByClassName('js-plotly-plot')[0];

        if (!plotDiv) {{
            console.error('Could not find Plotly div');
            return;
        }}

        const totalArcs = {};
        let currentlyVisibleCircle = null;

        console.log('Plotly hover script initialized');

        // On hover, show the corresponding arc circle
        plotDiv.on('plotly_hover', function(data) {{
            const point = data.points[0];
            const traceIndex = point.curveNumber;

            console.log('Hover on trace:', traceIndex, 'Total arcs:', totalArcs);

            // Point traces start after circle traces
            // If hovering over a point trace (not a circle)
            if (traceIndex >= totalArcs) {{
                const arcIndex = traceIndex - totalArcs;

                console.log('Showing circle for arc:', arcIndex);

                // Hide previously visible circle if any
                if (currentlyVisibleCircle !== null && currentlyVisibleCircle !== arcIndex) {{
                    Plotly.restyle(plotDiv, {{visible: false}}, [currentlyVisibleCircle]);
                }}

                // Show the corresponding circle
                Plotly.restyle(plotDiv, {{visible: true}}, [arcIndex]);
                currentlyVisibleCircle = arcIndex;
            }}
        }});

        // On unhover, hide the circle
        plotDiv.on('plotly_unhover', function() {{
            console.log('Unhover event');
            if (currentlyVisibleCircle !== null) {{
                Plotly.restyle(plotDiv, {{visible: false}}, [currentlyVisibleCircle]);
                currentlyVisibleCircle = null;
            }}
        }});
    }});
</script>
"#,
        total_arcs
    );

    let modified_html = html
        .replace(
            "<head>",
            "<head><style>html, body { height: 100%; margin: 0; padding: 0; }</style>",
        )
        .replace(
            "style=\"height:100%; width:100%;\"",
            "style=\"position:absolute;top:0;left:0;width:100%;height:100%;\"",
        )
        .replace("</body>", &format!("{}</body>", custom_js));

    fs::write(filename, modified_html)?;

    println!(
        "Arc points detailed plot with {} arcs saved to: {}",
        total_arcs, filename
    );
    Ok(())
}
