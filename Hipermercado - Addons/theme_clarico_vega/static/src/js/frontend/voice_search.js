import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.VoiceSearch = publicWidget.Widget.extend({
    selector: '#voiceSearchBtn',

    events: {
        'click': '_onClickVoiceSearch',
    },

    _onClickVoiceSearch: function () {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Voice search is not supported in this browser.");
            return;
        }
        // Get website language
        let websiteLang = document.documentElement.getAttribute("lang") || "en-US";
        let langCode = websiteLang.replace("_", "-");

        const recognition = new webkitSpeechRecognition();
        recognition.lang = langCode;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        // --- ADD FULL PAGE LOADER ---
        let overlay = document.createElement("div");
        overlay.className = "voice-search-overlay";
        overlay.innerHTML = `
            <div class="voice-search-spinner"></div>
            <div>Listening...</div>
        `;
        document.body.appendChild(overlay);

        recognition.start();

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;

            // Remove overlay
            let overlay = document.querySelector(".voice-search-overlay");
            if (overlay) overlay.remove();

            let input = document.querySelector("input[name='search']");
            if (input) {
                input.value = transcript;
                input.closest("form.o_searchbar_form").submit();
            }
        };

        recognition.onerror = function (event) {
            console.error("Voice recognition error:", event);

            // Remove overlay
            let overlay = document.querySelector(".voice-search-overlay");
            if (overlay) overlay.remove();
        };

        recognition.onend = function () {
            // Remove overlay if still visible
            let overlay = document.querySelector(".voice-search-overlay");
            if (overlay) overlay.remove();
        };
    },
});
