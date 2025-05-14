# Importación de módulos necesarios
import tkinter as tk  # Interfaz gráfica
from tkinter import filedialog, messagebox  # Diálogos para archivos y mensajes
import git  # Interfaz con Git
import os  # Operaciones del sistema operativo
import shutil  # Herramientas para manipular archivos/rutas

# Verifica si Git está en el PATH del sistema
git_path = shutil.which("git")

if git_path:
    # Si Git está disponible, se define su ruta para que GitPython lo use
    os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = git_path

else:
    # Si Git no está en el PATH, se solicita al usuario que seleccione git.exe manualmente
    from tkinter import filedialog
    git_path = filedialog.askopenfilename(title="Selecciona git.exe (usualmente en C:\\Program Files\\Git\\bin\\git.exe)", filetypes=[("Ejecutable Git", "git.exe")])
    if git_path:
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = git_path
    else:
        # Si no se proporciona git.exe, se muestra error y termina el programa
        messagebox.showerror("Error", "No se encontró git.exe. Por favor, instala Git o proporciona la ruta.")
        exit(1)

# Lista de pasos explicativos que se mostrarán al usuario en la GUI        
pasos_texto = [
    "PASO 1: Selecciona una carpeta con un repositorio Git válido o inicializa uno nuevo.",
    "PASO 2: Si es un repositorio nuevo, haz clic en 'Inicializar Repositorio (git init)'.",
    "PASO 3: Configura el repositorio remoto ingresando la URL y haciendo clic en 'Configurar Remoto'.",
    "PASO 4: Verifica que haya cambios para hacer commit en el repositorio.",
    "PASO 5: Ingresa un mensaje de commit claro que describa los cambios.",
    "PASO 6: Haz clic en 'Hacer Commit' para guardar los cambios en el repositorio.",
    "PASO 7: Haz clic en 'Subir a GitHub (Push)' para enviar los cambios al repositorio remoto en GitHub."
]

# Función que devuelve una instancia de un repositorio Git en la ruta seleccionada
def get_repo():
    path = repositorio.get()
    try:
        return git.Repo(path)
    except git.exc.InvalidGitRepositoryError:
        raise Exception("La carpeta seleccionada no es un repositorio Git válido o está vacía.")

# Selector de carpeta para elegir la ruta del repositorio
def seleccionar_ruta():
    carpeta = filedialog.askdirectory(title="Selecciona un directorio con un repositorio Git")
    if carpeta:
        repositorio.set(carpeta)
        actualizar_pasos("PASO 1 completado: Carpeta seleccionada.")
        actualizar_ramas()
        mostrar_estado()
        try:
            repo = get_repo()
            rama_actual.set(repo.active_branch.name)
        except:
            pass

# Inicializa un nuevo repositorio Git en la carpeta seleccionada
def inicializar_repositorio():
    try:
        git.Repo.init(repositorio.get())
        messagebox.showinfo("Inicialización", "Repositorio Git inicializado en la carpeta seleccionada.")
        actualizar_pasos("PASO 2 completado: Repositorio inicializado.")
        actualizar_ramas()
    except Exception as e:
        messagebox.showerror("Error", f"Error al inicializar el repositorio: {str(e)}")

# Configura el repositorio remoto con la URL proporcionada
def configurar_remoto():
    try:
        repo = get_repo()
        url = remote_url.get()
        if not url:
            messagebox.showerror("Error", "Debes ingresar la URL del repositorio remoto.")
            return
        if 'origin' in repo.remotes:
            repo.delete_remote('origin')
        repo.create_remote('origin', url)
        messagebox.showinfo("Remoto Configurado", f"Remoto configurado con la URL: {url}")
        actualizar_pasos("PASO 3 completado: Remoto configurado.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al configurar el repositorio remoto: {str(e)}")

# Muestra el estado actual del repositorio (git status)
def mostrar_estado():
    try:
        repo = get_repo()
        estado = repo.git.status()
        status_text.delete("1.0", tk.END)
        status_text.insert(tk.END, estado)
        rama_actual.set(repo.active_branch.name)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo mostrar el estado: {str(e)}")

