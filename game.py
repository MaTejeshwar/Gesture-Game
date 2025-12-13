import cv2
import mediapipe as mp
import random
from collections import deque
import math
import time

# ---------------- Parameters ----------------
WIDTH, HEIGHT = 640, 480
CELL = 20

# ---------------- Mediapipe Hand Detection ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# ---------------- Distance Function ----------------
def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

# ---------------- Player Snake ----------------
player_snake = deque()
player_snake_length = 20
player_x, player_y = WIDTH // 2, HEIGHT // 2

# ---------------- AI Snake ----------------
ai_snake = deque()
ai_snake_length = 20
ai_x, ai_y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)

# ---------------- Food ----------------
def spawn_food():
    return random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)

food_x, food_y = spawn_food()

# ---------------- Scores ----------------
player_score = 0
ai_score = 0

# ---------------- Pause Flag ----------------
pause = False

# ---------------- AI Chat ----------------
ai_messages = ["I'm coming!", "Got the food!", "Catch me if you can!", "Yummy!", "Too slow!"]
ai_chat = ""
chat_display_time = 0

# ---------------- Capture ----------------
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

print("Game started! Move your index finger to control the snake.")
print("Full palm to PAUSE. Press 'r' to RESTART, 'q' to QUIT.")

# ---------------- Game Loop ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    finger_found = False
    full_palm = False

    # ---------------- Player Snake Movement ----------------
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Coordinates
            x = int(hand_landmarks.landmark[8].x * WIDTH)
            y = int(hand_landmarks.landmark[8].y * HEIGHT)
            finger_found = True

            # Detect full palm (all fingers extended)
            fingers = []
            for tip in [8, 12, 16, 20]:
                if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip-2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
            if all(fingers):
                full_palm = True

            # Move player snake only if not paused
            if not pause:
                player_x += (x - player_x) * 0.2
                player_y += (y - player_y) * 0.2

    # ---------------- Pause ----------------
    if full_palm:
        pause = True
        cv2.putText(frame, "PAUSED", (WIDTH//2 - 80, HEIGHT//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
    else:
        pause = False

    if not finger_found or pause:
        player_x = player_x
        player_y = player_y

    # ---------------- Update Player Snake ----------------
    if not pause:
        player_snake.append((player_x, player_y))
        if len(player_snake) > player_snake_length:
            player_snake.popleft()

    # ---------------- AI Snake Movement ----------------
    if not pause:
        dx = food_x - ai_x
        dy = food_y - ai_y
        if abs(dx) > abs(dy):
            ai_direction = (CELL if dx > 0 else -CELL, 0)
        else:
            ai_direction = (0, CELL if dy > 0 else -CELL)
        ai_x += ai_direction[0]*0.1
        ai_y += ai_direction[1]*0.1

        ai_snake.append((ai_x, ai_y))
        if len(ai_snake) > ai_snake_length:
            ai_snake.popleft()

    # ---------------- Food Collision ----------------
    # Player eats food
    if dist(player_x, player_y, food_x, food_y) < CELL:
        player_score += 1
        player_snake_length += 5
        food_x, food_y = spawn_food()

    # AI eats food
    if dist(ai_x, ai_y, food_x, food_y) < CELL:
        ai_score += 1
        ai_snake_length += 5
        food_x, food_y = spawn_food()
        # Show a random AI chat when it eats
        ai_chat = random.choice(ai_messages)
        chat_display_time = time.time()

    # ---------------- Player Self-Collision ----------------
    if len(player_snake) > 30:
        head = player_snake[-1]
        for segment in list(player_snake)[:-20]:
            if dist(head[0], head[1], segment[0], segment[1]) < 10:
                cv2.putText(frame, "GAME OVER", (180, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                cv2.putText(frame, f"Score: {player_score}", (200, 300),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
                cv2.imshow("Snake Gesture Game", frame)
                cv2.waitKey(3000)
                player_snake.clear()
                player_snake_length = 20
                player_x, player_y = WIDTH // 2, HEIGHT // 2
                ai_snake.clear()
                ai_snake_length = 20
                ai_x, ai_y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)
                food_x, food_y = spawn_food()
                player_score = 0
                ai_score = 0

    # ---------------- Draw Food ----------------
    cv2.circle(frame, (food_x, food_y), CELL//2, (0, 255, 0), -1)

    # ---------------- Draw Player Snake ----------------
    for segment in player_snake:
        cv2.circle(frame, (int(segment[0]), int(segment[1])), 8, (255, 255, 255), -1)

    # ---------------- Draw AI Snake ----------------
    for segment in ai_snake:
        cv2.circle(frame, (int(segment[0]), int(segment[1])), 8, (0, 0, 255), -1)

    # ---------------- Draw Scores ----------------
    cv2.putText(frame, f"Player: {player_score}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
    cv2.putText(frame, f"AI: {ai_score}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # ---------------- Draw AI Chat ----------------
    if ai_chat and time.time() - chat_display_time < 2:  # display for 2 seconds
        cv2.putText(frame, f"AI: {ai_chat}", (WIDTH - 350, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        ai_chat = ""

    # ---------------- Key Handling ----------------
    key = cv2.waitKey(30) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        # Restart game
        player_snake.clear()
        player_snake_length = 20
        player_x, player_y = WIDTH // 2, HEIGHT // 2
        ai_snake.clear()
        ai_snake_length = 20
        ai_x, ai_y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)
        food_x, food_y = spawn_food()
        player_score = 0
        ai_score = 0
        pause = False

    # ---------------- Display ----------------
    cv2.imshow("Snake Gesture Game", frame)

cap.release()
cv2.destroyAllWindows()
