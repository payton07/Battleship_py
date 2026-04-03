import socket

class Client:
    def __init__(self, server_ip="127.0.0.1", server_port=5000, buffer_size=1024):
        """Initialise le client
        
        Args:
            server_ip: Adresse IP du serveur
            server_port: Port du serveur
            buffer_size: Taille du buffer de réception (défaut: 4096)
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.buffer_size = buffer_size
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True
            print(f"Connecté au serveur {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Erreur de connexion : {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Ferme la connexion au serveur"""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                print("Déconnecté du serveur")
            except Exception as e:
                print(f"Erreur lors de la déconnexion : {e}")
    
    def send_message(self, message):
        """Envoie un message texte au serveur
        
        Args:
            message: Message à envoyer (str)
            
        Returns:
            True si envoi réussi, False sinon
        """
        if not self.connected:
            print("Erreur : Non connecté au serveur")
            return False
        
        try:
            self.socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi : {e}")
            self.connected = False
            return False
    
    def receive_message(self):
        """Reçoit un message texte du serveur
        
        Returns:
            Le message reçu (str) ou None en cas d'erreur
        """
        if not self.connected:
            print("Erreur : Non connecté au serveur")
            return None
        
        try:
            data = self.socket.recv(self.buffer_size)
            if not data:
                print("Connexion fermée par le serveur")
                self.connected = False
                return None
            return data.decode('utf-8')
        except Exception as e:
            print(f"Erreur lors de la réception : {e}")
            self.connected = False
            return None

    def send_and_receive(self, message):
        """Envoie un message et attend une réponse
        
        Args:
            message: Message à envoyer (str)
            
        Returns:
            La réponse reçue (str) ou None
        """
        if self.send_message(message):
            return self.receive_message()
        return None
    
    def __enter__(self):
        """Permet d'utiliser le client avec 'with'"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme automatiquement la connexion à la sortie du 'with'"""
        self.disconnect()
        return False

if __name__ == "__main__":
    # Exemple 1 : Utilisation avec context manager
    print("=== Exemple avec context manager ===")
    with Client("10.236.185.181", 5000) as client:
        if client.connected:
            message = input("Tape quelque chose : ")
            response = client.send_and_receive(message)
            if response:
                print(f'Reçu du serveur: {response}')
    
    print("\n=== Exemple avec JSON ===")