# Realiza un commit con el mensaje proporcionado
def hacer_commit():
    try:
        repo = get_repo()
        mensaje = commit_message.get()
        if not mensaje:
            messagebox.showerror("Error", "Debes ingresar un mensaje de commit.")
            actualizar_pasos("PASO 5 incompleto: Faltó el mensaje de commit.")
            return
        repo.git.add(all=True)
        repo.index.commit(mensaje)
        rama = repo.active_branch.name
        rama_actual.set(rama)
        messagebox.showinfo(
            "Commit Realizado",
            f"Commit realizado en la rama: '{repo.active_branch.name}'\n\nMensaje del Commit:\n\"{mensaje}\""
        )
        actualizar_pasos("PASO 6 completado: Commit realizado.")
        mostrar_estado()
    except Exception as e:
        messagebox.showerror("Error", f"Error al hacer commit: {str(e)}")

# Realiza push de los cambios al repositorio remoto
def hacer_push():
    try:
        repo = get_repo()
        if 'origin' not in repo.remotes:
            messagebox.showerror("Error", "No se ha configurado un repositorio remoto.")
            return
        if repo.is_dirty(untracked_files=True):
            repo.git.add(all=True)
            repo.index.commit("Actualización antes de push (eliminación de archivos, cambios)")
        current_branch = repo.active_branch
        tracking = current_branch.tracking_branch()
        if tracking:
            rama_remota = tracking.remote_head
            messagebox.showinfo("Push", f"Haciendo push a la rama remota: '{rama_remota}' desde la rama local: '{current_branch.name}'")
        else:
            messagebox.showinfo("Push", f"Haciendo push inicial (no había seguimiento) desde la rama local: '{current_branch.name}'\nSe establecerá el upstream automáticamente.")
        # Primer push con --set-upstream y rama origin
        if not current_branch.tracking_branch():
            repo.git.push("--set-upstream", "origin", current_branch.name)
        else:
            repo.remotes.origin.push()
        messagebox.showinfo("Push", "Cambios subidos a GitHub.")
        actualizar_pasos("PASO 7 completado: Cambios subidos a GitHub.")
        rama_actual.set(repo.active_branch.name)
    except Exception as e:
        messagebox.showerror("Error", f"Error al subir cambios a GitHub: {str(e)}")

# Actualiza el menú desplegable de ramas disponibles
def actualizar_ramas():
    try:
        repo = git.Repo(repositorio.get())
        repo.remotes.origin.fetch()
        ramas_locales = [b.name for b in repo.branches]
        ramas_remotas = [ref.remote_head for ref in repo.remotes.origin.refs if ref.remote_head != 'HEAD']
        todas_las_ramas = list(set(ramas_locales + ramas_remotas))
        todas_las_ramas.sort()
        rama_seleccionada.set(todas_las_ramas[0] if todas_las_ramas else "")
        rama_menu['menu'].delete(0, 'end')
        for rama in todas_las_ramas:
            rama_menu['menu'].add_command(label=rama, command=lambda r=rama: [rama_seleccionada.set(r), cambiar_rama_remota()])
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener ramas: {str(e)}")

# Cambia a una rama seleccionada desde el menú
def cambiar_rama_remota():
    try:
        repo = get_repo()
        rama = rama_seleccionada.get()
        if rama:
            repo.remotes.origin.fetch()
            if rama not in repo.heads:
                repo.git.checkout('-b', rama, f'origin/{rama}')
            else:
                repo.git.checkout(rama)
            rama_actual.set(repo.active_branch.name)

            messagebox.showinfo("Cambio de Rama", f"Cambiado a la rama '{rama}'.")
            mostrar_estado()
        else:
            messagebox.showerror("Error", "Debe seleccionar una rama.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cambiar de rama: {str(e)}")

