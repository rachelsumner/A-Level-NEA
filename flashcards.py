import math
import os
import random
import sys
import sqlite3
import time

from PyQt4 import QtGui, QtCore
from random import randint
from math import floor


class Window(QtGui.QMainWindow):
    """Revision flashcards window"""
    def __init__(self, user, flashcard):
        """
        Window provides a GUI for the user to engage in the revision process with.
        user - an object reresenting the user
        flashcard - flashcard object used for choosing the words that appear
        userdb - used purely to access upodate_percentages when the revision process is over
        choices - total number of choices the user has made
        """
        super(Window, self).__init__()
        self.user = user
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("Revision Flashcards")
        self.flashcard = flashcard
        self.user.set_level(flashcard.language[0])
        self.flashcard.level = self.user.level
        self.choices = 0
        self.MAX_CHOICES = 20
        self.limited_questions = True
        self.userdb = UserDB()
        self.build_gui()

    def build_gui(self):
        """Builds the gui in a grid layout"""
        self.grid = QtGui.QGridLayout()
        self.font = QtGui.QFont("Courier", 20, QtGui.QFont.Bold)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.start_timer)

        self.timer_text = QtGui.QLineEdit()
        self.timer_text.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_text.setReadOnly(True)
        self.timer_text.setText(str(self.flashcard.time))

        self.score = QtGui.QLineEdit()
        self.score.setAlignment(QtCore.Qt.AlignCenter)
        self.score.setReadOnly(True)
        self.score.setText("100%")

        self.choice_button_array = []

        for i in range(1):
            """Generates the buttons the user presses to choose a word"""
            for j in range(3):
                try:
                    temp = QtGui.QPushButton(self.flashcard.guess_words[i][1])
                except:
                    temp = QtGui.QPushButton("".format(j+1))
                temp.clicked.connect(self.select_choice)
                self.grid.addWidget(temp, i+2, j)
                self.choice_button_array.append(temp)

        self.correct_translation_display = QtGui.QLineEdit()
        self.correct_translation_display.setReadOnly(True)
        self.correct_translation_display.setText("")

        self.grid.addWidget(self.score, 1, 2)
        self.grid.addWidget(self.timer_text, 1, 0)
        self.grid.addWidget(self.correct_translation_display, 1, 1)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.grid)

    def select_choice(self):
        """Resets the timer and updates the percentage every time the user makes a choice, and checks if the
        choice is correct
        """
        self.timer.start(1000)
        self.timer_text.setText(str(self.flashcard.time))
        self.choices += 1
        print(self.choices)
        self.flashcard.percentage_correct(self.sender().text(), self.flashcard.percentage)
        self.score.setText(str(self.flashcard.percentage[0])+"%")

        new_button_words = self.flashcard.choose_words()
        for i in range(3):
            self.choice_button_array[i].setText(new_button_words[i])
        self.correct_translation_display.setText(self.flashcard.correct_translation)
        if self.choices == self.MAX_CHOICES and self.limited_questions:
            QtGui.QMessageBox.warning(self, "It's over!", "You have done {} words and the revision has ended".format(str(self.choices)))
            self.close()
            self.calculate_experience()

    def start_timer(self):
        """Initializes the timer and also checks if it's ran out.
        If the timer's ran out the revision session terminates"""
        self.timer_text.setText(str(int(self.timer_text.text())-1))
        if self.timer_text.text() == "0" and self.choices != self.MAX_CHOICES:
            """self.choices != self.MAX_CHOICES prevents this window from popping up when the process has already terminated"""
            QtGui.QMessageBox.warning(self, "It's over!", "You've run out of time!")
            self.close()
            self.calculate_experience()

    def calculate_experience(self):
        """Calculates the experience gain/loss of the user, updates the percentages and reopens the home window"""
        experience = 0
        if self.timer_text.text() == "0":
            if self.flashcard.correct_english in self.flashcard.statistics:
                self.flashcard.statistics[self.flashcard.correct_english][1] += 1
            print("stats in calc exp",self.flashcard.statistics)
        for i in self.flashcard.statistics:
            """self.flashcard.statistics[i][0]: total times the user has gotten it correct
            self.flashcard.statistics[i][1]: total times words has appeared in current session
            self.flashcard.statistics[i][2]: word's level
            """
            word_level = self.flashcard.statistics[i][2]
            correct = self.flashcard.statistics[i][0]
            incorrect = self.flashcard.statistics[i][1]-self.flashcard.statistics[i][0]
            experience += math.floor((50*correct*word_level)/self.user.level)
            """self.flashcard.statistics[i][2]/self.user.level scales the experience relative to the user's level and the word's level
            If the user's level 6 and the word is level 1 they get 1/6th the experience.
            Example: level 5 user doing a level 2 word they got correct once:
            floor((50*1*2)/5) = 20 experience gained
            """
            experience -= math.floor((30*(total-correct)*word_level)/self.user.level)
            """floor((30*(total-correct)*(user level))/word level))
            Example: level 5 user doing a level 2 word that they got wrong once:
            floor((30*1*5)/2) = 75 experience lost
            Experience scales down for easier words relative to the user's level to do (user level)/(word level)"""
        experience = int(experience)
        self.userdb.update_percentages(self.flashcard.statistics, self.user, self.flashcard.language[0], experience)
        self.userdb.get_experience(self.user.ID, self.flashcard.language[0])
        #QtGui.QMessageBox.warning(self, "Experience gained", "You have gained {} experience and are now at {}".format(str(experience), ))

        self.home = Home(self.user)


class Home(QtGui.QMainWindow):

    def __init__(self, user):
        super(Home, self).__init__()
        self.user = user
        self.setFixedSize(500, 300)
        self.setWindowTitle("Home")
        self.flashcard = FlashCard(user, self)
        self.build_gui()
        self.show()

    def build_gui(self):
        self.grid = QtGui.QGridLayout()

        self.flashcard_button = QtGui.QPushButton("Revision Flashcards")
        self.flashcard_button.clicked.connect(self.open_flashcards)

        self.statistics_button = QtGui.QPushButton("View your statistics")
        self.statistics_button.clicked.connect(self.view_statistics)

        self.edit_language_button = QtGui.QPushButton("Edit a language's words")
        self.edit_language_button.clicked.connect(self.edit_language)

        self.grid.addWidget(self.flashcard_button, 0, 0)
        self.grid.addWidget(self.statistics_button, 1, 0)
        self.grid.addWidget(self.edit_language_button, 2, 0)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.grid)

    def open_flashcards(self):
        self.flashcard_window = ChooseLanguage(self, self.user, self.flashcard)
        self.flashcard_window.build_gui()
        self.flashcard_window.show()

    def view_statistics(self):
        self.statistics_window = Statistics(self.user, self)
        self.statistics_window.show()

    def edit_language(self):
        self.edit_language_window = EditLanguage(self, self.user)


