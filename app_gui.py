from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from transport.port_list import list_serial_ports


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BMS Protocol Probe MVP")
        self.geometry("700x450")
        self.port_var = tk.StringVar()
        self.include_unverified = tk.BooleanVar(value=False)

        ttk.Label(self, text="COM port:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.port_combo = ttk.Combobox(self, textvariable=self.port_var, width=25)
        self.port_combo.grid(row=0, column=1, sticky="w")
        ttk.Button(self, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=6)
        ttk.Checkbutton(self, text="Include unverified read probes", variable=self.include_unverified).grid(row=1, column=0, columnspan=3, sticky="w", padx=6)

        self.status = tk.Text(self, height=20, width=80)
        self.status.grid(row=2, column=0, columnspan=4, padx=6, pady=6)
        self.refresh_ports()

    def refresh_ports(self) -> None:
        ports = list_serial_ports()
        self.port_combo["values"] = ports
        if ports:
            self.port_var.set(ports[0])
        self.status.insert("end", f"Ports refreshed: {ports}\n")


if __name__ == "__main__":
    App().mainloop()
