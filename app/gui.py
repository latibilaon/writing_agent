from __future__ import annotations

import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from . import paths
from .logging_utils import QueueLogger
from .openrouter_client import OpenRouterClient
from .pipelines.lease_direct import LeaseDirectRequest, run_lease_direct_pipeline
from .pipelines.lease_template import LeaseTemplateRequest, run_lease_template_pipeline
from .pipelines.offer import OfferRequest, run_offer_pipeline
from .settings import AppSettings


C = {
    "bg": "#F5F2EC",
    "card": "#FFFCF7",
    "accent": "#163A5F",
    "acc_dk": "#0F2A45",
    "text": "#1F2329",
    "sub": "#5D6572",
    "border": "#D9D1C5",
    "ok": "#1E9E64",
    "err": "#CC3A2B",
    "warn": "#C98512",
    "logbg": "#12161C",
    "logfg": "#E9E3D8",
    "field": "#F7F1E7",
}

F = {
    "body": ("Avenir Next", 12),
    "title": ("Avenir Next", 16, "bold"),
    "mono": ("SF Mono", 11),
}


class PortableApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Uoffer Portable Application")
        self.root.geometry("1220x860")
        self.root.minsize(1060, 760)
        self.root.configure(bg=C["bg"])

        self.settings = AppSettings.load()
        data_root = Path(self.settings.data_root).expanduser() if self.settings.data_root else None
        self.dirs = paths.ensure_dirs(data_root)

        self._q = queue.Queue()
        self._running = False
        self._last_output = None

        self._build_ui()
        self._poll_log()

    # ---------- UI ----------
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=C["accent"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Uoffer Portable Application", font=F["title"], bg=C["accent"], fg="white").pack(anchor="w", padx=20, pady=14)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        left = tk.Frame(body, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.nb = ttk.Notebook(left)
        self.nb.pack(fill="both", expand=True)

        self.offer_tab = tk.Frame(self.nb, bg=C["card"])
        self.lease_direct_tab = tk.Frame(self.nb, bg=C["card"])
        self.lease_template_tab = tk.Frame(self.nb, bg=C["card"])
        self.settings_tab = tk.Frame(self.nb, bg=C["card"])

        self.nb.add(self.offer_tab, text="Offer Appeal")
        self.nb.add(self.lease_direct_tab, text="Lease Direct")
        self.nb.add(self.lease_template_tab, text="Lease Template")
        self.nb.add(self.settings_tab, text="Settings")

        self._build_offer_tab()
        self._build_lease_direct_tab()
        self._build_lease_template_tab()
        self._build_settings_tab()

        right = tk.Frame(body, bg=C["card"], highlightthickness=1, highlightbackground=C["border"], width=410)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        tk.Label(right, text="Live Log", font=("Avenir Next", 14, "bold"), bg=C["card"], fg=C["text"]).pack(anchor="w", padx=14, pady=(12, 8))

        self.log = scrolledtext.ScrolledText(right, font=F["mono"], bg=C["logbg"], fg=C["logfg"], relief="flat", state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log.tag_config("ok", foreground="#30D158")
        self.log.tag_config("err", foreground="#FF453A")
        self.log.tag_config("warn", foreground="#FFD60A")
        self.log.tag_config("head", foreground="#64D2FF")
        self.log.tag_config("info", foreground="#E9E3D8")

        ftr = tk.Frame(self.root, bg=C["card"], highlightthickness=1, highlightbackground=C["border"])
        ftr.pack(fill="x")
        self.status = tk.Label(ftr, text="Ready", bg=C["card"], fg=C["sub"], font=F["body"])
        self.status.pack(side="left", padx=16, pady=10)
        tk.Button(ftr, text="Open Last Output", command=self._open_last, bg=C["field"], relief="flat").pack(side="right", padx=8, pady=8)
        tk.Button(ftr, text="Clear Log", command=self._clear_log, bg=C["field"], relief="flat").pack(side="right", padx=8, pady=8)

    def _mk_entry(self, parent, label, default="", width=70):
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", padx=14, pady=5)
        tk.Label(row, text=label, width=24, anchor="w", bg=C["card"], fg=C["text"], font=F["body"]).pack(side="left")
        e = tk.Entry(row, width=width, bg=C["field"], relief="flat", font=F["body"])
        e.pack(side="left", fill="x", expand=True)
        if default:
            e.insert(0, default)
        return e

    def _mk_text(self, parent, label, h=4, default=""):
        box = tk.Frame(parent, bg=C["card"])
        box.pack(fill="x", padx=14, pady=5)
        tk.Label(box, text=label, anchor="w", bg=C["card"], fg=C["text"], font=F["body"]).pack(anchor="w")
        t = tk.Text(box, height=h, bg=C["field"], relief="flat", font=F["body"], wrap="word")
        t.pack(fill="x", expand=True)
        if default:
            t.insert("1.0", default)
        return t

    def _mk_path_selector(self, parent, label, default_path: Path):
        var = tk.StringVar(value=str(default_path))
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", padx=14, pady=5)
        tk.Label(row, text=label, width=24, anchor="w", bg=C["card"], fg=C["text"], font=F["body"]).pack(side="left")
        e = tk.Entry(row, textvariable=var, bg=C["field"], relief="flat", font=F["body"])
        e.pack(side="left", fill="x", expand=True)

        def pick():
            p = filedialog.askdirectory(initialdir=str(default_path))
            if p:
                var.set(p)

        tk.Button(row, text="Browse", command=pick, bg=C["accent"], fg="white", relief="flat").pack(side="left", padx=6)
        return var

    # ---------- tabs ----------
    def _build_offer_tab(self):
        self.offer_school = self._mk_entry(self.offer_tab, "Target School")
        self.offer_request = self._mk_text(self.offer_tab, "Requested Revision", h=4)
        self.offer_prof_url = self._mk_entry(self.offer_tab, "Professor URL", default="")
        self.offer_program_url = self._mk_entry(self.offer_tab, "Program URL", default="")
        self.offer_program = self._mk_entry(self.offer_tab, "Program (optional)")
        self.offer_student = self._mk_entry(self.offer_tab, "Student Name Override")
        self.offer_extra = self._mk_text(self.offer_tab, "Extra Instructions", h=3, default="Keep academic style; avoid generic AI wording.")

        self.offer_materials = self._mk_path_selector(self.offer_tab, "Materials Folder", self.dirs["materials"])
        self.offer_output = self._mk_path_selector(self.offer_tab, "Output Folder", self.dirs["output"])

        self.offer_model = self._mk_entry(self.offer_tab, "Model", default=self.settings.default_model)
        self.offer_word_min = self._mk_entry(self.offer_tab, "Word Min", default=str(self.settings.default_word_min), width=12)
        self.offer_word_max = self._mk_entry(self.offer_tab, "Word Max", default=str(self.settings.default_word_max), width=12)

        self.offer_skip = tk.BooleanVar(value=False)
        tk.Checkbutton(self.offer_tab, text="Skip conversion", variable=self.offer_skip, bg=C["card"]).pack(anchor="w", padx=14, pady=6)
        tk.Button(self.offer_tab, text="Generate Offer Appeal", command=self._run_offer, bg=C["accent"], fg="white", relief="flat").pack(anchor="e", padx=14, pady=10)

    def _build_lease_direct_tab(self):
        self.ld_name = self._mk_entry(self.lease_direct_tab, "Tenant Name")
        self.ld_address = self._mk_entry(self.lease_direct_tab, "Property Address")
        self.ld_deadline = self._mk_entry(self.lease_direct_tab, "Termination Deadline", default="immediately")
        self.ld_refund = self._mk_entry(self.lease_direct_tab, "Refund Amount")
        self.ld_jur = self._mk_entry(self.lease_direct_tab, "Jurisdiction", default="local")
        self.ld_issues = self._mk_text(self.lease_direct_tab, "Issues", h=5)
        self.ld_health = self._mk_text(self.lease_direct_tab, "Health Context", h=3)
        self.ld_demands = self._mk_text(self.lease_direct_tab, "Demands", h=3)
        self.ld_materials = self._mk_path_selector(self.lease_direct_tab, "Contract Materials", self.dirs["contracts"])
        self.ld_output = self._mk_path_selector(self.lease_direct_tab, "Output Folder", self.dirs["output"])
        self.ld_model = self._mk_entry(self.lease_direct_tab, "Model", default=self.settings.default_model)
        self.ld_skip = tk.BooleanVar(value=False)
        tk.Checkbutton(self.lease_direct_tab, text="Skip conversion", variable=self.ld_skip, bg=C["card"]).pack(anchor="w", padx=14, pady=6)
        tk.Button(self.lease_direct_tab, text="Generate Lease Direct", command=self._run_lease_direct, bg=C["accent"], fg="white", relief="flat").pack(anchor="e", padx=14, pady=10)

    def _build_lease_template_tab(self):
        self.lt_name = self._mk_entry(self.lease_template_tab, "Tenant Name")
        self.lt_address = self._mk_entry(self.lease_template_tab, "Property Address")
        self.lt_jur = self._mk_entry(self.lease_template_tab, "Jurisdiction", default="local")
        self.lt_issues = self._mk_text(self.lease_template_tab, "Issues", h=4)
        self.lt_demands = self._mk_text(self.lease_template_tab, "Demands", h=3)

        self.lt_materials = self._mk_path_selector(self.lease_template_tab, "Contract Materials", self.dirs["contracts"])
        self.lt_output = self._mk_path_selector(self.lease_template_tab, "Output Folder", self.dirs["output"])

        # template file selector
        row = tk.Frame(self.lease_template_tab, bg=C["card"])
        row.pack(fill="x", padx=14, pady=5)
        tk.Label(row, text="Template DOCX", width=24, anchor="w", bg=C["card"], fg=C["text"], font=F["body"]).pack(side="left")
        self.lt_template_var = tk.StringVar(value=str(self.dirs["templates"]))
        tk.Entry(row, textvariable=self.lt_template_var, bg=C["field"], relief="flat", font=F["body"]).pack(side="left", fill="x", expand=True)

        def pick_template():
            p = filedialog.askopenfilename(filetypes=[("Word", "*.docx"), ("All", "*.*")], initialdir=str(self.dirs["templates"]))
            if p:
                self.lt_template_var.set(p)

        tk.Button(row, text="Browse", command=pick_template, bg=C["accent"], fg="white", relief="flat").pack(side="left", padx=6)

        self.lt_model = self._mk_entry(self.lease_template_tab, "Model", default=self.settings.default_model)
        self.lt_skip = tk.BooleanVar(value=False)
        tk.Checkbutton(self.lease_template_tab, text="Skip conversion", variable=self.lt_skip, bg=C["card"]).pack(anchor="w", padx=14, pady=6)
        tk.Button(self.lease_template_tab, text="Generate Lease Template", command=self._run_lease_template, bg=C["accent"], fg="white", relief="flat").pack(anchor="e", padx=14, pady=10)

    def _build_settings_tab(self):
        self.st_key = self._mk_entry(self.settings_tab, "OpenRouter API Key", default=self.settings.openrouter_api_key)
        self.st_model = self._mk_entry(self.settings_tab, "Default Model", default=self.settings.default_model)
        self.st_timeout = self._mk_entry(self.settings_tab, "Timeout (sec)", default=str(self.settings.request_timeout_sec), width=12)
        self.st_retries = self._mk_entry(self.settings_tab, "Retries", default=str(self.settings.retries), width=12)
        self.st_word_min = self._mk_entry(self.settings_tab, "Default Word Min", default=str(self.settings.default_word_min), width=12)
        self.st_word_max = self._mk_entry(self.settings_tab, "Default Word Max", default=str(self.settings.default_word_max), width=12)

        self.st_data_root = self._mk_path_selector(self.settings_tab, "Data Root", Path(self.settings.data_root) if self.settings.data_root else self.dirs["root"])

        def save_settings():
            try:
                s = AppSettings(
                    openrouter_api_key=self.st_key.get().strip(),
                    default_model=self.st_model.get().strip() or "anthropic/claude-sonnet-4.6",
                    request_timeout_sec=int(self.st_timeout.get().strip() or "220"),
                    retries=int(self.st_retries.get().strip() or "1"),
                    data_root=self.st_data_root.get().strip(),
                    default_word_min=int(self.st_word_min.get().strip() or "750"),
                    default_word_max=int(self.st_word_max.get().strip() or "900"),
                )
                s.validate_word_range()
                s.save()
                self.settings = s
                self.dirs = paths.ensure_dirs(Path(s.data_root).expanduser() if s.data_root else None)
                messagebox.showinfo("Saved", "Settings saved. Restart app to refresh default paths in all tabs.")
            except Exception as exc:
                messagebox.showerror("Settings Error", str(exc))

        tk.Button(self.settings_tab, text="Save Settings", command=save_settings, bg=C["accent"], fg="white", relief="flat").pack(anchor="e", padx=14, pady=10)

    # ---------- actions ----------
    def _logger(self):
        return QueueLogger(self._emit)

    def _client(self, model: str):
        key = self.st_key.get().strip() if hasattr(self, "st_key") else self.settings.openrouter_api_key
        timeout = int(self.st_timeout.get().strip() or self.settings.request_timeout_sec)
        client = OpenRouterClient(key, timeout_sec=timeout)
        if not client.is_configured():
            raise RuntimeError("OpenRouter API key missing. Set it in Settings tab.")
        return client

    def _run_bg(self, fn):
        if self._running:
            messagebox.showwarning("Busy", "Another task is already running.")
            return

        def worker():
            self._running = True
            self._emit("[INFO] task started", "info")
            try:
                fn()
                self._emit("[OK] task completed", "ok")
                self.status.config(text="Complete")
            except Exception as exc:
                self._emit(f"[ERROR] {exc}", "err")
                self.status.config(text="Failed")
            finally:
                self._running = False

        threading.Thread(target=worker, daemon=True).start()

    def _run_offer(self):
        def task():
            school = self.offer_school.get().strip()
            request = self.offer_request.get("1.0", "end").strip()
            if not school or not request:
                raise RuntimeError("Offer tab requires school and requested revision.")
            req = OfferRequest(
                school=school,
                request=request,
                professor_url=self.offer_prof_url.get().strip(),
                program_url=self.offer_program_url.get().strip(),
                target_program=self.offer_program.get().strip(),
                student_name_override=self.offer_student.get().strip(),
                extra_instructions=self.offer_extra.get("1.0", "end").strip(),
                model=self.offer_model.get().strip() or self.settings.default_model,
                word_min=int(self.offer_word_min.get().strip() or self.settings.default_word_min),
                word_max=int(self.offer_word_max.get().strip() or self.settings.default_word_max),
                materials_dir=Path(self.offer_materials.get().strip()).expanduser(),
                converted_dir=self.dirs["converted"],
                output_dir=Path(self.offer_output.get().strip()).expanduser(),
                skip_convert=self.offer_skip.get(),
                retries=int(self.st_retries.get().strip() or self.settings.retries),
            )
            result = run_offer_pipeline(req, self._client(req.model), self._logger())
            self._last_output = result.get("docx") or result.get("markdown")

        self._run_bg(task)

    def _run_lease_direct(self):
        def task():
            req = LeaseDirectRequest(
                tenant_name=self.ld_name.get().strip(),
                property_address=self.ld_address.get().strip(),
                termination_deadline=self.ld_deadline.get().strip(),
                refund_amount=self.ld_refund.get().strip(),
                issues=self.ld_issues.get("1.0", "end").strip(),
                health_context=self.ld_health.get("1.0", "end").strip(),
                jurisdiction=self.ld_jur.get().strip() or "local",
                demands=self.ld_demands.get("1.0", "end").strip(),
                model=self.ld_model.get().strip() or self.settings.default_model,
                materials_dir=Path(self.ld_materials.get().strip()).expanduser(),
                converted_dir=self.dirs["converted"],
                output_dir=Path(self.ld_output.get().strip()).expanduser(),
                skip_convert=self.ld_skip.get(),
            )
            if not req.tenant_name or not req.issues:
                raise RuntimeError("Lease Direct requires tenant name and issues.")
            result = run_lease_direct_pipeline(req, self._client(req.model), self._logger())
            self._last_output = result.get("docx") or result.get("markdown")

        self._run_bg(task)

    def _run_lease_template(self):
        def task():
            tpath = Path(self.lt_template_var.get().strip()).expanduser()
            if not tpath.exists():
                raise RuntimeError("Template docx not found.")
            req = LeaseTemplateRequest(
                tenant_name=self.lt_name.get().strip(),
                property_address=self.lt_address.get().strip(),
                jurisdiction=self.lt_jur.get().strip() or "local",
                issues=self.lt_issues.get("1.0", "end").strip(),
                demands=self.lt_demands.get("1.0", "end").strip(),
                template_path=tpath,
                model=self.lt_model.get().strip() or self.settings.default_model,
                materials_dir=Path(self.lt_materials.get().strip()).expanduser(),
                converted_dir=self.dirs["converted"],
                output_dir=Path(self.lt_output.get().strip()).expanduser(),
                skip_convert=self.lt_skip.get(),
            )
            if not req.tenant_name or not req.issues:
                raise RuntimeError("Lease Template requires tenant name and issues.")
            result = run_lease_template_pipeline(req, self._client(req.model), self._logger())
            self._last_output = result.get("docx")

        self._run_bg(task)

    # ---------- logging ----------
    def _emit(self, msg: str, tag: str = "info"):
        self._q.put((msg, tag))

    def _poll_log(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                self.log.config(state="normal")
                self.log.insert("end", msg + "\n", tag)
                self.log.see("end")
                self.log.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(120, self._poll_log)

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _open_last(self):
        if not self._last_output:
            messagebox.showinfo("No output", "No output generated yet.")
            return
        p = Path(self._last_output)
        if not p.exists():
            messagebox.showwarning("Missing", f"Output not found: {p}")
            return
        subprocess.run(["open", str(p)])


def launch():
    root = tk.Tk()
    PortableApp(root)
    root.mainloop()
