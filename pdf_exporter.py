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
        self.max_pci_rows = None  # show all PCI devices
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

        # Add computer name
        comp = data.get("operating_system", {}).get("computer_info", {})
        env = data.get("operating_system", {}).get("environment_info", {})
        computer_name = comp.get("computer_name") or env.get("hostname") or "Unknown"
        overview_rows.append(["Computer Name", computer_name])

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

        # Network Interfaces section (Interface, IPs, Subnets only)
        story.append(Paragraph("Network Interfaces", self.section_style))
        net = data.get("network", {})
        nics = net.get("network_interfaces", [])
        net_table = [["Interface", "IP(s)", "Subnet(s)"]]
        for n in nics:
            ips = ", ".join(n.get("ip_addresses", []) or [])
            subs = ", ".join(n.get("subnet_masks", []) or [])
            net_table.append([
                Paragraph(n.get("interface_name", "Unknown"), self.small_style),
                Paragraph(ips or "", self.small_style),
                Paragraph(subs or "", self.small_style),
            ])
        if len(net_table) == 1:
            net_table.append(["None detected", "-", "-"])
        story.append(self._make_table(net_table, col_widths=[60 * mm, 74 * mm, 40 * mm]))

        # Network Scan section (with Serial if available)
        scan = net.get("network_scan", {})
        hosts = scan.get("hosts", [])
        story.append(Paragraph("Network Scan (172.22.10.1-172.22.10.255)", self.section_style))
        has_serial = any(h.get("serial") for h in hosts)
        scan_table = [["IP Address", "Hostname"] + (["Serial"] if has_serial else [])]
        for h in hosts:
            row = [h.get("ip", ""), h.get("hostname", "")]
            if has_serial:
                row.append(h.get("serial", ""))
            scan_table.append(row)
        if len(scan_table) == 1:
            scan_table.append(["No hosts found", "-"] + (["-"] if has_serial else []))
        story.append(self._make_table(scan_table, col_widths=[50 * mm, None] + ([45 * mm] if has_serial else [])))

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

        # PCI devices: list all, filter out standard/system devices; include Serial
        pci = data.get("pci", {})
        pci_devices = pci.get("pci_devices", [])
        filtered_pci = self._filter_pci_devices(pci_devices)
        story.append(Paragraph("PCI Devices", self.section_style))
        pci_table_data = [["Device Name", "Manufacturer", "Serial"]]
        for p in filtered_pci[: self.max_pci_rows]:
            pci_table_data.append([
                p.get("device_name", "Unknown"),
                p.get("manufacturer", "Unknown"),
                p.get("serial_number", ""),
            ])
        if len(pci_table_data) == 1:
            pci_table_data.append(["None detected", "-", "-"])
        story.append(self._make_table(pci_table_data))
        self._maybe_note_truncation(story, len(filtered_pci), len(pci_table_data) - 1, "PCI devices")

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

    def _make_table(self, data: List[List[Any]], col_widths: Optional[List[Any]] = None):
        table = Table(data, hAlign="LEFT", colWidths=col_widths)
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

    def _filter_pci_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            if not devices:
                return []
            excluded_name_tokens = [
                "motherboard resources",
                "system timer",
                "numeric data processor",
                "programmable interrupt controller",
                "direct memory access controller",
                "high precision event timer",
                "pci-to-pci bridge",
                "pci express root port",
                "root port",
                "root complex",
                "bus enumerator",
                "composite bus enumerator",
                "acpi",
                "standard sata ahci controller",
                "standard nvm express controller",
                "standard pci-to-pci bridge",
                "pci express downstream switch port",
                "pci express upstream switch port",
                "downstream switch port",
                "upstream switch port",
                "standard isa bridge",
                "standard host cpu bridge",
                # AMD generic/controller tokens from user feedback
                "usb 3.10 extensible host controller",
                "xhci host controller",
                "generic usb xhci host controller",
                "platform security processor",
                "psp",
                "smbus",
                "amd-raid",
                "raid bottom device",
                "raid controller",
                "amd raid",
                "amd pci",
            ]
            def is_standard(d: Dict[str, Any]) -> bool:
                name = (d.get("device_name") or "").lower()
                friendly = (d.get("friendly_name") or "").lower()
                manufacturer = (d.get("manufacturer") or "").lower()
                service = (d.get("service") or "").lower()
                combined = " ".join([name, friendly, service])
                if "microsoft" in manufacturer and ("standard" in name or any(tok in combined for tok in excluded_name_tokens)):
                    return True
                if any(tok in combined for tok in excluded_name_tokens):
                    return True
                if name.strip() in {"pci device"}:
                    return True
                # Extra guard: extremely short generic AMD entries
                if manufacturer.startswith("advanced micro devices") and name in {"amd pci", "amd psp", "amd smbus"}:
                    return True
                return False
            filtered = [d for d in devices if not is_standard(d)]
            try:
                filtered.sort(key=lambda x: (x.get("manufacturer") or "", x.get("device_name") or ""))
            except Exception:
                pass
            return filtered
        except Exception:
            return devices or []


