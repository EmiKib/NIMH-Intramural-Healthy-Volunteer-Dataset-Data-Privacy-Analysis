import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd

class FileAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("File Analyzer")
        
        
        self.root.geometry("800x600")
        
        
        self.root.configure(bg="#f0f0f0")
        
        self.file_path = None
        self.data = None
        self.column_unique_counts = {}  # Dictionary to store column names and their unique counts
        
        
        self.button_frame = tk.Frame(root, bg="#f0f0f0")
        self.button_frame.pack(pady=20, fill=tk.X)
        
        
        self.load_button = tk.Button(
            self.button_frame, 
            text="Load CSV/TSV File", 
            command=self.load_file, 
            height=2, width=20, 
            bg="#4CAF50", 
            fg="black", 
            font=("Helvetica", 12, "bold")
        )
        self.load_button.pack(padx=10, side=tk.LEFT)
        
        
        self.calculate_button = tk.Button(
            self.button_frame, 
            text="Calculate Unique Rows", 
            command=self.calculate_unique_rows, 
            height=2, width=20, 
            bg="#2196F3", 
            fg="black", 
            font=("Helvetica", 12, "bold")
        )
        self.calculate_button.pack(padx=10, side=tk.LEFT)
        
        
        self.columns_frame = tk.Frame(root, bg="#f0f0f0")
        self.columns_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.columns_treeview = ttk.Treeview(self.columns_frame, columns=("Column", "Unique Count"), show='headings', selectmode='none')
        self.columns_treeview.heading("Column", text="Column Name")
        self.columns_treeview.heading("Unique Count", text="Unique Count")
        self.columns_treeview.column("Column", width=400, anchor="w")
        self.columns_treeview.column("Unique Count", width=100, anchor="center")
        self.columns_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_scrollbar = tk.Scrollbar(self.columns_frame, orient="vertical", command=self.columns_treeview.yview)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.columns_treeview.config(yscrollcommand=self.tree_scrollbar.set)
        
        
        self.columns_treeview.bind("<ButtonRelease-1>", self.on_treeview_click)
        
    
        self.result_frame = tk.Frame(root, bg="#f0f0f0")
        self.result_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        self.result_label = tk.Label(self.result_frame, text="", font=("Helvetica", 12), bg="#f0f0f0")
        self.result_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

    def load_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("TSV files", "*.tsv"), ("All files", "*.*")]
        )
        if self.file_path:
            try:
                if self.file_path.endswith('.csv'):
                    self.data = pd.read_csv(self.file_path)
                elif self.file_path.endswith('.tsv'):
                    self.data = pd.read_csv(self.file_path, sep='\t')
                else:
                    raise ValueError("Unsupported file format")
                
             
                self.columns_treeview.delete(*self.columns_treeview.get_children())
                
                self.column_unique_counts = {}
                for col in self.data.columns:
                    unique_count = self.data[col].nunique()
                    self.column_unique_counts[col] = unique_count
                    self.columns_treeview.insert('', 'end', iid=col, values=(col, unique_count))
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    def on_treeview_click(self, event):
        
        item = self.columns_treeview.identify_row(event.y)
        if item:
            
            current_selection = self.columns_treeview.selection()
            if item in current_selection:
                self.columns_treeview.selection_remove(item)
            else:
                self.columns_treeview.selection_add(item)

    def calculate_unique_rows(self):
        selected_items = self.columns_treeview.selection()
        if not selected_items:
            self.result_label.config(text="Please select at least one column.")
            return
        
        selected_columns = [self.columns_treeview.item(item, 'values')[0] for item in selected_items]
        
        for col in selected_columns:
            if col not in self.data.columns:
                self.result_label.config(text=f"Column '{col}' is not found in the data.")
                return
        
        try:
            total_rows = len(self.data)
            unique_rows = self.data[selected_columns].drop_duplicates()
            unique_count = len(unique_rows)
            
            
            if unique_count >= 1:
                result_text = (f"Total rows: {total_rows}\n"
                               f"Unique rows based on the selected columns: {unique_count}\n"
                               f"k = 1")
            else:
                result_text = (f"Total rows: {total_rows}\n"
                               f"Unique rows based on the selected columns: {unique_count}")

            self.result_label.config(text=result_text)
        except Exception as e:
            self.result_label.config(text=f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileAnalyzer(root)
    root.mainloop()
