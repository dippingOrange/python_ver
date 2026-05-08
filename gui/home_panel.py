import tkinter as tk
from tkinter import ttk


class HomePanel(ttk.Frame):
    def __init__(self, parent, on_reading, on_conversation, on_settings):
        super().__init__(parent)
        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            inner, text="English Speaking Practice", font=("Arial", 18, "bold")
        ).pack(pady=(0, 20))

        ttk.Button(
            inner,
            text="Reading Test",
            command=on_reading,
            style="Accent.TButton",
        ).pack(fill="x", pady=4, ipady=4)

        ttk.Button(
            inner,
            text="Conversation Practice",
            command=on_conversation,
            style="Accent.TButton",
        ).pack(fill="x", pady=4, ipady=4)

        ttk.Button(inner, text="API Settings", command=on_settings).pack(
            fill="x", pady=4, ipady=2
        )