class Statistics(QtGui.QTabWidget):

    def __init__(self, user, home):
        super(Statistics, self).__init__()
        self.user = user
        self.userdb = UserDB()
        self.flashcard = FlashCard(self.user, home)
        valid_language = self.select_language()
        if valid_language:
            self.show()

    def build_gui(self, code):
        self.flashcard.language[0] = code
        self.grid = QtGui.QGridLayout()
        self.setGeometry(50, 50, 420, 360)

        self.failed_words_tab = QtGui.QWidget()
        self.unsure_words_tab = QtGui.QWidget()
        self.known_words_tab = QtGui.QWidget()
        self.all_words_tab = QtGui.QWidget()

        self.addTab(self.failed_words_tab, "Failed words")
        self.build_tab_ui(self.failed_words_tab, code)

        self.addTab(self.unsure_words_tab, "Unsure words")
        self.build_tab_ui(self.unsure_words_tab, code)

        self.addTab(self.known_words_tab, "Known words")
        self.build_tab_ui(self.known_words_tab, code)

        self.addTab(self.all_words_tab, "All words")
        self.build_tab_ui(self.all_words_tab, code)

        self.setWindowTitle("Your statistics")

    def build_tab_ui(self, tab, code):
        langdb = LanguageDB(code)

        words = self.load_words(tab, langdb)
        grid = QtGui.QGridLayout()

        self.english_label = QtGui.QLabel("English")
        self.translation_label = QtGui.QLabel("{}".format(self.flashcard.language[1]))
        self.percentage_label = QtGui.QLabel("Percentage")

        grid.addWidget(self.english_label, 0, 0)
        grid.addWidget(self.translation_label, 0, 1)
        grid.addWidget(self.percentage_label, 0, 2)

        table = self.get_table_values(words, langdb)

        for i in range(len(table)):
            """Builds the table of statistics
            """
            for j in range(2):
                grid.addWidget(QtGui.QLabel(table[i][j]), i+1, j)
            grid.addWidget(table[i][2], i+1, 2)
        tab.setLayout(grid)

    def get_table_values(self, words, langdb):
        table = []
        """table is a 2d array. Each index contains an array containing an english word, non english word and a
        percentage bar."""
        for i in range(len(words)):

            percentage_bar = QtGui.QProgressBar(self)
            percentage_bar.setValue(words[i][3]*100)

            english = words[i][0]

            query = "SELECT TRANSLATION \
            FROM {} \
            WHERE ENGLISH = ?".format(self.flashcard.language[1])
            translation = langdb.run_query(query, [english])

            if translation == []:
                """Automatically deletes any words that have been removed"""
                query = "DELETE FROM {}{}_PERCENTAGE \
                WHERE ENGLISH = ?".format(self.user.username, self.flashcard.language[0])
                self.userdb.run_query(query, [english])
                return
            translation = [i[0] for i in translation][0]

            table.append([english, translation, percentage_bar])

        return table

    def load_words(self, tab, langdb):
        query = "SELECT LANGUAGE \
            FROM language_codes \
            WHERE CODE = ?"
        parameters = [self.flashcard.language[0]]
        language = langdb.run_query(query, parameters, path="databases/language_codes.sqlite")

        self.flashcard.language[1] = [i[0] for i in language][0]

        start = 0
        end = 1.1
        if tab == self.failed_words_tab:
            start = 0
            end = 0.34
        elif tab == self.unsure_words_tab:
            start = 0.34
            end = 0.67
        elif tab == self.known_words_tab:
            start = 0.67
            end = 1.1
        """1.1 as the operator used in get_words is simply a lesser than. This is to prevent overlap on lower
        percentages
        """
        words = self.userdb.get_percentages(self.flashcard.language[0],
                                       username=self.user.username,
                                       percentage_start=start,
                                       percentage_end=end)
        return words

    def select_language(self):
        try:
            languages = self.userdb.get_user_languages(self.user.ID)
            languages = [i[0] for i in languages]
            print(languages)
            if len(languages) == 0:
                QtGui.QMessageBox.warning(self, "No languages", "You haven't practiced a language yet!")
                return
            language, valid = QtGui.QInputDialog.getItem(self, "Window Title",\
                                                  "List label", languages, 0, False)
            if valid and language:
                self.build_gui(language)
                return True
        except Exception as e:
            print("Error:",e)
        return False


class ChooseLanguage(QtGui.QWidget):
    """For inputting language, level, words and translations"""
    def __init__(self, home, user, flashcard=None, langdb=None):
        super(ChooseLanguage, self).__init__()
        self.home = home
        self.user = user
        self.flashcard = flashcard
        self.langdb = langdb


    def build_gui(self):
        grid = QtGui.QGridLayout()
        self.setWindowTitle("Choose your language")
        self.show_language = QtGui.QLineEdit(self)
        self.show_language.setReadOnly(True)

        self.choose_language_btn = QtGui.QPushButton("Choose language")
        self.choose_language_btn.clicked.connect(lambda: self.choose_language(self.show_language))

        self.confirm_btn = QtGui.QPushButton("Confirm")
        self.confirm_btn.clicked.connect(self.confirm)

        grid.addWidget(self.choose_language_btn, 0, 2)
        grid.addWidget(self.show_language, 0, 0)
        grid.addWidget(self.confirm_btn, 1, 2)
        self.setLayout(grid)

        self.show()

    def choose_language(self, lineedit):
        db = Database("databases/language_codes.sqlite")
        query = "SELECT language\
        FROM language_codes"
        items = db.run_query(query)
        items = [i[0] for i in items]
        print(items)
        """Based on https://www.tutorialspoint.com/pyqt/pyqt_qinputdialog_widget.htm"""
        item, ok = QtGui.QInputDialog.getItem(self, "Choose language",\
                                        "list of languages", items, 0, False)
        if ok and item:
            lineedit.setText(item)

    def confirm(self, revising):
        if self.show_language.text() == "":
            QtGui.QMessageBox.warning(self.parent(), "Invalid Language", "You must select a language")
            return

        language = self.show_language.text()
        self.langdb = LanguageDB(language=language)
        code = self.langdb.code

        self.flashcard.set_language(language)
        self.flashcard.set_code(code)

        self.main_window = Window(self.user, self.flashcard)

        print(self.main_window.flashcard.language)
        self.home.close()
        self.close()

        if not os.path.exists("databases/{}.sqlite".format(code)):
            """Could just execute ddl in langdb.run_query?"""
            ddl = "databases/create_language_table.sql"
            self.langdb.create_table(ddl)

        words = self.langdb.get_words(code, language, self.main_window.flashcard.level)
        if len(words) < 10:
            """If there are not enough words then a loop is entered until there are enough"""
            QtGui.QMessageBox.warning(self, "Not enough words", "There are not enough words available for this language")
            self.add_words = AddWord(revising, self.home, language=language).show()
            return

        self.main_window.show()


