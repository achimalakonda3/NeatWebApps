import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
from io import BytesIO

# Function to draw bounding boxes
def draw_bounding_boxes(image, labels, label_classes):
    h, w, _ = image.shape
    for label in labels:
        class_id, x_center, y_center, box_width, box_height = map(float, label)
        class_id = int(class_id)
        x_center, y_center = int(x_center * w), int(y_center * h)
        box_width, box_height = int(box_width * w), int(box_height * h)
        x1, y1 = x_center - box_width // 2, y_center - box_height // 2
        x2, y2 = x_center + box_width // 2, y_center + box_height // 2
        
        # Draw the bounding box
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label_text = label_classes[class_id] if class_id < len(label_classes) else f"Class {class_id}"
        cv2.putText(image, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return image

# Function to convert OpenCV image to bytes for download
def convert_to_bytes(image):
    _, buffer = cv2.imencode('.png', image)
    return BytesIO(buffer)

# Streamlit app
st.title("YOLO Bounding Box Visualizer")

# Upload images
uploaded_images = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
uploaded_labels = st.file_uploader("Upload YOLO Labels", type=["txt"], accept_multiple_files=True)
class_names_file = st.file_uploader("Upload Class Names File (Optional)", type=["txt"])

# Read class names
class_names = []
if class_names_file is not None:
    class_names = class_names_file.read().decode("utf-8").strip().split("\n")

if st.button("Process Images"):
    if len(uploaded_images) != len(uploaded_labels):
        st.error("The number of images and label files must be the same.")
    else:
        for img_file, lbl_file in zip(uploaded_images, uploaded_labels):
            # Read image
            img = Image.open(img_file)
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Read labels
            labels = lbl_file.read().decode("utf-8").strip().split("\n")
            labels = [line.split() for line in labels]

            # Draw bounding boxes
            img_with_boxes = draw_bounding_boxes(img_cv, labels, class_names)

            # Convert back to PIL for Streamlit display
            img_with_boxes_pil = Image.fromarray(cv2.cvtColor(img_with_boxes, cv2.COLOR_BGR2RGB))

            # Convert to bytes for download
            img_bytes = convert_to_bytes(img_with_boxes)

            # Display the image
            st.image(img_with_boxes_pil, caption=f"Processed: {img_file.name}", use_column_width=True)

            # Provide a download link
            st.download_button(
                label=f"Download {img_file.name} with Boxes",
                data=img_bytes,
                file_name=f"processed_{img_file.name}",
                mime="image/png"
            )
