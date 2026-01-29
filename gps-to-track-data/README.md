# GPS Data Smoothing v2

A Rust application for processing, smoothing, and visualizing GPS track data from racing/automotive applications.

## Features

- **CSV Import**: Read GPS data from CSV files with extensive telemetry fields
- **Coordinate Conversion**: Convert GPS coordinates (lat/lon) to local Cartesian coordinates
- **Segment Detection**: Automatically detect and split tracks at frozen GPS sensor readings
- **Velocity Capture**: Extract initial velocity for each segment for lap simulation
- **Spline Fitting**: Fit smooth parametric splines to track segments for path smoothing
- **Arc Conversion**: Convert splines into constant-radius circular arcs for racing analysis
- **Interactive Visualization**: Generate interactive HTML plots using Plotly

## Quick Start

```bash
# Build the project
cargo build --release

# Run with default data file
cargo run
```

## Output Files

The program generates four interactive HTML visualizations:

1. **track_2d.html** - Complete track in single color
2. **track_segmented.html** - Track split into colored segments showing data quality
3. **track_splines.html** - Segments with fitted smooth splines overlaid on data points
4. **track_arcs.html** - Track represented as constant-radius circular arcs with centers and radii labeled

## Documentation

- [PLOTTING.md](PLOTTING.md) - Details on visualization capabilities
- [SEGMENTS.md](SEGMENTS.md) - GPS segment detection algorithm and parameters
- [SPLINES.md](SPLINES.md) - Spline fitting implementation and usage
- [ARCS.md](ARCS.md) - Arc conversion algorithm and racing analysis applications
- [VELOCITY.md](VELOCITY.md) - Segment velocity capture and lap simulation integration
- [WORKFLOW.md](WORKFLOW.md) - Complete pipeline from CSV import to arc analysis

## Technical Details

### Coordinate System

Uses equirectangular approximation for GPS to Cartesian conversion:
- X-axis: East (meters)
- Y-axis: North (meters)
- Z-axis: Up (meters)
- Accurate for distances up to several kilometers

### Spline Fitting

- Uses cosine interpolation splines from the `splines` crate
- Parameterized by cumulative distance along track
- Provides smooth, continuous curves suitable for arc conversion
- Minimum 4 points required per segment

### Segment Detection

Automatically detects frozen GPS sensors:
- Splits track when GPS repeats same coordinates 20+ times
- Removes artificial jumps from GPS unfreezing
- Configurable tolerance and thresholds

## Dependencies

- `serde` - Serialization/deserialization
- `csv` - CSV file reading
- `plotly` - Interactive plotting
- `splines` - Spline interpolation

## Racing Analysis

The arc conversion and velocity features enable:
- **Corner radius analysis**: Identify tight hairpins vs. sweeping turns
- **Lap simulation**: Use actual starting velocities with arcs to simulate lap performance
- **Speed estimation**: Calculate theoretical maximum corner speeds
- **Performance comparison**: Compare simulated vs. actual lap times
- **Track characterization**: Analyze track difficulty and rhythm sections
- **Vehicle setup optimization**: Tune suspension for specific corner types
- **Driver analysis**: Identify sections where entry speed was too fast or too slow

## Future Work

- Additional smoothing algorithms
- Path optimization and racing line analysis
- Lap time simulation
- Clothoid transition modeling

## License

(License information to be added)