# Crea una nueva rama local y la sube al remoto origin
def crear_rama_remota():
    try:
        repo = get_repo()

        #si alguien escribe "mi nueva rama", se convertirá automáticamente en "mi-nueva-rama" antes de crearla.
        nombre = nueva_rama.get().strip().replace(" ", "-")
        
        if not nombre:
            messagebox.showerror("Error", "Debes ingresar un nombre para la nueva rama.")
            return
        if nombre in [b.name for b in repo.branches]:
            messagebox.showerror("Error", f"La rama '{nombre}' ya existe localmente.")
            return
        repo.git.checkout('-b', nombre)
        repo.git.push('--set-upstream', 'origin', nombre)
        repo.git.fetch('--all')
        rama_seleccionada.set(nombre)
        rama_actual.set(repo.active_branch.name)
        actualizar_ramas()
        messagebox.showinfo("Rama Remota", f"Rama remota '{nombre}' creada y subida a GitHub.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Error al crear la rama remota: {str(e)}")

# Muestra mensajes de avance en los pasos        
def actualizar_pasos(mensaje):
    pasos_completados.config(text=mensaje)

# ===================== INTERFAZ GRÁFICA ======================

# Ventana principal
root = tk.Tk()
root.title("PushProMaster")

# Variables para widgets
repositorio = tk.StringVar()
commit_message = tk.StringVar()
rama_seleccionada = tk.StringVar()
nueva_rama = tk.StringVar()
remote_url = tk.StringVar()
rama_actual = tk.StringVar()

# Frame principal
frame = tk.Frame(root)
frame.grid(row=0, column=0, padx=10, pady=10)

# Lista de widgets con su texto, tipo y fila correspondiente
widgets = [
    ("Repositorio Git:", tk.Entry(frame, textvariable=repositorio, width=40), 0),
    ("", tk.Button(frame, text="Seleccionar Repositorio", command=seleccionar_ruta), 1),
    ("", tk.Button(frame, text="Inicializar Repositorio (git init)", command=inicializar_repositorio), 2),
    ("URL del Repositorio Remoto:", tk.Entry(frame, textvariable=remote_url, width=40), 3),
    ("", tk.Button(frame, text="Configurar Remoto", command=configurar_remoto), 4),
    ("Mensaje de Commit:", tk.Entry(frame, textvariable=commit_message, width=40), 5),
    ("", tk.Button(frame, text="Hacer Commit", command=hacer_commit), 6),
    ("Seleccionar Rama:", None, 7),
    ("", tk.Button(frame, text="Cambiar de Rama", command=cambiar_rama_remota), 8),
    ("Nombre de Nueva Rama:", tk.Entry(frame, textvariable=nueva_rama, width=40), 9),
    ("", tk.Button(frame, text="Crear Nueva Rama", command=crear_rama_remota), 10),
    ("", tk.Button(frame, text="Subir a GitHub (Push)", command=hacer_push), 11),
    ("Estado del Repositorio:", None, 12)
]

# Añade widgets al grid
for label, widget, row in widgets:
    if label:
        tk.Label(frame, text=label).grid(row=row, column=0, pady=5)
    if widget:
        widget.grid(row=row, column=1, pady=5)

# Menú desplegable para ramas
rama_menu = tk.OptionMenu(frame, rama_seleccionada, "")
rama_menu.grid(row=7, column=1, pady=5)

# Cuadro de texto para mostrar estado del repositorio
status_text = tk.Text(frame, width=40, height=5)
status_text.grid(row=12, column=1, pady=5)

# Instrucciones paso a paso
tk.Label(frame, text="Instrucciones Paso a Paso:").grid(row=13, column=0, pady=10)
steps_frame = tk.Frame(frame)
steps_frame.grid(row=14, column=0, columnspan=2)
steps_text = tk.Text(steps_frame, width=40, height=6)
steps_text.grid(row=0, column=0)
steps_scroll = tk.Scrollbar(steps_frame, orient="vertical", command=steps_text.yview)
steps_scroll.grid(row=0, column=1, sticky='ns')
steps_text.config(yscrollcommand=steps_scroll.set)

# Inserta los pasos predefinidos
for paso in pasos_texto:
    steps_text.insert(tk.END, paso + "\n")

# Muestra el paso actual completado
pasos_completados = tk.Label(frame, text="", fg="green")
pasos_completados.grid(row=15, column=0, pady=5)

# Muestra la rama actual
tk.Label(frame, text="Rama actual:").grid(row=16, column=0, pady=5)
tk.Label(frame, textvariable=rama_actual, fg="blue").grid(row=16, column=1, pady=5)

# Ejecuta la aplicación
root.mainloop()