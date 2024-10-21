import sys
import json
from textwrap import indent

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, \
    QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QEvent


def load_quotes_from_file():
    # if quotes.json not exist, open() will create it
    print("Loading quotes from file...")
    try:
        with open('quotes.json', 'r') as file:
            File = json.load(file)
    except FileNotFoundError:
        with open('quotes.json', 'w') as file:
            json.dump([], file)
        File = []
    print("Quotes loaded.")
    return File


def save_quotes_to_file(quotes):
    print("Saving quotes to file...")
    with open('quotes.json', 'w') as file:
        json.dump(quotes, file, ensure_ascii=False, indent=4)
    print("Quotes saved.")


class QuotesApp(QWidget):
    def __init__(self):
        super().__init__()
        # table init
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(['Speaker', 'Quote'])
        self.init_ui()
        # detect key press
        self.tableWidget.installEventFilter(self)

    def init_ui(self):
        # table layout
        self.setWindowTitle('Quotes Viewer')
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()
        quotes = load_quotes_from_file()
        self.tableWidget.setRowCount(len(quotes))  # set table row count
        # print content
        for row, item in enumerate(quotes):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(item['speaker']))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(item['quote']))
        # stretch the last column
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)

        # button layout
        buttonLayout = QHBoxLayout()
        # add column button
        addColumnButton = QPushButton('Add Quote')
        addColumnButton.clicked.connect(self.add_column_button_on_click)
        # save button
        saveButton = QPushButton('Save')
        saveButton.clicked.connect(self.save_confirm_msg)  # when clicked, call SaveConfirmMSG to pop confirm box
        # add buttons to ButtonLayout
        buttonLayout.addWidget(addColumnButton)
        buttonLayout.addWidget(saveButton)

        # add all content to layout
        layout.addWidget(self.tableWidget)
        layout.addLayout(buttonLayout)
        # display the layout
        self.setLayout(layout)
        self.show()

    # detect key press
    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            print(f"Key Press Detected: {event.key()}")
            # detect delete
            if event.key() == 16777219:     # delete = 16777219
                print("Detected delete key press.")
                selectCells = self.tableWidget.selectionModel().selectedIndexes()
                selectedRows = self.tableWidget.selectionModel().selectedRows()
                for index in sorted(selectCells):
                    self.tableWidget.setItem(index.row(), index.column(), QTableWidgetItem(''))
                    print("Cell cleared.")
                for index in sorted(selectedRows):
                    self.tableWidget.removeRow(index.row())
                    print("Row removed.")
                return True
        return super().eventFilter(source, event)

    def add_column_button_on_click(self):
        print("Add Column Button Clicked")
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        self.tableWidget.setItem(self.tableWidget.rowCount() + 1, 0, QTableWidgetItem(''))
        self.tableWidget.setItem(self.tableWidget.rowCount() + 1, 1, QTableWidgetItem(''))

    def save_quotes(self):
        print("Save button clicked")
        # check if any cell is empty, show error message box
        for row in range(self.tableWidget.rowCount()):
            for column in range(self.tableWidget.columnCount()):
                if self.tableWidget.item(row, column) is None:
                    print("Empty cell detected, show error message box.")
                    QMessageBox.critical(self, 'Error', 'Please fill in all the cells.')
                    return
        quotes = []
        for row in range(self.tableWidget.rowCount()):
            speaker = self.tableWidget.item(row, 0).text()
            quote = self.tableWidget.item(row, 1).text()
            quotes.append({'speaker': speaker, 'quote': quote})
        save_quotes_to_file(quotes)

    def save_confirm_msg(self):
        print("Pop save confirm message box")
        reply = QMessageBox.question(self, '确认',
                                     "Are you sure to save the quotes?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            print("Confirm: Yes")
            QMessageBox.information(self, 'Saved', 'Quotes saved.')
            self.save_quotes()
        else:
            print("Confirm: No")
            return


def main():
    app = QApplication(sys.argv)
    ex = QuotesApp()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
