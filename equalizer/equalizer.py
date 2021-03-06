import functools
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import threading
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from scipy.io import wavfile
from scipy.fft import rfft, rfftfreq
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Equalizador(tk.Tk):
    def __init__(self):
        super().__init__()

        base_path = os.path.dirname(sys.argv[0])
        icon = base_path + "/img/icon.png"
        self.iconphoto(True, tk.PhotoImage(file=icon))

        self.title("Equalizador")
        self.audio_file = tk.StringVar()
        self.audio_file.set(os.getcwd() + "/audio/audio_test.wav")
        self.Gp = [(tk.IntVar(), "Graves"),
                   (tk.IntVar(), "Médios"),
                   (tk.IntVar(), "Agudos")]

        self.create_widgets()

    def start(self):
        self.mainloop()

    def create_widgets(self):
        """Cria cada um dos Widgets da janela."""
        ttk.Label(
            self,
            text="Equalizador de PDS",
            font=("Helvetica", 20, "bold")
        ).pack()

        self.set_file_frame()
        list(map(self.set_scale_frame, [1, 2, 3]))
        self.set_apply_button()

    def set_file_frame(self):
        """Cria o frame para escolha de áudio."""
        ttk.Label(self).pack()  # Blank row for better organization

        label_frame = ttk.LabelFrame(self, text="Seleção do arquivo de áudio")
        label_frame.pack(fill="both")

        ttk.Entry(
            label_frame,
            textvariable=self.audio_file,
            width=80
        ).pack(side="left", fill="both")

        # Select file path button
        title = f"Selecione o arquivo de áudio"
        ttk.Button(
            label_frame,
            text="...",
            command=lambda: self.audio_file.set(
                tk.filedialog.askopenfilename(
                    title=title,
                    initialdir="./audio/"
                )),
            width=3,
        ).pack(side="left")

        ttk.Label(self).pack()  # Blank row for better organization

    def set_scale_frame(self, i):
        """Cria o frame para escolha dos ganhos."""
        self.Gp[i-1][0].set(100)

        label_frame = ttk.LabelFrame(self, text=f"Ganho Gp{i} - {self.Gp[i - 1][1]}")
        label_frame.pack(side="left", fill="both")

        tk.Scale(
            label_frame,
            from_=0,
            to=100,
            variable=self.Gp[i-1][0],
            orient="horizontal",
            length=165,
        ).pack(side="left", fill="both")

    def set_apply_button(self):
        """Cria o botão para rodar os cálculos."""
        ttk.Label(self).pack()  # Blank row for better organization

        _wrapper = functools.partial(
            Results,
            master=self,
            audio_file=self.audio_file,
            Gp=[self.Gp[i][0] for i in range(3)])

        ttk.Button(
            self,
            text="Apply",
            command=_wrapper
        ).pack(side="right")


class Results(tk.Toplevel):
    """Window that shows the results.

    Where the magic happens!!!
    """
    def __init__(self, audio_file, Gp, master=None):  # noqa
        super().__init__(master)

        if not os.path.isfile(audio_file.get()):
            self.withdraw()
            tkinter.messagebox.showerror(
                title="Erro muito errado",
                message="Arquivo de áudio inválido ou inexistente")
            self.destroy()
        else:
            self.audiofile = audio_file.get()
            self.Gp = [Gp[i].get() for i in range(3)]

            self.audio = None
            self.sample_rate = None
            self.audio_fft = None
            self.duration = None
            self.freq = None

            self.do_the_magic()

    def do_the_magic(self):
        """It runs all"""
        self.read_audio_file()

    def read_audio_file(self):
        def calculate():
            self.sample_rate, self.audio = wavfile.read(self.audiofile)
            self.audio = np.transpose(self.audio)
            self.duration = len(self.audio[:][0]) / float(self.sample_rate)
            self.audio_fft = [None] * self.audio.ndim
            self.audio_fft[0] = rfft(self.audio[0])
            self.audio_fft[1] = rfft(self.audio[1])
            self.freq = rfftfreq(self.audio[0].size, 1. / self.sample_rate)

            print(f"Sample Rate: {self.sample_rate} with {self.audio.ndim} channels")

        calculate_thr = threading.Thread(target=calculate)
        calculate_thr.start()
        calculate_thr.join()

        self.show_analisys_spectrum_graph()

    def show_analisys_spectrum_graph(self):
        fig1 = plt.figure(figsize=(10, 5), dpi=100)
        fig1.subplots_adjust(hspace=.5)
        chart_type = FigureCanvasTkAgg(fig1, self)
        chart_type.get_tk_widget().pack()

        t = np.linspace(0, self.duration, len(self.audio[0]))
        plt_a = fig1.add_subplot(2, 2, (1, 2))
        plt_a.set_title("No tempo")
        plt_a.set_xlabel(f"Tempo [s]")
        plt_a.grid(linewidth=.5)
        plt_a.plot(t, self.audio[0], linewidth=.5)

        plt_b = fig1.add_subplot(223)
        plt_b.set_title("Canal 1")
        plt_b.set_xlabel("Frequência [Hz]")
        plt_b.set_xscale("log")
        plt_b.grid(which="both", linewidth=.5)
        plt_b.plot(self.freq, abs(self.audio_fft[0]), linewidth=.5)  # noqa

        plt_c = fig1.add_subplot(224)
        plt_c.set_title("Canal 2")
        # plt_c.set_xlabel("Frequência [Hz]")
        # plt_c.set_xscale("log")
        plt_c.grid(which="both", linewidth=.5)
        plt_c.specgram(abs(self.audio[0]), Fs=self.sample_rate, scale="dB",
                       mode="psd"
                       )  # noqa

    def filter_channels(self):
        pass