class AddWord(QtGui.QWidget):

    def __init__(self, revising, home, flashcard=None,  language=None, langdb=None):
        super(AddWord, self).__init__()
        self.home = home
        self.user = self.home.user
        if flashcard is not None:
            self.flashcard = flashcard
        else:
            self.flashcard = FlashCard(self.user, self.home)

        if langdb is not None:
            self.langdb = langdb
        else:
            self.langdb = LanguageDB(language=language)
        self.build_gui(revising, language)

    def build_gui(self, revising, language=None):
        super(AddWord, self).__init__()
        self.setWindowTitle("Add words")
        layout = QtGui.QGridLayout(self)
        if language is None:
            language = self.flashcard.language[1]

        self.langdb = LanguageDB(language=language)
        code = self.langdb.code
        self.flashcard.set_language(language)
        self.flashcard.set_code(code)

        self.english_word = QtGui.QLineEdit(self)
        self.english_word.returnPressed.connect(lambda: self.add_word_to_database(language=language))
        self.english_label = QtGui.QLabel("English")

        self.non_english_word = QtGui.QLineEdit(self)
        self.non_english_word.returnPressed.connect(lambda: self.add_word_to_database(language=language))
        self.non_english_label = QtGui.QLabel("{}".format(language))

        """returnPressed means that when the enter key is pressed while typing in the QLineEdit, trigger a method.
        In this instance it does the same as clicking the add word button."""

        self.add_word_btn = QtGui.QPushButton("Add word")
        self.add_word_btn.clicked.connect(lambda: self.add_word_to_database(language=language))

        self.level = QtGui.QComboBox(self)

        for i in range(1,7):
            self.level.addItem(str(i))

        self.confirm_btn = QtGui.QPushButton("Done")
        self.confirm_btn.clicked.connect(lambda: self.confirm(revising))

        layout.addWidget(self.add_word_btn, 0, 2)
        layout.addWidget(self.english_label, 0, 0)
        layout.addWidget(self.english_word, 0, 1)
        layout.addWidget(self.non_english_label, 1, 0)
        layout.addWidget(self.non_english_word, 1, 1)
        layout.addWidget(self.level, 0, 3)
        layout.addWidget(self.confirm_btn, 1, 2)


    def add_word_to_database(self, code=None, language=None):
        """English and non-english words gotten from repective inputs/QLineEdits
        Words are then checked to be alphanumeric. The isalpha() function also classes non-latin unicode characters
        (e.g. cyrllic, greek or even chinese characters) as alphanumeric so no additional validation is required."""
        if language is not None and code is None:
            code = self.langdb.get_code(language)
        if code is None:
            code = self.main_window.flashcard.language[0]
        if language is None:
            language = self.main_window.flashcard.language[1]
        english = self.english_word.text().strip()
        non_english = self.non_english_word.text().strip()

        if len(english) > 30 or len(non_english) > 30:
            self.invalid_word()
            return

        if len(english) == 0 or len(non_english) == 0:
            self.invalid_word()
            return

        english = self.validate_word(english)
        non_english = self.validate_word(non_english)

        english = english.strip()
        non_english = non_english.strip()
        self.langdb.add_word(english, non_english, int(self.level.currentText()))
        self.english_word.setText("")
        self.non_english_word.setText("")

    def confirm(self, revising):
        words = self.langdb.get_words(code=self.flashcard.get_code(), level=self.flashcard.level)
        print(words)
        if len(words) < 10:
            QtGui.QMessageBox.warning(self, "Not enough words", "There must be at least 10 words to practice")
            return
        self.close()
        if revising:
            self.main_window.show()
        else:
            self.home.show()

    def validate_word(self, word):
        validated_word = ""
        word_split = word.split()
        for i in range(len(word_split)):
            validated_word += word_split[i]
            if i != len(word_split):
                validated_word += " "
            if word.split()[i].isalpha() is not True:
                self.invalid_word()
                return False
        return validated_word

    def invalid_word(self):
        QtGui.QMessageBox.warning(self, "Invalid input", "The words you have entered are invalid")
        return


