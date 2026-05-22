# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 10:06:51 2026

@author: dgregory
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import os
from datetime import datetime, date

import matplotlib
matplotlib.use("Agg")  # For off-screen rendering
from matplotlib.figure import Figure

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors

from shared_utils.get_GCDdata import get_data as gcd


# ============================================================
#  Sample Data (for testing)
# ============================================================
Default_patient_info = {
    "lastname": "Doe",
    "firstname": "Jane",
    "id": "123456",
    "physician": "Dr. Smith",
    "injury": "ACL Tear",
    "injury_side": "Right",
    "age": 12,
    "dob": "2012-01-01",
    "therapist": "Jane Therapist",
    "injury_date": "2019-12-01",
    "surgery_date": "2020-01-01"
}

# ---- Sample visit data 

# Visits with dynamic knee valgus (DKV) and hip vs knee strategy measures
# Each measure: mean, sd, norm_mean, norm_sd
SAMPLE_VISITS = [
    {
        "visit_date": "2025-02-10",
        "dynamic_knee_valgus": {
            "max_knee_valgus_moment": {"mean": 1.2, "sd": 0.2, "norm_mean": 1.0, "norm_sd": 0.15},
            "knee_abduction_angle": {"mean": 5.0, "sd": 1.0, "norm_mean": 4.0, "norm_sd": 0.8},
            "frontal_plane_knee_angle": {"mean": 3.0, "sd": 0.5, "norm_mean": 2.5, "norm_sd": 0.4},
            "knee_internal_rotation": {"mean": 2.0, "sd": 0.3, "norm_mean": 1.8, "norm_sd": 0.25},
            "knee_flexion_angle": {"mean": 45.0, "sd": 3.0, "norm_mean": 47.0, "norm_sd": 2.5},
        },
        "hip_knee_strategy": {
            "hip_flexion": {"mean": 40.0, "sd": 4.0, "norm_mean": 42.0, "norm_sd": 3.0},
            "knee_flexion": {"mean": 45.0, "sd": 3.0, "norm_mean": 47.0, "norm_sd": 2.5},
            "hip_knee_ratio": {"mean": 0.9, "sd": 0.1, "norm_mean": 1.0, "norm_sd": 0.1},
            "hip_moment": {"mean": 1.5, "sd": 0.2, "norm_mean": 1.4, "norm_sd": 0.15},
            "knee_moment": {"mean": 1.2, "sd": 0.2, "norm_mean": 1.1, "norm_sd": 0.15},
            "hip_knee_moment_ratio": {"mean": 1.25, "sd": 0.1, "norm_mean": 1.2, "norm_sd": 0.1},
        }
    },
    {
        "visit_date": "2025-03-10",
        "dynamic_knee_valgus": {
            "max_knee_valgus_moment": {"mean": 1.1, "sd": 0.25, "norm_mean": 1.0, "norm_sd": 0.15},
            "knee_abduction_angle": {"mean": 4.8, "sd": 0.9, "norm_mean": 4.0, "norm_sd": 0.8},
            "frontal_plane_knee_angle": {"mean": 2.8, "sd": 0.4, "norm_mean": 2.5, "norm_sd": 0.4},
            "knee_internal_rotation": {"mean": 1.9, "sd": 0.35, "norm_mean": 1.8, "norm_sd": 0.25},
            "knee_flexion_angle": {"mean": 46.0, "sd": 2.5, "norm_mean": 47.0, "norm_sd": 2.5},
        },
        "hip_knee_strategy": {
            "hip_flexion": {"mean": 41.0, "sd": 3.5, "norm_mean": 42.0, "norm_sd": 3.0},
            "knee_flexion": {"mean": 46.0, "sd": 2.8, "norm_mean": 47.0, "norm_sd": 2.5},
            "hip_knee_ratio": {"mean": 0.95, "sd": 0.08, "norm_mean": 1.0, "norm_sd": 0.1},
            "hip_moment": {"mean": 1.45, "sd": 0.18, "norm_mean": 1.4, "norm_sd": 0.15},
            "knee_moment": {"mean": 1.15, "sd": 0.18, "norm_mean": 1.1, "norm_sd": 0.15},
            "hip_knee_moment_ratio": {"mean": 1.23, "sd": 0.09, "norm_mean": 1.2, "norm_sd": 0.1},
        }
    }
]

# ---- RTS cut points
cut_points = {
    "dynamic_knee_valgus": {
        "lateral_trunk_lean": {
            "heel_touch":       "<=a10", # less than or equal to 10 degrees both directions - i.e. absolute value
            "side_step_cut":    ">=-5",
            "lateral_shuffle":  "<=+10",
            "deceleration":     "<=a10",
            "single_hop":       "<=a10"
            }
        }
    }

