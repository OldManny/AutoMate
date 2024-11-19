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
}
"""

################ Card (Container) Style ################

# Style for container widgets like cards
CARD_STYLE = """
QWidget {
    border: 1px solid #444;  /* Dark border */
    border-radius: 10px;  /* Rounded corners */
    background-color: #2c2c2c;  /* Dark background */
    padding: 10px;  /* Padding for inner content */
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
