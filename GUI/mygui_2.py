import sys
import json
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QFileDialog, QMessageBox, QTreeView, QHeaderView, QLabel,
                               QFrame, QTableView, QStackedWidget, QComboBox, QInputDialog, QSizePolicy,
                               QStyledItemDelegate, QMenu, QListWidget, QDialog)  # Added QDialog

from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QAction
from PySide6.QtCore import Qt, QDir
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

class NumericStandardItem(QStandardItem):
    def __init__(self, text):
        super().__init__(text)
        try:
            self.numeric_value = float(text)
        except ValueError:
            self.numeric_value = None

    def __lt__(self, other):
        if self.numeric_value is not None and other.numeric_value is not None:
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.addItems(["Categorical", "Continuous"])
        return combo_box

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class FileAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path, self.data, self.column_unique_counts, self.metadata, self.sensitive_attr = None, None, {}, {}, None
        self.original_data = pd.DataFrame()  # To store the original data for reverting changes
        self.original_columns = {}  # To store the original data of individual columns
        self.combined_values = {} 
        self.combined_values_history = {}  
        
        # Initialize main UI elements
        self.initUI()

     
    def initUI(self):
        self.setWindowTitle('File Analyzer')
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("background-color: #121212; color: #FFFFFF;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Initialize stacked widget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Initialize main page
        self.main_page = QWidget()
        self.main_page_layout = QVBoxLayout(self.main_page)
        self.add_buttons(self.main_page_layout)
        self.add_frames(self.main_page_layout)
        self.stacked_widget.addWidget(self.main_page)

        # Initialize preview page
        self.preview_page = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_page)
        self.preview_layout.setContentsMargins(10, 10, 10, 10)  # Adjust margins if needed
        self.preview_layout.setSpacing(10)  # Adjust spacing if needed

        # Create a vertical layout for the preview table and buttons
        preview_and_buttons_layout = QVBoxLayout()
        preview_and_buttons_layout.setSpacing(10)  # Adjust spacing if needed

        self.preview_table = QTableView()
        self.preview_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Ensures the table expands to fit the available space
        preview_and_buttons_layout.addWidget(self.preview_table)

        # Add the preview table and buttons layout to the main preview layout
        self.preview_layout.addLayout(preview_and_buttons_layout)

        # Add preview page widgets including buttons right below the preview data
        self.add_preview_page_widgets(preview_and_buttons_layout)

        # Create a horizontal layout for the back button and add it at the bottom
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton('Back to Main')
        self.back_button.setStyleSheet("background-color: #F44336; color: #FFFFFF;")
        self.back_button.clicked.connect(self.show_main_page)
        back_button_layout.addWidget(self.back_button)

        self.preview_layout.addLayout(back_button_layout)

        self.stacked_widget.addWidget(self.preview_page)






    def update_value_list(self):
        self.column_combobox.clear()
        self.column_combobox.addItem("Select Column")

        if self.data is not None:
            for column in self.data.columns:
                self.column_combobox.addItem(column)

    def get_categorical_columns(self):
        return [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                if self.columns_model.item(row, 2).text() == "Categorical"]


    def show_combine_values_dialog(self):
        if self.data is not None:
            # Get categorical columns
            categorical_columns = self.get_categorical_columns()

            if not categorical_columns:
                QMessageBox.warning(self, "No Categorical Columns", "No categorical columns available for combining values.")
                return

            column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to combine values:", categorical_columns, 0, False)

            if ok and column_name:
                unique_values = self.data[column_name].unique()
                unique_values = [val for val in unique_values if pd.notna(val)]  # Remove NaN values

                if len(unique_values) < 2:
                    QMessageBox.warning(self, "Not Enough Values", "The selected column does not have enough unique values to combine.")
                    return

                # Create a dialog to select unique values
                dialog = QDialog(self)
                dialog.setWindowTitle("Select Values to Combine")
                dialog.setStyleSheet("background-color: #121212; color: #FFFFFF;")
                layout = QVBoxLayout(dialog)

                list_widget = QListWidget(dialog)
                list_widget.setSelectionMode(QListWidget.MultiSelection)
                list_widget.addItems(unique_values)
                layout.addWidget(list_widget)

                combine_button = QPushButton("Combine", dialog)
                combine_button.setStyleSheet("background-color: #4CAF50; color: #FFFFFF;")
                combine_button.clicked.connect(lambda: self.combine_selected_values(column_name, list_widget.selectedItems()))
                layout.addWidget(combine_button)

                dialog.setLayout(layout)
                dialog.resize(400, 300)
                dialog.exec()  # Use exec() for QDialog
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")


    def combine_selected_values(self, column_name, selected_items):
        selected_values = [item.text() for item in selected_items]

        if len(selected_values) < 2:
            QMessageBox.warning(self, "Insufficient Selection", "Please select at least two values to combine.")
            return

        # Store original data for the column if not already stored
        if column_name not in self.original_columns:
            self.original_columns[column_name] = self.data[column_name].copy()

        # Combine the selected values
        replacement_value = QInputDialog.getText(self, "Combine Values", "Enter the new value for the selected items:")
        
        if replacement_value[1]:  # Check if the user clicked OK and provided a value
            if column_name not in self.combined_values_history:
                self.combined_values_history[column_name] = []
            self.combined_values_history[column_name].append((selected_values, replacement_value[0]))
            self.data[column_name] = self.data[column_name].replace(selected_values, replacement_value[0])
            self.show_preview()  # Refresh the preview to show updated data
            QMessageBox.information(self, "Success", "Values have been successfully combined.")




    def add_buttons(self, layout):
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        buttons = [
            ("Load CSV/TSV File", self.load_file, "#4CAF50"),
            ("Privacy Calculation", self.calculate_unique_rows, "#2196F3"),
            ("Variable Optimization", self.find_lowest_unique_columns, "#FFC107"),
            ("Preview Data", self.show_preview, "#009688")
        ]
        for text, slot, color in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: #FFFFFF;")
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)

    def add_frames(self, layout):
        self.load_results_frame, self.variable_optimization_frame = QFrame(), QFrame()
        for frame in (self.load_results_frame, self.variable_optimization_frame):
            frame.setStyleSheet("border: 0.5px solid #FFFFFF;")
            layout.addWidget(frame)
        self.add_load_results_layout()
        self.add_variable_optimization_layout()
        self.result_label = QLabel('')
        self.result_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.result_label)

    def add_load_results_layout(self):
        load_results_layout = QVBoxLayout(self.load_results_frame)
        self.columns_view = QTreeView()
        self.columns_model = QStandardItemModel()
        self.columns_model.setHorizontalHeaderLabels(["Select Columns", "Unique Value", "Type", "Select Sensitive Attribute"])
        self.columns_view.setModel(self.columns_model)

        # Set up the delegate for the "Type" column
        self.type_delegate = ComboBoxDelegate(self.columns_view)
        self.columns_view.setItemDelegateForColumn(2, self.type_delegate)

        self.setup_treeview(self.columns_view)
        load_results_layout.addWidget(self.columns_view)

    def add_variable_optimization_layout(self):
        variable_optimization_layout = QVBoxLayout(self.variable_optimization_frame)
        self.results_view = QTreeView()
        self.results_model = QStandardItemModel()
        self.results_model.setHorizontalHeaderLabels(["Quasi Identifiers", "Unique Rows After Removal", "Difference", "Normalized"])
        self.results_view.setModel(self.results_model)
        self.setup_treeview(self.results_view)
        variable_optimization_layout.addWidget(self.results_view)

    def add_preview_page_widgets(self, layout):
        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        
        # Existing buttons
        button_data = [
            ('Round Continuous Values', '673AB7', self.round_values),
            ('Add Laplacian Noise', '009688', lambda: self.add_noise('laplacian')),
            ('Add Gaussian Noise', '4CAF50', lambda: self.add_noise('gaussian')),
            ('Revert to Original', 'FF5722', self.revert_to_original),
            ('Combine Values', 'FF9800', self.show_combine_values_dialog)  # Add Combine Values button
        ]

        for text, color, func in button_data:
            button = QPushButton(text)
            button.setStyleSheet(f"background-color: #{color}; color: #FFFFFF;")
            button.clicked.connect(func)
            button_layout.addWidget(button)
        
        # Add the new "Graph Categorical" button
        self.graph_button = QPushButton('Graph Categorical')
        self.graph_button.setStyleSheet("background-color: #3F51B5; color: #FFFFFF;")
        self.graph_button.clicked.connect(self.show_graph_categorical_dialog)
        button_layout.addWidget(self.graph_button)
        
        layout.addLayout(button_layout)

        # Metadata display
        self.metadata_display = QLabel('')
        self.metadata_display.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.metadata_display)

        # Create vertical layout for metadata controls
        metadata_layout = QVBoxLayout()
        self.column_dropdown = QComboBox()
        self.column_dropdown.addItem("Select Column")
        self.column_dropdown.currentIndexChanged.connect(self.show_metadata_for_column)
        self.column_dropdown.setStyleSheet("""
            QComboBox {
                border: 2px solid #FFFFFF;
                border-radius: 5px;
                padding: 2px 4px;
                background-color: #121212;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                border-left: 2px solid #FFFFFF;
            }
        """)
        metadata_layout.addWidget(self.column_dropdown)
        self.load_metadata_button = QPushButton('Load JSON Metadata')
        self.load_metadata_button.setStyleSheet("background-color: #3F51B5; color: #FFFFFF;")
        self.load_metadata_button.clicked.connect(self.load_metadata)
        metadata_layout.addWidget(self.load_metadata_button)

        layout.addLayout(metadata_layout)


    def show_graph_categorical_dialog(self):
        if self.data is not None:
            # Get categorical columns
            categorical_columns = self.get_categorical_columns()

            if not categorical_columns:
                QMessageBox.warning(self, "No Categorical Columns", "No categorical columns available for graphing.")
                return

            column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to graph:", categorical_columns, 0, False)

            if ok and column_name:
                self.plot_tree_graph(column_name)  # Plot with the updated combined values
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")



    def plot_tree_graph(self, column_name):
        # Create a NetworkX graph
        G = nx.DiGraph()  # Directed graph to show hierarchy

        # Add the column name as the root node
        G.add_node(column_name)

        # Track nodes and edges to add
        nodes_to_add = set()
        edges_to_add = set()

        # Process all combined values from history for the column
        if column_name in self.combined_values_history:
            for combined_values, replacement_value in self.combined_values_history[column_name]:
                nodes_to_add.add(replacement_value)
                edges_to_add.add((column_name, replacement_value))
                for value in combined_values:
                    if pd.notna(value):
                        nodes_to_add.add(value)
                        edges_to_add.add((replacement_value, value))

        # Ensure that all unique values are added, even if they are not part of the combined values
        unique_values = self.data[column_name].unique()
        for value in unique_values:
            if pd.notna(value) and value not in G.nodes:
                G.add_node(value)
                G.add_edge(column_name, value)

        # Add nodes and edges to the graph
        G.add_nodes_from(nodes_to_add)
        G.add_edges_from(edges_to_add)

        # Get positions for the nodes in the graph using graphviz_layout
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot')  # 'dot' is used for hierarchical layout

        # Create a plot
        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, with_labels=True, node_size=1000, node_color='white', font_size=6, font_weight='normal', edge_color='black', arrows=True)

        # Add title
        plt.title(f'Tree Graph of Values in Column "{column_name}"', fontsize=12)

        # Show the plot
        plt.show()






    def create_noise_menu(self):
        noise_menu = QMenu()
        laplacian_action = QAction('Add Laplacian Noise', self)
        laplacian_action.triggered.connect(lambda: self.add_noise('laplacian'))
        noise_menu.addAction(laplacian_action)
        gaussian_action = QAction('Add Gaussian Noise', self)
        gaussian_action.triggered.connect(lambda: self.add_noise('gaussian'))
        noise_menu.addAction(gaussian_action)
        return noise_menu

    def add_noise(self, noise_type):

        print(f"Add noise triggered with type: {noise_type}") 
        # Get columns of type "Continuous"
        continuous_columns = [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                              if self.columns_model.item(row, 2).text() == "Continuous"]

        if not continuous_columns:
            QMessageBox.warning(self, "No Continuous Columns", "No continuous columns available for adding noise.")
            return

        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to add noise:", continuous_columns, 0, False)
        if ok and column_name:
            try:
                if column_name in self.data.columns:
                    if column_name not in self.original_columns:
                        self.original_columns[column_name] = self.data[column_name].copy()  # Store original column data
                    if noise_type == 'laplacian':
                        noise = np.random.laplace(loc=0.0, scale=1.0, size=len(self.data[column_name]))
                    elif noise_type == 'gaussian':
                        noise = np.random.normal(loc=0.0, scale=1.0, size=len(self.data[column_name]))
                    self.data[column_name] += noise
                    self.show_preview()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while adding noise: {e}")

    def setup_treeview(self, view):
        # Configure tree view
        is_columns_view = view is self.columns_view
        view.setSelectionMode(QTreeView.MultiSelection if is_columns_view else QTreeView.NoSelection)
        view.setStyleSheet("background-color: #121212; color: #FFFFFF;")
        view.setSortingEnabled(True)
        view.header().setSectionResizeMode(QHeaderView.Stretch)
        view.header().setFont(QFont("Helvetica", 13))
        view.header().setStyleSheet("QHeaderView::section { background-color: #333; color: #FFFFFF; }")


    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath(), "CSV files (*.csv);;TSV files (*.tsv);;All files (*)")
        if file_path:
            self.load_data(file_path)

    def load_data(self, file_path):
        try:
            sep = '\t' if file_path.lower().endswith('.tsv') else ','
            self.data = pd.read_csv(file_path, sep=sep)
            self.data.columns = self.data.columns.str.strip()
            self.column_unique_counts = {col: self.data[col].nunique() for col in self.data.columns}
            sorted_columns = sorted(self.column_unique_counts.items(), key=lambda x: x[1], reverse=True)
            column_types = [(col, count, "Continuous" if count > 25 else "Categorical") for col, count in sorted_columns]
            self.original_data = self.data.copy()  # Store the original data
            self.update_treeview(self.columns_model, column_types, add_checkbox=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def update_treeview(self, model, data_list, add_checkbox=False):
        model.removeRows(0, model.rowCount())
        for values in data_list:
            items = [NumericStandardItem(str(value)) if isinstance(value, (int, float)) else QStandardItem(str(value)) for value in values]
            if add_checkbox:
                checkbox_item = QStandardItem()
                checkbox_item.setCheckable(True)
                items.append(checkbox_item)
            model.appendRow(items)

    def calculate_unique_rows(self):
        selected_columns = self.get_selected_columns()
        if selected_columns:
            sensitive_attr = self.get_sensitive_attribute()
            try:
                value_counts = self.data[selected_columns].value_counts()
                num_unique_rows = len(value_counts[value_counts == 1])
                k_anonymity = self.calculate_k_anonymity(selected_columns)
                l_diversity = self.calculate_l_diversity(selected_columns, sensitive_attr) if sensitive_attr else None
                result_text = (f"Unique Rows: {num_unique_rows}\n"
                               f"K-Anonymity: {k_anonymity}\n"
                               f"L-Diversity: {l_diversity}\n")
                self.result_label.setText(result_text)
            except Exception as e:
                self.result_label.setText(f"An error occurred: {e}")

    def get_selected_columns(self):
        selected_indexes = self.columns_view.selectionModel().selectedRows()
        selected_columns = [self.columns_model.itemFromIndex(index).text() for index in selected_indexes]
        if not selected_columns:
            self.result_label.setText("Please select at least one column.")
        return selected_columns

    def get_sensitive_attribute(self):
        for row in range(self.columns_model.rowCount()):
            if self.columns_model.item(row, 3).checkState() == Qt.Checked:
                return self.columns_model.item(row, 0).text()
        return None

    def calculate_k_anonymity(self, selected_columns):
        grouped = self.data.groupby(selected_columns).size().reset_index(name='counts')
        return grouped['counts'].min()

    def calculate_l_diversity(self, selected_columns, sensitive_attr):
        grouped = self.data.groupby(selected_columns)
        return grouped[sensitive_attr].nunique().min()

    def find_lowest_unique_columns(self):
        selected_columns = self.get_selected_columns()
        if selected_columns:
            try:
                subset_data = self.data[selected_columns]
                value_counts = subset_data.value_counts()
                unique_rows = value_counts[value_counts == 1].index
                all_unique_count = len(unique_rows)

                results = []
                for column in selected_columns:
                    temp_columns = [col for col in selected_columns if col != column]
                    if temp_columns:
                        subset_data_after_removal = self.data[temp_columns]
                        value_counts_after_removal = subset_data_after_removal.value_counts()
                        unique_rows_after_removal = value_counts_after_removal[value_counts_after_removal == 1].index
                        unique_count_after_removal = len(unique_rows_after_removal)
                        difference = all_unique_count - unique_count_after_removal
                        unique_values_count = subset_data[column].nunique()
                        normalized_difference = round(difference / unique_values_count, 1)
                        results.append((column, unique_count_after_removal, difference, normalized_difference))

                results.sort(key=lambda x: x[3], reverse=True)
                self.update_treeview(self.results_model, results, add_checkbox=False)
            except Exception as e:
                self.result_label.setText(f"An error occurred: {e}")

    def show_preview(self):
        if self.data is not None:
            preview_data = self.data.head(10)
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(preview_data.columns)
            for row in preview_data.itertuples(index=False):
                items = [NumericStandardItem(str(item)) if isinstance(item, (int, float)) else QStandardItem(str(item)) for item in row]
                model.appendRow(items)
            self.preview_table.setModel(model)
            self.preview_table.setMaximumHeight(200)  # Set a maximum height for the preview table
            self.update_column_dropdown()
            self.stacked_widget.setCurrentWidget(self.preview_page)
        else:
            QMessageBox.warning(self, "Warning", "No data loaded. Please load a file first.")

    def load_metadata(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", QDir.homePath(), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.metadata = json.load(f)
                self.update_column_dropdown()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def update_column_dropdown(self):
        self.column_dropdown.clear()
        self.column_dropdown.addItem("Select Column")
        if self.metadata:
            for column in self.metadata.keys():
                self.column_dropdown.addItem(column)

    def show_metadata_for_column(self):
        column_name = self.column_dropdown.currentText()
        if column_name in self.metadata:
            metadata_info = self.metadata[column_name]
            self.metadata_display.setText(f"Metadata for {column_name}:\n{json.dumps(metadata_info, indent=4)}")
        else:
            QMessageBox.warning(self, "No metadata available for the selected column.")

    def round_values(self):
        # Get continuous columns
        continuous_columns = [self.columns_model.item(row, 0).text() for row in range(self.columns_model.rowCount())
                              if self.columns_model.item(row, 2).text() == "Continuous"]

        if not continuous_columns:
            QMessageBox.warning(self, "No Continuous Columns", "No continuous columns available for rounding.")
            return

        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to round:", continuous_columns, 0, False)
        if ok and column_name:
            precision, ok = QInputDialog.getItem(self, "Select Precision", "Select rounding precision:", ["10^1", "10^2", "10^3", "10^4", "10^5", "10^6"], 0, False)
            if ok and precision:
                try:
                    factor = 10 ** int(precision.split('^')[1])
                    if column_name in self.data.columns:
                        self.original_columns.setdefault(column_name, self.data[column_name].copy())  # Store original data if not already
                        self.data[column_name] = (self.data[column_name] / factor).round() * factor
                        self.show_preview()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An error occurred while rounding: {e}")

    def revert_to_original(self):
        column_name, ok = QInputDialog.getItem(self, "Select Column", "Select column to revert:", list(self.original_columns.keys()), 0, False)
        if ok and column_name:
            try:
                if column_name in self.original_columns:
                    self.data[column_name] = self.original_columns[column_name]
                    self.show_preview()
                else:
                    QMessageBox.warning(self, "Warning", f"No original data available for column {column_name}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while reverting: {e}")

    def show_main_page(self):
        self.stacked_widget.setCurrentWidget(self.main_page)

    def show_preview_page(self):
        self.stacked_widget.setCurrentWidget(self.preview_page)

    def show_hierarchical_page(self):
        self.stacked_widget.setCurrentWidget(self.hierarchical_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileAnalyzer()
    window.show()
    sys.exit(app.exec())
