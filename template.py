"""
Anki template definitions for Sub2Anki.

This module contains the HTML templates, CSS styling, and model configuration
for creating interactive dictation flashcards in Anki.
"""

import random
import genanki

# --- Custom Anki Template ---
# Front template with interactive dictation features
CUSTOM_FRONT_TEMPLATE = r"""
<div class="card-header">Dictation Practice</div>

<br />
<div>
  <audio
    id="audio-{{UUID}}"
    src="{{AudioRaw}}"
    controls="controls"
    autoplay="autoplay"
  ></audio>
</div>
<div class="btnarea">
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(0.5)"
  >
    0.5x
  </button>
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(0.75)"
  >
    0.75x
  </button>
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(1.0)"
  >
    Normal
  </button>
  <button type="button" class="btn" onclick="cardHandlers['{{UUID}}'].toggleLoop(this)">
    Loop
  </button>
</div>

<div id="feedback-display-{{UUID}}" class="feedback-container"></div>

<textarea
  class="user-input"
  id="user-input-{{UUID}}"
  rows="3"
  placeholder="Type what you hear, use # for a hint..."
  oninput="cardHandlers['{{UUID}}'].checkTyping()"
  autocomplete="off"
  autocorrect="off"
  autocapitalize="off"
  spellcheck="false"
></textarea>

<div id="hint-area-{{UUID}}" class="hint-container" style="display: none">
  <div id="hint-content-{{UUID}}"></div>
</div>

<div id="correct-answer-{{UUID}}" style="display: none">{{Sentence}}</div>

<script>
  // Create a global object to hold handlers for each card, preventing conflicts.
  window.cardHandlers = window.cardHandlers || {};

  // Use an immediately-invoked function expression (IIFE) to create a private scope.
  (function () {
    const cardId = "{{UUID}}";

    // --- 1. Element Hooks ---
    const userInput = document.getElementById("user-input-" + cardId);
    const correctAnswerDiv = document.getElementById(
      "correct-answer-" + cardId,
    );
    const feedbackDisplay = document.getElementById(
      "feedback-display-" + cardId,
    );
    const hintArea = document.getElementById("hint-area-" + cardId);
    const hintContent = document.getElementById("hint-content-" + cardId);
    const audioPlayer = document.getElementById("audio-" + cardId);

    if (!userInput) return; // Stop if elements aren't found for this card

    // --- 2. Data Initialization ---
    const correctAnswer = correctAnswerDiv.textContent.trim();
    const correctWords = correctAnswer.split(/\s+/);
    let placeholderIndices = [];
    let mistakes = {}; // Object to store mistakes {correct: [incorrect1, incorrect2, ...]}
    let hintUsed = {}; // Object to track which words were filled using hints

    // --- 3. Core Functions ---
    userInput.focus(); // Auto-focus the input field

    function displayInitialHint() {
      hintContent.innerHTML = ""; // Clear previous hints
      correctWords.forEach((word, index) => {
        const hintSpan = document.createElement("span");
        hintSpan.id = `hint-word-${index}-${cardId}`;
        hintSpan.textContent = word[0] + "_".repeat(word.length - 1);
        hintContent.appendChild(hintSpan);
        hintContent.appendChild(document.createTextNode(" "));
      });
      hintArea.style.display = "block";
      updateHintHighlight(0);
    }

    function updateHintHighlight(currentIndex) {
      correctWords.forEach((word, index) => {
        document
          .getElementById(`hint-word-${index}-${cardId}`)
          ?.classList.remove("current-hint");
      });
      const currentHintEl = document.getElementById(
        `hint-word-${currentIndex}-${cardId}`,
      );
      if (currentHintEl) {
        currentHintEl.classList.add("current-hint");
      }
    }
    
    // Define the handlers for this specific card
    cardHandlers[cardId] = {
      checkTyping: function () {
        // Hint logic
        if (userInput.value.slice(-1) === "#") {
          userInput.value = userInput.value.slice(0, -1); // Remove '#'
          const typedWordsBeforeHint = userInput.value.trim().replace(/\s+/g, " ").split(" ");
          const nextWordIndex = typedWordsBeforeHint[0] === "" ? 0 : typedWordsBeforeHint.length;

          if (nextWordIndex < correctWords.length) {
            const wordToReveal = correctWords[nextWordIndex];
            if (!placeholderIndices.includes(nextWordIndex)) {
              placeholderIndices.push(nextWordIndex);
              // Mark this word as filled using hint
              hintUsed[nextWordIndex] = true;
            }
            userInput.value += (userInput.value.endsWith(" ") || userInput.value === "" ? "" : " ") + wordToReveal + " ";
          }
        }

        const rawInput = userInput.value;
        const endsWithSpace = rawInput.endsWith(' ') || rawInput.endsWith('\n');
        const typedWords = rawInput.trim().split(/\s+/);

        let feedbackHTML = "";
        let completedWords = typedWords;
        let currentWordFragment = "";

        if (!endsWithSpace && rawInput.trim() !== "") {
          currentWordFragment = completedWords.pop();
        }

        completedWords.forEach((word, i) => {
          if (word === "") return;
          let feedbackWord = word + " ";
          let classes = [];
          let isCorrect = false;

          if (i < correctWords.length) {
            const correctWord = correctWords[i];
            if (word.toLowerCase().replace(/[.,!?"]$/, "") === correctWord.toLowerCase().replace(/[.,!?"]$/, "")) {
              classes.push("correct");
              isCorrect = true;
              // Do NOT delete mistakes when user corrects - keep all historical incorrect attempts
            } else {
              classes.push("incorrect");
            }
            // Store all incorrect attempts for each word position
            if (!isCorrect && !placeholderIndices.includes(i)) {
              if (!mistakes[correctWord]) mistakes[correctWord] = [];
              // Only add unique mistakes
              if (!mistakes[correctWord].includes(word)) {
                mistakes[correctWord].push(word);
              }
            }
            // Also track words filled using hints
            if (hintUsed[i] && !mistakes[correctWord]) {
              mistakes[correctWord] = ["#"]; // Use # to indicate hint was used
            }
          } else {
            classes.push("incorrect");
          }

          if (placeholderIndices.includes(i)) {
            classes.push("placeholder-word");
          }
          feedbackHTML += `<span class="${classes.join(" ")}">${feedbackWord}</span>`;
        });

        feedbackHTML += currentWordFragment;
        feedbackDisplay.innerHTML = feedbackHTML;
        updateHintHighlight(completedWords.length);
        
        // Save state to session storage for the back of the card
        window.sessionStorage.setItem('mistakes-' + cardId, JSON.stringify(mistakes));
        window.sessionStorage.setItem('typedWordCount-' + cardId, completedWords.length);
      },

      setPlaySpeed: function (speed) {
        if (audioPlayer) {
          audioPlayer.playbackRate = speed;
          audioPlayer.play();
        }
      },

      toggleLoop: function (button) {
        if (audioPlayer) {
          audioPlayer.loop = !audioPlayer.loop;
          button.style.backgroundColor = audioPlayer.loop ? "#a5d6a7" : "";
          if (audioPlayer.paused) audioPlayer.play();
        }
      }
    };

    displayInitialHint();

    // --- 4. Event Listeners ---
    userInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        pycmd("ans");
      }
    });

    // Default to loop enabled
    if (audioPlayer) {
      audioPlayer.loop = true;
      const loopButton = Array.from(document.querySelectorAll(".btn")).find(
        (btn) => btn.textContent === "Loop" && btn.onclick.toString().includes(cardId)
      );
      if (loopButton) {
        loopButton.style.backgroundColor = "#a5d6a7";
      }
    }
  })();
</script>
"""


