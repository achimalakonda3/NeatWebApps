import streamlit as st
import pandas as pd
from io import BytesIO
import re
import base64
  

# Regular Expression Patterns
frame_pattern = re.compile(r"FrameCnt: (\d+), DiffTime: (\d+ms)")
datetime_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
parameters_pattern = re.compile(
    r"\[iso: (\d+)\] \[shutter: ([\d/\.]+)\] \[fnum: ([\d\.]+)\] \[ev: ([\d\-\.]+)\] "
    r"\[color_md: (\w+)\] \[focal_len: ([\d\.]+)\] \[latitude: ([\d\.\-]+)\] "
    r"\[longitude: ([\d\.\-]+)\] \[rel_alt: ([\d\.\-]+) abs_alt: ([\d\.\-]+)\] \[ct: (\d+)\]"
)

def parse_srt_to_csv(srt_file_content):
    lines = srt_file_content.splitlines()

    data = []
    current_frame = {}

    for line in lines:
        line = line.strip()

        # Check for frame number line
        if line.isdigit():
            current_frame['FrameNumber'] = int(line)
        
        # Check for the timestamp line
        elif '-->' in line:
            start_time, end_time = line.split(' --> ')
            current_frame['StartTime'] = start_time
            current_frame['EndTime'] = end_time
        
        # Extract data from content lines
        else:
            frame_match = frame_pattern.search(line)
            datetime_match = datetime_pattern.search(line)
            parameters_match = parameters_pattern.search(line)

            if frame_match:
                current_frame['FrameCnt'] = int(frame_match.group(1))
                current_frame['DiffTime'] = frame_match.group(2)

            if datetime_match:
                current_frame['DateTime'] = datetime_match.group(1)

            if parameters_match:
                current_frame.update({
                    'ISO': int(parameters_match.group(1)),
                    'ShutterSpeed': parameters_match.group(2),
                    'FNum': float(parameters_match.group(3)),
                    'EV': float(parameters_match.group(4)),
                    'ColorMode': parameters_match.group(5),
                    'FocalLength': float(parameters_match.group(6)),
                    'Latitude': float(parameters_match.group(7)),
                    'Longitude': float(parameters_match.group(8)),
                    'RelAlt': float(parameters_match.group(9)),
                    'AbsAlt': float(parameters_match.group(10)),
                    'CT': int(parameters_match.group(11)),
                })

        # If a blank line is reached, it means the end of a frame block
        if line == "":
            if current_frame:  # Add the frame data if it exists
                data.append(current_frame)
            current_frame = {}  # Reset for the next frame

    # Convert the data list to a pandas DataFrame
    df = pd.DataFrame(data)
    return df

def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)

@st.cache_data
def create_svg_from_coordinates(coordinates, frame_num, dot_size=5, filename='path.svg'):
    if not coordinates.any():
        raise ValueError("No coordinates provided")
    
    origin_lon, origin_lat = coordinates[0]
    
    # Convert coordinates to relative positions
    relative_coords = [(lon - origin_lon, origin_lat - lat) for lon, lat in coordinates]
    
    
    # Offset to center the path
    min_x = min(x for x, y in relative_coords)
    min_y = min(y for x, y in relative_coords)

    max_x = max(x for x, y in relative_coords)
    max_y = max(y for x, y in relative_coords)
    
    # Scale factor for visualization
    scale = 10000000
    scale = 500 / max((max_x-min_x), (max_y - min_y))
    st.write(dot_size)

    path_coords = [(int(scale * (x - min_x))+dot_size, int(scale * (y - min_y))+dot_size) for x, y in relative_coords]

    height = int(scale* (max_y-min_y)) + 2*dot_size + 50
    width = int(scale * (max_x-min_x)) + 2*dot_size

    dot_size = min(height, width) / 200
    
    # Create SVG
    map_to_display = f'<?xml version="1.0" encoding="utf-8"?>'
    map_to_display += f'\n<svg width="{width}px" height="{height}px" version="1.1" xmlns="http://www.w3.org/2000/svg">'
    # Graph all the points except first and last
    map_to_display += f'<g id="path_points">'
    for x, y in path_coords[1:-1]:
        map_to_display += f'\n    <circle cx="{x}" cy="{y}" r="{dot_size}" fill= "#FFA500" />'
    map_to_display += f'</g>'
    # Add a line:
    map_to_display += f'\n<g id="line">'
    map_to_display += f'\n    <polyline points="'
    for x, y in path_coords:
        map_to_display += f'{x},{y} '
    map_to_display += f'" \n    style="fill:none; stroke:blue; stroke-width:{dot_size/2}" />'
    map_to_display += f'</g>'

    # Add start point to a group
    map_to_display += f'\n<g id="start_point">'
    map_to_display += f'\n    <circle cx="{path_coords[0][0]}" cy="{path_coords[0][1]}" r="{2*dot_size}" fill="green" />'
    map_to_display += f'</g>'
    # Add end point to a group
    map_to_display += f'\n<g id="end_point">'
    map_to_display += f'\n    <circle cx="{path_coords[-1][0]}" cy="{path_coords[-1][1]}" r="{2*dot_size}" fill="red" />'
    map_to_display += f'</g>'

    # # Save the SVG (only from local prototyping)
    # with open('slightly_incorrectly_displayed_map.svg', 'w') as f:
    #     f.write(map_to_display)

    return(map_to_display, path_coords, dot_size)

def create_svg_fg_from_coordinates(path_coords, frame_num, dot_size=5):
    # Add the highlghted point to the svg
    map_to_display = f'\n<g id="Highlighted_point">'
    map_to_display += f'\n    <circle cx="{path_coords[frame_num-1][0]}" cy="{path_coords[frame_num-1][1]}" r="{5*dot_size}" fill="white" />'
    map_to_display += f'</g>'
    map_to_display += f'\n</svg>'

    return(map_to_display)


# Page Title
st.title("🪶🎈 Drone SRT File to CSV converter and visualizer")
st.markdown('###')


# File upload

uploaded_file = st.file_uploader("Upload your SRT file", type=["srt"])


if uploaded_file is not None:
    # Read file content
    srt_content = uploaded_file.read().decode("utf-8")

    # Process the file
    map_data = parse_srt_to_csv(srt_content)
    frame_num = st.slider("Flight Timeline Slider", 1, map_data["FrameCnt"].iloc[-1])
    coordinates = map_data[['Latitude', 'Longitude']].to_numpy()
    bg, path_coords, dot_size = create_svg_from_coordinates(coordinates, frame_num)
    fg = create_svg_fg_from_coordinates(path_coords, frame_num, dot_size)
    path_svg = bg + fg
    render_svg(path_svg)

    # Download SVG
    file_name = st.text_input("Name SVG File", value="path")
    st.download_button('Download Path as SVG', data=path_svg, file_name=f'{file_name}.svg')

    # Display the DataFrame
    st.subheader("Parsed Data")
    st.dataframe(map_data)

    # Download CSV
    csv_buffer = BytesIO()
    map_data.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    st.download_button(
        label="Download CSV",
        data=csv_buffer,
        file_name=f"{uploaded_file.name[:-4]}.csv",
        mime="text/csv",
    )
