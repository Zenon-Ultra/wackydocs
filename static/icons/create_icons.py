#!/usr/bin/env python3
"""
Generate PWA icons from SVG
"""

import os
from xml.etree.ElementTree import Element, SubElement, tostring

def create_svg_icon(size, filename):
    """Create an SVG icon with the WackyDocs logo"""
    
    # Create SVG root
    svg = Element('svg')
    svg.set('width', str(size))
    svg.set('height', str(size))
    svg.set('viewBox', f'0 0 {size} {size}')
    svg.set('xmlns', 'http://www.w3.org/2000/svg')
    
    # Background circle
    bg_circle = SubElement(svg, 'circle')
    bg_circle.set('cx', str(size//2))
    bg_circle.set('cy', str(size//2))
    bg_circle.set('r', str(size//2 - 2))
    bg_circle.set('fill', '#ffc107')
    bg_circle.set('stroke', '#fff')
    bg_circle.set('stroke-width', '4')
    
    # Document icon
    doc_width = size * 0.4
    doc_height = size * 0.5
    doc_x = (size - doc_width) / 2
    doc_y = (size - doc_height) / 2
    
    # Document body
    doc_rect = SubElement(svg, 'rect')
    doc_rect.set('x', str(doc_x))
    doc_rect.set('y', str(doc_y))
    doc_rect.set('width', str(doc_width))
    doc_rect.set('height', str(doc_height))
    doc_rect.set('fill', '#fff')
    doc_rect.set('rx', '4')
    
    # Document lines
    line_spacing = doc_height / 6
    for i in range(3):
        line = SubElement(svg, 'rect')
        line.set('x', str(doc_x + doc_width * 0.15))
        line.set('y', str(doc_y + line_spacing * (i + 1.5)))
        line.set('width', str(doc_width * 0.7))
        line.set('height', '2')
        line.set('fill', '#333')
    
    # Korean character "문" (door/document)
    text = SubElement(svg, 'text')
    text.set('x', str(size//2))
    text.set('y', str(size//2 + size * 0.08))
    text.set('text-anchor', 'middle')
    text.set('font-family', 'sans-serif')
    text.set('font-size', str(size * 0.2))
    text.set('font-weight', 'bold')
    text.set('fill', '#333')
    text.text = '문'
    
    # Save SVG
    svg_content = tostring(svg, encoding='unicode')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(svg_content)

# Icon sizes for PWA
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for size in sizes:
    filename = f'icon-{size}x{size}.svg'
    create_svg_icon(size, filename)
    print(f'Created {filename}')

# Create PNG placeholder script
png_script = '''#!/bin/bash
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
'''

with open('convert_to_png.sh', 'w') as f:
    f.write(png_script)

os.chmod('convert_to_png.sh', 0o755)
print('Created convert_to_png.sh script')