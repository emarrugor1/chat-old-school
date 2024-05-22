"""
    Este módulo implementa un servidor de chat utilizando sockets y threading y GUI 
    con tkinter.

    El servidor puede manejar múltiples clientes simultáneamente y permite la 
    autenticación de usuarios mediante credenciales hash SHA-256.
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import simpledialog, messagebox

class ChatServer:
    """
        Clase para el servidor de chat.

        Atributos:
            host (str): La dirección del servidor.
            port (int): El puerto en el que el servidor escucha.
            server_socket (socket.socket): El socket del servidor.
            clients (list): Lista de clientes conectados.
            users (dict): Diccionario de usuarios con sus contraseñas hash.
    """    
    def __init__(self):
        """
            Inicializa el cliente de chat, establece la conexión al servidor y configura la GUI.

            Args:
                host (str): La dirección del servidor.
                port (int): El puerto del servidor.
        """
        # Obteniendo los parametros del socket desde un archivo de configuración        
        host, port = self.get_server_and_port_of_config()
        #Falta implementar un metodo que me permita saber si 
        # el par host y puerto estan disponibles

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        
        self.valid_clients = []
        self.valid_users = {}
        self.init_users()
        
        # Configuracion de la GUI
        self.root = tk.Tk()
        self.root.title("Servidor de Chat")
        
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_area.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        
        #New
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        self.message_entry.bind("<Return>", self.send_message_to_clients)


        self.status_label = tk.Label(self.root, text=f"Servidor iniciado en {host}:{port}")
        self.status_label.pack(padx=20, pady=5)
        
        self.current_user = self.validate_user()
        self.update_chat_area(f"Servidor en linea... {self.current_user} [*--CONECTADO--*]")
        

        self.start_server_thread()

    def init_users(self):
        """
            Inicializa algunos usuarios válidos quemados en el código con contraseñas hash SHA-256.
        """
        self.valid_users["jonny"] = "jonnyl"
        self.valid_users["edwin"] = "edwinm"
        self.valid_users["alberto"] = "albertov"

    def authenticate_user(self, client_socket):
        """
            Autentica un usuario mediante su nombre de usuario y contraseña.

            Args:
                client_socket (socket.socket): El socket del cliente.

            Returns:
                str: El nombre de usuario si la autenticación es exitosa, None en caso contrario.
        """

        client_socket.send(b"Get usuario:")
        username = client_socket.recv(1024).decode().strip()
        client_socket.send(b"Get password:")
        password = client_socket.recv(1024).decode().strip()
        while username not in self.valid_users or self.valid_users[username] != password:
            client_socket.send(b"Usuario o clave invalida. Intente nuevamente.\n")
            client_socket.send(b"Get usuario:")
            username = client_socket.recv(1024).decode().strip()
            client_socket.send(b"Get password:")
            password = client_socket.recv(1024).decode().strip()
        client_socket.send(b"Autenticacion exitosa. Bienvenido al chat!\n")
        return username
      

    def send_message_to_clients(self, event=None):
        """Envia un mensaje a todos los clientes conectados."""
        message = self.message_entry.get()
        if message:
            for client_socket in self.valid_clients:
                try:
                    client_socket.send(f"Servidor: {message}".encode())
                except socket.error as e:
                    self.update_chat_area(f"Error al enviar mensaje a cliente: {e}")
            self.update_chat_area(f"Servidor: {message}")
            self.message_entry.delete(0, tk.END)


    def handle_client(self, client_socket, address):
        """
            Maneja la comunicación con un cliente.

            Args:
                client_socket (socket.socket): El socket del cliente.
        """

        username = self.authenticate_user(client_socket)
        self.valid_clients.append(client_socket)  # Agregar cliente a la lista de clientes v�lidos
        self.update_chat_area(f"{username} conectado a {address}")

        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                decoded_message = message.decode()
                self.update_chat_area(f"{username}@{address}: {decoded_message}")
                for other_client_socket in self.valid_clients:
                    if other_client_socket != client_socket:
                        try:
                            other_client_socket.send(f"{username}@{address}: {decoded_message}".encode())
                        except socket.error as e:
                            self.update_chat_area(f"Error al enviar mensaje a cliente: {e}")
            except socket.error as e:
                self.update_chat_area(f"Error: {e}")
                break

        self.valid_clients.remove(client_socket)  # Eliminar cliente de la lista de clientes v�lidos
        self.update_chat_area(f"{username} desconectado de {address}")
        client_socket.close()





    def update_chat_area(self, message):
        """
        Actualiza el área de chat con un nuevo mensaje.
        Args:
        message (str): El mensaje a mostrar en el área de chat.
        """        

        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def start_server(self):
        """
            Inicia el servidor de chat y acepta nuevas conexiones.
        """

        while True:
            client_socket, address = self.server.accept()
            self.update_chat_area(f"Conectado a {address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, address))
            client_handler.start()

    def start_server_thread(self):
        """
            Inicia el hilo para recibir mensajes del servidor.
        """

        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        self.root.mainloop()

    def validate_user(self):
        """
            Autentica al usuario mediante cuadros de diálogo de tkinter.

            Muestra cuadros de diálogo para solicitar el nombre de usuario y la contraseña.
            Envia esta información al servidor y espera una respuesta de autenticación.
            Si la autenticación es exitosa, se permite al usuario continuar utilizando la
            aplicación de chat. En caso contrario, se muestra un mensaje de error y se solicita
            nuevamente la información.

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
        if username in self.valid_users and self.valid_users[username] == password:
            return username
        else:
            messagebox.showerror("Error", "Usuario o contraseña invalido. Intente nuevamente.")
            return self.validate_user()

    def get_server_and_port_of_config(self):
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

    server = ChatServer()

if __name__ == "__main__":
    main()