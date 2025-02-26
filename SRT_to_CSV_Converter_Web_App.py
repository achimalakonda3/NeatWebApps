import streamlit as st
import pandas as pd
from io import BytesIO
import re
import svgwrite
  

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

def create_svg_from_coordinates(coordinates, dot_size=5, filename='path.svg'):
    if not coordinates:
        raise ValueError("No coordinates provided")
    
    origin_lon, origin_lat = coordinates[0]
    
    # Convert coordinates to relative positions
    relative_coords = [(lon - origin_lon, origin_lat - lat) for lon, lat in coordinates]
    
    # Scale factor for visualization
    scale = 1000  # Adjust as needed
    
    # Offset to center the path
    min_x = min(x for x, y in relative_coords)
    min_y = min(y for x, y in relative_coords)
    
    path_coords = [(scale * (x - min_x), scale * (y - min_y)) for x, y in relative_coords]
    
    # Create SVG
    dwg = svgwrite.Drawing(filename, profile='tiny')
    for x, y in path_coords:
        dwg.add(dwg.circle(center=(x, y), r=dot_size, fill='black'))
    
    render_svg(dwg)

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
    coordinates = map_data[['Latitude', 'Longitude']].to_numpy()
    create_svg_from_coordinates(coordinates, 2)

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