class BulkAdd(QtGui.QWidget):

    def __init__(self, home, user, language):
        super(BulkAdd, self).__init__()
        self.home = home
        self.user = user
        self.language = language
        self.langdb = LanguageDB(language=language)
        self.build_gui(language)
        self.show()

    def build_gui(self, language):
        super(BulkAdd, self).__init__()
        self.setWindowTitle("Bulk Addition")
        self.grid = QtGui.QGridLayout(self)

        self.word_input_label = QtGui.QLabel("English : {} : Level".format(language))
        self.word_input = QtGui.QTextEdit(self)

        self.confirm = QtGui.QPushButton("Confirm")
        self.confirm.clicked.connect(self.add_words)

        self.file_select = QtGui.QPushButton("Select a file")
        self.file_select.clicked.connect(self.open_file)

        self.save_to_file = QtGui.QPushButton("Save file")
        self.save_to_file.clicked.connect(lambda : self.save_file(self.file_name.text()))

        self.file_name = QtGui.QLineEdit(self)
        self.file_name_label = QtGui.QLabel("File name on save")

        self.show_all_words_btn = QtGui.QPushButton("Show all words")
        self.show_all_words_btn.clicked.connect(self.show_all_words)

        self.grid.addWidget(self.word_input_label, 0, 0)
        self.grid.addWidget(self.word_input, 0, 1)
        self.grid.addWidget(self.file_select, 0, 2)
        self.grid.addWidget(self.file_name, 1, 1)
        self.grid.addWidget(self.file_name_label, 1, 0)
        self.grid.addWidget(self.save_to_file, 1, 2)
        self.grid.addWidget(self.show_all_words_btn, 2, 1)
        self.grid.addWidget(self.confirm, 2, 2)
        self.setLayout(self.grid)

    def open_file(self):
        """Allows the user to open .txt files containing words. The text in this file is is copied into the textbox"""
        file_dialog = QtGui.QFileDialog(self)
        try:
            file = open(file_dialog.getOpenFileName(self, "Open file", filter="Text files (*.txt)"), "r")
        except FileNotFoundError:
            """FileNotFoundError is the error when a user closes the window without selecting a file"""
            return
        text = ""
        for line in file:
            text += line
        self.word_input.setText(text)

    def save_file(self, filename):
        """Saves the current content of the text box to a file"""
        try:
            file = open("words/"+filename+".txt", "w")
        except FileNotFoundError:
            os.mkdir("words")
            file = open("words/"+filename+".txt", "w")
        except:
            QtGui.QMessageBox.warning(self, "Invalid file name", "Invalid file name")
            return

        file.write(self.word_input.toPlainText())
        file.close()
        if self.sender() is not self.confirm:
            QtGui.QMessageBox.warning(self, "File saved", "Saved to file {}.txt".format(filename))

    def show_all_words(self):
        """Shows all the words that have been added to a language previously, with the same word : word : level
        formatting as above
        words - 2d array of words with their translations + levels
        """
        words = self.langdb.get_words()
        text = ""
        for i in words:
            text += "{} : {} : {}\n".format(i[0], i[1], str(i[2]))
        self.word_input.setText(text)

    def add_words(self):
        words_string = self.word_input.toPlainText()
        words_array = self.validate_words(words_string) #each line is validated to be of the structure word : word : level
        if words_array is False:
            return
        add_word = AddWord(False, self.home, language=self.language) #Each word is validated
        for i in range(len(words_array)):
            for j in range(len(words_array[i]) - 1):
                valid = add_word.validate_word(words_array[i][j])
                if valid is False:
                    return
            try:
                self.langdb.add_word(words_array[i][0], words_array[i][1], words_array[i][2])
            except sqlite3.OperationalError:
                self.langdb.create_table("databases/create_language_table.sql")
                self.langdb.add_word(words_array[i][0], words_array[i][1])
        self.save_file("recent") #saves the most recent bulk addition to a file
        self.word_input.setText("") #clears the input

    def validate_words(self, words_string):
        """Makes sure that each line is in the format word/phrase : word/phrase : level.
        After this is executed, the individual words are validated via the AddWord.validate_word method
        """
        words_array = words_string.split("\n")
        for i in range(len(words_array)):
            words_array[i] = words_array[i].split(":")
            if len(words_array[i]) != 3:
                self.error("Error on line {}".format(str(i+1)))
                return False
            for j in range(len(words_array[i])):
                words_array[i][j] = words_array[i][j].strip()
                if words_array[i][j] is "":
                    self.error("You missed either a word or level on line {}".format(str(i+1)))
                    return False
            try:
                words_array[i][2] = int(words_array[i][2])
            except ValueError or IndexError:
                self.error("No number on line {}".format(str(i+1)))
                return False
            if words_array[i][2] > 6 or words_array[i][2] < 1:
                self.error("Numbers must be between 1 and 6 (line {})".format(str(i+1)))
                return False
        return words_array

    def error(self, message):
        QtGui.QMessageBox.warning(self, "Error adding words", message)
        return


class RemoveWord(QtGui.QWidget):

    def __init__(self, home, user, language):
        super(RemoveWord, self).__init__()
        self.langdb = LanguageDB(language=language)
        self.build_gui(language)

    def build_gui(self, language):
        super(RemoveWord, self).__init__()

        grid = QtGui.QGridLayout(self)

        self.word_to_remove = QtGui.QLineEdit(self)
        self.word_to_remove.setReadOnly(True)

        self.choose_word = QtGui.QPushButton("Choose word")
        self.choose_word.clicked.connect(self.remove_words_combo_box)

        self.remove_word_btn = QtGui.QPushButton("Remove word")
        self.remove_word_btn.clicked.connect(lambda: self.confirm_removal(self.word_to_remove.text()))

        grid.addWidget(self.word_to_remove, 0, 0)
        grid.addWidget(self.choose_word, 1, 0)
        grid.addWidget(self.remove_word_btn, 0, 1)
        self.setLayout(grid)
        self.show()

    def remove_words_combo_box(self):
        english_words = self.langdb.get_words()
        print(english_words)
        english_words = [i[0] for i in english_words]
        print(english_words)
        if len(english_words) == 0:
            QtGui.QMessageBox.warning(self, "No words", "There are no words available")
            return
        item, ok = QtGui.QInputDialog.getItem(self, "Choose word",\
                                        "All words", english_words, 0, False)
        if ok and item:
            self.word_to_remove.setText(item)

    def confirm_removal(self, word):
        if word.strip() is not "":
            self.langdb.remove_word(word)
            self.word_to_remove.setText("")
        else:
            QtGui.QMessageBox.warning(self, "Error",)


class EditLanguage(QtGui.QWidget):

    def __init__(self, home, user):
        super(EditLanguage, self).__init__()
        self.language_code = ""
        self.home = home
        self.user = user

        self.build_gui()
        self.show()

    def build_gui(self):
        self.layout = QtGui.QGridLayout(self)
        self.setWindowTitle("Edit a language")
        self.show_language = QtGui.QLineEdit(self)
        self.show_language.setReadOnly(True)

        self.choose_language_btn = QtGui.QPushButton("Choose language")
        self.choose_language_btn.clicked.connect(lambda: ChooseLanguage(self.home, self.user).choose_language(self.show_language))

        self.add_words_btn = QtGui.QPushButton("Add words")
        self.add_words_btn.clicked.connect(self.connect)

        self.remove_words_btn = QtGui.QPushButton("Remove words")
        self.remove_words_btn.clicked.connect(self.connect)

        self.bulk_add_btn = QtGui.QPushButton("Bulk add words")
        self.bulk_add_btn.clicked.connect(self.connect)

        self.layout.addWidget(self.show_language, 0, 0)
        self.layout.addWidget(self.choose_language_btn, 0, 1)
        self.layout.addWidget(self.add_words_btn, 1, 0)
        self.layout.addWidget(self.remove_words_btn, 1, 1)
        self.layout.addWidget(self.bulk_add_btn, 2, 1)
        self.setLayout(self.layout)

    def connect(self):
        if self.show_language.text() == "":
            QtGui.QMessageBox.warning(self.parent(), "Invalid Language", "You must select a language")
            return
        language = self.show_language.text()
        if self.sender() is self.add_words_btn:
            self.add_words_window = AddWord(False, self.home, language=language).show()
        elif self.sender() is self.remove_words_btn:
            self.remove_words_window = RemoveWord(self.home, self.user, language=language)
        elif self.sender() is self.bulk_add_btn:
            self.bulk_add_window = BulkAdd(self.home, self.user, language=language)


