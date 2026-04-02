async function callEndpoint(endpoint) {
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        document.getElementById('response').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        document.getElementById('response').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}