# Back template showing answer with mistake analysis
CUSTOM_BACK_TEMPLATE = r"""
<div class="card-header">Answer</div>

<br />
<div>
  <audio
    id="audio-{{UUID}}"
    src="{{AudioRaw}}"
    controls="controls"
    autoplay="autoplay"
  ></audio>
</div>
<div class="btnarea">
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(0.5)"
  >
    0.5x
  </button>
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(0.75)"
  >
    0.75x
  </button>
  <button
    type="button"
    class="btn"
    onclick="cardHandlers['{{UUID}}'].setPlaySpeed(1.0)"
  >
    Normal
  </button>
  <button type="button" class="btn" onclick="cardHandlers['{{UUID}}'].toggleLoop(this)">
    Loop
  </button>
</div>

<hr />

<div class="answer-content">
  <div class="sentence" id="sentence-{{UUID}}">{{Sentence}}</div>
  <div class="meaning">{{Translation}}</div>
</div>

<div id="mistakes-table-container-{{UUID}}"></div>

<script>
  // Create a global object to hold handlers for each card, preventing conflicts.
  window.cardHandlers = window.cardHandlers || {};

  // Redefine functions for the back card to avoid conflicts
  cardHandlers["{{UUID}}"] = {
    setPlaySpeed: function (speed) {
      const audio = document.getElementById("audio-{{UUID}}");
      if (audio) {
        audio.playbackRate = speed;
        audio.play();
      }
    },
    toggleLoop: function (button) {
      const audio = document.getElementById("audio-{{UUID}}");
      if (audio) {
        audio.loop = !audio.loop;
        button.style.backgroundColor = audio.loop ? "#a5d6a7" : "";
        if (audio.paused) audio.play();
      }
    }
  };

  // Render mistakes table and highlight words with mistakes
  (function() {
      const cardId = "{{UUID}}";
      const container = document.getElementById("mistakes-table-container-" + cardId);
      const sentenceEl = document.getElementById("sentence-" + cardId);
      const mistakesJSON = window.sessionStorage.getItem('mistakes-' + cardId);
      
      if (container && mistakesJSON) {
          try {
              const mistakes = JSON.parse(mistakesJSON);
              
              // Highlight words with mistakes in the sentence
              if (sentenceEl && Object.keys(mistakes).length > 0) {
                  const sentenceText = sentenceEl.textContent;
                  const words = sentenceText.split(/\s+/);
                  
                  // Create a map of correct words to their positions
                  const wordPositions = {};
                  words.forEach((word, index) => {
                      // Clean the word for matching (remove punctuation)
                      const cleanWord = word.toLowerCase().replace(/[.,!?";]/g, '');
                      if (!wordPositions[cleanWord]) {
                          wordPositions[cleanWord] = [];
                      }
                      wordPositions[cleanWord].push(index);
                  });
                  
                  // Create array to track which word indices had mistakes
                  const mistakeIndices = new Set();
                  
                  // Find indices of words with mistakes
                  for (const correct in mistakes) {
                      const cleanCorrect = correct.toLowerCase().replace(/[.,!?";]/g, '');
                      if (wordPositions[cleanCorrect]) {
                          wordPositions[cleanCorrect].forEach(index => mistakeIndices.add(index));
                      }
                  }
                  
                  // Rebuild sentence with highlighted words
                  const highlightedWords = words.map((word, index) => {
                      // Clean the word for matching
                      const cleanWord = word.toLowerCase().replace(/[.,!?";]/g, '');
                      if (mistakeIndices.has(index)) {
                          return `<span class="mistake-word">${word}</span>`;
                      }
                      return word;
                  });
                  
                  sentenceEl.innerHTML = highlightedWords.join(' ');
              }
              
              // Render mistakes table
              if (Object.keys(mistakes).length > 0) {
                  let tableHTML = '<div class="mistakes-header">Mistake Review</div>';
              tableHTML += '<table class="mistakes-table">';
              tableHTML += '<tr><th>Target Word</th><th>Your Attempt</th></tr>';
                  for (const correct in mistakes) {
                      // Handle array display: join incorrect words array with commas
                      const incorrectDisplay = Array.isArray(mistakes[correct]) 
                        ? mistakes[correct].join(', ') 
                        : mistakes[correct];
                      tableHTML += `<tr><td>${correct}</td><td class="incorrect-word">${incorrectDisplay}</td></tr>`;
                  }
                  tableHTML += '</table>';
                  container.innerHTML = tableHTML;
              }
          } catch (e) {
              console.error("Could not parse mistakes JSON:", e);
          }
      }
  })();
</script>
"""

