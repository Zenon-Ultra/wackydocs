#!/bin/bash
# Convert SVG icons to PNG using ImageMagick (if available)
# Install ImageMagick: sudo apt-get install imagemagick

for size in 72 96 128 144 152 192 384 512; do
    if command -v convert &> /dev/null; then
        convert "icon-${size}x${size}.svg" "icon-${size}x${size}.png"
        echo "Converted icon-${size}x${size}.png"
    else
        echo "ImageMagick not available. Using SVG files directly."
        cp "icon-${size}x${size}.svg" "icon-${size}x${size}.png"
    fi
done