# ============================================================
#  Get data and calculate metrics (placeholder)
# ============================================================
class DataHandling:
        
    def getData_dialog(self):
        """
        Opens a file dialog to select .gcd files and extracts data from them.
        Returns a list of extracted data objects.
        """
        # Ask user to select one or more .gcd files
        file_paths = filedialog.askopenfilenames(
            title="Select GCD Data Files",
            filetypes=[("Patient Files", ["*.gcd", "*.py"])],
        )

        if not file_paths:
            messagebox.showinfo("No Files Selected", "No .gcd files were chosen.")
            return None

        gcd_data = []
        py_data  = []

        for path in file_paths:
            filename = os.path.basename(path)
            if '.py' in path.lower():
                try:
                    # Read the file contents
                    with open(path, "r", encoding="utf-8") as f:
                        file_text = f.read()
            
                    # parse data info key:value pairs with "self.name" as key, and stuff on the other side of "=" as the value
                    py_list = file_text.split("\n")
                    
                    # add key:value pairs and strip the quotes off the text - nested list comprehension within dictionary comprehension                     
                    py_dict = {pyitem[0].split(".")[1]: pyitem[1].split(" #")[0].strip().strip("'").strip('"')
                                    for pyitem in [listitem.split(" = ") 
                                    for listitem in py_list] if len(pyitem) > 1
                                    }
                    
                    py_data.append({
                        "file_path": filename,
                        "data": py_dict
                    })
            
                except Exception as e:
                    messagebox.showerror(
                        "Error Reading File",
                        f"Could not read Python file:\n{path}\n\nError:\n{e}"
                    )
                
            elif '.gcd' in path.lower():
                try:
                    # get GCD data function
                    data_dict = gcd(path)
    
                    gcd_data.append({
                        "file_path": filename,
                        "data": data_dict
                    })
                    
                except Exception as e:
                    messagebox.showerror(
                        "Error Reading File",
                        f"Could not extract data from:\n{path}\n\nError:\n{e}"
                    )

        return gcd_data, py_data
    
    def compute_days_out(self, visit_date_str, surgery_date_str):
        try:
            visit = datetime.strptime(visit_date_str, "%Y-%m-%d").date()
            surgery = datetime.strptime(surgery_date_str, "%Y-%m-%d").date()
            return (visit - surgery).days
        except Exception:
            return None
        
    def calculate_age(self, dob_str, on_date_str=None):
        """
        Calculate age from a DOB string (YYYY-MM-DD).
        If on_date_str is provided, age is calculated relative to that date.
        Otherwise, age is calculated relative to today.
        """

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except Exception:
            return None  # invalid DOB format

        if on_date_str:
            try:
                ref_date = datetime.strptime(on_date_str, "%Y-%m-%d").date()
            except Exception:
                ref_date = date.today()
        else:
            ref_date = date.today()

        # Compute age
        age = ref_date.year - dob.year - (
            (ref_date.month, ref_date.day) < (dob.month, dob.day)
        )

        return age


# ============================================================
#  Plot Manager
# ============================================================
class PlotManager:
    def __init__(self):
        pass

    def plot_errbar_data(self, fig, visits, measure_keys, title_prefix):
        """
        measure_keys: list of measure names (rows)
        visits: list of visit dicts (columns up to 5)
        """
        n_rows = len(measure_keys)
        n_cols = min(len(visits), 5)

        for r, measure in enumerate(measure_keys):
            for c, visit in enumerate(visits[:5]): # limit to 5
                ax = fig.add_subplot(n_rows, n_cols, r * n_cols + c + 1)
                vdate = visit["visit_date"]
                data = visit[title_prefix.lower().replace(" ", "_")][measure]

                # x is just a single point per visit; we plot as bar with errorbar
                x = [1]
                y = [data["mean"]]
                yerr = [data["sd"]]

                ax.errorbar(x, y, yerr=yerr, fmt='o', color='blue', label='Visit mean ±1SD')

                # Normative band
                norm_mean = data["norm_mean"]
                norm_sd = data["norm_sd"]
                ax.axhspan(norm_mean - norm_sd, norm_mean + norm_sd,
                           color='gray', alpha=0.3, label='Norm ±1SD')

                ax.set_title(f"{measure}\n{vdate}", fontsize=8)
                ax.set_xticks([])
                ax.grid(True, alpha=0.3)

                if c == 0:
                    ax.set_ylabel(measure, fontsize=7)

        fig.suptitle(title_prefix, fontsize=12)

    def dkv_errbar_figure(self, visits):
        measure_keys = [
            "max_knee_valgus_moment",
            "knee_abduction_angle",
            "frontal_plane_knee_angle",
            "knee_internal_rotation",
            "knee_flexion_angle",
        ]
        fig = Figure(figsize=(8.5, 11))  # full page
        self.plot_errbar_data(fig, visits, measure_keys, "dynamic_knee_valgus")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        return fig

    def hks_errbar_figure(self, visits):
        measure_keys = [
            "hip_flexion",
            "knee_flexion",
            "hip_knee_ratio",
            "hip_moment",
            "knee_moment",
            "hip_knee_moment_ratio",
        ]
        fig = Figure(figsize=(8.5, 11))
        self.plot_errbar_data(fig, visits, measure_keys, "hip_knee_strategy")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        return fig


