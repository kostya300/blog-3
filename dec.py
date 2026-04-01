import base64

def decode_password():
    enc_password = "0Nv32PTwgYjzg9/8j5TbmvPd3e7WhtWWyuPsyO76/Y+U193E"
    key = b"armando"

    # Шаг 1: декодируем Base64
    encrypted_bytes = base64.b64decode(enc_password)
    decrypted_bytes = bytearray()

    # Шаг 2: расшифровываем XOR
    for i, byte in enumerate(encrypted_bytes):
        # XOR с ключом (циклически) и константой 0xDF
        decrypted_byte = byte ^ key[i % len(key)] ^ 0xDF
        decrypted_bytes.append(decrypted_byte)

    # Шаг 3: преобразуем в строку
    return decrypted_bytes.decode('latin-1')  # latin-1 сохраняет все байты

# Запуск декодера
password = decode_password()
print(f"Decoded password: {password}")
