const healthEl = document.querySelector('#health');
const form = document.querySelector('#form');
const result = document.querySelector('#result');
const targets = document.querySelector('#targets');

function renderTargets(profiles) {
  targets.innerHTML = Object.entries(profiles).map(([key, profile]) => `
    <article class="target">
      <h3>${profile.label}</h3>
      <p><strong>Entrada:</strong> ${profile.input}</p>
      <p><strong>Gratuito:</strong> ${profile.free ? 'sim' : 'não'}</p>
      <p>${profile.notes}</p>
    </article>
  `).join('');
}

async function refreshHealth() {
  const response = await fetch('/api/health');
  const data = await response.json();
  healthEl.textContent = data.audiveris_available
    ? 'Audiveris encontrado: conversão real habilitada.'
    : 'Audiveris não encontrado: instale ou defina AUDIVERIS_CMD para habilitar conversão real.';
  healthEl.className = data.audiveris_available ? 'status ok' : 'status warn';
  renderTargets(data.targets || {});
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const files = Array.from(document.querySelector('#file').files);
  if (!files.length) return;
  result.textContent = 'Convertendo…';
  const body = new FormData();
  files.forEach((file) => body.append('files', file));
  const endpoint = files.length === 1 ? '/api/convert' : '/api/convert/batch';
  if (files.length === 1) {
    body.delete('files');
    body.append('file', files[0]);
  }
  const response = await fetch(endpoint, { method: 'POST', body });
  const data = await response.json();
  if (!response.ok) {
    result.textContent = data.detail || 'Erro desconhecido.';
    return;
  }
  const results = data.results || [data];
  result.textContent = results.map((item) => {
    const links = (item.outputs || []).map((url) => `${location.origin}${url}`).join('\n');
    return [
      `Arquivo: ${item.filename}`,
      `Status: ${item.status}`,
      `Mensagem: ${item.message}`,
      links ? `Saídas:\n${links}` : 'Saídas: nenhuma',
      item.log ? `Log:\n${item.log}` : '',
    ].filter(Boolean).join('\n');
  }).join('\n\n---\n\n');
});

refreshHealth().catch((error) => {
  healthEl.textContent = `Falha no healthcheck: ${error}`;
  healthEl.className = 'status warn';
});
