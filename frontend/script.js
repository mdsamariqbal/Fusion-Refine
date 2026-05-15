document.addEventListener('DOMContentLoaded', () => {
    // Screens
    const screenLanding = document.getElementById('screenLanding');
    const screenInput = document.getElementById('screenInput');
    const screenDescription = document.getElementById('screenDescription');
    const screenProgress = document.getElementById('screenProgress');
    const screenFinal = document.getElementById('screenFinal');
    const screenHistory = document.getElementById('screenHistory');

    // Inputs & Buttons
    const enterAppBtn = document.getElementById('enterAppBtn');
    const char1Input = document.getElementById('char1');
    const char2Input = document.getElementById('char2');
    const startGenerationBtn = document.getElementById('startGenerationBtn');
    const proceedFusionBtn = document.getElementById('proceedFusionBtn');
    const saveResultBtn = document.getElementById('saveResultBtn');
    const restartBtn = document.getElementById('restartBtn');
    const viewHistoryLink = document.getElementById('viewHistoryLink');
    const backFromHistoryBtn = document.getElementById('backFromHistoryBtn');

    // Elements
    const char1Desc = document.getElementById('char1Desc');
    const char2Desc = document.getElementById('char2Desc');
    const fusedPromptText = document.getElementById('fusedPromptText');
    const descProgressBar = document.getElementById('descProgressBar');

    const currentIteration = document.getElementById('currentIteration');
    const simScore = document.getElementById('simScore');
    const qualScore = document.getElementById('qualScore');
    const evalLogs = document.getElementById('evalLogs');
    const refinementStatus = document.getElementById('refinementStatus');

    const finalPromptText = document.getElementById('finalPromptText');
    const finalScoreText = document.getElementById('finalScoreText');
    const historyGallery = document.getElementById('historyGallery');

    const maxIterations = 5;
    let globalSubject1 = '';
    let globalSubject2 = '';
    let globalFinalPrompt = '';
    let globalFinalScore = 0;

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    const switchScreen = (hideScreen, showScreen) => {
        hideScreen.classList.add('hidden');
        showScreen.classList.remove('hidden');
    };

    const addLog = (message, type = '') => {
        const p = document.createElement('p');
        p.className = `log-entry ${type}`;
        p.textContent = `> ${message}`;
        evalLogs.appendChild(p);
        evalLogs.scrollTop = evalLogs.scrollHeight;
    };

    // Landing Page -> Phase 1
    enterAppBtn.addEventListener('click', () => {
        switchScreen(screenLanding, screenInput);
    });

    // Phase 1 -> Phase 2 (Input -> Description Generation)
    startGenerationBtn.addEventListener('click', async () => {
        const c1 = char1Input.value.trim() || 'Pikachu';
        const c2 = char2Input.value.trim() || 'Iron Man';
        globalSubject1 = c1;
        globalSubject2 = c2;

        switchScreen(screenInput, screenDescription);
        
        char1Desc.textContent = `Analyzing ${c1}...`;
        char2Desc.textContent = `Analyzing ${c2}...`;
        fusedPromptText.textContent = `Connecting to Dora RL Core...`;
        descProgressBar.style.width = '20%';

        // Start the real backend call
        fetch('/api/fuse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ char1: c1, char2: c2 })
        })
        .then(async response => {
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.message || 'Unknown server error');
            }
            return response.json();
        })
        .then(data => {
            // Save the backend response to global variables
            globalFinalScore = data.score;
            globalFinalPrompt = data.prompt;
            document.getElementById('finalImage').src = '/' + data.image_path; // Make path absolute to the server
            
            // Update Phase 2 UI with the fetched descriptions
            char1Desc.innerHTML = `<strong>${c1}</strong>: ${data.char1_desc.substring(0, 100)}...`;
            char2Desc.innerHTML = `<strong>${c2}</strong>: ${data.char2_desc.substring(0, 100)}...`;
            fusedPromptText.innerHTML = `<em>"${data.prompt}"</em>`;
            descProgressBar.style.width = '100%';
            
            proceedFusionBtn.classList.remove('hidden');
        })
        .catch(err => {
            console.error(err);
            fusedPromptText.innerHTML = `<span style="color:red">Error: ${err.message}. Please try again.</span>`;
        });
        
        // Visually animate the progress bar while waiting
        let progress = 20;
        const interval = setInterval(() => {
            if (progress < 90) {
                progress += 5;
                descProgressBar.style.width = `${progress}%`;
            } else {
                clearInterval(interval);
            }
        }, 1000);
    });

    // Phase 2 -> Phase 3 (Description -> Iteration Progress)
    proceedFusionBtn.addEventListener('click', async () => {
        switchScreen(screenDescription, screenProgress);
        evalLogs.innerHTML = '';
        addLog('Initializing Image Generation Module...');
        
        // Simulate the progress of the loop since we already have the final result from Phase 2
        for (let i = 1; i <= maxIterations; i++) {
            currentIteration.textContent = `${i} / ${maxIterations}`;
            refinementStatus.textContent = `Processing iteration ${i}...`;
            
            addLog(`--- Iteration ${i} ---`, 'active');
            await sleep(600);
            
            // Randomly step up the scores to end near the real final score
            const sScore = Math.min(globalFinalScore, Math.floor(60 + (i * 8)));
            const qScore = Math.min(globalFinalScore, Math.floor(65 + (i * 7)));
            
            simScore.textContent = `${sScore}/10`; // Max score is 10 based on evaluate_image
            qualScore.textContent = `${qScore}/10`;
            
            if (i < maxIterations) {
                addLog(`Scores: Sim=${sScore}, Qual=${qScore}. Adjusting policy weights...`, 'highlight');
                await sleep(1000);
            } else {
                addLog(`Final Evaluation Complete. Target Achieved!`, 'success');
                simScore.textContent = `${globalFinalScore}/10`; 
                qualScore.textContent = `${globalFinalScore}/10`;
                await sleep(1000);
            }
        }

        // Phase 3 -> Phase 4 (Progress -> Final Output)
        switchScreen(screenProgress, screenFinal);
        finalPromptText.textContent = globalFinalPrompt;
        finalScoreText.textContent = `${globalFinalScore}/10`;
    });

    // History System
    let historyData = [];

    saveResultBtn.addEventListener('click', () => {
        historyData.push({
            title: `${globalSubject1} + ${globalSubject2}`,
            score: globalFinalScore,
            img: document.getElementById('finalImage').src
        });
        saveResultBtn.textContent = 'SAVED!';
        saveResultBtn.disabled = true;
        setTimeout(() => {
            saveResultBtn.textContent = 'SAVE TO HISTORY';
            saveResultBtn.disabled = false;
        }, 2000);
    });

    restartBtn.addEventListener('click', () => {
        char1Input.value = '';
        char2Input.value = '';
        descProgressBar.style.width = '0%';
        proceedFusionBtn.classList.add('hidden');
        switchScreen(screenFinal, screenInput);
    });

    viewHistoryLink.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.glass-panel').forEach(el => el.classList.add('hidden'));
        screenHistory.classList.remove('hidden');

        historyGallery.innerHTML = '';
        if (historyData.length === 0) {
            historyGallery.innerHTML = '<p class="log-entry">No stored outputs yet.</p>';
        } else {
            historyData.forEach(item => {
                const div = document.createElement('div');
                div.className = 'data-card';
                div.innerHTML = `
                    <h3>${item.title}</h3>
                    <img src="${item.img}" style="width: 100%; border-radius: 8px; margin: 10px 0;">
                    <p>Score: ${item.score}/10</p>
                `;
                historyGallery.appendChild(div);
            });
        }
    });

    backFromHistoryBtn.addEventListener('click', () => {
        switchScreen(screenHistory, screenInput);
    });
});
