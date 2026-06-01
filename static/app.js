const healthEl = document.querySelector('#health');
const form = document.querySelector('#form');
const result = document.querySelector('#result');

async function refreshHealth() {
  const response = await fetch('/api/health');
  const data = await response.json();
  healthEl.textContent = data.audiveris_available
    ? 'Audiveris encontrado: conversão real habilitada.'
    : 'Audiveris não encontrado: instale para habilitar conversão real.';
  healthEl.className = data.audiveris_available ? 'status ok' : 'status warn';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = document.querySelector('#file').files[0];
  if (!file) return;
  result.textContent = 'Convertendo…';
  const body = new FormData();
  body.append('file', file);
  const response = await fetch('/api/convert', { method: 'POST', body });
  const data = await response.json();
  if (!response.ok) {
    result.textContent = data.detail || 'Erro desconhecido.';
    return;
  }
  const links = (data.outputs || []).map((url) => `${location.origin}${url}`).join('\n');
  result.textContent = [
    `Status: ${data.status}`,
    `Mensagem: ${data.message}`,
    links ? `Arquivos:\n${links}` : 'Arquivos: nenhum',
    data.log ? `Log:\n${data.log}` : '',
  ].filter(Boolean).join('\n\n');
});

refreshHealth().catch((error) => {
  healthEl.textContent = `Falha no healthcheck: ${error}`;
  healthEl.className = 'status warn';
});