# ============================================================
#  Data Formatter (JSON + HTML)
# ============================================================
class DataFormatter:
    def format_data(self, patient_data, visits):
        return {
            "patient": patient_data,
            "visits": visits
        }

    def save_to_json(self, data, filename):
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def save_to_html(self, patient_data, visits, filename):
        # Simple 3-section HTML with CSS page breaks for printing
        days_out = "-"
        if visits and patient_data.get("surgery_date"):
            try:
                visit_date = visits[-1]["visit_date"]
                visit = datetime.strptime(visit_date, "%Y-%m-%d").date()
                surgery = datetime.strptime(patient_data["surgery_date"], "%Y-%m-%d").date()
                days_out = (visit - surgery).days
            except Exception:
                pass

        html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <title>Patient Report</title>
            <style>
            .page {{
              page-break-after: always;
              padding: 20px;
              font-family: Arial, sans-serif;
            }}
            .header {{
              font-size: 12px;
              border-bottom: 1px solid #000;
              margin-bottom: 10px;
            }}
            .subheader {{
              font-size: 10px;
              border-bottom: 1px solid #000;
              margin-bottom: 10px;
            }}
            </style>
            </head>
            <body>
            
            <div class="page">
              <div class="header">
                <p>Name: {patient_data.get("name","")} |
                   ID: {patient_data.get("id","")} |
                   Physician: {patient_data.get("physician","")} |
                   Injury: {patient_data.get("injury","")} ({patient_data.get("injury_side","")})</p>
                <p>Age: {patient_data.get("age","")} |
                   DOB: {patient_data.get("dob","")} |
                   Visit Date: {visits[-1]["visit_date"] if visits else ""} |
                   Therapist: {patient_data.get("therapist","")}</p>
                <p>Surgery/Injury Date: {patient_data.get("surgery_date","")} |
                   Days Out: {days_out}</p>
              </div>
              <h3>Summary of Movements (Walk, Drop Jump, Heel Touch)</h3>
              <p>(Reserved for later data.)</p>
            </div>
            
            <div class="page">
              <div class="subheader">
                <p>Name: {patient_data.get("name","")} |
                   ID: {patient_data.get("id","")} |
                   Injury Side: {patient_data.get("injury_side","")} |
                   Visit Date: {visits[-1]["visit_date"] if visits else ""}</p>
              </div>
              <h3>Dynamic Knee Valgus Summary</h3>
              <p>Plots are in the PDF version.</p>
            </div>
            
            <div class="page">
              <div class="subheader">
                <p>Name: {patient_data.get("name","")} |
                   ID: {patient_data.get("id","")} |
                   Injury Side: {patient_data.get("injury_side","")} |
                   Visit Date: {visits[-1]["visit_date"] if visits else ""}</p>
              </div>
              <h3>Hip vs Knee Strategy Summary</h3>
              <p>Plots are in the PDF version.</p>
            </div>
            
            </body>
            </html>
            """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)


# ============================================================
#  Report Generator (PDF with ReportLab)
# ============================================================
class ReportGenerator:
    def __init__(self, plot_manager, metrics_calc):
        self.plot_manager   = plot_manager
        self.metrics_calc   = metrics_calc
        self.styles         = getSampleStyleSheet()
        
    # ---- For Spencer
    def generate_summary_page(self, patient_data):
        print("Hey Spencer, fix this")
        lastname = patient_data["lastname"]
        print(f'patient last name: {lastname}')
        return None
    
    def generate_pdf(self, filename, patient_data, visits, tmp_dir="tmp_plots"):
        os.makedirs(tmp_dir, exist_ok=True)

        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        # ---------- Page 1 ----------
        visit_date = visits[-1]["visit_date"] if visits else date.today().strftime("%Y-%m-%d")
        days_out = self.metrics_calc.compute_days_out(visit_date, patient_data.get("surgery_date", ""))

        header_text = (
            f"Name: {patient_data.get('name','')} | "
            f"ID: {patient_data.get('id','')} | "
            f"Physician: {patient_data.get('physician','')} | "
            f"Injury: {patient_data.get('injury','')} ({patient_data.get('injury_side','')})<br/>"
            f"Age: {patient_data.get('age','')} | "
            f"DOB: {patient_data.get('dob','')} | "
            f"Visit Date: {visit_date} | "
            f"Therapist: {patient_data.get('therapist','')}<br/>"
            f"Surgery/Injury Date: {patient_data.get('surgery_date','')} | "
            f"Days Out: {days_out if days_out is not None else '-'}"
        )
        story.append(Paragraph(header_text, self.styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("<b>Summary of Movements</b>", self.styles["Heading2"]))
        story.append(Paragraph("Walk, Drop Jump, Heel Touch (reserved for later data).", self.styles["Normal"]))
        story.append(Spacer(1, 6 * inch))  # leave room
        story.append(PageBreak())

        # ---------- Page 2 (dynamic_knee_valgus) ----------
        small_header = (
            f"Name: {patient_data.get('name','')} | "
            f"ID: {patient_data.get('id','')} | "
            f"Injury Side: {patient_data.get('injury_side','')} | "
            f"Visit Date: {visit_date}"
        )
        story.append(Paragraph(small_header, self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("<b>Dynamic Knee Valgus Summary</b>", self.styles["Heading2"]))
        story.append(Spacer(1, 0.2 * inch))

        dkv_fig = self.plot_manager.dkv_errbar_figure(visits)
        dkv_path = os.path.join(tmp_dir, "dynamic_knee_valgus_page.png")
        dkv_fig.savefig(dkv_path, dpi=150, bbox_inches="tight")
        story.append(Image(dkv_path, width=7.5 * inch, height=9 * inch))
        story.append(PageBreak())

        # ---------- Page 3 (Hip vs Knee) ----------
        story.append(Paragraph(small_header, self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("<b>Hip vs Knee Strategy Summary</b>", self.styles["Heading2"]))
        story.append(Spacer(1, 0.2 * inch))

        hip_fig = self.plot_manager.hks_errbar_figure(visits)
        hip_path = os.path.join(tmp_dir, "hip_knee_page.png")
        hip_fig.savefig(hip_path, dpi=150, bbox_inches="tight")
        story.append(Image(hip_path, width=7.5 * inch, height=9 * inch))

        doc.build(story)


# ============================================================
#  Main Application
# ============================================================
class PatientReportApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Patient Report Generator")
        self.geometry("850x395")

        # Classes
        self.plot_manager           = PlotManager()
        self.metrics_calc           = DataHandling()
        self.data_formatter         = DataFormatter()
        self.report_generator       = ReportGenerator(self.plot_manager, self.metrics_calc)

        # Data
        self.patient_data           = Default_patient_info.copy()
        self.visits                 = SAMPLE_VISITS.copy()
        self.data_handler           = DataHandling()
        self.loaded_gcd_data        = None
        self.loaded_py_data         = None

        # Previewing
        self.plot_window            = None
        self.first_preview_render   = True # preview window render set
        self.current_preview_page   = 1
        self.preview_figures        = {}   # will store fig objects for the report pages
        self.create_widgets()
        
        # open file explorer and pick data
        # self.load_gcd_data()
    def call_ReportGeneratorfuncs(self, function_to_call):
        '''
        SUMMARY: need to call functions across apps through a specific function call
        The function call requires a function within the class where it is being
        called, which is this function

        Returns: whatever the function that is called in the other app is, will be returned
        '''
        if function_to_call == 'generate_summary':
            self.report_generator.generate_summary_page(self.patient_data)
    
    def add_placeholder(self, entry, placeholder, color="gray"):
        entry.insert(0, placeholder)
        entry.config(foreground=color)
    
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(foreground="black")
    
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(foreground=color)
    
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def reset_app(self):
        """
        Reset the entire application to its initial state,
        as if it was just opened.
        """
    
        # --- Reset stored data ---
        self.patient_data = Default_patient_info
    
        self.loaded_gcd_data = None
        self.loaded_python_data = None
        self.current_preview_page = 1
    
        # --- Clear all entry widgets ---
        for entry in [
            self.entry_first_name,
            self.entry_last_name,
            self.entry_dob,
            self.entry_visit_date,
            self.entry_side,
            self.entry_height,
            self.entry_weight,
            self.entry_notes,
        ]:
            entry.delete(0, "end")
    
        # If you replaced age with a label:
        if hasattr(self, "label_age"):
            self.label_age.config(text=Default_patient_info["age"])
    
        # --- Close preview window if open ---
        if self.plot_window is not None:
            try:
                self.plot_window.destroy()
            except:
                pass
            self.plot_window = None
    
        # --- Reset plot manager or other helper classes ---
        if hasattr(self, "plot_manager"):
            self.plot_manager.reset()  # only if you have a reset() method
    
        # --- Update preview box text ---
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("end", "All data cleared. Ready for new patient.")
    
        # --- Reset any flags ---
        self.first_preview_render = True


    def load_gcd_data(self):
        # need to use a data handler function to get data from the other class in a clean way
        # ---- call function across classes
        gcd_data, py_data = self.data_handler.getData_dialog()
    
        if gcd_data:
            # assign to self to use across the app
            self.loaded_gcd_data = gcd_data
            self.loaded_py_data  = py_data
    
            messagebox.showinfo(
                "Data Loaded",
                f"Successfully loaded {len(gcd_data)} GCD file(s).\nSuccessfully loaded {len(py_data)} static python file."
            )
    
    # --------------------------------------------------------
    #  UI
    # --------------------------------------------------------
    def create_widgets(self):
        # ---------- Patient frame ----------
        # -----------------------------------
        patient_info_frame = tk.LabelFrame(self, text='Patient Information')
        patient_info_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=5) # in row 1 column 1 in frame 1

        # Patient/session fields
        ttk.Label(patient_info_frame, text="Last Name").grid(row=0, column=0, sticky="e")
        self.entry_lastname = ttk.Entry(patient_info_frame, width=20)
        self.entry_lastname.grid(row=0, column=1, sticky="w", padx=3, pady=2)
        # self.entry_lastname.insert(0, self.patient_data["lastname"])
        self.add_placeholder(self.entry_lastname, self.patient_data["lastname"])
        
        ttk.Label(patient_info_frame, text="First Name").grid(row=0, column=2, sticky="e")
        self.entry_firstname = ttk.Entry(patient_info_frame, width=20)
        self.entry_firstname.grid(row=0, column=3, sticky="w", padx=3, pady=2)
        # self.entry_firstname.insert(0, self.patient_data["firstname"])
        self.add_placeholder(self.entry_firstname, self.patient_data["firstname"])

        ttk.Label(patient_info_frame, text="DOB").grid(row=1, column=0, sticky="e")
        self.entry_dob = ttk.Entry(patient_info_frame, width=20)
        self.entry_dob.grid(row=1, column=1, sticky="w", padx=3, pady=2)
        # self.entry_dob.insert(0, self.patient_data["dob"])
        self.add_placeholder(self.entry_dob, self.patient_data["dob"])
        
        ttk.Label(patient_info_frame, text="Age").grid(row=1, column=2, sticky="e")
        self.label_age = ttk.Label(patient_info_frame, text=str(self.patient_data["age"]))
        self.label_age.grid(row=1, column=3, sticky="w", padx=3, pady=2)

        ttk.Label(patient_info_frame, text="ID").grid(row=2, column=0, sticky="e")
        self.entry_id = ttk.Entry(patient_info_frame, width=20)
        self.entry_id.grid(row=2, column=1, sticky="w", padx=3, pady=2)
        # self.entry_id.insert(0, self.patient_data["id"])
        self.add_placeholder(self.entry_id, self.patient_data["id"])
        
        ttk.Label(patient_info_frame, text="Visit Date").grid(row=2, column=2, sticky="e")
        self.entry_visit_date = ttk.Entry(patient_info_frame, width=20)
        self.entry_visit_date.grid(row=2, column=3, sticky="w", padx=3, pady=2)
        self.entry_visit_date.insert(0, date.today())
        # self.add_placeholder(self.entry_visit_date, date.today())
        
        ttk.Label(patient_info_frame, text="**all dates in YYYY-MM-DD format**").grid(row=3, column=1, columnspan=2, sticky="e")
        
        # ---------- Clinical frame ----------
        # ------------------------------------
        clinical_info_frame = tk.LabelFrame(self, text='Clinical Information')
        clinical_info_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=5) # in row 1 column 1 in frame 1

        # left
        ttk.Label(clinical_info_frame, text="Physician").grid(row=0, column=0, sticky="e")
        self.entry_physician = ttk.Entry(clinical_info_frame, width=20)
        self.entry_physician.grid(row=0, column=1, sticky="w", padx=3, pady=2)
        # self.entry_physician.insert(0, self.patient_data["physician"])
        self.add_placeholder(self.entry_physician, self.patient_data["physician"])
        
        ttk.Label(clinical_info_frame, text="Therapist").grid(row=1, column=0, sticky="e")
        self.entry_therapist = ttk.Entry(clinical_info_frame, width=20)
        self.entry_therapist.grid(row=1, column=1, sticky="w", padx=3, pady=2)
        # self.entry_therapist.insert(0, self.patient_data["therapist"])
        self.add_placeholder(self.entry_therapist, self.patient_data["therapist"])

        ttk.Label(clinical_info_frame, text="Injury").grid(row=2, column=0, sticky="e")
        self.entry_injury = ttk.Entry(clinical_info_frame, width=20)
        self.entry_injury.grid(row=2, column=1, sticky="w", padx=3, pady=2)
        # self.entry_injury.insert(0, self.patient_data["injury"])
        self.add_placeholder(self.entry_injury, self.patient_data["injury"])
        
        # right
        ttk.Label(clinical_info_frame, text="Injury Side").grid(row=0, column=2, sticky="e")
        self.entry_side = ttk.Entry(clinical_info_frame, width=20)
        self.entry_side.grid(row=0, column=3, sticky="w", padx=3, pady=2)
        # self.entry_side.insert(0, self.patient_data["injury_side"])
        self.add_placeholder(self.entry_side, self.patient_data["injury_side"])

        ttk.Label(clinical_info_frame, text="Injury Date").grid(row=1, column=2, sticky="e")
        self.entry_injury_date = ttk.Entry(clinical_info_frame, width=20)
        self.entry_injury_date.grid(row=1, column=3, sticky="w", padx=3, pady=2)
        # self.entry_injury_date.insert(0, self.patient_data["surgery_date"])
        self.add_placeholder(self.entry_injury_date, self.patient_data["injury_date"])
        
        ttk.Label(clinical_info_frame, text="Surgery Date").grid(row=2, column=0, sticky="e")
        self.entry_surgery_date = ttk.Entry(clinical_info_frame, width=20)
        self.entry_surgery_date.grid(row=2, column=1, sticky="w", padx=3, pady=2)
        # self.entry_surgery_date.insert(0, self.patient_data["surgery_date"])
        self.add_placeholder(self.entry_surgery_date, self.patient_data["surgery_date"])

        # ---------- Navigation frame ----------
        # --------------------------------------
        navigation_frame = tk.LabelFrame(self, text='Navigation')
        navigation_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=5) # in row 1 column 1 in frame 1

        
        ttk.Button(navigation_frame, text="Update Patient Info", width=65, command=lambda: (self.update_data())).grid(row=0, column=0, pady=5, padx=5, sticky="w")
        ttk.Button(navigation_frame, text="Load GCD Data", width=65, command=lambda: (self.load_gcd_data(), self.update_data())).grid(row=0, column=1, pady=5, padx=5, sticky="w")
        ttk.Button(navigation_frame, text="Export Summary Report", width=133, command=lambda: self.call_ReportGeneratorfuncs("generate_summary")).grid(row=1, column=0, columnspan=2, ipady=10, pady=5, padx=5, sticky="w")
        ttk.Button(navigation_frame, text="Open Plot Window", width=65, command=self.open_plot_window).grid(row=2, column=0, pady=5, padx=5, sticky="w")
        ttk.Button(navigation_frame, text="Generate Full Report", width=65, command=self.export_pdf).grid(row=2, column=1, pady=5, padx=5, sticky="w")
        ttk.Button(navigation_frame, text="Save Data", width=133, command=self.save_json_html).grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky="n")
        ttk.Button(navigation_frame, text="Reset to Default", width=133, command=self.reset_app).grid(row=4, column=0, columnspan=2, pady=5, padx=5, sticky="n")
        ttk.Button(navigation_frame, text="Close App", width=133, command=self.destroy).grid(row=5, column=0, rowspan=2, columnspan=2, ipady=10, pady=5, padx=5, sticky="n")
        
        # ipadx is *internal* spacing as apposed to external with padx
        
        # # Right: preview text
        # right = ttk.Frame(self)
        # right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        # self.grid_columnconfigure(1, weight=1)
        # self.grid_rowconfigure(0, weight=1)

        # ttk.Label(right, text="Report Preview (Text)").grid(row=0, column=0, sticky="w")
        # self.preview_box = ScrolledText(right, width=70, height=30)
        # self.preview_box.grid(row=1, column=0, sticky="nsew")
        # self.refresh_preview()

    # --------------------------------------------------------
    def update_data(self):
        try:
            self.patient_data["lastname"]   = self.loaded_py_data[0]['data']['valueLastName']
            self.patient_data["firstname"]  = self.loaded_py_data[0]['data']['valueFirstName']
            self.patient_data["id"]         = self.loaded_py_data[0]['data']['valuePatientNumber']
            dob_string                      = self.loaded_py_data[0]['data']['valueDateOfBirth_Year'] + "-" + self.loaded_py_data[0]['data']['valueDateOfBirth_Month'] + "-" + self.loaded_py_data[0]['data']['valueDateOfBirth_Day']
            dob                             = datetime.strptime(dob_string, "%Y-%b-%d").strftime("%Y-%m-%d") # date string has month value as "Apr" e.g. so needs to be translated back to "YYYY-MM-DD" with all integer values
            self.patient_data["dob"]        = dob 
        except:
            self.patient_data["lastname"]   = self.entry_lastname.get()
            self.patient_data["firstname"]  = self.entry_firstname.get()
            self.patient_data["id"]         = self.entry_id.get()
            self.patient_data["dob"]        = self.entry_dob.get()
            dob                             = self.entry_dob.get()
            
        self.patient_data["physician"]      = self.entry_physician.get()
        self.patient_data["therapist"]      = self.entry_therapist.get()
        self.patient_data["injury"]         = self.entry_injury.get()
        self.patient_data["injury_date"]    = self.entry_injury_date.get()
        self.patient_data["injury_side"]    = self.entry_side.get()
        self.patient_data["surgery_date"]   = self.entry_surgery_date.get()
        visit_date                          = self.entry_visit_date.get()
        age                                 = self.data_handler.calculate_age(dob, visit_date)
        self.patient_data["age"]            = age
        # update age label on frame after age is calculated from dob
        self.label_age.config(text=str(self.patient_data["age"]))

            
        # Update last visit date
        if self.visits:
            self.visits[-1]["visit_date"]   = visit_date
        else:
            self.visits.append({
                "visit_date": self.entry_visit_date.get(),
                "dynamic_knee_valgus": {},
                "hip_knee_strategy": {}
            })
        
        # self.refresh_preview()
        messagebox.showinfo("Updated", "Patient and visit data updated.")

    # def refresh_preview(self):
    #     # self.preview_box.delete("1.0", tk.END) **removed
    #     visit_date  = self.visits[-1]["visit_date"] if self.visits else ""
    #     days_out    = self.metrics_calc.compute_days_out(visit_date, self.patient_data.get("surgery_date", ""))

    #     text = (
    #         f"Name: {self.patient_data['name']}\n"
    #         f"ID: {self.patient_data['id']}\n"
    #         f"Physician: {self.patient_data['physician']}\n"
    #         f"Injury: {self.patient_data['injury']} ({self.patient_data['injury_side']})\n"
    #         f"Age: {self.patient_data['age']}\n"
    #         f"DOB: {self.patient_data['dob']}\n"
    #         f"Therapist: {self.patient_data['therapist']}\n"
    #         f"Surgery/Injury Date: {self.patient_data['surgery_date']}\n"
    #         f"Visit Date: {visit_date}\n"
    #         f"Days Out: {days_out if days_out is not None else '-'}\n\n"
    #         f"Visits loaded: {len(self.visits)}\n"
    #         f"(Sample Knee valgus and Hip/Knee strategy data included for testing.)\n"
    #     )
    #     self.preview_box.insert(tk.END, text)

    # --------------------------------------------------------
    #  Plot Window
    # --------------------------------------------------------
    # ---- For Spencer
    def show_preview_page(self, page_number):
        """Render the selected page into the preview window as a scaled image."""
        self.current_preview_page = page_number
        
        # If window isn't ready, delay once
        if self.first_preview_render:
            self.first_preview_render = False
            self.plot_window.after(50, lambda: self.show_preview_page(page_number))
            return
    
        # Clear old content
        for widget in self.preview_canvas_frame.winfo_children():
            widget.destroy()
    
        fig = self.preview_figures[page_number]
    
        # --- Convert figure to PNG in memory ---
        import io
        from PIL import Image, ImageTk
    
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
    
        img = Image.open(buf)
    
        # --- Determine available space in the preview window ---
        self.plot_window.update_idletasks()
        frame_w = self.preview_canvas_frame.winfo_width()
        frame_h = self.preview_canvas_frame.winfo_height()
    
        if frame_w < 50 or frame_h < 50:
            # Window not fully drawn yet; use defaults
            frame_w, frame_h = 850, 1100
    
        # --- Scale image to fit while preserving aspect ratio ---
        img_ratio = img.width / img.height
        frame_ratio = frame_w / frame_h
    
        if img_ratio > frame_ratio:
            # Fit to width
            new_w = frame_w
            new_h = int(frame_w / img_ratio)
        else:
            # Fit to height
            new_h = frame_h
            new_w = int(frame_h * img_ratio)
    
        img = img.resize((new_w, new_h), Image.LANCZOS)
    
        # --- Convert to Tkinter image ---
        tk_img = ImageTk.PhotoImage(img)
    
        # Keep reference so it doesn't get garbage-collected
        self.current_preview_image = tk_img
    
        # --- Display ---
        # label = tk.Label(self.preview_canvas_frame, image=tk_img, bg="white")
        # label.pack(fill="both", expand=True)
        # --- Create a bordered frame for the preview ---
        border_frame = tk.Frame(
            self.preview_canvas_frame,
            bg="#444444",       # dark gray border color
            highlightthickness=0,
            padx=5, pady=5    # padding between border and image
        )
        border_frame.pack(fill="both", expand=True)
        
        inner_frame = tk.Frame(
            border_frame,
            bg="white",
            bd=2,
            relief="solid"      # gives a clean rectangular border
        )
        inner_frame.pack(expand=True)
        
        # --- Display the scaled image inside the inner frame ---
        label = tk.Label(inner_frame, image=tk_img, bg="white")
        label.pack()


    def show_next_page(self):
        if self.current_preview_page < 3:
            self.show_preview_page(self.current_preview_page + 1)


    def show_previous_page(self):
        if self.current_preview_page > 1:
            self.show_preview_page(self.current_preview_page - 1)

    # ---- For Spencer
    def generate_preview_pages(self):
        """Generate matplotlib figures for all 3 pages."""
    
        # PAGE 1 — Summary page (simple text figure)
        fig1 = Figure(figsize=(8.5, 11))
        ax1 = fig1.add_subplot(111)
        ax1.axis("off")
    
        visit_date = self.visits[-1]["visit_date"]
        days_out = self.metrics_calc.compute_days_out(
            visit_date, self.patient_data.get("surgery_date", "")
        )
    
        text = (
            f"Patient Summary\n\n"
            f"Name: {self.patient_data['name']}\n"
            f"ID: {self.patient_data['id']}\n"
            f"Physician: {self.patient_data['physician']}\n"
            f"Injury: {self.patient_data['injury']} ({self.patient_data['injury_side']})\n"
            f"Age: {self.patient_data['age']}\n"
            f"DOB: {self.patient_data['dob']}\n"
            f"Therapist: {self.patient_data['therapist']}\n"
            f"Surgery/Injury Date: {self.patient_data['surgery_date']}\n"
            f"Visit Date: {visit_date}\n"
            f"Days Out: {days_out}\n\n"
            f"Summary of Movements:\n"
            f"Walk, Drop Jump, Heel Touch (reserved)\n"
        )
    
        ax1.text(0.05, 0.95, text, va="top", fontsize=12)
        self.preview_figures[1] = fig1
    
        # PAGE 2 — DKV plots
        self.preview_figures[2] = self.plot_manager.dkv_errbar_figure(self.visits)
    
        # PAGE 3 — Hip vs Knee plots
        self.preview_figures[3] = self.plot_manager.hks_errbar_figure(self.visits)

    def open_plot_window(self):
        # If already open, bring to front
        if self.plot_window and tk.Toplevel.winfo_exists(self.plot_window):
            self.plot_window.lift()
            return
    
        # --- Create window ---
        self.plot_window = tk.Toplevel(self)
        self.plot_window.title("Report Preview")
        
        # Match PDF page size (8.5x11 inches)
        scrn_ratio = 80 # adjusts scale for the screen only
        page_w = int(8.5 * scrn_ratio)
        page_h = int(10.5 * scrn_ratio)
        self.plot_window.geometry(f"{page_w}x{page_h+60}")  # +60 for buttons
    
        # --- Button bar ---
        btn_frame = ttk.Frame(self.plot_window)
        btn_frame.pack(side="top", fill="x")
    
        ttk.Button(btn_frame, text="Previous Page",
                   command=self.show_previous_page).pack(side="left", padx=5)
    
        ttk.Button(btn_frame, text="Next Page",
                   command=self.show_next_page).pack(side="left", padx=5)
    
        ttk.Button(btn_frame, text="Close Preview",
                   command=self.plot_window.destroy).pack(side="right", padx=5)
    
        # --- Canvas area for figure ---
        self.preview_canvas_frame = ttk.Frame(self.plot_window)
        self.preview_canvas_frame.pack(fill="both", expand=True)
    
        # Pre-generate all 3 pages
        self.generate_preview_pages()
    
        # Delay initial render so the window can compute its real size
        # self.plot_window.after(50, lambda: self.show_preview_page(1))
        self.show_preview_page(1)

    # --------------------------------------------------------
    #  Export PDF
    # --------------------------------------------------------
    def export_pdf(self):
        self.update_data()
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not filename:
            return

        try:
            self.report_generator.generate_pdf(filename, self.patient_data, self.visits)
            messagebox.showinfo("PDF Export", f"PDF saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")

    # --------------------------------------------------------
    #  Save JSON + HTML
    # --------------------------------------------------------
    def save_json_html(self):
        self.update_data()
        data = self.data_formatter.format_data(self.patient_data, self.visits)

        base = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if not base:
            return

        json_path = base
        html_path = os.path.splitext(base)[0] + ".html"

        try:
            self.data_formatter.save_to_json(data, json_path)
            self.data_formatter.save_to_html(self.patient_data, self.visits, html_path)
            messagebox.showinfo("Saved", f"JSON: {json_path}\nHTML: {html_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON/HTML:\n{e}")


# ============================================================
#  Run
# ============================================================
if __name__ == "__main__":
    app = PatientReportApp()
    app.mainloop()