class FlashCard():

    def __init__(self, user, home):
        self.language = ["ISO 639-1", "Language"]
        self.home = home
        self.user = user
        #language codes sourced from https://www.sitepoint.com/web-foundations/iso-2-letter-language-codes/
        self.level = self.user.level
        self.time = 5
        #used_words will be a list of the words that have been chosen by the algorithm, so that there are no repeats.
        self.used_words = []
        #initalise the percentage as 0, with a string  of 0s and 1s to represent correct and incorrect answers.
        self.percentage = [0,[]]
        self.statistics = {}
        self.userdb = UserDB()

    def choose_words(self):
        langdb = LanguageDB(self.language[0])
        all_words = langdb.get_words(self.language[0], self.language[1])
        print("all:", all_words)
        """All words that are accessible for a certain level."""
        possible_words = [i for i in all_words if int(i[2]) <= self.level]
        print("possible:", possible_words)
        try:
            user_percentages = self.userdb.get_percentages(self, self.language[0], self.user.username)
        except sqlite3.OperationalError:
            user_percentages = []
        for i in user_percentages:
            if (i[3] > 0.9 and i[2] > 10) or self.used_words.count(i[0]) >= 3:
                """i[0] is english, i[1] is total amount of times correct, i[2] the total amount of times the user has
                guessed the word, i[3] is the percentage correctness. (see UserDB.get_percentages below)
                If the percentage is greater than 90% and the amount of times the user has gotten the word correct is
                greater than 10, or if the word has been used more than 3 times.
                """
                for j in possible_words:
                    if i[0] == j[0]:
                        if  self.used_words.count(i[0]) >= 3 or random.randint(1,10) > 1:
                            """The word is not removed every time. This means that it may still show up, only at a
                            reduced rate. self.used_words.count(i[0]) >= 3 means that if the word appears more than 3
                            times it will be removed 100% of the time."""
                            print(i[0],"removed")
                            possible_words.remove(j)
                        break
        print(len(possible_words))
        if len(possible_words) <= 3:
            QtGui.QMessageBox.warning(self, " ", "Each word has appeared 3 times or more.")
            Window(self.user, self).calculate_experience()
            return []

        guess_words = []

        index = random.randint(0, len(possible_words)-1)
        self.correct_array = possible_words[index]
        print("chosen word:",self.correct_array)

        self.correct_english = self.correct_array[0]
        self.correct_translation = self.correct_array[1]

        guess_words.append(self.correct_english)
        self.used_words.append(self.correct_english)

        while len(guess_words) < 3:
            guess_index = random.randint(0, len(possible_words) - 1)
            if guess_index != index and possible_words[guess_index][0] not in guess_words:
                guess_words.append(possible_words[guess_index][0])
        guess_words = self.shuffle(guess_words)
        return guess_words

    def check_answer(self, word):
        if word == self.correct_english:
            return ["1", self.correct_array[2]]
        return ["0", self.correct_array[2]]

    def percentage_correct(self, word, percentage_array):
        try:
            if self.correct_english in self.statistics:
                """self.statistics is a dictionary as follows
                {english : [correct_amount, total_amount, level]}
                """
                self.statistics[self.correct_english][0] += int(self.check_answer(word)[0])
                self.statistics[self.correct_english][1] += 1
            else:
                self.statistics[self.correct_english] = [int(self.check_answer(word)[0]), 1, self.correct_array[2]]
        except:
            return
        print(self.statistics)
        percentage_array[1].append(self.check_answer(word)[0])
        percentage_array[0] = (100 * percentage_array[1].count("1")) / len(percentage_array[1])
        percentage_array[0] = str(round(percentage_array[0]))
        print("%",percentage_array)
        return percentage_array

    def shuffle(self, unshuffled_list):
        """Based on the Fisher-Yates shuffle"""
        shuffled_list = []
        while len(unshuffled_list) != 0:
            i = random.randint(0, len(unshuffled_list) - 1)
            shuffled_list.append(unshuffled_list[i])
            unshuffled_list.remove(unshuffled_list[i])
        return shuffled_list

    def set_code(self, code):
        self.language[0] = code

    def set_language(self, language):
        self.language[1] = language

    def set_level(self, level):
        self.level = level

    def get_code(self):
        return self.language[0]

    def get_language(self):
        return self.language[1]


class Login(QtGui.QDialog):
    """Login window"""
    def __init__(self):
        super(Login, self).__init__()
        self.setWindowTitle("Login to Revision Flashcards")
        self.setGeometry(50, 50, 200, 100)
        self.logindb = LoginDB()
        self.build_gui()
        self.show()

    def build_gui(self):
        grid = QtGui.QGridLayout(self)

        self.username = QtGui.QLineEdit(self)

        self.password = QtGui.QLineEdit(self)
        self.password.setEchoMode(QtGui.QLineEdit.Password)

        self.login_button = QtGui.QPushButton("Login")
        self.login_button.clicked.connect(self.__login)

        self.change_password_button = QtGui.QPushButton("Change Password")
        self.change_password_button.clicked.connect(self.change_password)

        self.create_user_button = QtGui.QPushButton("Create Account")
        self.create_user_button.clicked.connect(self.create_user_window)

        grid.addWidget(self.username, 0, 1)
        grid.addWidget(self.password, 0, 2)
        grid.addWidget(self.login_button, 0, 3)
        grid.addWidget(self.change_password_button, 1, 2)
        grid.addWidget(self.create_user_button, 1, 3)

    def create_user_window(self):
        self.new_user_window = CreateNewUser(self)

    def __login(self):

        username = self.username.text()
        password = self.password.text()

        hashed_username = self.encrypt(username.lower())
        hashed_password = self.encrypt(password)

        verified = self.logindb.verify(hashed_username, hashed_password)

        if verified:
            self.accept()
            return

        QtGui.QMessageBox.warning(self, "Failed Login", "Invalid username or password")

    def encrypt(self, data):
        import hashlib
        salt = "this is a great salt"

        data += salt
        data = data.encode()

        hash = hashlib.sha512()
        hash.update(data)
        hashed_data = hash.hexdigest()
        #hexdigest better than digest?
        #hexdigest shorter representation of 512bit integer

        return hashed_data

    def validate_password(self, password):
        """Validates the password with the requirements of at least one lower case letter, one capital letter, one digit, and a length of 8"""
        import re
        password_regex = r"(?=.*[a-z])(?=.*[A-Z])(?=.*[\d]){8,64}"
        if re.findall(password_regex, password):
            return True
        return False

    def validate_username(self, username):
        """Username can be any alphanumeric characters and dash and underscore. Must be between 3 and 20 characters long."""
        import re
        username_regex = r"[\w-]{3,20}"
        if re.findall(username_regex, username):
            return True
        return False

    def change_password(self):
        self.change_password_window = ChangePasswordWindow(self, self.logindb)


