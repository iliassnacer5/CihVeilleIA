/**
 * CIH Veille IA — PDF Export Utility
 *
 * Generates branded PDF reports from document data.
 * Uses the browser's built-in print functionality for maximum compatibility.
 */

interface ExportDocumentData {
    title: string
    source: string
    date: string
    theme: string
    confidence: number
    summary: string
    content: string
    entities?: string[]
    url?: string
}

/**
 * Exports a document as a branded CIH PDF report.
 * Opens a new window with styled HTML and triggers the print dialog.
 */
export function exportDocumentAsPDF(doc: ExportDocumentData): void {
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
        alert('Impossible d\'ouvrir la fenêtre d\'impression. Vérifiez les popups bloqués.')
        return
    }

    const formattedDate = new Date(doc.date).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    })

    const today = new Date().toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    })

    const entitiesHtml = doc.entities?.length
        ? `
    <div class="section">
      <h2>Entités Détectées</h2>
      <div class="entities">
        ${doc.entities.map((e) => `<span class="entity">${e}</span>`).join('')}
      </div>
    </div>`
        : ''

    const html = `
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>${doc.title} — Rapport CIH Veille IA</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Inter', -apple-system, sans-serif;
      color: #1a2332;
      line-height: 1.7;
      padding: 0;
    }

    .page {
      max-width: 800px;
      margin: 0 auto;
      padding: 48px;
    }

    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding-bottom: 24px;
      border-bottom: 3px solid #1a3a6b;
      margin-bottom: 32px;
    }
    .header-logo {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header-logo .dot {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #1a3a6b, #d63333);
      border-radius: 10px;
    }
    .header-logo h1 {
      font-size: 20px;
      font-weight: 700;
      color: #1a3a6b;
    }
    .header-logo p {
      font-size: 11px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 2px;
    }
    .header-date {
      text-align: right;
      font-size: 11px;
      color: #6b7280;
    }
    .header-date .label {
      font-weight: 600;
      color: #1a3a6b;
    }

    /* Title */
    .doc-title {
      font-size: 26px;
      font-weight: 700;
      color: #1a3a6b;
      margin-bottom: 16px;
      line-height: 1.3;
    }

    /* Metadata */
    .meta {
      display: flex;
      gap: 24px;
      align-items: center;
      margin-bottom: 32px;
      flex-wrap: wrap;
    }
    .meta-item {
      font-size: 12px;
      color: #6b7280;
    }
    .meta-item strong {
      color: #1a2332;
    }
    .badge {
      display: inline-block;
      background: #eef2ff;
      color: #1a3a6b;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
    }
    .confidence-bar {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .confidence-bar .bar {
      width: 80px;
      height: 6px;
      background: #e5e7eb;
      border-radius: 6px;
      overflow: hidden;
    }
    .confidence-bar .fill {
      height: 100%;
      background: linear-gradient(90deg, #1a3a6b, #d63333);
      border-radius: 6px;
    }

    /* Sections */
    .section {
      margin-bottom: 28px;
    }
    .section h2 {
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #1a3a6b;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #e5e7eb;
    }
    .section p {
      font-size: 13px;
      color: #374151;
      white-space: pre-wrap;
    }

    /* Entities */
    .entities {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .entity {
      background: #f3f4f6;
      color: #374151;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
    }

    /* Footer */
    .footer {
      margin-top: 48px;
      padding-top: 16px;
      border-top: 2px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: #9ca3af;
    }

    /* Print */
    @media print {
      body { padding: 0; }
      .page { padding: 32px; max-width: none; }
      @page { margin: 1cm; size: A4; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div class="header-logo">
        <div class="dot"></div>
        <div>
          <h1>CIH Veille IA</h1>
          <p>Rapport de veille stratégique</p>
        </div>
      </div>
      <div class="header-date">
        <p class="label">Généré le</p>
        <p>${today}</p>
      </div>
    </div>

    <h1 class="doc-title">${doc.title}</h1>

    <div class="meta">
      <div class="meta-item"><strong>Source:</strong> ${doc.source}</div>
      <div class="meta-item"><strong>Date:</strong> ${formattedDate}</div>
      <span class="badge">${doc.theme}</span>
      <div class="confidence-bar">
        <span class="meta-item"><strong>Confiance IA:</strong></span>
        <div class="bar">
          <div class="fill" style="width: ${doc.confidence}%"></div>
        </div>
        <span class="meta-item">${doc.confidence}%</span>
      </div>
    </div>

    <div class="section">
      <h2>Synthèse</h2>
      <p>${doc.summary}</p>
    </div>

    ${entitiesHtml}

    <div class="section">
      <h2>Contenu Intégral</h2>
      <p>${doc.content}</p>
    </div>

    ${doc.url ? `
    <div class="section">
      <h2>Source Originale</h2>
      <p><a href="${doc.url}" style="color: #1a3a6b;">${doc.url}</a></p>
    </div>` : ''}

    <div class="footer">
      <span>CIH Veille IA — Intelligence Bancaire Automatisée</span>
      <span>Document confidentiel — CIH Bank © ${new Date().getFullYear()}</span>
    </div>
  </div>

  <script>
    window.onload = function() {
      window.print();
    };
  </script>
</body>
</html>`

    printWindow.document.write(html)
    printWindow.document.close()
}
