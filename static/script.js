function speak(text) {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    synth.speak(utter);
}

function startListening() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    speak("What should I search on Flipkart?");
    recognition.start();

    recognition.onresult = function(event) {
        const query = event.results[0][0].transcript;
        speak("Searching for " + query);
        fetchResults(query);
    };

    recognition.onerror = function(event) {
        speak("Sorry, I couldn't hear you properly.");
    };
}

function fetchResults(query) {
    fetch("/process", {
        method: "POST",
        body: JSON.stringify({ query: query }),
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('results');
        container.innerHTML = "";

        if (data.error) {
            speak("There was an error getting product details.");
            return;
        }

        // Display top 3 affordable products
        let html = "<h3>Top Affordable Products</h3><ul>";
        data.products.forEach(p => {
            html += `<li>
                <img src="${p.Image}" width="100" />
                <strong>${p.Name}</strong><br>
                ₹${p.Price} | ⭐ ${p.Rating}
            </li>`;
        });
        html += "</ul>";
        container.innerHTML = html;

        // Speak best product
        const best = data.best_product;
        speak(`The best product is ${best.Name}, priced at ₹${parseInt(best.Price)} with a rating of ${best.Rating}.`);
        window.open(best.Link, "_blank");
    });
}