class ChangePasswordWindow(QtGui.QDialog):

    def __init__(self, login, logindb):
        super(ChangePasswordWindow, self).__init__()
        self.login = login
        self.logindb = logindb
        self.build_gui()
        self.show()

    def build_gui(self):
        super(QtGui.QDialog, self).__init__()

        self.setWindowTitle("Change Password")
        self.grid = QtGui.QGridLayout(self)

        self.username_label = QtGui.QLabel("Username")
        self.username = QtGui.QLineEdit(self)

        self.old_password_label = QtGui.QLabel("Current Password")
        self.old_password = QtGui.QLineEdit(self)
        self.old_password.setEchoMode(QtGui.QLineEdit.Password) #Password is only black dots

        self.new_password_label = QtGui.QLabel("New Password")
        self.new_password = QtGui.QLineEdit(self)
        self.new_password.setEchoMode(QtGui.QLineEdit.Password)

        self.confirm_password_label = QtGui.QLabel("Confirm New Password")
        self.confirm_password = QtGui.QLineEdit(self)
        self.confirm_password.setEchoMode(QtGui.QLineEdit.Password)

        self.confirm_details = QtGui.QPushButton("Confirm")
        self.confirm_details.clicked.connect(self.change_password)

        self.grid.addWidget(self.username_label, 0, 0)
        self.grid.addWidget(self.username, 0, 1)
        self.grid.addWidget(self.old_password_label, 1, 0)
        self.grid.addWidget(self.old_password, 1, 1)
        self.grid.addWidget(self.new_password_label, 2, 0)
        self.grid.addWidget(self.new_password, 2, 1)
        self.grid.addWidget(self.confirm_password_label, 3, 0)
        self.grid.addWidget(self.confirm_password, 3, 1)
        self.grid.addWidget(self.confirm_details, 4, 1)

    def change_password(self):
        if self.old_password.text() == self.new_password.text():
            QtGui.QMessageBox.warning(self, "New Password Error", "Your new password must be different from your old one")
            return
        if self.new_password.text() != self.confirm_password.text():
            QtGui.QMessageBox.warning(self, "New Password Error", "Your new password doesn't match")
            return
        if self.login.validate_password(self.new_password.text()) is False:
            QtGui.QMessageBox.warning(self, "New Password Error", "Your new password does not meet at least one of the minimum requirements\n\
•Length of 8 characters\n\
•One numeric character\n\
•One upper case letter\n\
•One lower case letter")
            return
        username = self.login.encrypt(self.username.text().lower())
        old_pass = self.login.encrypt(self.old_password.text())
        new_pass = self.login.encrypt(self.new_password.text())

        password_changed = self.logindb.change_password(username, old_pass, new_pass)
        if password_changed:
            QtGui.QMessageBox.warning(self, "New password", "Your password has been changed")
            self.close()
        else:
            QtGui.QMessageBox.warning(self, "Username or password error", "Either your username or password is invalid")
            return


class CreateNewUser(QtGui.QDialog):

    def __init__(self, login):
        super(CreateNewUser, self).__init__()
        self.login = login
        self.logindb = LoginDB()
        self.build_gui()
        self.show()

    def build_gui(self):
        """This creates the window in which the user may create an account"""
        super(QtGui.QDialog, self).__init__()

        self.setWindowTitle("Create New Account")
        grid = QtGui.QGridLayout(self)

        self.username_label = QtGui.QLabel("Username")
        self.new_username = QtGui.QLineEdit(self)

        self.password_label = QtGui.QLabel("Password")
        self.new_password = QtGui.QLineEdit(self)

        self.confirm_password_label = QtGui.QLabel("Confirm Password")
        self.confirm_password = QtGui.QLineEdit(self)

        self.confirm = QtGui.QPushButton("Confirm")
        self.confirm.clicked.connect(self.__confirm_new_user_details)

        grid.addWidget(self.new_username, 0, 1)
        grid.addWidget(self.username_label, 0, 0)
        grid.addWidget(self.password_label, 1, 0)
        grid.addWidget(self.new_password, 1, 1)
        grid.addWidget(self.confirm_password_label, 2, 0)
        grid.addWidget(self.confirm_password, 2, 1)
        grid.addWidget(self.confirm, 3, 1)

    def __confirm_new_user_details(self):
        """Private method that avlidates a new user's details
        new_username/new_password - user's desired login details
        hashed_username/hashed_password - the above username and password salted and then hashed using sha512
        """
        new_username = self.new_username.text()
        new_password = self.new_password.text()
        if new_username in new_password or new_password in new_username:
            """Username and password must not be contained in one another"""
            QtGui.QMessageBox.warning(self, "Username and Password Error", "Your username and password are not allowed to match")
            return

        hashed_username = self.login.encrypt(new_username.lower())
        query = "SELECT USERNAME \
        FROM USER_DETAILS \
        WHERE USERNAME = ?"
        parameters = [hashed_username]
        users = self.logindb.run_query(query, parameters)
        print(users)
        """Username handling"""
        if len(users) > 0 or self.login.validate_username(new_username) is False:
            QtGui.QMessageBox.warning(self, "Username Error", "Your username already exists or is invalid")
            return

        """Password handling"""
        if self.login.validate_password(new_password) is False:
            QtGui.QMessageBox.warning(self, "Password Error", "Your password does not meet at least one of the minimum requirements\n\
•Length of 8 characters\n\
•One numeric character\n\
•One upper case letter\n\
•One lower case letter")
            return

        if self.new_password.text() != self.confirm_password.text():
            QtGui.QMessageBox.warning(self, "Password Error", "Your passwords do not match")
            return

        hashed_password = self.login.encrypt(new_password)
        user_id = random.randint(1,1000000) #Lower amount of collisions with a higher number

        """Username, password and the user's ID inserted into database.
        Random ID generation makes it harder for a user to figure out who they are if they
        gain access to the database.
        """
        query = "INSERT INTO USER_DETAILS(USER_ID, USERNAME, PASSWORD) \
                VALUES(?, ?, ?)"
        parameters = [user_id, hashed_username, hashed_password]
        collision = True
        while collision:
            try:
                self.logindb.run_query(query, parameters)
                collision = False
            except:
                print("A collision has occured")

        self.close()
        self.build_gui()


