const grid = document.getElementById("grid");
const scoreDisplay = document.getElementById("score");
const highScoreDisplay = document.getElementById("highScore");

let board = Array(16).fill(0);
let score = 0;
let currentLevel = 0;

let highScore = localStorage.getItem("highScore") || 0;
highScoreDisplay.textContent = "High Score: " + highScore;

function createBoard() {
    grid.innerHTML = "";

    board.forEach(value => {
        const cell = document.createElement("div");
        cell.className = "cell";

        if (value !== 0) {
            cell.textContent = value;
            cell.setAttribute("data-value", value);
        }

        grid.appendChild(cell);
    });

    checkLevel();
}

function addNumber() {
    let empty = board.map((v, i) => v === 0 ? i : null).filter(v => v !== null);
    if (empty.length === 0) return;
    const index = empty[Math.floor(Math.random() * empty.length)];
    board[index] = Math.random() < 0.9 ? 2 : 4;
}

function updateScore() {
    scoreDisplay.textContent = "Score: " + score;

    if (score > highScore) {
        highScore = score;
        localStorage.setItem("highScore", highScore);
        highScoreDisplay.textContent = "High Score: " + highScore;
    }
}

function move(direction) {
    let moved = false;

    for (let i = 0; i < 4; i++) {
        let row = [];

        for (let j = 0; j < 4; j++) {
            let index = direction === "left" || direction === "right"
                ? i * 4 + j
                : j * 4 + i;
            row.push(board[index]);
        }

        if (direction === "right" || direction === "down") row.reverse();

        let filtered = row.filter(v => v !== 0);

        for (let k = 0; k < filtered.length - 1; k++) {
            if (filtered[k] === filtered[k + 1]) {
                filtered[k] *= 2;
                score += filtered[k];
                filtered[k + 1] = 0;
                moved = true;
            }
        }

        filtered = filtered.filter(v => v !== 0);
        while (filtered.length < 4) filtered.push(0);

        if (direction === "right" || direction === "down") filtered.reverse();

        for (let j = 0; j < 4; j++) {
            let index = direction === "left" || direction === "right"
                ? i * 4 + j
                : j * 4 + i;

            if (board[index] !== filtered[j]) moved = true;
            board[index] = filtered[j];
        }
    }

    if (moved) {
        addNumber();
        createBoard();
        updateScore();
    }
}

function checkLevel() {
    const maxTile = Math.max(...board);

    const levels = {128:1,256:2,512:3,1024:4,2048:5};

    if (levels[maxTile] && levels[maxTile] > currentLevel) {
        currentLevel = levels[maxTile];
        showLevel(currentLevel);
    }
}

function showLevel(level) {
    const popup = document.getElementById("levelPopup");
    popup.innerText = "LEVEL " + level;
    popup.style.display = "block";

    setTimeout(() => popup.style.display = "none", 2000);

    confetti({
        particleCount: 200,
        spread: 120,
        origin: { y: 0.6 }
    });
}

function restartGame() {
    board = Array(16).fill(0);
    score = 0;
    currentLevel = 0;
    updateScore();
    addNumber();
    addNumber();
    createBoard();
}

function toggleDarkMode() {
    document.body.classList.toggle("dark");
}

document.addEventListener("keydown", e => {
    if (e.key === "ArrowLeft") move("left");
    if (e.key === "ArrowRight") move("right");
    if (e.key === "ArrowUp") move("up");
    if (e.key === "ArrowDown") move("down");
});

restartGame();
