import pygame
import cv2
import mediapipe as mp
import random
import time
import math

# Başlangıç ayarları
pygame.init()
width, height = 1280, 720  # Increase screen resolution
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Parmak Takibi Oyunu")

# Renk tanımları
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# MediaPipe el tanımlama
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Kamera açma
cap = cv2.VideoCapture(0)

# Oyun değişkenleri
score = 0
missed = 0
speed = 1.5
target_spawn_time = 2.5  # Başlangıçta daha seyrek
target_last_spawn = time.time()
targets = []

# Hedeflerin özellikleri
class Target:
    def __init__(self, color, value, is_missable):
        self.color = color
        self.value = value
        self.is_missable = is_missable
        self.size = 30
        self.x = random.randint(0, width - self.size)
        self.y = random.randint(-height, 0)  # Üstten aşağıya düşmeye başlasın
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self):
        self.y += speed
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def is_off_screen(self):
        return self.y > height

    def center(self):
        # Hedefin merkez noktasını döndürür
        return (self.x + self.size // 2, self.y + self.size // 2)


def spawn_target():
    color, value, is_missable = random.choices(
        [(GREEN, 1, True), (RED, -1, False), (BLUE, 5, True)],
        weights=[9, 3, 2],  # Yeşil hedefler daha sık çıkacak
        k=1
    )[0]
    targets.append(Target(color, value, is_missable))


# İşaret parmağı ucu ile hedef arasındaki mesafeyi kontrol et
def is_touching(finger_pos, target_center, threshold=30):  # Adjust threshold for more forgiving touch
    dist = math.hypot(finger_pos[0] - target_center[0], finger_pos[1] - target_center[1])
    return dist < threshold


# Oyun döngüsü
running = True
while running:
    screen.fill(WHITE)
    ret, frame = cap.read()
    if not ret:
        break

    # Mediapipe işlemleri
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Tüm parmak uçlarını bul
    finger_tips = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Add each fingertip to the list
            for fingertip in [mp_hands.HandLandmark.INDEX_FINGER_TIP,
                              mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                              mp_hands.HandLandmark.RING_FINGER_TIP,
                              mp_hands.HandLandmark.PINKY_TIP,
                              mp_hands.HandLandmark.THUMB_TIP]:
                x = int(hand_landmarks.landmark[fingertip].x * width)
                y = int(hand_landmarks.landmark[fingertip].y * height)
                finger_tips.append((x, y))
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Kamerayı pygame ekranına uygun hale getirip çizin
    frame = cv2.resize(frame, (width, height))
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)  # Rotate the camera feed counterclockwise
    frame = cv2.flip(frame, 1)  # Apply mirror effect after rotation
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame)
    screen.blit(frame_surface, (0, 0))  # Kamera görüntüsünü önce çizin

    # Hedefleri güncelle ve çarpışma kontrolü yap
    for target in targets[:]:
        target.move()
        pygame.draw.rect(screen, target.color, target.rect)  # Kamera üzerinde hedefleri çizin

        # Her hedefe tüm parmaklarla dokunma kontrolü
        for finger_pos in finger_tips:
            if is_touching(finger_pos, target.center()):
                score += target.value
                targets.remove(target)  # Çarpışma durumunda hedefi kaldır
                if score < 0:
                    score = 0
                break

        # Kaçırma durumunu sadece yeşil ve mavi hedefler için sayıyoruz
        if target.is_off_screen():
            if target.is_missable:
                missed += 1
            targets.remove(target)

    # Puanı ve kaçırılan hedef sayısını güncelle
    if missed >= 5:
        running = False
    elif time.time() - target_last_spawn > target_spawn_time:
        spawn_target()
        target_last_spawn = time.time()

    # Oyun hızını artır, ancak nokta çıkma sıklığını azalt
    if score > 0 and score % 10 == 0:
        speed += 0.1
        target_spawn_time = min(3.5, target_spawn_time + 0.2)  # Spawn süresini artırarak hedef sıklığını azalt

    # Puan ve kaçırılanları göster
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Puan: {score}", True, (255,255,255))
    missed_text = font.render(f"Kaçırılan: {missed}/5", True, (255,255,255))
    screen.blit(score_text, (10, 10))  # Kamera üzerinde skor ve kaçırılan sayısını çizin
    screen.blit(missed_text, (10, 50))

    pygame.display.flip()

    # Çıkış kontrolü
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

cap.release()
pygame.quit()
