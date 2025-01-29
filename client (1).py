import tkinter as tk
from tkinter import messagebox
import threading
import requests
import random
import pygame
import sys

class FlappyBird:
    def __init__(self, token):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 708))
        self.token = token
        self.bird = pygame.Rect(65, 50, 50, 50)
        self.background = pygame.image.load("assets/background.png").convert()
        self.birdSprites = [pygame.image.load("assets/1.png").convert_alpha(),
                            pygame.image.load("assets/2.png").convert_alpha()]
        self.wallUp = pygame.image.load("assets/bottom.png").convert_alpha()
        self.wallDown = pygame.image.load("assets/top.png").convert_alpha()
        self.gap = 130
        self.wallx = 400
        self.birdY = 350
        self.dead = False
        self.counter = 0
        self.offset = random.randint(-110, 110)

    def game_loop(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 50)

        while not self.dead:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.birdY -= 50
            self.birdY += 5

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(self.wallUp, (self.wallx, 300 + self.gap - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gap - self.offset))
            self.screen.blit(self.birdSprites[0], (70, self.birdY))
            pygame.display.update()
            clock.tick(30)

    def run(self):
        self.game_loop()

class AuthApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Авторизация")
        self.token = None

        tk.Label(self.root, text="Логин").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Пароль").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Войти", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Регистрация", command=self.open_registration).pack(pady=5)
        tk.Button(self.root, text="Закрыть", command=self.root.quit).pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post("http://127.0.0.1:8001/login", json={"username": username, "password": password})
            response.raise_for_status()
            self.token = response.json().get("token")
            messagebox.showinfo("Успех", "Вы вошли в систему!")
            self.root.destroy()
            self.start_game()
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка входа: {e}")

    def open_registration(self):
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Регистрация")

        tk.Label(reg_window, text="Логин").pack(pady=5)
        username_entry = tk.Entry(reg_window)
        username_entry.pack(pady=5)

        tk.Label(reg_window, text="Пароль").pack(pady=5)
        password_entry = tk.Entry(reg_window, show="*")
        password_entry.pack(pady=5)

        tk.Label(reg_window, text="Подтверждение пароля").pack(pady=5)
        confirm_password_entry = tk.Entry(reg_window, show="*")
        confirm_password_entry.pack(pady=5)

        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()

            if password != confirm_password:
                messagebox.showerror("Ошибка", "Пароли не совпадают!")
                return

            try:
                response = requests.post("http://127.0.0.1:8001/register", json={"username": username, "password": password})
                response.raise_for_status()
                messagebox.showinfo("Успех", "Регистрация успешна! Теперь вы можете войти.")
                reg_window.destroy()
            except requests.RequestException as e:
                messagebox.showerror("Ошибка", f"Ошибка регистрации: {e}")

        tk.Button(reg_window, text="Зарегистрироваться", command=register).pack(pady=5)

    def start_game(self):
        game = FlappyBird(self.token)
        threading.Thread(target=game.run).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuthApp()
    app.run()
