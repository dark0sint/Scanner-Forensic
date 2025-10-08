document.getElementById('scanForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const evidence = document.getElementById('evidence').value;
    if (!evidence) return alert('Please enter evidence');

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ evidence: evidence })
        });
        const result = await response.json();

        if (response.ok) {
            displayResults(result);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    const profileDiv = document.getElementById('profile');
    const matchDiv = document.getElementById('match');

    profileDiv.innerHTML = `
        <h5>Input Profile:</h5>
        <p><strong>Hash:</strong> ${result.input_hash}</p>
        <p><strong>Profile:</strong> ${result.input_profile}</p>
        <p><strong>Keywords:</strong> ${result.input_keywords}</p>
    `;

    if (result.score === 100) {
        matchDiv.innerHTML = `
            <h5>Match: Exact Hit (100%)</h5>
            <p><strong>Description:</strong> ${result.match[3]}</p>
            <p class="match-high">Full match found in database!</p>
        `;
    } else if (result.score > 50) {
        matchDiv.innerHTML = `
            <h5>Match: Partial (${result.score.toFixed(1)}%)</h5>
            <p><strong>Best Match Description:</strong> ${result.match ? result.match[1] : 'None'}</p>
            <p class="match-low">Possible similarity detected.</p>
        `;
    } else {
        matchDiv.innerHTML = `
            <h5>Match: No Significant Match (${result.score.toFixed(1)}%)</h5>
            <p class="match-none">No matches found in database.</p>
        `;
    }

    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}
