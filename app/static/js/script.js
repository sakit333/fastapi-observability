async function callEndpoint(endpoint) {
    const responseBox = document.getElementById("response");

    // If it's the home route → navigate normally
    if (endpoint === "/") {
        window.location.href = "/";
        return;
    }

    responseBox.innerHTML = "⏳ Loading...";
    const start = performance.now();

    try {
        const res = await fetch(endpoint);
        const duration = (performance.now() - start).toFixed(2);

        const contentType = res.headers.get("content-type");

        let content;

        if (contentType && contentType.includes("application/json")) {
            const data = await res.json();
            content = JSON.stringify(data, null, 2);
        } else {
            content = await res.text();
        }

        const statusClass = res.status >= 400 ? "error" : "success";

        responseBox.innerHTML = `
<span class="${statusClass}">Status: ${res.status}</span>
⏱ Time: ${duration} ms

<pre>${content}</pre>
        `;

    } catch (error) {
        responseBox.innerHTML = `
❌ Request Failed
<pre style="color:red;">${error.message}</pre>
        `;
    }
}