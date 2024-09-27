document.getElementById('reviewForm').addEventListener('submit', async function (e) {
    e.preventDefault(); // Prevent form from reloading the page

    const reviewText = document.getElementById('reviewText').value;

    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: reviewText })
    });

    const data = await response.json();

    document.getElementById('sentiment').textContent = data.sentiment;
    document.getElementById('comment').textContent = data.comment;
});
