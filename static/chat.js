/* Streaming AI chat client (progressive enhancement).
 *
 * The chat form works on its own with a plain POST. When JS is available we
 * intercept the submit, POST to the SSE endpoint (data-stream-url), and render
 * the tutor's reply token-by-token — with a typing indicator, auto-scroll, and
 * MathJax typeset once the reply is complete. If the network call fails, we let
 * the native form submit take over so the demo never hard-fails.
 */
(function () {
  var form = document.getElementById("chat-form");
  if (!form || !window.fetch || !window.ReadableStream) return;

  var streamUrl = form.getAttribute("data-stream-url");
  var input = document.getElementById("chat-input");
  var sendBtn = document.getElementById("chat-send");
  var scroll = document.getElementById("chat-scroll");
  var list = document.getElementById("chat-messages");
  var empty = document.getElementById("chat-empty");
  var selector = document.getElementById("assignment-select");
  var feedbackBox = document.getElementById("feedback-box");

  function scrollToBottom() {
    scroll.scrollTop = scroll.scrollHeight;
  }

  function addBubble(role, text) {
    var li = document.createElement("li");
    li.className = "chat-msg chat-msg--" + role;
    var who = document.createElement("span");
    who.className = "chat-msg__who";
    who.textContent = role === "user" ? "You" : "AI";
    var body = document.createElement("div");
    body.className = "chat-msg__text";
    if (text) body.textContent = text;
    li.appendChild(who);
    li.appendChild(body);
    list.appendChild(li);
    scrollToBottom();
    return body;
  }

  function showTyping(bubble) {
    var dots = document.createElement("span");
    dots.className = "typing-indicator";
    dots.innerHTML = "<span></span><span></span><span></span>";
    bubble.appendChild(dots);
    return dots;
  }

  function typeset(el) {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([el]).catch(function (err) {
        console.error(err);
      });
    }
  }

  form.addEventListener("submit", function (e) {
    var message = input.value.trim();
    if (!message) return; // let the browser's "required" handling deal with it
    e.preventDefault();

    if (empty) empty.hidden = true;

    var data = new FormData();
    data.append("message", message);
    if (selector && selector.value) data.append("assignment_id", selector.value);

    addBubble("user", message);
    var aiBubble = addBubble("ai", "");
    var typing = showTyping(aiBubble);
    var gotFirstToken = false;

    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;

    fetch(streamUrl, {
      method: "POST",
      body: data,
      headers: { Accept: "text/event-stream" },
      credentials: "same-origin",
    })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("stream unavailable");
        var reader = resp.body.getReader();
        var decoder = new TextDecoder();
        var buffer = "";

        function handleEvent(payload) {
          var evt;
          try {
            evt = JSON.parse(payload);
          } catch (err) {
            return;
          }
          if (evt.delta) {
            if (!gotFirstToken) {
              gotFirstToken = true;
              if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
            }
            aiBubble.textContent += evt.delta;
            scrollToBottom();
          } else if (evt.error) {
            if (typing && typing.parentNode) typing.parentNode.removeChild(typing);
            aiBubble.textContent = evt.error;
            aiBubble.classList.add("chat-msg__text--error");
          } else if (evt.done) {
            typeset(aiBubble);
            if (feedbackBox) feedbackBox.hidden = false;
            // The conversation now has a server-side session: subsequent sends
            // are follow-ups, so drop the assignment picker.
            if (selector) selector.hidden = true;
            scrollToBottom();
          }
        }

        function pump() {
          return reader.read().then(function (result) {
            if (result.done) return;
            buffer += decoder.decode(result.value, { stream: true });
            var parts = buffer.split("\n\n");
            buffer = parts.pop(); // keep the trailing incomplete event
            parts.forEach(function (chunk) {
              var line = chunk.trim();
              if (line.indexOf("data:") === 0) {
                handleEvent(line.slice(5).trim());
              }
            });
            return pump();
          });
        }

        return pump();
      })
      .catch(function (err) {
        console.error(err);
        // Network/stream failure: fall back to the plain form submit so the
        // student still gets a reply.
        input.value = message;
        input.disabled = false;
        form.submit();
      })
      .finally(function () {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
      });
  });
})();
