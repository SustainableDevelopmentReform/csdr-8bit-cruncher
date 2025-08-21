#!/usr/bin/env python3
"""
Converts multi-band geospatial raster images to 8-bit RGB GeoTIFFs.

This script takes a multi-band raster (16-bit or float) and converts it to an
8-bit RGB GeoTIFF by selecting three bands and scaling them to 0-255 range.
"""

import argparse
import sys
import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling


def create_world_file(transform, output_path):
    """
    Create a .tfw world file from a rasterio transform.
    
    Args:
        transform: Affine transform from rasterio
        output_path: Path to the output GeoTIFF (used to derive .tfw path)
    """
    # Replace extension with .tfw
    base_path = os.path.splitext(output_path)[0]
    tfw_path = base_path + '.tfw'
    
    # Extract parameters from affine transform
    # Transform format: | a  b  c |
    #                   | d  e  f |
    #                   | 0  0  1 |
    # Where: a = pixel width, e = pixel height (negative), 
    #        c = upper left x, f = upper left y
    
    with open(tfw_path, 'w') as f:
        f.write(f"{transform.a}\n")  # pixel size in x direction
        f.write(f"{transform.b}\n")  # rotation term (usually 0)
        f.write(f"{transform.d}\n")  # rotation term (usually 0)
        f.write(f"{transform.e}\n")  # pixel size in y direction (negative)
        f.write(f"{transform.c}\n")  # x coordinate of upper left pixel center
        f.write(f"{transform.f}\n")  # y coordinate of upper left pixel center
    
    return tfw_path


def scale_to_8bit(bands_data, nodata=None):
    """
    Scale multi-band data to 8-bit (0-255) using global min/max.
    
    Args:
        bands_data: numpy array of shape (3, height, width)
        nodata: NoData value to exclude from calculations
    
    Returns:
        uint8 numpy array of shape (3, height, width)
    """
    # Create mask for valid data
    if nodata is not None:
        valid_mask = bands_data != nodata
    else:
        valid_mask = ~np.isnan(bands_data)
    
    # Find global min and max across all three bands
    if np.any(valid_mask):
        global_min = np.min(bands_data[valid_mask])
        global_max = np.max(bands_data[valid_mask])
    else:
        # Fallback if all data is NoData
        global_min = 0
        global_max = 1
    
    # Avoid division by zero
    if global_max == global_min:
        scaled = np.zeros_like(bands_data, dtype=np.uint8)
    else:
        # Scale to 0-255 range
        scaled = (bands_data - global_min) / (global_max - global_min) * 255
        
        # Handle NoData values
        scaled = np.where(valid_mask, scaled, 0)
        
        # Clip values and convert to uint8
        scaled = np.clip(scaled, 0, 255).astype(np.uint8)
    
    return scaled


def convert_raster_to_rgb(input_path, output_path, band_r, band_g, band_b, 
                         min_value=None, max_value=None):
    """
    Convert a multi-band raster to 8-bit RGB GeoTIFF.
    
    Args:
        input_path: Path to input raster file
        output_path: Path to output GeoTIFF
        band_r: Band number for red channel (1-indexed)
        band_g: Band number for green channel (1-indexed)
        band_b: Band number for blue channel (1-indexed)
        min_value: Optional minimum value for scaling
        max_value: Optional maximum value for scaling
    """
    # Open the input raster
    with rasterio.open(input_path) as src:
        # Validate band indices
        num_bands = src.count
        for band_idx, band_name in [(band_r, 'Red'), (band_g, 'Green'), (band_b, 'Blue')]:
            if band_idx < 1 or band_idx > num_bands:
                raise ValueError(f"{band_name} band index {band_idx} is out of range. "
                               f"File has {num_bands} bands.")
        
        # Read selected bands
        print(f"Reading bands {band_r}, {band_g}, {band_b} from {input_path}")
        band_data = np.array([
            src.read(band_r),
            src.read(band_g),
            src.read(band_b)
        ])
        
        # Get NoData value if it exists
        nodata = src.nodata
        
        # Override min/max if provided
        if min_value is not None and max_value is not None:
            # Create mask for valid data
            if nodata is not None:
                valid_mask = band_data != nodata
            else:
                valid_mask = ~np.isnan(band_data)
            
            # Scale using provided values
            if max_value == min_value:
                scaled_data = np.zeros_like(band_data, dtype=np.uint8)
            else:
                scaled_data = (band_data - min_value) / (max_value - min_value) * 255
                scaled_data = np.where(valid_mask, scaled_data, 0)
                scaled_data = np.clip(scaled_data, 0, 255).astype(np.uint8)
        else:
            # Use automatic scaling
            scaled_data = scale_to_8bit(band_data, nodata)
        
        # Prepare output metadata
        out_meta = src.meta.copy()
        out_meta.update({
            'driver': 'GTiff',
            'dtype': 'uint8',
            'count': 3,
            'compress': 'lzw',  # Add compression for smaller files
            'photometric': 'RGB',  # Specify RGB interpretation
            'nodata': None  # 8-bit RGB typically doesn't use NoData
        })
        
        # Write the output GeoTIFF
        print(f"Writing 8-bit RGB GeoTIFF to {output_path}")
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(scaled_data[0], 1)  # Red
            dst.write(scaled_data[1], 2)  # Green
            dst.write(scaled_data[2], 3)  # Blue
            
            # Set color interpretation
            dst.colorinterp = [
                rasterio.enums.ColorInterp.red,
                rasterio.enums.ColorInterp.green,
                rasterio.enums.ColorInterp.blue
            ]
        
        # Create world file
        tfw_path = create_world_file(src.transform, output_path)
        print(f"Created world file: {tfw_path}")
        
        # Print summary statistics
        print("\nConversion complete!")
        print(f"Input: {num_bands} bands, {src.dtypes[0]}")  # Get dtype from first band
        print(f"Output: 3 bands (RGB), uint8")
        print(f"Dimensions: {src.width} x {src.height}")
        if src.crs:
            print(f"CRS: {src.crs}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert multi-band geospatial raster to 8-bit RGB GeoTIFF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert bands 4, 3, 2 to RGB
  python raster_to_rgb.py input.tif output.tif -r 4 -g 3 -b 2
  
  # Use custom min/max values for scaling
  python raster_to_rgb.py input.tif output.tif -r 1 -g 2 -b 3 --min 0 --max 10000
        """
    )
    
    # Required arguments
    parser.add_argument('input', help='Path to input raster file')
    parser.add_argument('output', help='Path to output GeoTIFF file')
    
    # Band selection arguments
    parser.add_argument('-r', '--red', type=int, required=True,
                       help='Band number for red channel (1-indexed)')
    parser.add_argument('-g', '--green', type=int, required=True,
                       help='Band number for green channel (1-indexed)')
    parser.add_argument('-b', '--blue', type=int, required=True,
                       help='Band number for blue channel (1-indexed)')
    
    # Optional scaling parameters
    parser.add_argument('--min', type=float, default=None,
                       help='Minimum value for scaling (default: auto from data)')
    parser.add_argument('--max', type=float, default=None,
                       help='Maximum value for scaling (default: auto from data)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Validate min/max arguments
    if (args.min is not None) != (args.max is not None):
        print("Error: Both --min and --max must be specified together.", file=sys.stderr)
        sys.exit(1)
    
    try:
        convert_raster_to_rgb(
            args.input,
            args.output,
            args.red,
            args.green,
            args.blue,
            args.min,
            args.max
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()