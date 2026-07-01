const $ = (s) => document.querySelector(s);
let difficulty = "medium";
let currentGame = null;
let soundOn = true;

const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const keyboard = $("#keyboard");
alphabet.forEach(letter => {
  const button = document.createElement("button");
  button.textContent = letter;
  button.dataset.letter = letter.toLowerCase();
  button.addEventListener("click", () => makeGuess(button.dataset.letter));
  keyboard.appendChild(button);
});

document.querySelectorAll(".difficulty").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll(".difficulty").forEach(b => b.classList.remove("active"));
  button.classList.add("active");
  difficulty = button.dataset.level;
}));

function showOnly(id) {
  ["setup", "game", "result"].forEach(name => $("#" + name).classList.toggle("hidden", name !== id));
}

function toast(text, error = false) {
  const el = $("#toast");
  el.textContent = text;
  el.className = `toast show ${error ? "error" : ""}`;
  setTimeout(() => el.classList.remove("show"), 2200);
}

function ping(frequency = 520, duration = .07) {
  if (!soundOn) return;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.frequency.value = frequency;
  gain.gain.setValueAtTime(.055, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(.001, ctx.currentTime + duration);
  oscillator.connect(gain).connect(ctx.destination);
  oscillator.start(); oscillator.stop(ctx.currentTime + duration);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

async function startGame() {
  const player = $("#playerName").value.trim() || "Explorer";
  $("#startBtn").disabled = true;
  try {
    currentGame = await api("/api/start", {
      method: "POST", body: JSON.stringify({player, difficulty})
    });
    $("#navName").textContent = player;
    $("#avatar").textContent = player[0].toUpperCase();
    showOnly("game");
    $("#stats").classList.add("hidden");
    render(currentGame);
    ping(650, .12);
  } catch (e) { toast(e.message, true); }
  finally { $("#startBtn").disabled = false; }
}

function render(data) {
  currentGame = data;
  $("#levelBadge").textContent = data.difficulty.toUpperCase();
  $("#levelBadge").className = `level-badge ${data.difficulty}`;
  $("#category").textContent = data.category.toUpperCase();
  $("#score").textContent = data.score;
  $("#hint").textContent = data.hint;
  $("#attemptText").textContent = `${data.attemptsLeft} / ${data.maxAttempts}`;
  $("#attemptBar").style.width = `${data.attemptsLeft / data.maxAttempts * 100}%`;
  $("#attemptBar").classList.toggle("danger", data.attemptsLeft <= 2);
  $("#message").textContent = data.message;

  $("#wordSlots").innerHTML = data.masked.map((letter, i) =>
    `<span class="${letter ? "revealed" : ""}" style="animation-delay:${i * 35}ms">${letter.toUpperCase() || "?"}</span>`
  ).join("");
  keyboard.querySelectorAll("button").forEach(button => {
    const letter = button.dataset.letter;
    button.disabled = data.guessed.includes(letter);
    button.className = data.wrongLetters.includes(letter) ? "wrong" :
      data.guessed.includes(letter) ? "correct" : "";
  });
  if (data.status !== "playing") finish(data);
}

async function makeGuess(letter) {
  try {
    const before = currentGame?.attemptsLeft;
    const data = await api("/api/guess", {method: "POST", body: JSON.stringify({letter})});
    ping(data.attemptsLeft < before ? 220 : 620);
    render(data);
  } catch (e) { toast(e.message, true); }
}

async function revealLetter() {
  try { render(await api("/api/reveal", {method: "POST", body: "{}"})); ping(760, .15); }
  catch (e) { toast(e.message, true); }
}

function finish(data) {
  setTimeout(() => {
    const won = data.status === "won";
    $("#resultIcon").textContent = won ? "🏆" : "🌤️";
    $("#resultLabel").textContent = won ? "QUEST COMPLETE" : "KEEP EXPLORING";
    $("#resultTitle").textContent = won ? "Brilliant work!" : "So close!";
    $("#resultMessage").textContent = data.message;
    $("#resultScore").textContent = data.score;
    $("#result").classList.toggle("lost", !won);
    showOnly("result");
    if (won) confetti();
  }, 700);
}

function confetti() {
  const colors = ["#6c5ce7", "#ffb84d", "#28c9a6", "#ff6b8a"];
  for (let i = 0; i < 55; i++) {
    const bit = document.createElement("i");
    bit.className = "confetti";
    bit.style.cssText = `left:${Math.random()*100}%;background:${colors[i%4]};animation-delay:${Math.random()*.4}s;transform:rotate(${Math.random()*180}deg)`;
    document.body.appendChild(bit);
    setTimeout(() => bit.remove(), 2600);
  }
}

async function showStats() {
  try {
    const data = await api("/api/stats");
    $("#gamesStat").textContent = data.games;
    $("#winsStat").textContent = data.wins;
    $("#bestStat").textContent = data.best_score;
    $("#rateStat").textContent = data.games ? `${Math.round(data.wins / data.games * 100)}%` : "0%";
    $("#recentList").innerHTML = data.recent.length ? data.recent.map(item => `
      <div class="recent-row"><span class="result-dot ${item.won ? "win" : ""}">${item.won ? "✓" : "×"}</span>
      <div><strong>${item.word.toUpperCase()}</strong><small>${item.difficulty} quest</small></div>
      <b>${item.score} pts</b></div>`).join("") : `<p class="empty">Your completed quests will appear here.</p>`;
    $("#stats").classList.remove("hidden");
    $("#stats").scrollIntoView({behavior: "smooth"});
  } catch(e) { toast(e.message, true); }
}

$("#startBtn").addEventListener("click", startGame);
$("#playerName").addEventListener("keydown", e => { if (e.key === "Enter") startGame(); });
$("#revealBtn").addEventListener("click", revealLetter);
$("#newBtn").addEventListener("click", () => showOnly("setup"));
$("#playAgainBtn").addEventListener("click", () => showOnly("setup"));
$("#statsBtn").addEventListener("click", showStats);
$("#profileBtn").addEventListener("click", showStats);
$("#closeStats").addEventListener("click", () => $("#stats").classList.add("hidden"));
$("#soundBtn").addEventListener("click", e => {
  soundOn = !soundOn; e.currentTarget.textContent = soundOn ? "🔊" : "🔇";
});
document.addEventListener("keydown", e => {
  if (!$("#game").classList.contains("hidden") && /^[a-z]$/i.test(e.key)) makeGuess(e.key.toLowerCase());
});
