"""Network information collector."""

from typing import Dict, Any, List, Optional, Tuple

try:
    import wmi
except Exception:  # pragma: no cover
    wmi = None  # type: ignore

import psutil
import socket
import subprocess
import errno
import re
import sys
import struct
import ipaddress
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_collector import BaseCollector


class NetworkCollector(BaseCollector):
    """Collects network interface configuration (IPs, subnets, gateways, DNS),
    and performs a lightweight scan of a fixed subnet on the local network.
    Includes FRAMOS strobe controller UDP discovery (port 30311) to retrieve
    device identification even when ICMP is disabled.
    """

    def collect(self) -> Dict[str, Any]:
        """Collect network interface information and perform subnet scan."""
        interfaces: List[Dict[str, Any]] = []
        collected = False

        # Preferred: WMI for Windows rich info
        try:
            if wmi is not None:
                c = wmi.WMI()
                for nic in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):  # type: ignore[attr-defined]
                    try:
                        iface: Dict[str, Any] = {
                            "interface_name": nic.Description or nic.Caption or "Unknown",
                            "index": int(nic.InterfaceIndex) if getattr(nic, "InterfaceIndex", None) is not None else None,
                            "mac_address": nic.MACAddress or "Unknown",
                            "dhcp_enabled": bool(nic.DHCPEnabled) if getattr(nic, "DHCPEnabled", None) is not None else None,
                            "ip_addresses": list(nic.IPAddress) if getattr(nic, "IPAddress", None) else [],
                            "subnet_masks": list(nic.IPSubnet) if getattr(nic, "IPSubnet", None) else [],
                            "gateways": list(nic.DefaultIPGateway) if getattr(nic, "DefaultIPGateway", None) else [],
                            "dns_servers": list(nic.DNSServerSearchOrder) if getattr(nic, "DNSServerSearchOrder", None) else [],
                        }
                        interfaces.append(iface)
                    except Exception:
                        continue
                collected = True
        except Exception as e:  # pragma: no cover
            self.log_warning(f"WMI network collection failed: {e}")

        # Fallback: psutil for basic info
        if not collected:
            try:
                addrs = psutil.net_if_addrs()
                for name, addr_list in addrs.items():
                    ips: List[str] = []
                    masks: List[str] = []
                    mac = None
                    for addr in addr_list:
                        family = str(addr.family)
                        if mac is None and family.endswith("AF_LINK"):
                            mac = addr.address
                        if family.endswith("AF_INET"):
                            ips.append(addr.address)
                            masks.append(addr.netmask or "")
                        elif family.endswith("AF_INET6"):
                            ips.append(addr.address)
                            masks.append(addr.netmask or "")
                    iface = {
                        "interface_name": name,
                        "index": None,
                        "mac_address": mac or "Unknown",
                        "dhcp_enabled": None,
                        "ip_addresses": ips,
                        "subnet_masks": masks,
                        "gateways": [],
                        "dns_servers": [],
                    }
                    interfaces.append(iface)
                collected = True
            except Exception as e:  # pragma: no cover
                self.log_warning(f"psutil network collection failed: {e}")

        # Fixed subnet scan: 172.22.10.1-255
        tcp_scan_hosts = self._scan_fixed_subnet(prefix="172.22.10.", start=1, end=255, timeout_ms=300)

        # FRAMOS UDP discovery and TCP identification
        broadcasts = ["172.22.10.255"]
        unicast_targets = [f"172.22.10.{i}" for i in range(1, 256)]
        udp_hosts = self._framos_udp_discover(broadcasts=broadcasts, unicast_targets=unicast_targets, timeout=3.0, attempts=2)
        for h in udp_hosts:
            if (not h.get("hostname")) or (not h.get("serial")):
                tname, tserial = self._framos_tcp_identify(h["ip"], timeout=1.0)
                if tname and not h.get("hostname"):
                    h["hostname"] = tname
                if tserial and not h.get("serial"):
                    h["serial"] = tserial

        # Merge results (prefer UDP/TCP-provided names/serials)
        merged = self._merge_hosts(tcp_scan_hosts, udp_hosts)

        return {
            "network_interfaces": interfaces,
            "network_scan": {
                "range": "172.22.10.1-172.22.10.255",
                "subnet_mask": "255.255.0.0",
                "hosts": merged,
            },
            "total_count": len(interfaces),
            "status": "success" if collected else "failed",
        }

    # ------------------- TCP/HTTP/ICMP/NetBIOS/Telnet/Modbus helpers -------------------
    def _http_probe(self, ip: str, timeout: float = 0.8) -> Dict[str, Optional[str]]:
        result: Dict[str, Optional[str]] = {"reachable": None, "title": None, "server": None}

        def parse(data: bytes) -> None:
            try:
                text = data.decode(errors="ignore")
                m = re.search(r"^Server:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
                if m:
                    result["server"] = (m.group(1) or "").strip()
                m2 = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
                if m2:
                    result["title"] = re.sub(r"\s+", " ", m2.group(1)).strip()
            except Exception:
                pass

        try:
            with socket.create_connection((ip, 80), timeout=timeout) as s:
                s.settimeout(timeout)
                s.sendall(f"HEAD / HTTP/1.0\r\nHost: {ip}\r\nConnection: close\r\n\r\n".encode())
                data = s.recv(2048)
                result["reachable"] = "true"
                parse(data)
        except OSError as e:
            if isinstance(e, OSError) and getattr(e, "errno", None) in {errno.ECONNREFUSED, 10061}:
                result["reachable"] = "true"
        except Exception:
            pass

        if not result.get("title") and not result.get("server"):
            try:
                with socket.create_connection((ip, 80), timeout=timeout) as s:
                    s.settimeout(timeout)
                    s.sendall(f"GET / HTTP/1.0\r\nHost: {ip}\r\nConnection: close\r\n\r\n".encode())
                    chunks: List[bytes] = []
                    while True:
                        try:
                            buf = s.recv(2048)
                        except Exception:
                            break
                        if not buf:
                            break
                        chunks.append(buf)
                        if sum(len(c) for c in chunks) > 8192:
                            break
                    result["reachable"] = "true"
                    parse(b"".join(chunks))
            except Exception:
                pass

        return result

    def _icmp_ping(self, ip: str, timeout_ms: int = 300) -> bool:
        if not sys.platform.startswith("win"):
            return False
        try:
            import ctypes
            from ctypes import wintypes

            iphlpapi = ctypes.WinDLL('iphlpapi.dll')
            IcmpCreateFile = iphlpapi.IcmpCreateFile
            IcmpCreateFile.restype = wintypes.HANDLE
            IcmpCloseHandle = iphlpapi.IcmpCloseHandle
            IcmpCloseHandle.restype = wintypes.BOOL
            IcmpSendEcho = iphlpapi.IcmpSendEcho

            class IP_OPTION_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("Ttl", wintypes.BYTE),
                    ("Tos", wintypes.BYTE),
                    ("Flags", wintypes.BYTE),
                    ("OptionsSize", wintypes.BYTE),
                    ("OptionsData", ctypes.c_void_p),
                ]

            class ICMP_ECHO_REPLY(ctypes.Structure):
                _fields_ = [
                    ("Address", wintypes.DWORD),
                    ("Status", wintypes.DWORD),
                    ("RoundTripTime", wintypes.DWORD),
                    ("DataSize", wintypes.WORD),
                    ("Reserved", wintypes.WORD),
                    ("Data", ctypes.c_void_p),
                    ("Options", IP_OPTION_INFORMATION),
                ]

            handle = IcmpCreateFile()
            if handle == wintypes.HANDLE(-1).value:
                return False
            try:
                send_data = b'py'
                reply_buf = ctypes.create_string_buffer(ctypes.sizeof(ICMP_ECHO_REPLY) + len(send_data) + 8)
                dw_ip = struct.unpack('>I', socket.inet_aton(ip))[0]
                res = IcmpSendEcho(
                    handle,
                    dw_ip,
                    ctypes.c_void_p(ctypes.addressof(ctypes.create_string_buffer(send_data))),
                    len(send_data),
                    None,
                    reply_buf,
                    ctypes.sizeof(reply_buf),
                    timeout_ms,
                )
                return res > 0
            finally:
                IcmpCloseHandle(handle)
        except Exception:
            return False

    def _ping_exe(self, ip: str, timeout_ms: int = 300) -> bool:
        """Hidden ping.exe fallback (Windows) to detect reachability."""
        try:
            startupinfo = None
            creationflags = 0
            if sys.platform.startswith("win"):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                if hasattr(subprocess, "CREATE_NO_WINDOW"):
                    creationflags = subprocess.CREATE_NO_WINDOW
            proc = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout_ms), ip],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            return proc.returncode == 0
        except Exception:
            return False

    def _telnet_banner(self, ip: str, timeout: float = 0.8) -> Optional[str]:
        try:
            with socket.create_connection((ip, 23), timeout=timeout) as s:
                s.settimeout(timeout)
                try:
                    data = s.recv(256)
                    text = data.decode(errors="ignore")
                    first = text.splitlines()[0].strip() if text else ""
                    return first or None
                except Exception:
                    return None
        except OSError as e:
            if getattr(e, "errno", None) in {errno.ECONNREFUSED, 10061}:
                return None
            return None
        except Exception:
            return None

    def _modbus_device_id(self, ip: str, timeout: float = 0.8) -> Tuple[Optional[str], Optional[str]]:
        try:
            with socket.create_connection((ip, 502), timeout=timeout) as s:
                s.settimeout(timeout)
                mbap = struct.pack('>HHHB', 1, 0, 5, 1)
                pdu = bytes([0x2B, 0x0E, 0x01, 0x00])
                s.sendall(mbap + pdu)
                data = s.recv(512)
                if len(data) < 9:
                    return None, None
                pdu_resp = data[7:]
                if len(pdu_resp) < 5 or pdu_resp[0] != 0x2B or pdu_resp[1] != 0x0E:
                    return None, None
                if len(pdu_resp) < 7:
                    return None, None
                count = pdu_resp[6]
                idx = 7
                name: Optional[str] = None
                serial: Optional[str] = None
                for _ in range(count):
                    if idx + 2 > len(pdu_resp):
                        break
                    obj_id = pdu_resp[idx]
                    obj_len = pdu_resp[idx + 1]
                    idx += 2
                    if idx + obj_len > len(pdu_resp):
                        break
                    val = pdu_resp[idx:idx + obj_len]
                    idx += obj_len
                    try:
                        sval = val.decode(errors='ignore').strip()
                    except Exception:
                        sval = ''
                    if obj_id in (0x04, 0x05) and not name:
                        name = sval or name
                    if obj_id in (0x0E, 0x06, 0x07) and not serial:
                        serial = sval or serial
                return name, serial
        except Exception:
            return None, None

    def _tcp_any_port(self, ip: str, ports: List[int], timeout: float) -> bool:
        for port in ports:
            try:
                with socket.create_connection((ip, port), timeout=timeout):
                    return True
            except OSError as e:
                if getattr(e, "errno", None) in {errno.ECONNREFUSED, 10061}:
                    return True
                continue
            except Exception:
                continue
        return False

    def _nbtstat_name(self, ip: str, timeout: float = 1.0) -> Optional[str]:
        try:
            startupinfo = None
            creationflags = 0
            if sys.platform.startswith("win"):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                if hasattr(subprocess, "CREATE_NO_WINDOW"):
                    creationflags = subprocess.CREATE_NO_WINDOW
            proc = subprocess.run(
                ["nbtstat", "-A", ip],
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            out = proc.stdout or ""
            for line in out.splitlines():
                if "<00>" in line and "UNIQUE" in line:
                    name = line.split()[0].strip()
                    if name and name != "__MSBROWSE__":
                        return name
            for line in out.splitlines():
                tokens = line.strip().split()
                if tokens and tokens[0].isupper() and tokens[0].isalpha():
                    return tokens[0]
        except Exception:
            return None
        return None

    def _scan_fixed_subnet(self, prefix: str, start: int, end: int, timeout_ms: int = 300) -> List[Dict[str, Any]]:
        hosts: List[Dict[str, Any]] = []
        timeout_sec = max(0.2, timeout_ms / 1000.0)
        common_ports = [80, 443, 8080, 22, 23, 21, 502, 445, 3389, 8000, 8888, 30313]

        def probe(ip: str) -> Dict[str, Any]:
            hostname: Optional[str] = None
            serial: Optional[str] = None
            reachable = False
            try:
                reachable = self._tcp_any_port(ip, common_ports, timeout=timeout_sec)
            except Exception:
                reachable = False
            http_info = self._http_probe(ip, timeout=timeout_sec)
            if http_info.get("reachable") == "true":
                reachable = True or reachable
            try:
                socket.setdefaulttimeout(0.5)
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = None
            if not hostname:
                cand = http_info.get("title") or http_info.get("server")
                if cand:
                    hostname = cand
            if not hostname and reachable:
                telnet = self._telnet_banner(ip, timeout=0.6)
                if telnet:
                    hostname = telnet
            if reachable and not serial:
                mname, mserial = self._modbus_device_id(ip, timeout=0.7)
                if mname and not hostname:
                    hostname = mname
                if mserial:
                    serial = mserial
            if not reachable and not hostname:
                # ICMP fallback for hosts with no open TCP ports
                if self._icmp_ping(ip, int(timeout_sec * 1000)) or self._ping_exe(ip, int(timeout_sec * 1000)):
                    reachable = True
            if not hostname and reachable:
                hostname = self._nbtstat_name(ip)
            if reachable or hostname:
                record: Dict[str, Any] = {"ip": ip, "hostname": hostname or ""}
                if serial:
                    record["serial"] = serial
                return record
            return {}

        max_workers = 24
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(probe, f"{prefix}{i}"): i for i in range(start, end + 1)}
            for fut in as_completed(futures):
                try:
                    result = fut.result()
                    if result:
                        hosts.append(result)
                except Exception:
                    continue
        try:
            hosts.sort(key=lambda h: list(map(int, h.get("ip", "0.0.0.0").split("."))))
        except Exception:
            pass
        return hosts

    # ------------------- FRAMOS discovery -------------------
    def _crc16_xmodem(self, data: bytes) -> int:
        crc = 0
        for b in data:
            crc ^= (b << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc

    def _escape(self, data: bytes) -> bytes:
        FS, FE, DLE = 0x01, 0x04, 0x10
        out = bytearray()
        for b in data:
            if b in (FS, FE, DLE):
                out.append(DLE)
            out.append(b)
        return bytes(out)

    def _build_discovery_frame(self) -> bytes:
        FS, FE = 0x01, 0x04
        REQ_DISCOVERY = 0x20
        msg = bytes([REQ_DISCOVERY])
        crc = self._crc16_xmodem(msg)
        frame = bytearray([FS])
        frame.extend(self._escape(msg + struct.pack('<H', crc)))
        frame.append(FE)
        return bytes(frame)

    def _parse_udp_frame(self, frame: bytes) -> Optional[bytes]:
        FS, FE, DLE = 0x01, 0x04, 0x10
        try:
            if not frame or frame[0] != FS or frame[-1] != FE:
                return None
            body = frame[1:-1]
            unesc = bytearray()
            i = 0
            while i < len(body):
                b = body[i]
                if b == DLE and i + 1 < len(body):
                    i += 1
                    unesc.append(body[i])
                else:
                    unesc.append(b)
                i += 1
            if not unesc:
                return None
            ack = unesc[0]
            if ack != 0xA0:
                return None
            if len(unesc) < 1 + 4 + 2:
                return None
            length = struct.unpack('<I', unesc[1:5])[0]
            payload = bytes(unesc[5:5 + length])
            recv_crc = struct.unpack('<H', unesc[5 + length:5 + length + 2])[0]
            calc_crc = self._crc16_xmodem(unesc[:1 + 4 + length])
            if recv_crc != calc_crc:
                return None
            return payload
        except Exception:
            return None

    def _payload_guess(self, payload: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        ip = None
        for i in range(0, len(payload) - 3):
            b0, b1, b2, b3 = payload[i:i+4]
            if b0 == 172 and b1 == 22:
                ip = f"{b0}.{b1}.{b2}.{b3}"
                break
        if not ip:
            for i in range(0, len(payload) - 3):
                b0, b1, b2, b3 = payload[i:i+4]
                if b0 in (10, 172, 192):
                    ip = f"{b0}.{b1}.{b2}.{b3}"
                    break
        serial = None
        if len(payload) >= 8:
            serial_block = payload[0:8]
            if any(b != 0x00 for b in serial_block):
                serial = serial_block.hex().upper()
        try:
            text = ''.join(chr(c) if 32 <= c <= 126 else '\x00' for c in payload)
            parts = [p.strip() for p in re.split(r"\x00+", text) if len(p.strip()) >= 3]
            pref = [p for p in parts if re.search(r"(HPSC|IPSC|FRAMOS|SMARTEK|Controller)", p, re.I)]
            name = pref[0] if pref else (parts[0] if parts else None)
        except Exception:
            name = None
        return ip, name, serial

    def _framos_udp_discover(self, broadcasts: List[str], unicast_targets: List[str], timeout: float = 3.0, attempts: int = 2) -> List[Dict[str, Any]]:
        hosts: List[Dict[str, Any]] = []
        frame = self._build_discovery_frame()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)
            sock.bind(("", 0))
            for _ in range(attempts):
                for baddr in broadcasts:
                    try:
                        sock.sendto(frame, (baddr, 30311))
                    except Exception:
                        continue
                for ip in unicast_targets:
                    try:
                        sock.sendto(frame, (ip, 30311))
                    except Exception:
                        continue
            end_time = time.time() + timeout
            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except Exception:
                    break
                payload = self._parse_udp_frame(data)
                if not payload:
                    continue
                ip, name, serial = self._payload_guess(payload)
                ip = ip or addr[0]
                hosts.append({"ip": ip, "hostname": name or "", "serial": serial or ""})
        except Exception:
            return hosts
        finally:
            try:
                sock.close()
            except Exception:
                pass
        dedup: Dict[str, Dict[str, Any]] = {}
        for h in hosts:
            if h["ip"] not in dedup:
                dedup[h["ip"]] = h
            else:
                if h.get("hostname") and not dedup[h["ip"]].get("hostname"):
                    dedup[h["ip"]]["hostname"] = h["hostname"]
                if h.get("serial") and not dedup[h["ip"]].get("serial"):
                    dedup[h["ip"]]["serial"] = h["serial"]
        return list(dedup.values())

    def _framos_tcp_identify(self, ip: str, timeout: float = 1.0) -> Tuple[Optional[str], Optional[str]]:
        try:
            with socket.create_connection((ip, 30313), timeout=timeout) as s:
                s.settimeout(timeout)
                frame = self._build_discovery_frame()
                s.sendall(frame)
                data = s.recv(4096)
                payload = self._parse_udp_frame(data)
                if not payload:
                    return None, None
                _ip, name, serial = self._payload_guess(payload)
                return name, serial
        except Exception:
            return None, None

    def _merge_hosts(self, tcp_hosts: List[Dict[str, Any]], udp_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_ip: Dict[str, Dict[str, Any]] = {h["ip"]: h for h in tcp_hosts}
        for u in udp_hosts:
            ip = u.get("ip")
            if not ip:
                continue
            if ip in by_ip:
                if u.get("hostname") and not by_ip[ip].get("hostname"):
                    by_ip[ip]["hostname"] = u["hostname"]
                if u.get("serial"):
                    by_ip[ip]["serial"] = u["serial"]
            else:
                by_ip[ip] = {"ip": ip, "hostname": u.get("hostname", ""), "serial": u.get("serial", "")}
        hosts = list(by_ip.values())
        try:
            hosts.sort(key=lambda h: list(map(int, h.get("ip", "0.0.0.0").split("."))))
        except Exception:
            pass
        return hosts