# CSS styling for both front and back of cards
CUSTOM_CSS = r"""
.card {
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial,
    sans-serif;
  text-align: center;
  background-color: #f0f2f5;
}

/* --- Front Side Styling (remains similar) --- */
.card-header,
.dash-title {
  background-color: #4a5568;
  color: white;
  padding: 12px;
  font-size: 1em;
  font-weight: 600;
}
.audio-player {
  padding: 20px;
}
.controls button {
  background-color: #4a5568;
  color: white;
  border: none;
  padding: 10px 20px;
  margin: 5px;
  font-size: 0.8em;
  cursor: pointer;
  border-radius: 5px;
  transition: background-color 0.2s;
}
.controls button:hover {
  background-color: #2d3748;
}
.user-input {
  width: 90%;
  min-height: 100px;
  font-synthesis: 1.2em;
  line-height: 1.5;
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  resize: vertical;
}
.feedback-container {
  font-synthesis: 1.3em;
  font-family: "Courier New", Courier, monospace;
  padding: 15px;
  border: 1px dashed #ddd;
  margin: 20px auto;
  width: 90%;
  min-height: 40px;
  line-height: 1.5;
  background-color: white;
  text-align: left;
}
.correct {
  color: #2f855a;
}
.incorrect {
  color: #c53030;
  text-decoration: underline;
  background-color: #fed7d7;
}
.untyped-word {
    color: #c53030;
    text-decoration: underline;
}
.hint-container {
  margin-top: 15px;
  padding: 10px;
  background-color: #fffaf0;
  border: 1px solid #fbd38d;
  color: #b45309;
  border-radius: 5px;
}

/* --- Back Side Styling --- */
.answer-content {
  padding: 15px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin: 20px auto;
  width: 90%;
  text-align: left;
}

.answer-content .sentence {
  font-size: 1.4em;
  font-weight: 500;
  color: #2d3748; /* A dark gray, almost black */
  margin-bottom: 12px;
  line-height: 1.4;
}

.answer-content .meaning {
  font-size: 1.1em;
  color: #718096; /* A lighter gray for the translation */
  border-left: 3px solid #4a5568;
  padding-left: 10px;
}

/* --- Mistakes Table Styling --- */
.mistakes-header {
  font-size: 1.2em;
  font-weight: 600;
  color: #c53030;
  margin-top: 25px;
  margin-bottom: 10px;
  text-align: center;
}

.mistakes-table {
  width: 90%;
  margin: 0 auto 20px auto;
  border-collapse: collapse;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.mistakes-table th, .mistakes-table td {
  border: 1px solid #e2e8f0;
  padding: 10px 12px;
  text-align: center;
}

.mistakes-table th {
  background-color: #4a5568;
  color: white;
  font-weight: 600;
}

.mistakes-table td {
  background-color: #ffffff;
}

.mistakes-table .incorrect-word {
  color: #c53030;
  font-weight: 500;
  background-color: #fed7d7;
}

.mistake-word {
  color: #c53030;
  font-weight: bold;
}
"""


# --- Anki Model Configuration (Shared) ---
# Define the Anki model with fields and templates
MODEL_NAME = "Dictation"
MODEL_ID = random.randrange(1 << 30, 1 << 31)

ANKI_MODEL = genanki.Model(
    model_id=MODEL_ID,
    name=MODEL_NAME,
    fields=[
        {"name": "Audio"},
        {"name": "AudioRaw"},
        {"name": "Sentence"},
        {"name": "Translation"},
        {"name": "UUID"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": CUSTOM_FRONT_TEMPLATE,
            "afmt": CUSTOM_BACK_TEMPLATE,
        },
    ],
    css=CUSTOM_CSS,
)
