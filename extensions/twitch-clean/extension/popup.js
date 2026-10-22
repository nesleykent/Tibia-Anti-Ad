// Twitch Clean popup: turns the Tibia filter (tibia-filter.js) on or off.
// The setting is stored as {tibiaFilter: boolean}, on by default.
const api = globalThis.browser || globalThis.chrome;
const box = document.getElementById('tibia');
const status = document.getElementById('status');

const show = enabled => {
    box.checked = enabled;
    status.textContent = enabled ? 'Ligado: recarregue o diretório Tibia se já estiver aberto.' : 'Desligado: todas as lives aparecem.';
};

api.storage.local.get({ tibiaFilter: true }).then(({ tibiaFilter }) => show(tibiaFilter));
box.addEventListener('change', () => api.storage.local.set({ tibiaFilter: box.checked }).then(() => show(box.checked)));
