const colors = ["green", "teal", "gold", "darkgreen"];

let sequence = [];
let userSequence = [];
let isUserTurn = false;
let level = 0;

const message = document.getElementById("message");
const startBtn = document.getElementById("startBtn");
const buttons = document.querySelectorAll(".color-btn");
const levelCount = document.getElementById("levelCount");
const themeToggle = document.getElementById("themeToggle");
const levelPopup = document.getElementById("levelPopup");

startBtn.addEventListener("click", startGame);

buttons.forEach(btn => {
  btn.addEventListener("click", () => {
    if (!isUserTurn) return;
    handleUser(btn.dataset.color);
  });
});

function startGame() {
  sequence = [];
  userSequence = [];
  level = 0;
  levelCount.innerText = 0;
  message.innerText = "Watch carefully 👀";
  nextRound();
}

function nextRound() {
  isUserTurn = false;
  userSequence = [];
  level++;
  levelCount.innerText = level;

  showLevelPopup(level);
  launchConfetti();

  const randomColor = colors[Math.floor(Math.random() * colors.length)];
  sequence.push(randomColor);

  setTimeout(playSequence, 800);
}

function playSequence() {
  let index = 0;

  const interval = setInterval(() => {
    blink(sequence[index]);
    index++;

    if (index >= sequence.length) {
      clearInterval(interval);
      isUserTurn = true;
      message.innerText = "Your turn 🎯";
    }
  }, 700);
}

function blink(color) {
  const btn = document.querySelector(`[data-color="${color}"]`);
  btn.classList.add("blink");
  setTimeout(() => btn.classList.remove("blink"), 400);
}

function handleUser(color) {
  userSequence.push(color);
  blink(color);

  const currentIndex = userSequence.length - 1;

  if (userSequence[currentIndex] !== sequence[currentIndex]) {
    message.innerText = "❌ Game Over! Press Start";
    isUserTurn = false;
    return;
  }

  if (userSequence.length === sequence.length) {
    message.innerText = "✅ Correct!";
    setTimeout(nextRound, 1000);
  }
}

function showLevelPopup(level) {
  levelPopup.innerText = `LEVEL ${level}`;
  levelPopup.classList.add("show");

  setTimeout(() => {
    levelPopup.classList.remove("show");
  }, 800);
}

function launchConfetti() {
  const confColors = ["#4caf50", "#00897b", "#d4af37", "#1b5e20"];

  for (let i = 0; i < 40; i++) {
    const confetti = document.createElement("div");
    confetti.classList.add("confetti");

    confetti.style.left = Math.random() * 100 + "vw";
    confetti.style.background =
      confColors[Math.floor(Math.random() * confColors.length)];

    confetti.style.animationDuration =
      Math.random() * 1 + 1 + "s";

    document.body.appendChild(confetti);

    setTimeout(() => confetti.remove(), 2000);
  }
}

themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  themeToggle.textContent =
    document.body.classList.contains("dark") ? "☀️" : "🌙";
});
