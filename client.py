import requests
import os

# Ścieżka do certyfikatu serwera SSL
SSL_CERT_PATH = 'path/to/cert.pem'

def get_downloads_path():
    "Zwraca ścieżkę do folderu Pobrane użytkownika."
    return os.path.join(os.path.expanduser("~"), "Downloads")


def send_image_for_encryption(image_path):
    "Szyfrowanie obrazu i zapis do systemowego folderu Pobrane."
    downloads_path = get_downloads_path()

    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post('https://localhost:5000/encrypt', files=files, verify=SSL_CERT_PATH)

        if response.status_code == 200:
            encrypted_file_path = os.path.join(downloads_path, 'encrypted_image.bin')
            with open(encrypted_file_path, 'wb') as f:
                f.write(response.content)
            print(f"Zaszyfrowany obraz zapisany w: {encrypted_file_path}")
        else:
            print(f"Błąd podczas szyfrowania: {response.status_code}, {response.text}")
    except FileNotFoundError:
        print(f"Błąd: Plik {image_path} nie istnieje.")
    except requests.RequestException as e:
        print(f"Błąd połączenia: {e}")


def send_image_for_decryption(encrypted_image_path):
    downloads_path = get_downloads_path()

    try:
        with open(encrypted_image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post('https://localhost:5000/decrypt', files=files, verify=SSL_CERT_PATH)

        if response.status_code == 200:
            decrypted_file_path = os.path.join(downloads_path, 'decrypted_image.jpg')
            with open(decrypted_file_path, 'wb') as f:
                f.write(response.content)
            print(f"Odszyfrowany obraz zapisany w: {decrypted_file_path}")
        else:
            print(f"Błąd podczas deszyfrowania: {response.status_code}, {response.text}")
    except FileNotFoundError:
        print(f"Błąd: Plik {encrypted_image_path} nie istnieje.")
    except requests.RequestException as e:
        print(f"Błąd połączenia: {e}")


def main():
    "Interfejs klienta"
    while True:
        print("\nWybierz akcję:")
        print("1. Szyfrowanie obrazu")
        print("2. Deszyfrowanie obrazu")
        print("3. Wyjście")
        choice = input("Podaj opcję (1, 2 lub 3): ").strip()

        if choice == "1":
            image_path = input("Podaj ścieżkę do obrazu, który chcesz zaszyfrować: ").strip()
            if os.path.exists(image_path):
                send_image_for_encryption(image_path)
            else:
                print("Błąd: Podana ścieżka do pliku jest nieprawidłowa.")
        elif choice == "2":
            encrypted_image_path = input("Podaj ścieżkę do zaszyfrowanego obrazu: ").strip()
            if os.path.exists(encrypted_image_path):
                send_image_for_decryption(encrypted_image_path)
            else:
                print("Błąd: Podana ścieżka do pliku jest nieprawidłowa.")
        elif choice == "3":
            print("Kończenie programu.")
            break
        else:
            print("Nieprawidłowa opcja. Wybierz 1, 2 lub 3.")


if __name__ == "__main__":
    main()
