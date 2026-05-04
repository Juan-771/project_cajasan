import imaplib
import email

EMAIL = "abrilromanj@gmail.com"
PASSWORD = "amnfrcsvugibsuyy"

print("🔌 Conectando...")

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL, PASSWORD)

print("✅ Conectado")

mail.select("inbox")

print("Buscando correos...")

status, mensajes = mail.search(None, 'ALL')

lista_ids = mensajes[0].split()

print(f"Total correos encontrados: {len(lista_ids)}")

# ⚠️ SOLO LOS ÚLTIMOS 5 (para que no se demore)
for num in lista_ids[-5:]:
    print(f"📨 Leyendo correo {num.decode()}")

    status, data = mail.fetch(num, "(RFC822)")
    
    for response in data:
        if isinstance(response, tuple):
            msg = email.message_from_bytes(response[1])
            
            print("➡️ Asunto:", msg["subject"])
            
            for part in msg.walk():
                filename = part.get_filename()
                
                if filename:
                    print("📎 Adjunto encontrado:", filename)