class User():
    """Object that reperesents the user"""
    def __init__(self):
        """User object initiated and the values are assigned via a series of SQL statements
        username - the user's username
        ID - the user's ID
        level - their level in the language they're revising
        userdb - used to access data about the user i.e run SQL queries.
        """
        self.username = ""
        self.ID = 0
        self.level = 0
        self.userdb = UserDB()

    def set_level(self, code):
        """Retrieves a user's experience for a specific language and processes this number into a level. This level
        is used to retrieve the words that the user may revise.
        query - Retrieves the experience from the user_experience table
        """
        query = "SELECT EXPERIENCE \
        FROM USER_EXPERIENCE \
        WHERE USER_ID = ? \
        AND CODE = ?"
        parameters = [self.ID, code]
        try:
            experience = self.userdb.run_query(query, parameters)[0][0]
            print(experience)
        except:
            self.level = 1
            return
        self.level = math.ceil(experience / 1000)
        if self.level > 6:
            self.level = 6
        if self.level < 1:
            self.level = 1

    def set_ID(self, ID=None):
        """By default, sets the ID property on the object to what it is in the database. Optional parameter ID can also
        be assigned to this property.
        hashed_username - The username on the class lowered and hashed using sha512
        query - SQL query retrieve the ID of the user from the user_details table.
        parameters - array of what is passed in; in this case the hashed_username is used to fetch the ID of the user
        """
        if ID is not None:
            self.ID = ID
            return
        hashed_username = Login().encrypt(self.username.lower())
        query = "SELECT USER_ID\
                FROM USER_DETAILS\
                WHERE USERNAME = ?"
        parameters = [hashed_username]
        self.ID = self.userdb.run_query(query, parameters)[0][0]

    def get_ID(self):
        """Getter for ID"""
        return self.ID


class Database():
    """Generic database class"""
    def __init__(self, path):
        """Initalizes database.
        path - the path of the database being accessed"""
        self.path = path

    def run_query(self, query, parameters=[], path=None):
        """Generalized query. Will run any SQLite compatible query
        query - the query to be executed
        parameters - parameters that are necessary for the SQL to be executed properly, and are inserted into the
        parameterized query upon execution
        path - the query may require a different path to that on the object"""
        if path is None:
            path = self.path

        with sqlite3.connect(path) as conn:
            cur = conn.cursor()
            cur.execute(query, parameters)
            #Works fine if no parameters are required as long as parameters is an empty array
            try:
                """Rarely is it that one item is required. If it is then array indexing can be used afterwards.
                """
                items = cur.fetchall()
            except Exception as e:
                """Most likely error is running an INSERT INTO query and thus having no values to return"""
                print("Error in run_query:", e)
                return
        return items
        #returns an array of tuples of all items found

    """Setter and getter for truer object orientation"""
    def set_path(self, path):
        self.path = path

    def get_path(self):
        return self.path


class UserDB(Database):
    """Handles retrieval and editing of values pertaining directly to the user"""
    def __init__(self):
        """Initalizes UserDB as a child class of Database
        path - the path that the databases are accessed through"""
        path = "databases/user_details.sqlite"
        super().__init__(path)

    def add_user_language(self, user, code):
        """Adds a user + language as a composite key in a table.
        user - user object that was created upon login
        code - 2 digit language code that will be inserted
        parameters - an array that contains the user's ID and language code so that they may be inserted into the
        parameterised query"""
        query = "INSERT INTO USER_EXPERIENCE(USER_ID, CODE, EXPERIENCE) \
                VALUES(?, ?, ?)"
        #Experience being inserted is always 0
        parameters = [user.ID, code, 0]
        add = self.run_query(query, parameters)

    def get_user_languages(self, user_id):
        """Retrieves the languages that a user has started revising in the past using their ID
        user_id - the user's unique identifier
        query - retrieves the codes that are composite keys with the user's ID in user_experience
        languages - an array of 2 digit language codes
        """
        query = "SELECT CODE \
                FROM USER_EXPERIENCE \
                WHERE USER_ID = ?"
        parameters = [user_id]
        languages = self.run_query(query, parameters)
        return languages

    def get_experience(self, user_id, code):
        """Retrieves the epexerience value froa certain user id + language combo"""
        query = "SELECT EXPERIENCE \
                 FROM USER_EXPERIENCE \
                 WHERE USER_ID = ? AND CODE = ?"
        parameters = [user_id, code]
        experience = self.run_query(query, parameters)
        return experience[0]

    def get_percentages(self, code, username, percentage_start=0, percentage_end=1.1):
        """
        percentage_start is the minimum value and percentage_end is the maximum value.
        percentage_start=0 and percentage_end=1.1 means that it defaults to all words.
        Ranges are customisable. Percentages are stored as REAL values between 0 and 1 inclusive.
        """
        query = "SELECT ENGLISH, CORRECT, TOTAL, PERCENTAGE \
                 FROM {}{}_PERCENTAGE \
                 WHERE PERCENTAGE >= ? AND PERCENTAGE < ?".format(username, code)
        parameters = [percentage_start, percentage_end]
        percentages = self.run_query(query, parameters)
        return percentages

    def update_percentages(self, statistics, user, code, experience):
        """Checks if there is a table for this user and the language. If it doesn't exist it is created.
        The statistics are loaded from the table, then converted to a dictionary.
        This data is then combined with the data from the last revision. This data is then turned into a 2d array and
        dumped.
        A detailed explanation of this method is present under the Pseudocode subheading of Documented Design
        """
        username = user.username
        try:
            """The try block will only not have an exception if the user is new to the language.
            This is why the experience can be set to the value the user has just got
            """
            query = "INSERT INTO USER_EXPERIENCE(USER_ID, CODE, EXPERIENCE) \
            VALUES(?, ?, ?)"
            parameters = [user.ID, code, experience]
            self.run_query(query, parameters)
        except Exception as e:
            """Only exception occurs when the user_id + language already exist as a composite key.
            """
            print(e)
            query = "UPDATE USER_EXPERIENCE SET \
            EXPERIENCE = EXPERIENCE + ? \
            WHERE USER_ID = ? AND CODE = ?"
            parameters = [experience, user.ID, code]
            self.run_query(query, parameters)

        ddl = "CREATE TABLE IF NOT EXISTS {}{}_PERCENTAGE( \
        ENGLISH VARCHAR(30), \
        CORRECT INTEGER, \
        TOTAL INTEGER, \
        PERCENTAGE REAL, \
        PRIMARY KEY(ENGLISH));".format(username, code)
        self.run_query(ddl)

        query = "SELECT ENGLISH, CORRECT, TOTAL, PERCENTAGE \
        FROM {}{}_PERCENTAGE".format(username, code)
        old_stats = self.run_query(query)

        print("OLD STATS:",old_stats)
        stats_dict = {i[0] : [i[1], i[2], i[3]] for i in old_stats}
        print("dict form:",stats_dict)

        for key in statistics:
            """
            Key: English word (primary key in the database)
            Index 0: Amount of times the user has gotten the word correct
            Index 1: Amount of times the word has appeared
            Index 2: The percentage i.e amount of times right divided by total amount
            """
            if key not in stats_dict:
                stats_dict[key] = statistics[key]
            else:
                stats_dict[key][0] += statistics[key][0]
                stats_dict[key][1] += statistics[key][1]
            stats_dict[key][2] = stats_dict[key][0] / stats_dict[key][1]
        print("New stats:", stats_dict)

        query = "DELETE FROM {}{}_PERCENTAGE \
        WHERE PERCENTAGE >= -1".format(username, code)
        self.run_query(query)
        """Everything is deleted so that there are no unique constraint errors. Also because all the data is being
        re-entered anyway.
        """

        query = "INSERT INTO {}{}_PERCENTAGE(ENGLISH, CORRECT, TOTAL, PERCENTAGE) \
        VALUES(?, ?, ?, ?)".format(username, code)

        for key in stats_dict:
            parameters = [key, stats_dict[key][0], stats_dict[key][1], stats_dict[key][2]]
            self.run_query(query, parameters)


