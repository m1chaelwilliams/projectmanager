import customtkinter as tk
from tkinter import filedialog
import json
import subprocess
import os

PROJECTDATAPATH = "data/projects.json"
ACTIONDATAPATH = "data/actions.json"
SETTINGSDATAPATH = "data/settings.json"

def load_app_settings() -> dict:
	with open(SETTINGSDATAPATH, 'r') as f:
		return json.load(f)

def load_project_data() -> dict[str, dict[str, str]]:
	with open(PROJECTDATAPATH, 'r') as f:
		return json.load(f)
	
def save_project_data(data) -> None:
	with open(PROJECTDATAPATH, 'w') as f:
		json.dump(data, f)
	
def load_action_data() -> dict[str, str]:
	with open(ACTIONDATAPATH, 'r') as f:
		return json.load(f)

class App(tk.CTk):
	def __init__(self):
		super().__init__()
	def setup(self):
		# setup app settings
		settings: dict = load_app_settings()
		width, height = settings["dimensions"]

		self.title(settings["title"])
		self.geometry(f"{width}x{height}")

		# configure app grid
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=0)
		self.grid_columnconfigure(1, weight=1)

		# setup page dict
		self.pages: dict[str, tk.CTkFrame] = {}
		self.projects: dict[str, tk.CTkFrame] = {}

		# create project page
		self.project_page = tk.CTkScrollableFrame(self)
		self.project_page.grid_columnconfigure(0, weight=1)
		self.project_page.grid_rowconfigure(0, weight=1)
		self.project_page.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

		self.project_data_list = load_project_data()
		self.action_data_list = load_action_data()

		# add projects to project page
		for name, project_data in self.project_data_list.items():
			project = tk.CTkFrame(self.project_page)
			project.pack(padx=5, pady=5, fill="x")
			self.projects[name] = project

			# populate project
			name_label = tk.CTkLabel(project, text=name)
			name_label.pack(side="left", padx=10)

			edit_btn = tk.CTkButton(project, text="Edit", command=lambda n=name: self.open_project_in_editor(n))
			edit_btn.pack(side="right", padx=10)

			open_with_cbtn = tk.CTkComboBox(project, values=list(self.action_data_list.keys()), variable=tk.StringVar(value=project_data["action"]), command=lambda c, p=name: self.on_action_change(c,p))

			open_btn = tk.CTkButton(project, text="Open", command=lambda n=name: self.use_project_action(n))
			open_btn.pack(side="right", padx=10)
			
			open_with_cbtn.pack(side="right", padx=10)

		# create sidebar
		self.sidebar = tk.CTkFrame(self)
		self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

		# populate sidebar
		create_project_btn = tk.CTkButton(self.sidebar, text="Create Project", command=lambda: self.open_project_in_editor(""))
		create_project_btn.pack(padx=5, pady=5)

		save_btn = tk.CTkButton(self.sidebar, text="Save", command=lambda data=self.project_data_list: save_project_data(data))
		save_btn.pack(padx=5, pady=5)

		self.pages["projects"] = self.project_page

	# project page callback
	def use_project_action(self, project_name: str):
		project_data: dict[str, str] = self.project_data_list[project_name]
		action = self.action_data_list[project_data["action"]]
		path = project_data["path"]

		subprocess.run(f"{action}{os.path.normpath(path)}", shell=True)

	def open_project_in_editor(self, project_name: str):
		if project_name:
			path = self.project_data_list[project_name]["path"]
			action = self.project_data_list[project_name]["action"]
		else:
			path = action = ""

		# create edit project app
		project_editor = tk.CTkFrame(self)
		project_editor.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

		# populate project editor
		if project_name:
			editor_name_entry = tk.CTkEntry(project_editor, placeholder_text="Enter Name:", textvariable=tk.StringVar(value=project_name))
			editor_path_entry = tk.CTkEntry(project_editor, placeholder_text="Enter Path:", textvariable=tk.StringVar(value=path))
			editor_action_cbtn = tk.CTkComboBox(project_editor, values=list(self.action_data_list.keys()), variable=tk.StringVar(value=action))
		else:
			editor_name_entry = tk.CTkEntry(project_editor, placeholder_text="Enter Name:")
			editor_path_entry = tk.CTkEntry(project_editor, placeholder_text="Enter Path:")
			editor_action_cbtn = tk.CTkComboBox(project_editor, values=list(self.action_data_list.keys()))

		editor_locate_btn = tk.CTkButton(project_editor, text="Locate", command=lambda entry=editor_path_entry: self.ask_directory(entry))

		editor_name_entry.pack(pady=5, padx=5, fill="x")
		editor_path_entry.pack(pady=5, padx=5, fill="x")
		editor_locate_btn.pack(pady=5, padx=5, fill="x")
		editor_action_cbtn.pack(pady=5, padx=5, fill="x")

		editor_btn_group = tk.CTkFrame(project_editor)
		editor_btn_group.pack(pady=5)

		def save_button_click():
			n = editor_name_entry.get()
			p = editor_path_entry.get()
			a = editor_action_cbtn.get()
			self.publish_project(project_name, n, p, a, project_name)

		editor_save_btn = tk.CTkButton(editor_btn_group, text="Save", command=save_button_click)
		editor_save_btn.pack(pady=5, padx=5, fill="x", side="left")

		if project_name:
			editor_remove_btn = tk.CTkButton(editor_btn_group, text="Remove", command=lambda: self.prompt_remove_project(project_name))
			editor_remove_btn.pack(pady=5, padx=5, fill="x", side="left")

		editor_cancel_btn = tk.CTkButton(editor_btn_group, text="Cancel", command=lambda: project_editor.destroy())
		editor_cancel_btn.pack(pady=5, padx=5, side="left")

	def on_action_change(self, choice: str, project_name: str):
		project_data = self.project_data_list[project_name]
		project_data["action"] = choice

	def publish_project(self, previous_name: str, project_name: str, path: str, action: str, project_exists: bool):
		self.project_data_list[project_name] = {"path":path, "action":action}

		project_frame = None

		if project_exists:
			self.projects[project_name] = self.projects.pop(previous_name, None)
			self.project_data_list[project_name] = self.project_data_list.pop(previous_name, None)

			project_frame = self.projects[project_name]

			for child in project_frame.winfo_children():
				child.destroy()
		else:
			project_frame = tk.CTkFrame(self.project_page)
			project_frame.pack(padx=5, pady=5, fill="x")

			self.projects[project_name] = project_frame

		name_label = tk.CTkLabel(project_frame, text=project_name)
		name_label.pack(side="left", padx=10)

		edit_btn = tk.CTkButton(project_frame, text="Edit", command=lambda n=project_name: self.open_project_in_editor(n))
		edit_btn.pack(side="right", padx=10)

		open_with_cbtn = tk.CTkComboBox(project_frame, values=list(self.action_data_list.keys()), variable=tk.StringVar(value=action), command=lambda c, p=project_name: self.on_action_change(c,p))

		open_btn = tk.CTkButton(project_frame, text="Open", command=lambda n=project_name: self.use_project_action(n))
		open_btn.pack(side="right", padx=10)
		
		open_with_cbtn.pack(side="right", padx=10)

		self.raise_page("projects")

	def prompt_remove_project(self, name: str):
		popup = tk.CTkFrame(self)
		popup.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

		warning_label = tk.CTkLabel(popup, text=f"Removing: {name}")
		warning_label.pack(pady=5)

		yes_btn = tk.CTkButton(popup, text="Delete", command=lambda: self.remove_project(name))
		yes_btn.pack(pady=5)

		no_btn = tk.CTkButton(popup, text="Cancel", command=popup.destroy)
		no_btn.pack(pady=5)

	def remove_project(self, name: str):
		self.projects[name].destroy()
		self.projects.pop(name)
		self.project_data_list.pop(name)
		self.raise_page("projects")

	# app utils
	def raise_page(self, page_name: str):
		self.pages[page_name].lift()

	def ask_directory(self, entry: tk.CTkEntry) -> None:
		dir = filedialog.askdirectory()
		if dir:
			entry.configure(textvariable = tk.StringVar(value=dir))

	def run(self):
		self.raise_page("projects")
		self.mainloop()