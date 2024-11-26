################ Button Styles ################

# Style for blue-colored buttons
BLUE_BUTTON_STYLE = """
QPushButton {
    background-color: #007BFF;
    color: white;
    border: none;
    border-radius: 7px;
}
QPushButton:hover {
    background-color: #0056b3;
}
"""

# Style for gray-colored buttons
GRAY_BUTTON_STYLE = """
QPushButton {
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 7px;
}
QPushButton:hover {
    background-color: #5a6268;
}
"""

################ Input Field Style ################

# Style for folder input fields
FOLDER_INPUT_STYLE = """
QLineEdit {
    background-color: #6c757d;
    color: white;
    border-radius: 13px;
    padding: 4px;
    padding-left: 12px;
}
"""

################ General Button Styles for MainApp ################

# Style buttons in the MainApp with a green color
MAIN_APP_BUTTON_STYLE = """
QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
}
QPushButton:hover {
    background-color: #45a049;
}
"""

################ TextEdit (Status Area) Styles ################

# Style for QTextEdit areas - status display
STATUS_AREA_STYLE = """
QTextEdit {
    color: white;
    background-color: #2c2c2c;
    border: none;
    padding: 5px;
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
    border: 1px solid #4f4f4f;
    border-radius: 8px;
    margin: 1px 0px;
    padding: 8px 8px;
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

# Style for InfoWindow's central widget
INFO_WINDOW_STYLE = """
QWidget#central_widget {
    background-color: #2E3030;
    border-radius: 10px;
    border: 1px solid #4f4f4f;
}
"""
