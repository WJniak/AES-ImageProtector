from flask import Flask, request, send_file, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from PIL import Image
import numpy as np
import io
import os
app = Flask(__name__)


app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


SECRET_KEY = os.getenv("AES_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Brak klucza AES w zmiennych środowiskowych!")
SECRET_KEY = SECRET_KEY.encode('utf-8')


HTML_FORM = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Szyfrowanie i Deszyfrowanie zdjęć</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        h1 {
            color: #333;
        }
        .container {
            background: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 500px;
            text-align: center;
        }
        .form-group {
            margin: 15px 0;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        button {
            background-color: #007BFF;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #0056b3;
        }
        footer {
            margin-top: 20px;
            font-size: 14px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Szyfrowanie i Deszyfrowanie zdjęć</h1>
        <h2>Szyfrowanie obrazu</h2>
        <form method="post" action="/encrypt" enctype="multipart/form-data">
            <div class="form-group">
                <input type="file" name="image" accept="image/*" required>
            </div>
            <button type="submit">Szyfruj obraz</button>
        </form>
        <h2>Deszyfrowanie obrazu</h2>
        <form method="post" action="/decrypt" enctype="multipart/form-data">
            <div class="form-group">
                <input type="file" name="image" accept=".bin" required>
            </div>
            <button type="submit">Deszyfruj obraz</button>
        </form>
    </div>
    <footer>
        &copy; 2024 Aplikacja | Wiktor Janiak | Wszystkie prawa zastrzeżone
    </footer>
</body>
</html>
"""


@app.route('/')
def home():
    return HTML_FORM


@app.route('/encrypt', methods=['POST'])
def encrypt_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Brak pliku obrazu w żądaniu'}), 400

        image_file = request.files['image']

        try:
            image = Image.open(image_file).convert("RGB")
        except Exception as e:
            print(f"Błąd podczas otwierania obrazu: {e}")
            return jsonify({'error': 'Nieprawidłowy plik obrazu'}), 400

        width, height = image.size
        image_bytes = image.tobytes()

        try:
            cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
            iv = cipher.iv
            padded_data = pad(image_bytes, AES.block_size)
            encrypted_bytes = cipher.encrypt(padded_data)
        except Exception as e:
            print(f"Błąd podczas szyfrowania: {e}")
            return jsonify({'error': 'Wystąpił błąd podczas szyfrowania obrazu'}), 500

        size_data = f"{width},{height}".encode('utf-8')
        encrypted_data = iv + len(size_data).to_bytes(4, 'big') + size_data + encrypted_bytes

        encrypted_file = io.BytesIO(encrypted_data)
        encrypted_file.name = "encrypted_image.bin"
        return send_file(
            encrypted_file,
            as_attachment=True,
            download_name="encrypted_image.bin",
            mimetype="application/octet-stream"
        )
    except Exception as e:
        import traceback
        print(f"Nieoczekiwany błąd podczas szyfrowania: {traceback.format_exc()}")
        return jsonify({'error': 'Nieoczekiwany błąd podczas szyfrowania obrazu'}), 500


@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Brak pliku z zaszyfrowanym obrazem'}), 400

        encrypted_file = request.files['image']
        encrypted_data = encrypted_file.read()

        try:
            iv = encrypted_data[:AES.block_size]
            encrypted_data = encrypted_data[AES.block_size:]
            size_length = int.from_bytes(encrypted_data[:4], 'big')
            encrypted_data = encrypted_data[4:]
            size_data = encrypted_data[:size_length].decode('utf-8')
            encrypted_data = encrypted_data[size_length:]
            width, height = map(int, size_data.split(','))
        except Exception as e:
            print(f"Błąd podczas odczytu metadanych: {e}")
            return jsonify({'error': 'Nieprawidłowy format zaszyfrowanego pliku'}), 400

        try:
            cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        except Exception as e:
            print(f"Błąd podczas deszyfrowania: {e}")
            return jsonify({'error': 'Błąd podczas deszyfrowania danych obrazu'}), 500

        try:
            image_array = np.frombuffer(decrypted_bytes, dtype=np.uint8).reshape((height, width, 3))
            image = Image.fromarray(image_array, 'RGB')
            output = io.BytesIO()
            image.save(output, format='JPEG')
            output.seek(0)
            output.name = "decrypted_image.jpg"
            return send_file(
                output,
                as_attachment=True,
                download_name="decrypted_image.jpg",
                mimetype="image/jpeg"
            )
        except Exception as e:
            print(f"Błąd podczas przetwarzania obrazu: {e}")
            return jsonify({'error': 'Błąd podczas przetwarzania odszyfrowanego obrazu'}), 500

    except Exception as e:
        import traceback
        print(f"Nieoczekiwany błąd podczas deszyfrowania: {traceback.format_exc()}")
        return jsonify({'error': 'Nieoczekiwany błąd podczas deszyfrowania obrazu'}), 500



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, ssl_context=('path/to/cert.pem', 'path/to/key.pem')) #ścieżki do certyfikatu i klucza
