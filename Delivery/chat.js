const chatBox = document.getElementById("chatBox");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");

function addMessage(text, sender="bot") {

    const div = document.createElement("div");
    div.classList.add(sender, "msg");
    div.innerHTML = text;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

    // ✅ BOTÕES DENTRO DO CHAT
    div.querySelectorAll("button[data-message]").forEach(btn => {

        btn.addEventListener("click", () => {

            const message = btn.dataset.message;

            console.log("Botão clicado:", message); // DEBUG

            sendMessage(message);
        });

    });
}

function sendMessage(msg) {

    if (!msg) return;

    addMessage(msg, "user");

    fetch("/chat", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({message: msg})
    })
    .then(res => res.json())
    .then(data => {

        console.log("Resposta servidor:", data); // DEBUG

        if (data.replies) {

            data.replies.forEach(r => addMessage(r));

        } else if (data.reply) {

            addMessage(data.reply);
        }

    });

    messageInput.value = "";
}

chatForm.addEventListener("submit", e => {

    e.preventDefault();

    sendMessage(messageInput.value.trim());
});
// BOTÕES QUE JÁ EXISTEM NO HTML (ex: botão cardápio inicial)

document.querySelectorAll("button[data-message]").forEach(btn => {

    btn.addEventListener("click", () => {

        sendMessage(btn.dataset.message);

    });

});