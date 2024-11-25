################ Button Styles ################

# Style for blue-colored buttons
BLUE_BUTTON_STYLE = """
QPushButton {
    background-color: #007BFF;  /* Blue background */
    color: white;  /* White text color */
    border: none;  /* Remove default border */
    border-radius: 7px;  /* Rounded corners */
}
QPushButton:hover {
    background-color: #0056b3;  /* Darker blue when hover */
}
"""

# Style for gray-colored buttons
GRAY_BUTTON_STYLE = """
QPushButton {
    background-color: #6c757d;  /* Gray background */
    color: white;  /* White text color */
    border: none;  /* Remove default border */
    border-radius: 7px;  /* Rounded corners */
}
QPushButton:hover {
    background-color: #5a6268;  /* Darker gray when hover */
}
"""

################ Input Field Style ################

# Style for folder input fields
FOLDER_INPUT_STYLE = """
QLineEdit {
    background-color: #6c757d;  /* Dark gray background */
    color: white;  /* White text color */
    border-radius: 13px;  /* Rounded corners */
    padding: 4px;  /* Padding for spacing */
    padding-left: 12px;
}
"""

################ General Button Styles for MainApp ################

# Style buttons in the MainApp with a green color
MAIN_APP_BUTTON_STYLE = """
QPushButton {
    background-color: #4CAF50;  /* Green background */
    color: white;  /* White text color */
    border: none;  /* Remove default border */
    border-radius: 5px;  /* Rounded corners */
}
QPushButton:hover {
    background-color: #45a049;  /* Darker green on hover */
}
"""

################ TextEdit (Status Area) Styles ################

# Style for QTextEdit areas - status display
STATUS_AREA_STYLE = """
QTextEdit {
    color: white;  /* White text color for readability */
    background-color: #2c2c2c;  /* Dark background for contrast */
    border: none;  /* Remove default border */
    padding: 5px;  /* Padding for inner spacing */
}
"""

################ Dialog and Card Styles ################

# Style for the File Organizer Customization Dialog
FILE_ORGANIZER_DIALOG_STYLE = """
QDialog {
    background-color: #2E3030;
    border-radius: 10px;
}
QCheckBox {
    color: white;
    padding: 5px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
"""

# Style for card widgets
CARD_STYLE = """
QWidget[class="card"] {
    background-color: #333333;
    border: 1px solid #4f4f4f;  /* Dark border */
    border-radius: 8px;
    margin: 5px 0px;
    padding: 10px 10px;  /* Padding to add space at top and bottom */
}
"""

# Style for the separator line
SEPARATOR_STYLE = """
QFrame {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(79, 79, 79, 0),
        stop:0.1 rgba(79, 79, 79, 255),
        stop:0.9 rgba(79, 79, 79, 255),
        stop:1 rgba(79, 79, 79, 0)
    );
    margin-left: 10px;
    margin-right: 10px;
}
"""
