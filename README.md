# Raster to RGB Converter

A lightweight Python script that converts multi-band geospatial raster images (16-bit or float) into 8-bit RGB GeoTIFFs suitable for web mapping and GIS dashboard applications.

## Features

- Convert any 3 bands from a multi-band raster to RGB channels
- Automatic scaling from 16-bit/float to 8-bit (0-255) values
- Global min/max scaling across all three selected bands
- Preserves geospatial metadata (CRS, georeferencing)
- Generates accompanying `.tfw` world file
- Optional custom min/max values for scaling
- LZW compression for smaller output files

## Requirements

### Python Version
- Python 3.7 or higher

### Required Libraries

```bash
pip install rasterio numpy
```

Or using conda:

```bash
conda install -c conda-forge rasterio numpy
```

### Full Installation Example

```bash
# Create a virtual environment (optional but recommended)
python -m venv raster_env
source raster_env/bin/activate  # On Windows: raster_env\Scripts\activate

# Install required packages
pip install rasterio numpy

# Verify installation
python -c "import rasterio; print(f'Rasterio version: {rasterio.__version__}')"
```

## Usage

### Basic Syntax

```bash
python raster_to_rgb.py <input_file> <output_file> -r <red_band> -g <green_band> -b <blue_band>
```

### Parameters

- `input_file`: Path to the input multi-band raster file (GeoTIFF or other GDAL-supported format)
- `output_file`: Path for the output 8-bit RGB GeoTIFF
- `-r, --red`: Band number for the red channel (1-indexed)
- `-g, --green`: Band number for the green channel (1-indexed)
- `-b, --blue`: Band number for the blue channel (1-indexed)
- `--min`: (Optional) Minimum value for scaling
- `--max`: (Optional) Maximum value for scaling

### Examples

#### Example 1: Basic Conversion
Convert a Landsat-style image using bands 4 (NIR), 3 (Red), and 2 (Green) for false color composite:

```bash
python raster_to_rgb.py example.tiff example_rgb.tiff -r 4 -g 3 -b 2
```

#### Example 2: True Color Composite
Create a true color image using bands 3 (Red), 2 (Green), and 1 (Blue):

```bash
python raster_to_rgb.py example.tiff example_truecolor.tiff -r 3 -g 2 -b 1
```

#### Example 3: Custom Scaling
Use specific min/max values for scaling (useful for consistent rendering across multiple images):

```bash
python raster_to_rgb.py example.tiff example_scaled.tiff -r 1 -g 2 -b 3 --min 0 --max 10000
```

#### Example 4: Sentinel-2 False Color
Convert Sentinel-2 imagery to false color (bands 8, 4, 3):

```bash
python raster_to_rgb.py sentinel2_image.tiff sentinel2_rgb.tiff -r 8 -g 4 -b 3
```

## How It Works

1. **Input Reading**: The script reads the specified bands from your multi-band raster file
2. **Scaling**: 
   - Finds the global minimum and maximum values across all three selected bands
   - Scales the values linearly to the 0-255 range using the formula: `(value - min) / (max - min) * 255`
   - Handles NoData values appropriately
3. **Output Generation**:
   - Creates an 8-bit RGB GeoTIFF with proper color interpretation
   - Preserves all geospatial metadata (CRS, transform, etc.)
   - Generates a `.tfw` world file for compatibility with older GIS software

## Output Files

For each conversion, the script generates two files:

1. **GeoTIFF file** (`.tiff` or `.tif`): The 8-bit RGB image with embedded geospatial information
2. **World file** (`.tfw`): A text file containing georeferencing information for GIS compatibility

## Tips and Best Practices

### Band Selection for Common Satellites

**Landsat 8/9:**
- True Color: `-r 4 -g 3 -b 2`
- False Color (vegetation): `-r 5 -g 4 -b 3`
- Natural Color: `-r 4 -g 3 -b 2`

**Sentinel-2:**
- True Color: `-r 4 -g 3 -b 2`
- False Color (vegetation): `-r 8 -g 4 -b 3`
- Agriculture: `-r 11 -g 8 -b 2`

**MODIS:**
- True Color: `-r 1 -g 4 -b 3`
- False Color: `-r 7 -g 2 -b 1`

### Performance Considerations

- The script uses LZW compression by default to reduce file size
- Large rasters (>1GB) may take several seconds to process
- Memory usage is approximately 3x the size of the selected bands

### Troubleshooting

**"Band index out of range" error:**
- Check how many bands your input file has
- Remember that band numbering starts at 1, not 0

**Output looks too dark or too bright:**
- Try using custom `--min` and `--max` values
- Check if your input data has outliers affecting the scaling

**Missing world file:**
- Ensure you have write permissions in the output directory
- The `.tfw` file will have the same base name as your output file

## License

This script is provided as-is for scientific and educational purposes.

## Contributing

Feel free to submit issues or pull requests for improvements and bug fixes.