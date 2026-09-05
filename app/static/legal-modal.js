async function showLegalDocument(path) {
  showModal('<div class="legal-loading">Загрузка документа…</div>');

  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error('Document unavailable');

    const html = await response.text();
    const documentPage = new DOMParser().parseFromString(html, 'text/html');
    const title = documentPage.querySelector('h1');
    const effectiveDate = documentPage.querySelector('header p');
    const article = documentPage.querySelector('article');

    if (!title || !article) throw new Error('Invalid document');

    content.innerHTML = `
      <div class="legal-modal-content">
        <span class="eyebrow">HAVA VPN · LEGAL</span>
        <h3>${title.textContent}</h3>
        ${effectiveDate ? `<p class="legal-date">${effectiveDate.textContent}</p>` : ''}
        <div class="legal-sections">${article.innerHTML}</div>
      </div>
    `;
  } catch (error) {
    content.innerHTML = `
      <div class="legal-modal-content">
        <h3>Документ недоступен</h3>
        <p>Не удалось загрузить текст. Попробуйте ещё раз.</p>
      </div>
    `;
  }
}

document.querySelectorAll('[data-legal]').forEach((button) => {
  button.addEventListener('click', () => showLegalDocument(button.dataset.legal));
});
