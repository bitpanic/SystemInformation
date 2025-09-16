"""PDF report exporter for System Information Collector."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


class PDFExporter:
    """Generates a styled PDF report summarizing key system information."""

    def __init__(self, logger=None):
        self.logger = logger
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            name="TitleStyle",
            parent=self.styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=12,
        )
        self.section_style = ParagraphStyle(
            name="SectionStyle",
            parent=self.styles["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
        )
        self.normal_style = self.styles["BodyText"]
        self.small_style = ParagraphStyle(
            name="Small",
            parent=self.styles["BodyText"],
            fontSize=9,
            leading=11,
        )
        # Default caps to keep report concise
        self.max_software_rows = None  # show all installed programs
        self.max_pci_rows = 25
        self.max_usb_rows = 20

    def generate_report(self, data: Dict[str, Any], output_filename: str) -> str:
        """Create the PDF report.

        Focus per user:
        - Overview-like summary
        - USB: what's connected (concise)
        - RAM: module count, size, speed
        - Storage: list all disks
        - Dell service tag
        """
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
        )

        story: List[Any] = []

        # Title
        title = "System Information Report"
        story.append(Paragraph(title, self.title_style))
        subtitle = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(subtitle, self.small_style))
        story.append(Spacer(1, 8))

        # Overview section
        story.append(Paragraph("Overview", self.section_style))
        overview_rows = []
        collection_ts = data.get("collection_timestamp", "Unknown")
        overview_rows.append(["Collection Time", collection_ts])

        # CPU, OS, GPU, RAM total
        cpu = data.get("system", {}).get("cpu_info", {})
        os_info = data.get("operating_system", {}).get("os_info", {})
        gpu_list = data.get("system", {}).get("gpu_info", [])
        memory = data.get("memory", {})
        dell = data.get("system", {}).get("dell_info", {})

        overview_rows.append(["CPU", cpu.get("name", "Unknown")])
        if gpu_list:
            overview_rows.append(["Primary GPU", gpu_list[0].get("name", "Unknown")])
        windows_version = f"{os_info.get('name', 'Unknown')} {os_info.get('version', '')} (Build {os_info.get('build_number', 'Unknown')})"
        overview_rows.append(["Windows Version", windows_version])
        if memory:
            overview_rows.append(["Total RAM", f"{memory.get('total_ram_gb', 0)} GB"]) 
            overview_rows.append(["Memory Modules", str(memory.get("total_modules", 0))])

        if dell:
            overview_rows.append(["Manufacturer", dell.get("manufacturer", "Unknown")])
            overview_rows.append(["Model", dell.get("model", "Unknown")])
            overview_rows.append(["Dell Service Tag", dell.get("service_tag", "Unknown")])

        overview_table = self._make_kv_table(overview_rows)
        story.append(overview_table)

        # USB section (concise): name, class, vendor:product, serial
        story.append(Paragraph("USB Devices (Connected)", self.section_style))
        usb = data.get("usb", {})
        usb_devices = usb.get("usb_devices", [])
        usb_table_data = [["Name", "Class", "VID:PID", "Serial"]]
        for d in usb_devices[: self.max_usb_rows]:
            vid = d.get("vendor_id", "??")
            pid = d.get("product_id", "??")
            usb_table_data.append([
                d.get("device_name", "Unknown"),
                d.get("usb_class", "Unknown"),
                f"{vid}:{pid}",
                d.get("serial_number", ""),
            ])
        story.append(self._make_table(usb_table_data))
        self._maybe_note_truncation(story, len(usb_devices), len(usb_table_data) - 1, "USB devices")

        # RAM section: per-module locator, size, speed
        story.append(Paragraph("Memory Modules", self.section_style))
        modules = memory.get("memory_modules", [])
        ram_table_data = [["Slot", "Size (GB)", "Speed (MHz)", "Type"]]
        for m in modules:
            ram_table_data.append([
                m.get("device_locator", "Unknown"),
                m.get("capacity_gb", "0"),
                m.get("speed_mhz", "Unknown"),
                m.get("memory_type", "Unknown"),
            ])
        story.append(self._make_table(ram_table_data))

        # Storage section: list all disks
        story.append(Paragraph("Storage Devices", self.section_style))
        storage = data.get("storage", {})
        disks = storage.get("storage_devices", [])
        storage_table_data = [["Model", "Type", "Size (GB)", "Serial", "Interface"]]
        for s in disks:
            storage_table_data.append([
                s.get("model", "Unknown"),
                s.get("drive_type", s.get("media_type", "Unknown")),
                s.get("size_gb", 0),
                s.get("serial_number", "Unknown"),
                s.get("interface_type", "Unknown"),
            ])
        story.append(self._make_table(storage_table_data))

        # PCI devices: name and manufacturer
        pci = data.get("pci", {})
        pci_devices = pci.get("pci_devices", [])
        story.append(Paragraph("PCI Devices", self.section_style))
        pci_table_data = [["Device Name", "Manufacturer"]]
        for p in pci_devices[: self.max_pci_rows]:
            pci_table_data.append([
                p.get("device_name", "Unknown"),
                p.get("manufacturer", "Unknown"),
            ])
        story.append(self._make_table(pci_table_data))
        self._maybe_note_truncation(story, len(pci_devices), len(pci_table_data) - 1, "PCI devices")

        # SPIN version and CodeMeter dongles
        story.append(Paragraph("Software Highlights", self.section_style))
        spin = data.get("software", {}).get("spin_info", {})
        spin_rows = [["SPIN Installed", str(spin.get("installed", False))],
                     ["SPIN Version", spin.get("version", "Not found")],
                     ["SPIN License", spin.get("license_number", "Not found")],
                     ["SPIN Path", spin.get("install_path", "Not found")]]
        story.append(self._make_kv_table(spin_rows))

        story.append(Paragraph("CodeMeter Dongles", self.section_style))
        dongles = data.get("software", {}).get("codemeter_dongles", {})
        dongle_list = dongles.get("dongles", [])
        dongle_table = [["Name", "Serial", "Version", "Status", "Source"]]
        for d in dongle_list:
            dongle_table.append([
                d.get("device_name", "CodeMeter Dongle"),
                d.get("serial_number", "Unknown"),
                d.get("version", ""),
                d.get("status", ""),
                d.get("source", "")
            ])
        if len(dongle_table) == 1:
            dongle_table.append(["None detected", "-", "-", "-", "-"])
        story.append(self._make_table(dongle_table))

        # Short software list (filtered non-Microsoft)
        story.append(Paragraph("Installed Software (Filtered)", self.section_style))
        sw_section = data.get("software", {})
        programs = sw_section.get("installed_programs_filtered")
        if not programs:
            # Fallback: lightly filter the raw list if filtered list is empty/unavailable
            raw_programs = sw_section.get("installed_programs", []) or []
            programs = self._fallback_filter_programs(raw_programs)
        sw_table = [["Name", "Version", "Publisher"]]
        programs_to_show = programs if self.max_software_rows is None else programs[: self.max_software_rows]
        for prog in programs_to_show:
            sw_table.append([
                prog.get("name", prog.get("display_name", "Unknown")),
                prog.get("version", prog.get("displayversion", "")),
                prog.get("publisher", "")
            ])
        story.append(self._make_table(sw_table))
        if self.max_software_rows is not None:
            self._maybe_note_truncation(story, len(programs), len(sw_table) - 1, "installed programs")

        # Build document
        doc.build(story)
        if self.logger:
            self.logger.log_info(f"PDF report generated: {output_filename}")
        return output_filename

    def _make_kv_table(self, rows: List[List[Any]]):
        table = Table(rows, hAlign="LEFT", colWidths=[45 * mm, None])
        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
        table.setStyle(style)
        return table

    def _make_table(self, data: List[List[Any]]):
        table = Table(data, hAlign="LEFT")
        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fbff")]),
        ])
        table.setStyle(style)
        return table

    def _fallback_filter_programs(self, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            result: List[Dict[str, Any]] = []
            if not programs:
                return result
            exclude_tokens = [
                "security update", "update", "hotfix", "servicing stack", "cumulative update", "feature update", "kb"
            ]
            for p in programs:
                name = (p.get("name") or p.get("display_name") or "").strip()
                if not name:
                    continue
                lname = name.lower()
                if any(tok in lname for tok in exclude_tokens):
                    continue
                # Prefer non-Microsoft, but keep some if list would be empty
                publisher = (p.get("publisher") or "").lower()
                if "microsoft" in publisher and len(result) > 0:
                    continue
                result.append({
                    "name": name,
                    "version": p.get("version") or p.get("displayversion") or "",
                    "publisher": p.get("publisher") or ""
                })
            # Sort and cap
            result.sort(key=lambda x: (x.get("name") or "", x.get("version") or ""))
            return result[:40]
        except Exception:
            return []

    def _maybe_note_truncation(self, story: List[Any], total: int, shown: int, label: str) -> None:
        try:
            if total > shown and shown > 0:
                story.append(Spacer(1, 2))
                story.append(Paragraph(f"Showing first {shown} of {total} {label}.", self.small_style))
                story.append(Spacer(1, 6))
        except Exception:
            pass


