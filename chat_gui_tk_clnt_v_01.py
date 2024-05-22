"""
    Este módulo implementa un cliente de chat utilizando sockets y threading y GUI 
    con tkinter.

    El servidor puede manejar múltiples clientes simultáneamente y permite la 
    autenticación de usuarios mediante credenciales hash SHA-256.
"""


import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

class ChatClient:
    """
            Inicializa el cliente de chat y configura la GUI.

            Args:
                host (str): La dirección del servidor.
                port (int): El puerto en el que el servidor escucha.
    """

    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        
        # Configuracion de la GUI
        self.root = tk.Tk()
        self.root.title("Cliente de Chat")
        
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_area.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.username = self.authenticate_user()
        self.start_receive_thread()

    def authenticate_user(self):
        """
            Autentica el usuario mediante cuadros de diálogo de tkinter.

            Returns:
                str: El nombre de usuario autenticado.
        """        
        while True:
            username = simpledialog.askstring("Nombre de Usuario", "Escriba nombre de usuario:")
            if username:
                break
            messagebox.showerror("Error", "Nombre de usuario no puede estar vacio.")
        while True:
            password = simpledialog.askstring("Contraseña", "Escriba contraseña:", show='*')
            if password:
                break
            messagebox.showerror("Error", "Contraseña no puede estar vacia.")
        
        self.client_socket.send(f"{username}\n".encode())
        self.client_socket.send(f"{password}\n".encode())
        
        response = self.client_socket.recv(1024).decode()
        if "Autenticacion exitosa" in response:
            messagebox.showinfo("Exito", "Autenticacion exitosa. Bienvenido al chat.")
            return username
        else:
            messagebox.showerror("Error", "Usuario o contraseña invalido. Intente nuevamente.")
            return self.authenticate_user()

    def send_message(self, event=None):

        """
            Envía un mensaje al servidor y lo muestra en el área de chat.

            Args:
                event (tk.Event, optional): Evento de teclado. Default es None.
        """        
        message = self.message_entry.get()
        if message:
            self.client_socket.send(message.encode())
            self.message_entry.delete(0, tk.END)
            if message.lower() == 'quit':
                self.client_socket.close()
                self.root.quit()

    def receive_messages(self):
        """
            Recibe mensajes del servidor y los muestra en el área de chat.
        """        
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                self.update_chat_area(message)
            except socket.error as e:
                self.update_chat_area(f"Error: {e}")
                break

    def update_chat_area(self, message):
        """
            Actualiza el area de chat con un nuevo mensaje.

            Args:
                message (str): El mensaje a mostrar en el área de chat.
        """

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def start_receive_thread(self):
        """
            Inicia el hilo para recibir mensajes del servidor.
        """        
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        self.root.mainloop()

def get_server_and_port_of_config():
    """
        Lee la configuración del servidor desde un archivo y obtiene la dirección IP 
        y el puerto del servidor.

        El contenido del archivo srvr_config.sys debe estar formateado asi ej:
            server_ip=192.168.1.76
            server_port=9999
        Returns:
            tuple: Una tupla que contiene la dirección IP y el puerto del servidor.
    """        

    server_ip = None
    server_port = None
    with open("srvr_config.sys", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("server_ip="):
                server_ip = line.split("=")[1].strip()
            elif line.startswith("server_port="):
                server_port = int(line.split("=")[1].strip())
    if server_ip is None or server_port is None:
        raise ValueError("El archivo de configuracion debe contener 'server_ip' y 'server_port'.")
    return server_ip, server_port

def main():
    """
        Función principal Server de la aplicación de chat.                
    """     

    host, port = get_server_and_port_of_config()
    client = ChatClient(host, port)

if __name__ == "__main__":
    main()