class LanguageDB(Database):

    def __init__(self, code=None, language=None):
        """Initializes LanguageDB as a child class of Database
        code - 2 digit language code
        language - language that corresponds to the code
        """
        self.codes_path = "databases/language_codes.sqlite"
        if language is not None and code is None:
            code = self.get_code(language)
        path = "databases/{}.sqlite".format(code)
        super().__init__(path)
        self.code = code

    def get_language(self, code=None):
        """Gets the language from the code
        code - 2 digit language code
        language - language that corresponds to the code
        query - query that retrieves the code
        parameters - array that contains language so that it may be inserted into query
        """
        if code is None:
            code = self.code
        query = "SELECT language \
            FROM language_codes \
            WHERE code = ?"
        parameters = [code]
        language = self.run_query(query, parameters, path=self.codes_path)
        language = [i[0] for i in language][0]
        return language

    def get_code(self, language):
        """Gets the code from a sprecified language
        query - query that retrieves the code
        parameters - array that contains language so that it may be inserted into query
        code - 2 digit language code
        language - language that corresponds to the code
        """
        query = "SELECT code \
            FROM language_codes \
            WHERE language = ?"
        parameters = [language]
        code = self.run_query(query, parameters, path=self.codes_path)
        code = [i[0] for i in code][0]
        return code

    def add_word(self, english, translation, level=1, code=None, language=None):
        if code is None:
            code = self.code
        if language is None:
            language = self.get_language()
        query = "INSERT INTO {}(ENGLISH, TRANSLATION, LEVEL) \
                    VALUES(?, ?, ?);".format(language)
        parameters = [english, translation, level]
        try:
            self.run_query(query, parameters)
            print("EN:{} and {}:{}, added".format(english, code, translation))
        except Exception as e:
            print(e)
            query = "UPDATE {} SET \
             LEVEL = ?, TRANSLATION = ? \
             WHERE ENGLISH = ?".format(language)
            print(level, english, translation)
            parameters = [level, translation, english]
            self.run_query(query, parameters)
            #QtGui.QMessageBox.warning(self, "Already added", "A word ({}) you are trying to add has already been added, so its level has been updated".format(english))

    def remove_word(self, word, code=None, language=None):
        """Method name is rather self-explanatory; removes a specified word from a specified language.
        word - the word to be removed
        code - 2 digit language code
        language - language that is appropriate to the code
        query - query to delete the word from a table of name language
        parameters - array containing the word to be removed so that it may be inserted into the query
        remove - simply exists so that the query may be executed
        """
        if code is None:
            code = self.code
        if language is None:
            language = self.get_language()
        query = "DELETE FROM {} \
            WHERE ENGLISH = ?".format(language)
        parameters = [word]
        remove = self.run_query(query, parameters)

    def get_words(self, code=None, language=None, level=6):
        """If the values are None then it defaults to the code property on the object, and gets the language.
        level=6 means that it defaults to all words
        code - 2 digit language code
        language - language that is appropriate to the code
        level - the maximum level of the words being retrieved
        query - Retrieves all records where the level is less than or equal to level
        parameters - array containing level so that it may be inserted
        """
        if code is None:
            code = self.code
        if language is None:
            language = self.get_language(code)

        query = "SELECT ENGLISH, TRANSLATION, LEVEL \
            FROM {} \
            WHERE LEVEL <= ?".format(language)
        parameters = [level]
        try:
            words = self.run_query(query, parameters)
        except Exception as e:
            print(e)
            return []
        print(words)
        return words

    def create_table(self, ddl_file, path=None):
        """Creates a table corresponding to a language"""
        if path is None:
            path = self.path

        language = self.get_language()
        with sqlite3.connect(path) as conn:
            cur = conn.cursor()
            with open(ddl_file, "r") as infile:
                """Opens a file instead of directly executing the DDL for better future-proofing in case the table
                structure changes."""
                for query in infile:
                    cur.execute(query.format(language))
                    conn.commit()


class LoginDB(Database):
    """Handles login information"""
    def __init__(self):
        """path - the sqlite file in which the user_details database is located.
        """
        path = "databases/user_details.sqlite"
        super().__init__(path) #initalize as a childclass of Database

    def verify(self, username, password):
        """Hashed username compared to all values in the table.
        If present then the password the user entered is compared with the password value received
        query - SQL query that retrieves any username/password combo where the username is the same as the username the
        user's entered.
        return values - True if the user's details are valid, False if not
        """
        print(username, password)
        query = "SELECT USERNAME, PASSWORD \
                FROM USER_DETAILS \
                WHERE USERNAME = ?"
        user_and_pass = self.run_query(query, [username])
        if len(user_and_pass) == 0:
            return False
        user_and_pass = user_and_pass[0]
        if password in user_and_pass:
            #no need to compare username as it has already been established as present.
            return True
        return False

    def change_password(self, username, old_pass, new_pass):
        """Calls verify to verify that the user exists. This checks that the user got their old password right and then
        attempts to insert the new password. This is done after validating that the new password is valid.
        valid - Whether the user's username + old password is valid
        query - SQL query that updates the user's password
        parameters - user's new password and username are inserted into parameterized query
        """
        valid = self.verify(username, old_pass)
        if valid:
            query = "UPDATE USER_DETAILS \
            SET PASSWORD = ? \
            WHERE USERNAME = ?"
            parameters = [new_pass, username]
            self.run_query(query, parameters)
            return True
        return False


def run():
    import ctypes
    """http://stackoverflow.com/questions/11812000/login-dialog-pyqt"""
    """http://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105"""

    app = QtGui.QApplication(sys.argv)
    app_id = u"revisionflashcards.v1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    app.setWindowIcon(QtGui.QIcon("style/icon.png"))
    login = Login()
    if login.exec_() == QtGui.QDialog.Accepted:
        """The user logs in and the home screen appears, which acts as a central menu
        Their information is updated as necessary
        """
        username = login.username.text()
        user = User()
        user.username = username
        user.set_ID()
        home = Home(user)
        sys.exit(app.exec_())


if __name__ == "__main__":
    run()
